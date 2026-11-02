"""Routes package."""
from .health import health_bp
from .auth import auth_bp
from .dashboard import dashboard_bp
from .emails import emails_bp
from .models import models_bp
from .gmail import gmail_bp
from .settings import settings_bp
from .feedback import feedback_bp
from .analytics import analytics_bp

__all__ = [
    "health_bp", "auth_bp", "dashboard_bp",
    "emails_bp", "models_bp", "gmail_bp", "settings_bp",
    "feedback_bp", "analytics_bp",
]

