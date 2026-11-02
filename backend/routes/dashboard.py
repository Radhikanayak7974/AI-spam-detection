"""
Dashboard statistics endpoint.
GET /api/dashboard/stats
GET /api/dashboard/recent-activity
"""
from flask import Blueprint
from database import db
from models import Email, OAuthToken, Prediction, SyncHistory, User
from utils.response import success_response, error_response

dashboard_bp = Blueprint("dashboard", __name__)


def _get_active_user():
    token = (
        OAuthToken.query.join(User)
        .filter(User.is_active == True)  # noqa: E712
        .order_by(OAuthToken.created_at.desc())
        .first()
    )
    return token.user if token else None


@dashboard_bp.route("/dashboard/stats", methods=["GET"])
def get_stats():
    """
    Return dashboard overview statistics from real database records.
    """
    try:
        total_emails = db.session.query(Email).count()
        spam_emails = (
            db.session.query(Prediction)
            .filter(Prediction.label == "spam")
            .count()
        )
        safe_emails = (
            db.session.query(Prediction)
            .filter(Prediction.label == "ham")
            .count()
        )
        review_emails = (
            db.session.query(Prediction)
            .filter(Prediction.label == "review")
            .count()
        )
        # Emails stored but not yet classified
        pending_review = (
            db.session.query(Email)
            .outerjoin(Prediction)
            .filter(Prediction.id.is_(None))
            .count()
        )

        # Last sync record
        last_sync = (
            db.session.query(SyncHistory)
            .order_by(SyncHistory.started_at.desc())
            .first()
        )

        # Gmail connection status
        from models import OAuthToken, User
        from services.oauth_service import OAuthService
        connection = OAuthService.get_current_connection()
        gmail_connected = connection.get("connected", False)

        from services.ml_service import MLService
        models_trained = MLService.is_trained()
        model_status_str = "trained" if models_trained else "not_trained"

        # Scheduler info
        from services.scheduler import get_scheduler_info, is_scheduler_running
        scheduler_running = is_scheduler_running()

        return success_response(
            data={
                "total_emails_scanned": total_emails,
                "spam_detected": spam_emails,
                "safe_emails": safe_emails,
                "review_required": review_emails,
                "pending_review": pending_review,
                "gmail_connected": gmail_connected,
                "connected_user": connection.get("user"),
                "last_sync": last_sync.to_dict() if last_sync else None,
                "model_status": {
                    "logistic_regression": model_status_str,
                    "naive_bayes": model_status_str,
                },
                "scheduler_running": scheduler_running,
            },
            message="Dashboard stats retrieved",
        )
    except Exception as exc:
        return error_response(
            message=f"Failed to retrieve dashboard stats: {str(exc)}",
            status_code=500,
        )


@dashboard_bp.route("/dashboard/recent-activity", methods=["GET"])
def get_recent_activity():
    """Return the most recent email predictions."""
    try:
        predictions = (
            db.session.query(Prediction)
            .join(Email)
            .order_by(Prediction.created_at.desc())
            .limit(10)
            .all()
        )
        activity = [
            {
                "email_id": p.email_id,
                "subject": p.email.subject if p.email else None,
                "sender": p.email.sender_email if p.email else None,
                "label": p.label,
                "confidence": round(p.confidence, 4),
                "model": p.model_name,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in predictions
        ]
        return success_response(data=activity, message="Recent activity retrieved")
    except Exception as exc:
        return error_response(
            message=f"Failed to retrieve recent activity: {str(exc)}",
            status_code=500,
        )
