"""
Health check endpoint.
GET /api/health
"""
import sys
import platform
from datetime import datetime, timezone
from flask import Blueprint
from utils.response import success_response

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Application health check."""
    return success_response(
        data={
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version,
            "platform": platform.system(),
            "phase": "Phase 1 – Foundation",
        },
        message="AI Email Spam Detection API is running",
    )
