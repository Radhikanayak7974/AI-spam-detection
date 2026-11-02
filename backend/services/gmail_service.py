"""
SpamGuard AI – Gmail API Service (Phase 3)
Builds authenticated Gmail API clients, fetches messages, extracts MIME bodies,
handles token refresh, pagination, and quota errors.
"""

import base64
import logging
import re
import time
from datetime import datetime, timezone
from email import message_from_bytes
from email.header import decode_header as _decode_header
from typing import Any, Dict, List, Optional, Tuple

from google.auth.exceptions import RefreshError, TransportError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from database import db
from models import OAuthToken

logger = logging.getLogger(__name__)

# Gmail API constants
GMAIL_API_SERVICE_NAME = "gmail"
GMAIL_API_VERSION = "v1"
MAX_RESULTS_PER_PAGE = 100
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 2


# ─────────────────────────────────────────────────────────────────────────────
# Header decoding helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_decode_header(raw: str) -> str:
    """Decode RFC-2047 encoded email headers to plain Unicode string."""
    if not raw:
        return ""
    try:
        parts = _decode_header(raw)
        decoded = []
        for part, enc in parts:
            if isinstance(part, bytes):
                decoded.append(part.decode(enc or "utf-8", errors="replace"))
            else:
                decoded.append(str(part))
        return " ".join(decoded).strip()
    except Exception:
        return str(raw)


def _parse_sender(raw_from: str) -> Tuple[str, str]:
    """
    Split 'Display Name <email@example.com>' into (name, email).
    Returns (raw_from, raw_from) if parsing fails.
    """
    if not raw_from:
        return "", ""
    match = re.match(r"^(.*?)\s*<([^>]+)>$", raw_from.strip())
    if match:
        name = match.group(1).strip().strip('"')
        addr = match.group(2).strip()
        return name or addr, addr
    if "@" in raw_from:
        return raw_from.strip(), raw_from.strip()
    return raw_from.strip(), ""


# ─────────────────────────────────────────────────────────────────────────────
# MIME body extraction
# ─────────────────────────────────────────────────────────────────────────────

def _decode_base64url(data: str) -> bytes:
    """Decode base64url-encoded Gmail message part data."""
    # Gmail uses URL-safe base64; pad to multiple of 4
    padded = data.replace("-", "+").replace("_", "/")
    padding = 4 - len(padded) % 4
    if padding != 4:
        padded += "=" * padding
    return base64.b64decode(padded)


def _strip_html(html: str) -> str:
    """Convert HTML to readable plain text by removing tags."""
    try:
        # Try using html.parser via stdlib
        from html.parser import HTMLParser

        class _Stripper(HTMLParser):
            def __init__(self):
                super().__init__()
                self.reset()
                self.fed = []
                self._skip = False

            def handle_starttag(self, tag, attrs):
                if tag.lower() in ("script", "style", "head"):
                    self._skip = True
                elif tag.lower() in ("br", "p", "div", "tr"):
                    self.fed.append("\n")

            def handle_endtag(self, tag):
                if tag.lower() in ("script", "style", "head"):
                    self._skip = False

            def handle_data(self, d):
                if not self._skip:
                    self.fed.append(d)

            def get_text(self):
                return "".join(self.fed)

        s = _Stripper()
        s.feed(html)
        text = s.get_text()
        # Collapse excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception:
        # Fallback: naive regex strip
        return re.sub(r"<[^>]+>", " ", html).strip()


def _extract_body_from_parts(parts: list, prefer_plain: bool = True) -> Tuple[str, str]:
    """
    Recursively walk Gmail message parts and return (plain_text, html_text).
    Prefers text/plain. Falls back to text/html converted to plain text.
    """
    plain = ""
    html = ""

    for part in parts:
        mime_type = part.get("mimeType", "")
        sub_parts = part.get("parts", [])
        body = part.get("body", {})
        data = body.get("data", "")

        if sub_parts:
            sub_plain, sub_html = _extract_body_from_parts(sub_parts, prefer_plain)
            if not plain:
                plain = sub_plain
            if not html:
                html = sub_html

        elif mime_type == "text/plain" and data:
            try:
                plain = _decode_base64url(data).decode("utf-8", errors="replace")
            except Exception as exc:
                logger.debug("Failed to decode text/plain part: %s", exc)

        elif mime_type == "text/html" and data:
            try:
                html = _decode_base64url(data).decode("utf-8", errors="replace")
            except Exception as exc:
                logger.debug("Failed to decode text/html part: %s", exc)

    return plain, html


def extract_body(payload: dict) -> Tuple[str, str]:
    """
    Extract (plain_text, html_text) from a Gmail message payload dict.
    Returns (plain_text_for_ml, raw_html).
    """
    parts = payload.get("parts", [])
    body_data = payload.get("body", {}).get("data", "")
    mime_type = payload.get("mimeType", "")

    plain, html = "", ""

    if parts:
        plain, html = _extract_body_from_parts(parts)
    elif body_data:
        try:
            raw = _decode_base64url(body_data).decode("utf-8", errors="replace")
            if "html" in mime_type.lower():
                html = raw
            else:
                plain = raw
        except Exception as exc:
            logger.debug("Failed to decode single-part body: %s", exc)

    # If we only have HTML, derive plain text from it
    if not plain and html:
        plain = _strip_html(html)

    return plain.strip(), html.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Credentials management
# ─────────────────────────────────────────────────────────────────────────────

def _build_credentials(token_record: OAuthToken) -> Optional[Credentials]:
    """Build a google.oauth2.credentials.Credentials object from a DB token record."""
    import os
    from services.oauth_service import GMAIL_SCOPES

    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        logger.error("GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set")
        return None

    expires = token_record.expires_at
    if expires and expires.tzinfo is not None:
        expires = expires.replace(tzinfo=None)

    creds = Credentials(
        token=token_record.access_token,
        refresh_token=token_record.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=GMAIL_SCOPES,
        expiry=expires,
    )
    return creds


def _refresh_and_persist(creds: Credentials, token_record: OAuthToken) -> bool:
    """Refresh expired credentials and persist new tokens to the database."""
    try:
        creds.refresh(Request())
        token_record.access_token = creds.token
        if creds.refresh_token:
            token_record.refresh_token = creds.refresh_token
        if creds.expiry:
            exp = creds.expiry
            if exp.tzinfo is not None:
                exp = exp.replace(tzinfo=None)
            token_record.expires_at = exp
        db.session.commit()
        logger.info("Access token refreshed for user_id=%s", token_record.user_id)
        return True
    except RefreshError as exc:
        logger.warning("Token refresh failed (revoked?): %s", exc)
        return False
    except Exception as exc:
        logger.error("Unexpected error during token refresh: %s", exc)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Gmail API client factory
# ─────────────────────────────────────────────────────────────────────────────

def get_gmail_service(user_id: int):
    """
    Build and return an authenticated Gmail API service resource.
    Refreshes the access token if it has expired.
    Returns (service, error_message).
    """
    token_record = (
        OAuthToken.query.filter_by(user_id=user_id)
        .order_by(OAuthToken.created_at.desc())
        .first()
    )
    if not token_record:
        return None, "No OAuth token found for this user. Please connect Gmail first."

    creds = _build_credentials(token_record)
    if creds is None:
        return None, "OAuth credentials are not configured in environment variables."

    # Refresh if expired
    if token_record.is_expired or not creds.valid:
        if not creds.refresh_token:
            return None, "Access token expired and no refresh token available. Please reconnect Gmail."
        if not _refresh_and_persist(creds, token_record):
            return None, "Failed to refresh access token. Please reconnect Gmail."

    try:
        service = build(
            GMAIL_API_SERVICE_NAME,
            GMAIL_API_VERSION,
            credentials=creds,
            cache_discovery=False,
        )
        return service, None
    except Exception as exc:
        logger.error("Failed to build Gmail service: %s", exc)
        return None, f"Failed to initialize Gmail client: {str(exc)}"


# ─────────────────────────────────────────────────────────────────────────────
# Message listing
# ─────────────────────────────────────────────────────────────────────────────

def list_message_ids(
    service,
    label_ids: List[str] = None,
    max_results: int = 500,
    page_token: str = None,
) -> Tuple[List[str], Optional[str], Optional[str]]:
    """
    List Gmail message IDs from INBOX.
    Returns (message_ids, next_page_token, error_message).
    """
    if label_ids is None:
        label_ids = ["INBOX"]

    try:
        params = {
            "userId": "me",
            "labelIds": label_ids,
            "maxResults": min(max_results, MAX_RESULTS_PER_PAGE),
        }
        if page_token:
            params["pageToken"] = page_token

        response = service.users().messages().list(**params).execute()
        messages = response.get("messages", [])
        ids = [m["id"] for m in messages]
        next_token = response.get("nextPageToken")
        return ids, next_token, None

    except HttpError as exc:
        logger.error("Gmail list messages HTTP error: %s", exc)
        if exc.resp.status == 429:
            return [], None, "Gmail API quota exceeded. Please wait and try again."
        if exc.resp.status in (401, 403):
            return [], None, "Gmail authorization error. Please reconnect your account."
        return [], None, f"Gmail API error: {exc.reason}"
    except TransportError as exc:
        return [], None, f"Network error contacting Gmail API: {str(exc)}"
    except Exception as exc:
        return [], None, f"Unexpected error listing Gmail messages: {str(exc)}"


# ─────────────────────────────────────────────────────────────────────────────
# Message detail fetching
# ─────────────────────────────────────────────────────────────────────────────

def get_message_detail(service, message_id: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Fetch full message detail for a single Gmail message ID.
    Returns (parsed_message_dict, error_message).
    """
    for attempt in range(RETRY_ATTEMPTS):
        try:
            raw = (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
            return _parse_message(raw), None

        except HttpError as exc:
            if exc.resp.status == 429:
                # Quota error — backoff
                wait = RETRY_DELAY_SECONDS * (attempt + 1)
                logger.warning("Gmail quota hit fetching %s, waiting %ss", message_id, wait)
                time.sleep(wait)
                continue
            if exc.resp.status == 404:
                return None, f"Message {message_id} not found"
            logger.error("HTTP error fetching message %s: %s", message_id, exc)
            return None, f"Gmail API error for message {message_id}: {exc.reason}"
        except TransportError as exc:
            if attempt < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_DELAY_SECONDS)
                continue
            return None, f"Network error fetching message {message_id}: {str(exc)}"
        except Exception as exc:
            logger.error("Unexpected error fetching message %s: %s", message_id, exc)
            return None, f"Error fetching message {message_id}: {str(exc)}"

    return None, f"Failed to fetch message {message_id} after {RETRY_ATTEMPTS} attempts"


def _parse_message(raw: dict) -> Dict[str, Any]:
    """
    Parse a raw Gmail API message dict into a clean structured dict.
    Extracts headers, body, labels, timestamps, etc.
    """
    headers = {
        h["name"].lower(): h["value"]
        for h in raw.get("payload", {}).get("headers", [])
    }

    raw_from = _safe_decode_header(headers.get("from", ""))
    sender_name, sender_email = _parse_sender(raw_from)
    subject = _safe_decode_header(headers.get("subject", "")) or "(no subject)"

    # Parse received date from internalDate (milliseconds UTC)
    internal_date_ms = int(raw.get("internalDate", 0))
    received_at = None
    if internal_date_ms:
        received_at = datetime.fromtimestamp(internal_date_ms / 1000, tz=timezone.utc)

    # Extract message body
    payload = raw.get("payload", {})
    body_plain, body_html = extract_body(payload)

    # Labels
    label_ids = raw.get("labelIds", [])
    is_read = "UNREAD" not in label_ids
    has_attachments = any(
        p.get("filename") and p.get("body", {}).get("attachmentId")
        for p in _flatten_parts(payload.get("parts", []))
    )

    return {
        "gmail_message_id": raw["id"],
        "thread_id": raw.get("threadId", ""),
        "subject": subject,
        "sender": sender_name,
        "sender_email": sender_email,
        "snippet": raw.get("snippet", "")[:512],
        "body_plain": body_plain,
        "body_html": body_html,
        "received_at": received_at,
        "is_read": is_read,
        "has_attachments": has_attachments,
        "labels": ",".join(label_ids),
    }


def _flatten_parts(parts: list) -> list:
    """Recursively flatten nested MIME parts into a flat list."""
    result = []
    for part in parts:
        result.append(part)
        sub = part.get("parts", [])
        if sub:
            result.extend(_flatten_parts(sub))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Gmail History API (incremental sync)
# ─────────────────────────────────────────────────────────────────────────────

def list_history(
    service,
    start_history_id: str,
    label_ids: List[str] = None,
) -> Tuple[List[str], Optional[str], Optional[str]]:
    """
    Use the Gmail History API to fetch message IDs added since start_history_id.
    Returns (new_message_ids, latest_history_id, error_message).
    """
    if label_ids is None:
        label_ids = ["INBOX"]

    new_ids = []
    latest_history_id = start_history_id

    try:
        params = {
            "userId": "me",
            "startHistoryId": start_history_id,
            "labelId": label_ids[0] if label_ids else "INBOX",
            "historyTypes": ["messageAdded"],
        }
        response = service.users().history().list(**params).execute()
        history_records = response.get("history", [])
        latest_history_id = response.get("historyId", start_history_id)

        for record in history_records:
            for added in record.get("messagesAdded", []):
                msg = added.get("message", {})
                msg_labels = msg.get("labelIds", [])
                if any(lbl in msg_labels for lbl in label_ids):
                    new_ids.append(msg["id"])

        return new_ids, latest_history_id, None

    except HttpError as exc:
        if exc.resp.status == 404:
            # historyId expired — caller should do a full sync
            return [], None, "HISTORY_EXPIRED"
        logger.error("Gmail history list error: %s", exc)
        return [], None, f"History API error: {exc.reason}"
    except Exception as exc:
        logger.error("Unexpected error in list_history: %s", exc)
        return [], None, f"History error: {str(exc)}"


def get_current_history_id(service) -> Optional[str]:
    """Fetch the current mailbox historyId for future incremental sync."""
    try:
        profile = service.users().getProfile(userId="me").execute()
        return str(profile.get("historyId", ""))
    except Exception as exc:
        logger.warning("Could not fetch historyId: %s", exc)
        return None

