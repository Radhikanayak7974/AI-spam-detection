"""
SpamGuard AI – Gmail Sync API Endpoints (Phase 3)
POST /api/gmail/sync           – trigger a manual full sync
POST /api/gmail/sync/start     – alias for full sync
POST /api/gmail/sync/stop      – placeholder (sync is not real-time streaming)
GET  /api/gmail/sync-status    – last sync record + running flag
GET  /api/gmail/messages       – paginated list of synced messages
"""

from flask import Blueprint, request
from database import db
from models import Email, OAuthToken, Prediction, SyncHistory, User
from services.sync_service import (
    get_sync_status,
    run_full_sync,
    run_incremental_sync,
)
from utils.response import error_response, paginated_response, success_response

gmail_bp = Blueprint("gmail", __name__)


def _get_active_user():
    """Return the most recently authenticated active user, or None."""
    token = (
        OAuthToken.query.join(User)
        .filter(User.is_active == True)  # noqa: E712
        .order_by(OAuthToken.created_at.desc())
        .first()
    )
    if token and token.user:
        return token.user
    return None


# ─────────────────────────────────────────────────────────────────────────────

@gmail_bp.route("/gmail/sync", methods=["POST"])
def gmail_sync():
    """Trigger a manual Gmail sync (full if no historyId, else incremental)."""
    user = _get_active_user()
    if not user:
        return error_response("Gmail account not connected. Please authenticate first.", 401)

    force_full = request.get_json(silent=True, force=True) or {}
    if force_full.get("full", False):
        result = run_full_sync(user.id)
    else:
        result = run_incremental_sync(user.id)

    if result.get("success"):
        return success_response(data=result, message=result.get("message", "Sync complete"))
    return error_response(result.get("message", "Sync failed"), status_code=500)


@gmail_bp.route("/gmail/sync/start", methods=["POST"])
def gmail_sync_start():
    """Alias: start a full inbox sync."""
    user = _get_active_user()
    if not user:
        return error_response("Gmail account not connected.", 401)

    result = run_full_sync(user.id)
    if result.get("success"):
        return success_response(data=result, message=result.get("message"))
    return error_response(result.get("message", "Sync failed"), 500)


@gmail_bp.route("/gmail/sync/stop", methods=["POST"])
def gmail_sync_stop():
    """
    Placeholder stop endpoint (sync is request-scoped, not a long-running stream).
    Returns the current sync status.
    """
    user = _get_active_user()
    if not user:
        return error_response("Gmail account not connected.", 401)

    status = get_sync_status(user.id)
    return success_response(
        data=status,
        message="Sync stop requested (sync will finish its current batch)",
    )


@gmail_bp.route("/gmail/sync-status", methods=["GET"])
def gmail_sync_status():
    """Return current sync status and last sync record."""
    user = _get_active_user()
    if not user:
        return success_response(
            data={"is_running": False, "last_sync": None, "connected": False},
            message="Gmail not connected",
        )

    status = get_sync_status(user.id)
    status["connected"] = True
    return success_response(data=status, message="Sync status retrieved")


@gmail_bp.route("/gmail/messages", methods=["GET"])
def gmail_messages():
    """Return paginated list of synced Gmail messages with predictions."""
    user = _get_active_user()
    if not user:
        return error_response("Gmail account not connected.", 401)

    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
    label_filter = request.args.get("label")  # "spam" | "ham" | "review" | None

    query = (
        db.session.query(Email)
        .filter_by(user_id=user.id)
        .order_by(Email.received_at.desc())
    )
    if label_filter:
        query = query.join(Prediction).filter(Prediction.label == label_filter)

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return paginated_response(
        items=[e.to_dict() for e in items],
        total=total,
        page=page,
        per_page=per_page,
        message="Messages retrieved",
    )

