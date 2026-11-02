"""
SpamGuard AI - User Account Authentication Service
Provides password hashing, account creation, credential verification,
and secure signed token generation & verification using itsdangerous.
"""

import os
import re
from datetime import datetime, timezone
from functools import wraps
from typing import Optional, Tuple, Dict, Any

from flask import current_app, request, session
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from database import db
from models import User

TOKEN_SALT = "spamguard-user-auth"
DEFAULT_EXPIRY = 86400        # 24 hours
REMEMBER_ME_EXPIRY = 2592000  # 30 days


def _get_serializer() -> URLSafeTimedSerializer:
    secret = current_app.config.get("SECRET_KEY", "dev-secret-key-spamguard")
    return URLSafeTimedSerializer(secret, salt=TOKEN_SALT)


class UserAuthService:
    """Authentication service for SpamGuard user accounts."""

    @staticmethod
    def register_user(name: str, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """Validate input and register a new user account."""
        name = (name or "").strip()
        email = (email or "").strip().lower()
        password = (password or "").strip()

        if not name or len(name) < 2:
            return None, "Please enter a valid full name (at least 2 characters)."

        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not email or not re.match(email_regex, email):
            return None, "Please enter a valid email address."

        if not password or len(password) < 6:
            return None, "Password must be at least 6 characters long."

        # Check for existing account
        existing = User.query.filter_by(email=email).first()
        if existing:
            if existing.password_hash:
                return None, "An account with this email already exists. Please sign in."
            else:
                # User exists from Google OAuth; attach password to allow local login as well
                existing.name = name or existing.name
                existing.set_password(password)
                existing.is_active = True
                db.session.commit()
                return existing, None

        # Create new user
        new_user = User(
            name=name,
            email=email,
            is_active=True,
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return new_user, None

    @staticmethod
    def authenticate_user(email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """Verify user credentials."""
        email = (email or "").strip().lower()
        password = (password or "").strip()

        if not email or not password:
            return None, "Email and password are required."

        user = User.query.filter_by(email=email).first()
        if not user or not user.password_hash:
            return None, "Invalid email or password. Please check your credentials."

        if not user.check_password(password):
            return None, "Invalid email or password. Please check your credentials."

        if not user.is_active:
            return None, "Your account has been deactivated. Please contact support."

        return user, None

    @staticmethod
    def create_token(user: User, remember_me: bool = False) -> str:
        """Create a cryptographically signed token containing user_id."""
        s = _get_serializer()
        payload = {
            "user_id": user.id,
            "email": user.email,
            "remember": remember_me,
        }
        return s.dumps(payload)

    @staticmethod
    def verify_token(token: str) -> Optional[User]:
        """Verify and decode a signed auth token."""
        if not token:
            return None
        s = _get_serializer()
        try:
            # Check payload without max_age first to inspect remember flag
            payload = s.loads(token, max_age=REMEMBER_ME_EXPIRY)
            user_id = payload.get("user_id")
            if not user_id:
                return None
            user = User.query.get(user_id)
            if user and user.is_active:
                return user
        except (SignatureExpired, BadSignature, Exception):
            return None
        return None

    @staticmethod
    def get_current_user() -> Optional[User]:
        """Extract user from Authorization header or session."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            user = UserAuthService.verify_token(token)
            if user:
                return user

        # Check session
        user_id = session.get("spamguard_user_id")
        if user_id:
            user = User.query.get(user_id)
            if user and user.is_active:
                return user

        return None


def login_required(f):
    """Decorator to protect routes requiring SpamGuard account authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = UserAuthService.get_current_user()
        if not user:
            return {
                "success": False,
                "message": "Authentication required. Please sign in to access this resource.",
                "data": None,
            }, 401
        return f(*args, **kwargs)
    return decorated_function

