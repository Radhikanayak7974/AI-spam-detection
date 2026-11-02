"""
SpamGuard AI – Sync Settings Endpoints (Phase 3)
GET /api/settings/sync  – retrieve sync settings for the connected user
PUT /api/settings/sync  – update sync settings (auto_sync, interval)
"""

import json
import logging

from flask import Blueprint, current_app, request
from database import db
from models import OAuthToken, User
from utils.response import error_response, success_response

logger = logging.getLogger(__name__)
settings_bp = Blueprint("settings", __name__)

# Sync settings are stored as JSON in OAuthToken.scope (piggybacked for simplicity)
# We add a dedicated helper so the logic is centralised.

_DEFAULT_SETTINGS = {
    "auto_sync_enabled": True,
    "sync_interval_minutes": 5,
}


def _get_active_token():
    return (
        OAuthToken.query.join(User)
        .filter(User.is_active == True)  # noqa: E712
        .order_by(OAuthToken.created_at.desc())
        .first()
    )


def _read_sync_settings(token: OAuthToken) -> dict:
    raw = getattr(token, "sync_settings", None) or "{}"
    try:
        stored = json.loads(raw) if raw else {}
    except Exception:
        stored = {}
    return {**_DEFAULT_SETTINGS, **stored}


def _write_sync_settings(token: OAuthToken, settings: dict):
    token.sync_settings = json.dumps(settings)
    db.session.commit()


@settings_bp.route("/settings/sync", methods=["GET"])
def get_sync_settings():
    """Retrieve auto-sync preferences for the currently connected user."""
    token = _get_active_token()
    if not token:
        return success_response(
            data=_DEFAULT_SETTINGS,
            message="Default settings (no account connected)",
        )
    settings = _read_sync_settings(token)
    from services.scheduler import get_scheduler_info, is_scheduler_running
    settings["scheduler_running"] = is_scheduler_running()
    settings["scheduler_info"] = get_scheduler_info()
    return success_response(data=settings, message="Sync settings retrieved")


@settings_bp.route("/settings/sync", methods=["PUT"])
def update_sync_settings():
    """Update auto-sync preferences and optionally reschedule background jobs."""
    token = _get_active_token()
    if not token:
        return error_response("No Gmail account connected", 401)

    body = request.get_json(silent=True, force=True) or {}
    current = _read_sync_settings(token)

    auto_sync = body.get("auto_sync_enabled", current["auto_sync_enabled"])
    interval = int(body.get("sync_interval_minutes", current["sync_interval_minutes"]))
    interval = max(1, min(interval, 60))

    new_settings = {
        "auto_sync_enabled": bool(auto_sync),
        "sync_interval_minutes": interval,
    }
    _write_sync_settings(token, new_settings)

    # Update background scheduler if running
    from services.scheduler import is_scheduler_running, update_sync_interval, shutdown_scheduler
    if new_settings["auto_sync_enabled"]:
        update_sync_interval(interval, current_app._get_current_object())
    else:
        # User turned off auto-sync; stop scheduler if it's only used for this
        if is_scheduler_running():
            shutdown_scheduler()

    from services.scheduler import get_scheduler_info
    new_settings["scheduler_running"] = is_scheduler_running()
    new_settings["scheduler_info"] = get_scheduler_info()

    return success_response(data=new_settings, message="Sync settings updated")

