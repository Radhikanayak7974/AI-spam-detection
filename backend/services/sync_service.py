"""
SpamGuard AI – Gmail Synchronization Service (Phase 3)
Orchestrates full and incremental Gmail inbox sync, duplicate prevention,
ML classification of each new email, and sync history recording.
"""

import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from database import db
from models import Email, OAuthToken, Prediction, SyncHistory, User
from services.gmail_service import (
    get_current_history_id,
    get_gmail_service,
    get_message_detail,
    list_history,
    list_message_ids,
)
from services.ml_service import MLService

logger = logging.getLogger(__name__)

# Per-user locks to prevent overlapping sync jobs
_sync_locks: Dict[int, threading.Lock] = {}
_sync_locks_mutex = threading.Lock()


def _get_user_lock(user_id: int) -> threading.Lock:
    with _sync_locks_mutex:
        if user_id not in _sync_locks:
            _sync_locks[user_id] = threading.Lock()
        return _sync_locks[user_id]


# ─────────────────────────────────────────────────────────────────────────────
# ML classification helper
# ─────────────────────────────────────────────────────────────────────────────

def _classify_email(email_text: str) -> Dict[str, Any]:
    """
    Run text through both ML models.
    Returns a dict with both model results and a final_label.
    """
    if not MLService.is_trained():
        MLService.load_models()

    lr_result = MLService.predict(email_text, model_name="logistic_regression")
    nb_result = MLService.predict(email_text, model_name="naive_bayes")

    lr_label = lr_result.get("label", "ham")
    nb_label = nb_result.get("label", "ham")

    if lr_label == "spam" and nb_label == "spam":
        final_label = "spam"
    elif lr_label == "ham" and nb_label == "ham":
        final_label = "ham"
    else:
        final_label = "review"

    return {
        "lr": lr_result,
        "nb": nb_result,
        "final_label": final_label,
    }


def _save_prediction(email_obj: Email, classification: Dict[str, Any]) -> None:
    """
    Save the combined prediction to the Prediction table.
    Stores both Logistic Regression and Naive Bayes metrics plus final classification.
    """
    if email_obj.prediction:
        return  # already classified

    lr = classification["lr"]
    nb = classification["nb"]
    final_label = classification["final_label"]

    signals = lr.get("top_signals", [])

    model_breakdown = {
        "final_label": final_label,
        "logistic_regression": {
            "prediction": lr.get("label", "ham").upper(),
            "confidence": round(lr.get("confidence", 0.0), 4),
            "spam_probability": round(lr.get("spam_probability", 0.0), 4),
        },
        "naive_bayes": {
            "prediction": nb.get("label", "ham").upper(),
            "confidence": round(nb.get("confidence", 0.0), 4),
            "spam_probability": round(nb.get("spam_probability", 0.0), 4),
        },
        "top_signals": signals[:8],
    }

    from services.retraining_service import RetrainingService
    active_ver = RetrainingService.get_manifest().get("active_version", "v7")

    pred = Prediction(
        email_id=email_obj.id,
        model_name="ensemble_lr_nb",
        label=final_label,
        confidence=round(lr.get("confidence", 0.0), 4),
        spam_probability=round(lr.get("spam_probability", 0.0), 4),
        ham_probability=round(lr.get("ham_probability", 0.0), 4),
        features_used=json.dumps(model_breakdown),
        model_version=active_ver,
    )
    db.session.add(pred)


def _build_classification_detail(classification: Dict[str, Any]) -> Dict[str, Any]:
    """Return a serializable classification summary for API responses."""
    lr = classification["lr"]
    nb = classification["nb"]
    return {
        "logistic_regression": {
            "prediction": lr.get("label", "ham").upper(),
            "confidence": round(lr.get("confidence", 0.0), 4),
            "spam_probability": round(lr.get("spam_probability", 0.0), 4),
        },
        "naive_bayes": {
            "prediction": nb.get("label", "ham").upper(),
            "confidence": round(nb.get("confidence", 0.0), 4),
            "spam_probability": round(nb.get("spam_probability", 0.0), 4),
        },
        "final_prediction": classification["final_label"].upper(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Core sync logic
# ─────────────────────────────────────────────────────────────────────────────

def _process_message_ids(
    service,
    message_ids: List[str],
    user_id: int,
    sync_record: SyncHistory,
    app_context,
) -> Tuple[int, int, int]:
    """
    For each message_id: fetch detail, save Email, classify, save Prediction.
    Returns (fetched, classified, spam_count).
    Already-synced emails are skipped (duplicate prevention via gmail_message_id).
    """
    fetched = 0
    classified = 0
    spam_count = 0

    for msg_id in message_ids:
        try:
            # Skip if already in DB
            existing = Email.query.filter_by(gmail_message_id=msg_id).first()
            if existing:
                # Classify if prediction is missing
                if not existing.prediction:
                    text = existing.body_plain or existing.subject or ""
                    if text.strip():
                        clf = _classify_email(text)
                        _save_prediction(existing, clf)
                        db.session.commit()
                        classified += 1
                        if clf["final_label"] == "spam":
                            spam_count += 1
                continue

            # Fetch from Gmail API
            detail, err = get_message_detail(service, msg_id)
            if err or not detail:
                logger.warning("Skipping message %s: %s", msg_id, err)
                continue

            # Persist Email record
            email_obj = Email(
                user_id=user_id,
                gmail_message_id=detail["gmail_message_id"],
                thread_id=detail.get("thread_id"),
                subject=detail.get("subject"),
                sender=detail.get("sender"),
                sender_email=detail.get("sender_email"),
                snippet=detail.get("snippet"),
                body_plain=detail.get("body_plain"),
                body_html=detail.get("body_html"),
                received_at=detail.get("received_at"),
                is_read=detail.get("is_read", False),
                has_attachments=detail.get("has_attachments", False),
                labels=detail.get("labels"),
            )
            db.session.add(email_obj)
            db.session.flush()  # get email_obj.id before committing
            fetched += 1

            # ML classification
            text_for_ml = (detail.get("body_plain") or "").strip()
            if not text_for_ml:
                text_for_ml = (detail.get("subject") or "").strip()

            if text_for_ml:
                clf = _classify_email(text_for_ml)
                _save_prediction(email_obj, clf)
                classified += 1
                if clf["final_label"] == "spam":
                    spam_count += 1

            db.session.commit()

        except Exception as exc:
            db.session.rollback()
            logger.error("Error processing message %s: %s", msg_id, exc, exc_info=True)
            # Do NOT re-raise — continue with next message

    return fetched, classified, spam_count


# ─────────────────────────────────────────────────────────────────────────────
# Public sync entry points
# ─────────────────────────────────────────────────────────────────────────────

def run_full_sync(user_id: int, max_messages: int = 200) -> Dict[str, Any]:
    """
    Perform a full inbox synchronization for the given user.
    Safe to call from Flask request context or background scheduler.
    """
    lock = _get_user_lock(user_id)
    if not lock.acquire(blocking=False):
        return {
            "success": False,
            "message": "Sync already in progress for this account",
        }

    sync_record = SyncHistory(
        user_id=user_id,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.session.add(sync_record)
    db.session.commit()

    try:
        # Build Gmail service
        service, err = get_gmail_service(user_id)
        if err:
            sync_record.status = "failed"
            sync_record.error_message = err
            sync_record.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            return {"success": False, "message": err}

        # Fetch all message IDs (paginated)
        all_ids: List[str] = []
        page_token = None
        remaining = max_messages

        while remaining > 0:
            batch_size = min(remaining, 100)
            ids, next_token, err = list_message_ids(
                service, max_results=batch_size, page_token=page_token
            )
            if err:
                logger.warning("Error listing messages: %s", err)
                break
            all_ids.extend(ids)
            remaining -= len(ids)
            page_token = next_token
            if not next_token:
                break

        logger.info("Full sync: found %d message IDs for user %d", len(all_ids), user_id)

        # Process messages
        fetched, classified, spam = _process_message_ids(
            service, all_ids, user_id, sync_record, None
        )

        # Store current historyId for future incremental sync
        history_id = get_current_history_id(service)
        if history_id:
            token_record = (
                OAuthToken.query.filter_by(user_id=user_id)
                .order_by(OAuthToken.created_at.desc())
                .first()
            )
            if token_record:
                token_record.gmail_history_id = history_id
                db.session.commit()

        # Finalize sync record
        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - sync_record.started_at.replace(tzinfo=timezone.utc)).total_seconds()
        sync_record.status = "completed"
        sync_record.emails_fetched = fetched
        sync_record.emails_processed = classified
        sync_record.spam_detected = spam
        sync_record.completed_at = completed_at
        sync_record.duration_seconds = round(duration, 2)
        db.session.commit()

        return {
            "success": True,
            "message": f"Sync completed: {fetched} new emails, {classified} classified, {spam} spam detected",
            "sync": sync_record.to_dict(),
            "stats": {
                "emails_fetched": fetched,
                "emails_classified": classified,
                "spam_detected": spam,
                "history_id": history_id,
            },
        }

    except Exception as exc:
        logger.exception("Full sync failed for user %d: %s", user_id, exc)
        try:
            sync_record.status = "failed"
            sync_record.error_message = str(exc)[:1000]
            sync_record.completed_at = datetime.now(timezone.utc)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {"success": False, "message": f"Sync failed: {str(exc)}"}

    finally:
        lock.release()


def run_incremental_sync(user_id: int) -> Dict[str, Any]:
    """
    Perform incremental sync using Gmail History API.
    Falls back to a capped full sync if historyId has expired.
    """
    token_record = (
        OAuthToken.query.filter_by(user_id=user_id)
        .order_by(OAuthToken.created_at.desc())
        .first()
    )
    history_id = getattr(token_record, "gmail_history_id", None)

    if not history_id:
        logger.info("No historyId for user %d — running full sync", user_id)
        return run_full_sync(user_id, max_messages=100)

    lock = _get_user_lock(user_id)
    if not lock.acquire(blocking=False):
        return {"success": False, "message": "Sync already in progress for this account"}

    sync_record = SyncHistory(
        user_id=user_id,
        status="running",
        started_at=datetime.now(timezone.utc),
    )
    db.session.add(sync_record)
    db.session.commit()

    try:
        service, err = get_gmail_service(user_id)
        if err:
            sync_record.status = "failed"
            sync_record.error_message = err
            sync_record.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            return {"success": False, "message": err}

        new_ids, latest_history_id, err = list_history(service, history_id)
        if err == "HISTORY_EXPIRED":
            lock.release()
            logger.info("historyId expired for user %d — falling back to full sync", user_id)
            return run_full_sync(user_id, max_messages=100)
        if err:
            sync_record.status = "failed"
            sync_record.error_message = err
            sync_record.completed_at = datetime.now(timezone.utc)
            db.session.commit()
            return {"success": False, "message": err}

        fetched, classified, spam = 0, 0, 0
        if new_ids:
            fetched, classified, spam = _process_message_ids(
                service, new_ids, user_id, sync_record, None
            )

        # Update historyId
        if latest_history_id and token_record:
            token_record.gmail_history_id = latest_history_id
            db.session.commit()

        completed_at = datetime.now(timezone.utc)
        duration = (completed_at - sync_record.started_at.replace(tzinfo=timezone.utc)).total_seconds()
        sync_record.status = "completed"
        sync_record.emails_fetched = fetched
        sync_record.emails_processed = classified
        sync_record.spam_detected = spam
        sync_record.completed_at = completed_at
        sync_record.duration_seconds = round(duration, 2)
        db.session.commit()

        return {
            "success": True,
            "message": f"Incremental sync: {fetched} new, {classified} classified, {spam} spam",
            "sync": sync_record.to_dict(),
            "stats": {
                "emails_fetched": fetched,
                "emails_classified": classified,
                "spam_detected": spam,
            },
        }

    except Exception as exc:
        logger.exception("Incremental sync failed for user %d: %s", user_id, exc)
        try:
            sync_record.status = "failed"
            sync_record.error_message = str(exc)[:1000]
            sync_record.completed_at = datetime.now(timezone.utc)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return {"success": False, "message": f"Incremental sync failed: {str(exc)}"}

    finally:
        # Only release if we still hold it (full-sync fallback already releases)
        try:
            lock.release()
        except RuntimeError:
            pass


def get_sync_status(user_id: int) -> Dict[str, Any]:
    """Return the current sync status and last sync record for a user."""
    last_sync = (
        SyncHistory.query.filter_by(user_id=user_id)
        .order_by(SyncHistory.started_at.desc())
        .first()
    )
    token_record = (
        OAuthToken.query.filter_by(user_id=user_id)
        .order_by(OAuthToken.created_at.desc())
        .first()
    )

    is_running = False
    if last_sync and last_sync.status == "running":
        is_running = True

    return {
        "is_running": is_running,
        "last_sync": last_sync.to_dict() if last_sync else None,
        "has_history_id": bool(getattr(token_record, "gmail_history_id", None)),
    }

