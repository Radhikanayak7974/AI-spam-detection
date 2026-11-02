"""
SpamGuard AI - Feedback API Routes (Phase 4)
Handles user feedback submissions, corrections, approvals, and feedback statistics.
"""

from datetime import datetime, timezone
from flask import Blueprint, request
from database import db
from models import Feedback, Email, Prediction, User
from utils.response import success_response, error_response, paginated_response

feedback_bp = Blueprint("feedback", __name__)


def utcnow():
    return datetime.now(timezone.utc)


@feedback_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    """
    Submit or update user feedback on an email's spam/ham classification.
    Request Body:
        {
            "email_id": 123,
            "user_label": "spam" | "ham",
            "notes": "Optional feedback reason",
            "status": "approved" (default) | "pending"
        }
    """
    try:
        data = request.get_json(silent=True) or {}
        email_id = data.get("email_id")
        user_label = (data.get("user_label") or "").strip().lower()
        notes = data.get("notes", "").strip()
        status = data.get("status", "approved").strip().lower()

        if not email_id:
            return error_response("Field 'email_id' is required", status_code=400)

        if user_label not in ("spam", "ham"):
            return error_response("Field 'user_label' must be 'spam' or 'ham'", status_code=400)

        if status not in ("approved", "pending", "rejected"):
            status = "approved"

        # Check if email exists
        email = db.session.get(Email, email_id)
        if not email:
            return error_response(f"Email with id {email_id} not found", status_code=404)

        # Get existing prediction to record original model classification
        pred = email.prediction
        model_label = pred.label if pred else "unknown"
        is_correction = bool(model_label != "unknown" and user_label != model_label)

        # Check if feedback record already exists for this email (prevent duplicates)
        existing_fb = Feedback.query.filter_by(email_id=email_id).first()
        if existing_fb:
            existing_fb.user_label = user_label
            existing_fb.model_label = model_label
            existing_fb.is_correction = is_correction
            existing_fb.notes = notes
            existing_fb.status = status
            existing_fb.updated_at = utcnow()
            db.session.commit()
            return success_response(
                data=existing_fb.to_dict(),
                message="Feedback updated successfully",
            )

        # Create new feedback record
        feedback = Feedback(
            email_id=email_id,
            user_id=email.user_id,
            user_label=user_label,
            model_label=model_label,
            is_correction=is_correction,
            status=status,
            notes=notes,
            created_at=utcnow(),
            updated_at=utcnow(),
        )
        db.session.add(feedback)
        db.session.commit()

        return success_response(
            data=feedback.to_dict(),
            message="Feedback submitted successfully",
            status_code=201,
        )

    except Exception as exc:
        db.session.rollback()
        return error_response(f"Failed to submit feedback: {str(exc)}", status_code=500)


@feedback_bp.route("/feedback", methods=["GET"])
def list_feedback():
    """
    Retrieve paginated feedback records with filtering and search.
    Query params:
        page, per_page, search, status, label, correction_only, start_date, end_date
    """
    try:
        page = max(1, request.args.get("page", 1, type=int))
        per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
        search = (request.args.get("search") or "").strip()
        status_filter = (request.args.get("status") or "").strip().lower()
        label_filter = (request.args.get("label") or "").strip().lower()
        correction_only = request.args.get("correction_only", "").lower() in ("true", "1")
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        query = db.session.query(Feedback).join(Email, Feedback.email_id == Email.id)

        # Filter by search string across subject, sender, and notes
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                (Email.subject.ilike(search_pattern))
                | (Email.sender.ilike(search_pattern))
                | (Email.sender_email.ilike(search_pattern))
                | (Feedback.notes.ilike(search_pattern))
            )

        # Filter by status
        if status_filter and status_filter != "all":
            query = query.filter(Feedback.status == status_filter)

        # Filter by user label
        if label_filter and label_filter != "all":
            query = query.filter(Feedback.user_label == label_filter)

        # Filter corrections only
        if correction_only:
            query = query.filter(Feedback.is_correction == True)  # noqa: E712

        # Date filtering
        if start_date_str:
            try:
                start_dt = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
                query = query.filter(Feedback.created_at >= start_dt)
            except Exception:
                pass

        if end_date_str:
            try:
                end_dt = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))
                query = query.filter(Feedback.created_at <= end_dt)
            except Exception:
                pass

        query = query.order_by(Feedback.created_at.desc())
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        return paginated_response(
            items=[fb.to_dict() for fb in items],
            total=total,
            page=page,
            per_page=per_page,
            message="Feedback records retrieved successfully",
        )

    except Exception as exc:
        return error_response(f"Failed to list feedback: {str(exc)}", status_code=500)


@feedback_bp.route("/feedback/stats", methods=["GET"])
def get_feedback_stats():
    """Return summary statistics for user feedback."""
    try:
        total = Feedback.query.count()
        corrections = Feedback.query.filter_by(is_correction=True).count()
        approved = Feedback.query.filter_by(status="approved").count()
        pending = Feedback.query.filter_by(status="pending").count()
        rejected = Feedback.query.filter_by(status="rejected").count()

        agreement_rate = round(1.0 - (corrections / total), 4) if total > 0 else 1.0

        return success_response(
            data={
                "total_feedback": total,
                "corrections_count": corrections,
                "confirmations_count": total - corrections,
                "approved_count": approved,
                "pending_count": pending,
                "rejected_count": rejected,
                "agreement_rate": agreement_rate,
                "disagreement_rate": round(1.0 - agreement_rate, 4),
            },
            message="Feedback stats retrieved successfully",
        )
    except Exception as exc:
        return error_response(f"Failed to get feedback stats: {str(exc)}", status_code=500)


@feedback_bp.route("/feedback/<int:feedback_id>", methods=["PATCH"])
def update_feedback(feedback_id):
    """Update feedback status, notes, or corrected label."""
    try:
        fb = db.session.get(Feedback, feedback_id)
        if not fb:
            return error_response("Feedback record not found", status_code=404)

        data = request.get_json(silent=True) or {}
        if "status" in data:
            status = data["status"].strip().lower()
            if status in ("approved", "pending", "rejected"):
                fb.status = status

        if "user_label" in data:
            user_label = data["user_label"].strip().lower()
            if user_label in ("spam", "ham"):
                fb.user_label = user_label
                if fb.model_label:
                    fb.is_correction = bool(user_label != fb.model_label)

        if "notes" in data:
            fb.notes = data["notes"].strip()

        fb.updated_at = utcnow()
        db.session.commit()

        return success_response(data=fb.to_dict(), message="Feedback updated successfully")

    except Exception as exc:
        db.session.rollback()
        return error_response(f"Failed to update feedback: {str(exc)}", status_code=500)


@feedback_bp.route("/feedback/<int:feedback_id>", methods=["DELETE"])
def delete_feedback(feedback_id):
    """Delete a feedback record."""
    try:
        fb = db.session.get(Feedback, feedback_id)
        if not fb:
            return error_response("Feedback record not found", status_code=404)

        db.session.delete(fb)
        db.session.commit()
        return success_response(data={"id": feedback_id}, message="Feedback deleted successfully")

    except Exception as exc:
        db.session.rollback()
        return error_response(f"Failed to delete feedback: {str(exc)}", status_code=500)

