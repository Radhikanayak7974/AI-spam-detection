"""
SpamGuard AI - Google OAuth 2.0 & Gmail Authentication Service
Handles Google OAuth authorization URL generation, authorization code exchange,
user profile fetching, token storage, and token refresh.
"""

import os
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple

from flask import current_app, session
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import requests

from database import db
from models import User, OAuthToken

logger = logging.getLogger(__name__)

# Cache for OAuth state to code_verifier mapping (for PKCE flows if used)
_oauth_state_store: Dict[str, str] = {}

# Scopes needed for Gmail reading and user identification
GMAIL_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


class OAuthService:
    """Service to manage Google OAuth 2.0 flows and Gmail API credentials."""

    @classmethod
    def get_client_config(cls) -> Optional[Dict[str, Any]]:
        """
        Build client configuration dictionary from environment variables
        or credentials.json if available.
        """
        client_id = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "").strip()
        redirect_uri = os.environ.get(
            "GOOGLE_REDIRECT_URI", "http://localhost:5000/api/auth/callback"
        ).strip()

        if client_id and client_secret:
            return {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri],
                }
            }

        # Check for credentials.json in backend/ or root
        cred_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "credentials.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "credentials.json"),
        ]
        for path in cred_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as exc:
                    logger.error("Failed to read %s: %s", path, exc)

        return None

    @classmethod
    def create_flow(cls, state: Optional[str] = None) -> Tuple[Optional[Flow], Optional[str]]:
        """
        Create and configure a Google OAuth Flow instance.
        Returns (Flow, error_message).
        """
        client_config = cls.get_client_config()
        if not client_config:
            return None, "Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env or provide credentials.json."

        redirect_uri = os.environ.get(
            "GOOGLE_REDIRECT_URI", "http://localhost:5000/api/auth/callback"
        ).strip()

        try:
            flow = Flow.from_client_config(
                client_config,
                scopes=GMAIL_SCOPES,
                state=state,
            )
            flow.redirect_uri = redirect_uri
            flow.autogenerate_code_verifier = False
            return flow, None
        except Exception as exc:
            logger.error("Failed to initialize Google OAuth Flow: %s", exc)
            return None, str(exc)

    @classmethod
    def get_authorization_url(cls) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Generate Google OAuth 2.0 authorization URL.
        Returns (auth_url, state, error_message).
        """
        # Allow insecure localhost redirect for development
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        flow, error = cls.create_flow()
        if error:
            return None, None, error

        flow.autogenerate_code_verifier = False
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="select_account consent",
        )
        if state and flow.code_verifier:
            _oauth_state_store[state] = flow.code_verifier
        return auth_url, state, None

    @classmethod
    def handle_callback(
        cls, code: str, state: str, redirect_uri: Optional[str] = None
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Exchange authorization code for tokens, fetch user profile, and save to DB.
        """
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        flow, error = cls.create_flow(state=state)
        if error:
            return None, error

        flow.autogenerate_code_verifier = False
        if redirect_uri:
            flow.redirect_uri = redirect_uri.strip()

        if state and state in _oauth_state_store:
            flow.code_verifier = _oauth_state_store.pop(state)

        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Fetch user profile using userinfo endpoint
            headers = {"Authorization": f"Bearer {credentials.token}"}
            userinfo_res = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers=headers,
                timeout=10,
            )
            if not userinfo_res.ok:
                return None, f"Failed to fetch Google user profile: {userinfo_res.text}"

            user_data = userinfo_res.json()
            email = user_data.get("email")
            google_id = user_data.get("sub")
            name = user_data.get("name")
            avatar_url = user_data.get("picture")

            if not email:
                return None, "No email address found in Google profile"

            # Check if user already exists
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    google_id=google_id,
                    name=name,
                    picture=avatar_url,
                    is_active=True,
                )
                db.session.add(user)
                db.session.flush()
            else:
                user.name = name or user.name
                user.picture = avatar_url or user.picture
                user.is_active = True

            # Save or update OAuthToken
            token = OAuthToken.query.filter_by(user_id=user.id).first()
            expires_at = None
            if credentials.expiry:
                expires_at = credentials.expiry
                if expires_at.tzinfo is not None:
                    expires_at = expires_at.replace(tzinfo=None)

            if not token:
                token = OAuthToken(
                    user_id=user.id,
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    token_type="Bearer",
                    scope=" ".join(credentials.scopes or GMAIL_SCOPES),
                    expires_at=expires_at,
                )
                db.session.add(token)
            else:
                token.access_token = credentials.token
                if credentials.refresh_token:
                    token.refresh_token = credentials.refresh_token
                token.scope = " ".join(credentials.scopes or GMAIL_SCOPES)
                token.expires_at = expires_at

            db.session.commit()

            return {
                "user": user.to_dict(),
                "connected": True,
            }, None

        except Exception as exc:
            db.session.rollback()
            logger.exception("OAuth callback processing error: %s", exc)
            return None, f"Failed to complete OAuth authorization: {str(exc)}"

    @classmethod
    def get_current_connection(cls) -> Dict[str, Any]:
        """Check active connected user in database."""
        token = OAuthToken.query.order_by(OAuthToken.created_at.desc()).first()
        if token and token.user and token.user.is_active:
            return {
                "connected": True,
                "provider": "gmail",
                "user": token.user.to_dict(),
                "expires_at": token.expires_at.isoformat() if token.expires_at else None,
                "message": f"Connected to {token.user.email}",
            }
        return {
            "connected": False,
            "provider": "gmail",
            "user": None,
            "message": "Gmail account is not connected. Configure credentials in .env to connect.",
        }

    @classmethod
    def logout(cls) -> bool:
        """Revoke or disconnect OAuth tokens."""
        try:
            tokens = OAuthToken.query.all()
            for t in tokens:
                db.session.delete(t)
            users = User.query.all()
            for u in users:
                u.is_active = False
            db.session.commit()
            return True
        except Exception as exc:
            db.session.rollback()
            logger.error("Logout error: %s", exc)
            return False

