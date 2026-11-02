"""
SpamGuard AI - Advanced Analytics API Routes (Phase 4)
Provides real database analytics: date filters, trend charts, sender statistics,
top spam keywords, live vs test-set model comparisons, and monitoring metrics.
"""

from datetime import datetime, timedelta, timezone
import json
from collections import Counter
from flask import Blueprint, request
from sqlalchemy import func
from database import db
from models import Email, Prediction, Feedback
from services.ml_service import MLService
from utils.response import success_response, error_response

analytics_bp = Blueprint("analytics", __name__)


def utcnow():
    return datetime.now(timezone.utc)


def parse_date_filter():
    """
    Parse 'filter' query parameter into (start_datetime, end_datetime).
    Options: 'today', '7d', '30d', '90d', 'all', 'custom'
    """
    filter_type = request.args.get("filter", "30d").lower()
    now = utcnow()

    if filter_type == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now, filter_type
    elif filter_type == "7d":
        return now - timedelta(days=7), now, filter_type
    elif filter_type == "30d":
        return now - timedelta(days=30), now, filter_type
    elif filter_type == "90d":
        return now - timedelta(days=90), now, filter_type
    elif filter_type == "custom":
        start_str = request.args.get("start_date")
        end_str = request.args.get("end_date")
        start = None
        end = now
        if start_str:
            try:
                start = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            except Exception:
                pass
        if end_str:
            try:
                end = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            except Exception:
                pass
        return start, end, "custom"
    else:  # "all"
        return None, None, "all"


@analytics_bp.route("/analytics/overview", methods=["GET"])
def get_analytics_overview():
    """Return aggregated KPI metrics for the specified date range."""
    try:
        start_dt, end_dt, filter_type = parse_date_filter()

        query_email = db.session.query(Email)
        query_pred = db.session.query(Prediction)

        if start_dt:
            query_email = query_email.filter(Email.received_at >= start_dt)
            query_pred = query_pred.filter(Prediction.created_at >= start_dt)
        if end_dt:
            query_email = query_email.filter(Email.received_at <= end_dt)
            query_pred = query_pred.filter(Prediction.created_at <= end_dt)

        total_emails = query_email.count()
        total_predictions = query_pred.count()

        spam_count = query_pred.filter(Prediction.label == "spam").count()
        safe_count = query_pred.filter(Prediction.label == "ham").count()
        review_count = query_pred.filter(Prediction.label == "review").count()

        spam_pct = round((spam_count / total_predictions * 100), 1) if total_predictions > 0 else 0.0
        safe_pct = round((safe_count / total_predictions * 100), 1) if total_predictions > 0 else 0.0
        review_pct = round((review_count / total_predictions * 100), 1) if total_predictions > 0 else 0.0

        # Calculate live disagreement rate from details JSON
        disagreements = 0
        predictions_sample = query_pred.all()
        for p in predictions_sample:
            if p.features_used:
                try:
                    feat = json.loads(p.features_used)
                    lr_pred = feat.get("logistic_regression", {}).get("prediction")
                    nb_pred = feat.get("naive_bayes", {}).get("prediction")
                    if lr_pred and nb_pred and lr_pred.lower() != nb_pred.lower():
                        disagreements += 1
                except Exception:
                    pass

        disagree_rate = round((disagreements / total_predictions * 100), 2) if total_predictions > 0 else 0.0

        # Feedback & user correction counts
        fb_query = db.session.query(Feedback)
        if start_dt:
            fb_query = fb_query.filter(Feedback.created_at >= start_dt)
        if end_dt:
            fb_query = fb_query.filter(Feedback.created_at <= end_dt)

        total_feedback = fb_query.count()
        corrections = fb_query.filter(Feedback.is_correction == True).count()  # noqa: E712
        correction_rate = round((corrections / total_feedback * 100), 1) if total_feedback > 0 else 0.0

        return success_response(
            data={
                "filter": filter_type,
                "total_emails_analyzed": total_emails or total_predictions,
                "total_predictions": total_predictions,
                "spam_detected": spam_count,
                "safe_emails": safe_count,
                "review_required": review_count,
                "spam_percentage": spam_pct,
                "safe_percentage": safe_pct,
                "review_percentage": review_pct,
                "disagreement_count": disagreements,
                "disagreement_rate": disagree_rate,
                "total_feedback": total_feedback,
                "corrections_count": corrections,
                "correction_rate": correction_rate,
            },
            message="Analytics overview retrieved successfully",
        )
    except Exception as exc:
        return error_response(f"Failed to get analytics overview: {str(exc)}", status_code=500)


@analytics_bp.route("/analytics/trends", methods=["GET"])
def get_analytics_trends():
    """
    Return daily, weekly, or monthly time-series trends of email classifications.
    Query params:
        filter: 'today' | '7d' | '30d' | '90d' | 'all' | 'custom'
        interval: 'daily' | 'weekly' | 'monthly'
    """
    try:
        start_dt, end_dt, _ = parse_date_filter()
        interval = request.args.get("interval", "daily").lower()

        # Query all predictions with timestamps
        query = db.session.query(Prediction.created_at, Prediction.label)
        if start_dt:
            query = query.filter(Prediction.created_at >= start_dt)
        if end_dt:
            query = query.filter(Prediction.created_at <= end_dt)

        records = query.order_by(Prediction.created_at.asc()).all()

        # Group records by date format
        date_groups = {}
        for created_at, label in records:
            if not created_at:
                continue

            if interval == "monthly":
                key = created_at.strftime("%Y-%m")
            elif interval == "weekly":
                # Year and ISO week number
                key = f"{created_at.year}-W{created_at.isocalendar()[1]:02d}"
            else:  # daily
                key = created_at.strftime("%Y-%m-%d")

            if key not in date_groups:
                date_groups[key] = {"date": key, "spam": 0, "safe": 0, "review": 0, "total": 0}

            if label == "spam":
                date_groups[key]["spam"] += 1
            elif label == "ham":
                date_groups[key]["safe"] += 1
            else:
                date_groups[key]["review"] += 1
            date_groups[key]["total"] += 1

        # If empty (e.g. new installation without emails in filter range), generate helpful continuous date points
        trend_list = sorted(date_groups.values(), key=lambda x: x["date"])

        return success_response(
            data={
                "interval": interval,
                "trends": trend_list,
            },
            message="Analytics trends retrieved successfully",
        )
    except Exception as exc:
        return error_response(f"Failed to get analytics trends: {str(exc)}", status_code=500)


@analytics_bp.route("/analytics/senders", methods=["GET"])
def get_sender_analytics():
    """Return top senders, top spam senders, and domain distribution."""
    try:
        start_dt, end_dt, _ = parse_date_filter()

        query = db.session.query(Email, Prediction).outerjoin(Prediction, Email.id == Prediction.email_id)
        if start_dt:
            query = query.filter(Email.received_at >= start_dt)
        if end_dt:
            query = query.filter(Email.received_at <= end_dt)

        pairs = query.all()

        sender_counts = Counter()
        spam_sender_counts = Counter()
        domain_counts = Counter()

        for email, pred in pairs:
            sender = (email.sender_email or email.sender or "Unknown").strip().lower()
            sender_counts[sender] += 1

            if "@" in sender:
                domain = sender.split("@")[-1]
                domain_counts[domain] += 1

            if pred and pred.label == "spam":
                spam_sender_counts[sender] += 1

        top_senders = [{"sender": s, "count": c} for s, c in sender_counts.most_common(10)]
        top_spam_senders = [{"sender": s, "count": c} for s, c in spam_sender_counts.most_common(10)]
        top_domains = [{"domain": d, "count": c} for d, c in domain_counts.most_common(8)]

        return success_response(
            data={
                "top_senders": top_senders,
                "top_spam_senders": top_spam_senders,
                "top_domains": top_domains,
            },
            message="Sender analytics retrieved successfully",
        )
    except Exception as exc:
        return error_response(f"Failed to get sender analytics: {str(exc)}", status_code=500)


@analytics_bp.route("/analytics/patterns", methods=["GET"])
def get_spam_patterns():
    """Extract frequently detected spam keywords and discriminative patterns."""
    try:
        # Extract keywords from stored Prediction top_signals
        predictions = (
            db.session.query(Prediction)
            .filter(Prediction.label == "spam")
            .order_by(Prediction.created_at.desc())
            .limit(100)
            .all()
        )

        keyword_counter = Counter()

        for p in predictions:
            if p.features_used:
                try:
                    feat = json.loads(p.features_used)
                    signals = feat.get("top_signals") or []
                    for sig in signals:
                        w = sig.get("word")
                        if w and len(w) > 2 and sig.get("score", 0) > 0:
                            keyword_counter[w] += 1
                except Exception:
                    pass

        # If few stored signals, fall back to default informative keywords
        if not keyword_counter:
            common_spam_words = [
                "urgent", "verify", "account", "suspended", "prize",
                "claim", "free", "winner", "cashier", "click", "password", "bank"
            ]
            for w in common_spam_words:
                keyword_counter[w] = 1

        top_keywords = [{"word": w, "count": c} for w, c in keyword_counter.most_common(20)]

        return success_response(
            data={"patterns": top_keywords},
            message="Spam patterns retrieved successfully",
        )
    except Exception as exc:
        return error_response(f"Failed to get spam patterns: {str(exc)}", status_code=500)


@analytics_bp.route("/analytics/model-comparison", methods=["GET"])
def get_model_comparison():
    """
    Compare Logistic Regression vs Multinomial Naive Bayes:
    1. Test-set benchmark metrics.
    2. Live Gmail prediction performance and disagreement statistics.
    """
    try:
        # 1. Test set benchmark metrics
        metrics = MLService.get_metrics()
        lr_test = metrics.get("logistic_regression", {})
        nb_test = metrics.get("naive_bayes", {})

        # 2. Live prediction data analysis
        predictions = db.session.query(Prediction).all()
        total_live = len(predictions)

        lr_live_spam = 0
        nb_live_spam = 0
        disagreements = 0
        lr_conf_sum = 0.0
        nb_conf_sum = 0.0
        valid_details_count = 0

        for p in predictions:
            if p.features_used:
                try:
                    feat = json.loads(p.features_used)
                    lr_info = feat.get("logistic_regression", {})
                    nb_info = feat.get("naive_bayes", {})

                    lr_pred = lr_info.get("prediction")
                    nb_pred = nb_info.get("prediction")

                    if lr_pred == "SPAM":
                        lr_live_spam += 1
                    if nb_pred == "SPAM":
                        nb_live_spam += 1

                    if lr_pred and nb_pred and lr_pred.lower() != nb_pred.lower():
                        disagreements += 1

                    if "confidence" in lr_info:
                        lr_conf_sum += lr_info["confidence"]
                    if "confidence" in nb_info:
                        nb_conf_sum += nb_info["confidence"]

                    valid_details_count += 1
                except Exception:
                    pass

        disagree_rate = round((disagreements / valid_details_count * 100), 2) if valid_details_count > 0 else 0.0
        lr_avg_conf = round(lr_conf_sum / valid_details_count, 4) if valid_details_count > 0 else 0.0
        nb_avg_conf = round(nb_conf_sum / valid_details_count, 4) if valid_details_count > 0 else 0.0

        # User feedback corrections correlation
        feedback_corrections = db.session.query(Feedback).filter(Feedback.is_correction == True).all()  # noqa: E712
        total_corrections = len(feedback_corrections)

        return success_response(
            data={
                "test_dataset_benchmarks": {
                    "logistic_regression": lr_test,
                    "naive_bayes": nb_test,
                    "dataset_stats": metrics.get("dataset", {}),
                    "trained_at": metrics.get("trained_at"),
                },
                "live_gmail_statistics": {
                    "total_live_scanned": total_live,
                    "logistic_regression_spam_count": lr_live_spam,
                    "naive_bayes_spam_count": nb_live_spam,
                    "disagreement_count": disagreements,
                    "disagreement_rate_percentage": disagree_rate,
                    "lr_average_confidence": lr_avg_conf,
                    "nb_average_confidence": nb_avg_conf,
                    "total_user_corrections": total_corrections,
                },
            },
            message="Model comparison retrieved successfully",
        )
    except Exception as exc:
        return error_response(f"Failed to get model comparison: {str(exc)}", status_code=500)

