"""
SpamGuard AI - Authentication & Google OAuth 2.0 Endpoints
Phase 2: Google OAuth 2.0 Flow
"""

import os
import threading
from flask import Blueprint, request, redirect, current_app, session
from services.oauth_service import OAuthService
from services.auth_service import UserAuthService
from utils.response import success_response, error_response

auth_bp = Blueprint("auth", __name__)


# ─────────────────────────────────────────────────────────────────────────────
# SpamGuard User Account Authentication (Sign Up, Sign In, Sign Out, Me)
# ─────────────────────────────────────────────────────────────────────────────

@auth_bp.route("/auth/register", methods=["POST"])
@auth_bp.route("/auth/user/register", methods=["POST"])
def user_register():
    """Register a new SpamGuard user account with secure password hashing."""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "")
    email = data.get("email", "")
    password = data.get("password", "")

    user, err = UserAuthService.register_user(name=name, email=email, password=password)
    if err:
        return error_response(message=err, status_code=400)

    return success_response(
        data={"user": user.to_dict()},
        message="Account created successfully! Please sign in with your credentials.",
        status_code=201,
    )


@auth_bp.route("/auth/user/login", methods=["POST"])
def user_login_dedicated():
    """Sign in using SpamGuard email and password."""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "")
    password = data.get("password", "")
    remember = bool(data.get("remember", False))

    user, err = UserAuthService.authenticate_user(email=email, password=password)
    if err:
        return error_response(message=err, status_code=401)

    token = UserAuthService.create_token(user, remember_me=remember)
    session["spamguard_user_id"] = user.id

    return success_response(
        data={
            "token": token,
            "user": user.to_dict(),
        },
        message=f"Welcome back, {user.name or user.email}!",
    )


@auth_bp.route("/auth/user/me", methods=["GET"])
def user_me():
    """Return the currently authenticated SpamGuard user account."""
    user = UserAuthService.get_current_user()
    if not user:
        return success_response(
            data={"authenticated": False, "user": None},
            message="No active user session",
        )

    return success_response(
        data={"authenticated": True, "user": user.to_dict()},
        message="Active user session retrieved",
    )


@auth_bp.route("/auth/user/logout", methods=["POST"])
def user_logout():
    """Log out of SpamGuard user account."""
    session.pop("spamguard_user_id", None)
    return success_response(
        data={"authenticated": False},
        message="Signed out successfully.",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Google OAuth 2.0 Flow for Gmail Sync
# ─────────────────────────────────────────────────────────────────────────────


@auth_bp.route("/auth/status", methods=["GET"])
def auth_status():
    """Return current Gmail OAuth connection status from database."""
    try:
        status_info = OAuthService.get_current_connection()
        return success_response(
            data=status_info,
            message="Auth status retrieved",
        )
    except Exception as exc:
        return error_response(f"Failed to check auth status: {str(exc)}", status_code=500)


@auth_bp.route("/auth/login", methods=["GET", "POST"])
def auth_login():
    """
    Dual-mode endpoint:
    - POST: User Account Sign In with email & password.
    - GET:  Generate Google OAuth authorization URL for Gmail sync.
    """
    if request.method == "POST":
        return user_login_dedicated()

    try:
        auth_url, state, err = OAuthService.get_authorization_url()
        if err:
            return error_response(
                message=err,
                status_code=400,
                errors={"configured": False, "instructions": "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"},
            )

        # Store state in session if session available
        session["oauth_state"] = state

        should_redirect = request.args.get("redirect", "false").lower() == "true"
        if should_redirect:
            return redirect(auth_url)

        return success_response(
            data={
                "oauth_url": auth_url,
                "state": state,
                "configured": True,
            },
            message="OAuth authorization URL generated",
        )
    except Exception as exc:
        return error_response(f"OAuth initialization failed: {str(exc)}", status_code=500)


@auth_bp.route("/auth/callback", methods=["GET"])
@auth_bp.route("/auth/google/callback", methods=["GET"])
def auth_callback():
    """
    Google OAuth 2.0 redirect callback.
    Receives code & state from Google, exchanges for tokens, and redirects back to frontend.
    """
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")
    frontend_url = current_app.config.get("FRONTEND_URL", "http://localhost:5173")

    if error:
        return redirect(f"{frontend_url}/inbox?error={error}")

    if not code:
        return redirect(f"{frontend_url}/inbox?error=missing_code")

    # Pass the actual base URL so redirect_uri exactly matches the callback path Google used
    callback_uri = request.base_url
    data, err = OAuthService.handle_callback(code=code, state=state, redirect_uri=callback_uri)
    if err:
        return redirect(f"{frontend_url}/inbox?error={err}")

    # Auto-trigger full sync in background immediately after connecting
    user_info = data.get("user") if isinstance(data, dict) else None
    if user_info and user_info.get("id"):
        user_id = user_info["id"]
        app = current_app._get_current_object()

        def _bg_initial_sync():
            with app.app_context():
                try:
                    from services.sync_service import run_full_sync
                    current_app.logger.info("Starting initial background sync for user %s", user_id)
                    run_full_sync(user_id)
                except Exception as ex:
                    current_app.logger.error("Initial background sync failed: %s", ex)

        threading.Thread(target=_bg_initial_sync, daemon=True).start()

    return redirect(f"{frontend_url}/inbox?connected=true")


@auth_bp.route("/auth/logout", methods=["POST"])
def auth_logout():
    """
    Disconnect active Google OAuth account OR log out user account based on target.
    If body contains {"target": "user"}, logs out user account.
    Default: Disconnects Gmail OAuth.
    """
    data = request.get_json(silent=True) or {}
    if data.get("target") == "user":
        return user_logout()

    try:
        success = OAuthService.logout()
        return success_response(
            data={"connected": False},
            message="Logged out and disconnected successfully" if success else "Failed to disconnect",
        )
    except Exception as exc:
        return error_response(f"Logout failed: {str(exc)}", status_code=500)
