"""
Email routes.
GET /api/emails         – paginated list of all emails
GET /api/emails/<id>    – single email detail
GET /api/emails/spam    – paginated spam emails
GET /api/emails/safe    – paginated safe emails
"""
from flask import Blueprint, request
from database import db
from models import Email, Prediction
from utils.response import success_response, error_response, paginated_response

emails_bp = Blueprint("emails", __name__)


def _paginate_query(query):
    """Extract pagination params from request and apply them."""
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 20, type=int)))
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total, page, per_page


@emails_bp.route("/emails", methods=["GET"])
def get_emails():
    """Return a paginated list of all emails, optionally filtered by label."""
    try:
        label = request.args.get("label")
        query = db.session.query(Email)
        if label:
            query = query.join(Prediction).filter(Prediction.label == label)
        query = query.order_by(Email.received_at.desc())
        items, total, page, per_page = _paginate_query(query)
        return paginated_response(
            items=[e.to_dict() for e in items],
            total=total,
            page=page,
            per_page=per_page,
            message="Emails retrieved",
        )
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@emails_bp.route("/emails/<int:email_id>", methods=["GET"])
def get_email(email_id):
    """Return a single email with prediction details."""
    try:
        email = db.session.get(Email, email_id)
        if not email:
            return error_response(message="Email not found", status_code=404)
        return success_response(
            data=email.to_dict(include_body=True),
            message="Email retrieved",
        )
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@emails_bp.route("/emails/spam", methods=["GET"])
def get_spam_emails():
    """Return a paginated list of emails predicted as spam."""
    try:
        query = (
            db.session.query(Email)
            .join(Prediction)
            .filter(Prediction.label == "spam")
            .order_by(Email.received_at.desc())
        )
        items, total, page, per_page = _paginate_query(query)
        return paginated_response(
            items=[e.to_dict() for e in items],
            total=total,
            page=page,
            per_page=per_page,
            message="Spam emails retrieved",
        )
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@emails_bp.route("/emails/safe", methods=["GET"])
def get_safe_emails():
    """Return a paginated list of emails predicted as ham (safe)."""
    try:
        query = (
            db.session.query(Email)
            .join(Prediction)
            .filter(Prediction.label == "ham")
            .order_by(Email.received_at.desc())
        )
        items, total, page, per_page = _paginate_query(query)
        return paginated_response(
            items=[e.to_dict() for e in items],
            total=total,
            page=page,
            per_page=per_page,
            message="Safe emails retrieved",
        )
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)


@emails_bp.route("/emails/review", methods=["GET"])
def get_review_emails():
    """Return a paginated list of emails where models disagreed (review required)."""
    try:
        query = (
            db.session.query(Email)
            .join(Prediction)
            .filter(Prediction.label == "review")
            .order_by(Email.received_at.desc())
        )
        items, total, page, per_page = _paginate_query(query)
        return paginated_response(
            items=[e.to_dict() for e in items],
            total=total,
            page=page,
            per_page=per_page,
            message="Review required emails retrieved",
        )
    except Exception as exc:
        return error_response(message=str(exc), status_code=500)
