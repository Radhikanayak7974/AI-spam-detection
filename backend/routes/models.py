"""
SpamGuard AI - Model Performance & Retraining API Routes
Phase 2 & Phase 4: Machine Learning Pipeline, Controlled Retraining, Versioning & Monitoring
"""

import os
import json
from flask import Blueprint, request
from database import db
from models import TrainingHistory, Feedback, Prediction
from services.ml_service import MLService
from services.retraining_service import RetrainingService
from services.build_dataset import generate_dataset, DATASET_PATH
from utils.response import success_response, error_response

models_bp = Blueprint("models", __name__)


@models_bp.route("/models/performance", methods=["GET"])
def get_model_performance():
    """Return model performance metrics for both Logistic Regression and Naive Bayes."""
    try:
        # If not trained yet, ensure dataset exists and train models
        if not MLService.is_trained():
            if not os.path.exists(DATASET_PATH):
                generate_dataset()
            metrics = MLService.train_models()
        else:
            MLService.load_models()
            metrics = MLService.get_metrics()
            # If metrics file was missing or empty, train
            if not metrics:
                metrics = MLService.train_models()

        # Add version manifest metadata
        manifest = RetrainingService.get_manifest()
        metrics["active_version"] = manifest.get("active_version", "v1")

        return success_response(
            data=metrics,
            message="Model performance metrics retrieved successfully",
        )
    except Exception as exc:
        return error_response(message=f"Failed to load model metrics: {str(exc)}", status_code=500)


@models_bp.route("/models/predict", methods=["POST"])
def predict_spam():
    """
    Run email text through chosen ML model.
    Request body:
        {
            "text": "Email body or subject...",
            "model": "logistic_regression" | "naive_bayes"
        }
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    model_name = data.get("model", "logistic_regression")

    if not text:
        return error_response("Field 'text' cannot be empty", status_code=400)

    try:
        # Ensure models are loaded / trained
        if not MLService.is_trained():
            if not os.path.exists(DATASET_PATH):
                generate_dataset()
            MLService.train_models()
        else:
            MLService.load_models()

        result = MLService.predict(text=text, model_name=model_name)
        return success_response(data=result, message="Prediction completed successfully")
    except Exception as exc:
        return error_response(f"Prediction failed: {str(exc)}", status_code=500)


@models_bp.route("/models/train", methods=["POST"])
def retrain_models_basic():
    """Trigger basic retraining of models (legacy Phase 2 endpoint)."""
    try:
        if not os.path.exists(DATASET_PATH):
            generate_dataset()
        metrics = MLService.train_models()
        return success_response(
            data=metrics,
            message="Models retrained successfully",
        )
    except Exception as exc:
        return error_response(f"Model retraining failed: {str(exc)}", status_code=500)


@models_bp.route("/models/retrain", methods=["POST"])
def retrain_models_controlled():
    """
    Phase 4: Controlled Model Retraining Pipeline.
    Combines verified user feedback with the dataset, trains new candidate models,
    evaluates them against acceptance criteria, and safely promotes or rejects.
    """
    try:
        data = request.get_json(silent=True) or {}
        acceptance_margin = float(data.get("acceptance_margin", 0.05))
        created_by = data.get("created_by", "admin")

        result = RetrainingService.retrain_pipeline(
            acceptance_threshold_margin=acceptance_margin,
            created_by=created_by,
        )

        return success_response(
            data=result,
            message=result["message"],
        )
    except Exception as exc:
        return error_response(f"Controlled model retraining failed: {str(exc)}", status_code=500)


@models_bp.route("/models/versions", methods=["GET"])
def get_model_versions():
    """Return model version history and training audit log."""
    try:
        manifest = RetrainingService.get_manifest()
        history_records = (
            TrainingHistory.query.order_by(TrainingHistory.trained_at.desc()).all()
        )

        approved_feedback_count = Feedback.query.filter_by(status="approved").count()

        return success_response(
            data={
                "current_version": manifest.get("current_version", "v1"),
                "active_version": manifest.get("active_version", "v1"),
                "available_versions": manifest.get("versions", ["v1"]),
                "approved_feedback_count": approved_feedback_count,
                "history": [h.to_dict() for h in history_records],
            },
            message="Model version history retrieved successfully",
        )
    except Exception as exc:
        return error_response(f"Failed to get model versions: {str(exc)}", status_code=500)


@models_bp.route("/models/monitoring", methods=["GET"])
def get_model_monitoring():
    """
    Return model monitoring metrics:
    - Prediction distribution
    - Disagreement rate
    - Correction rate
    - System health alerts
    """
    try:
        total_preds = Prediction.query.count()
        spam_preds = Prediction.query.filter_by(label="spam").count()
        ham_preds = Prediction.query.filter_by(label="ham").count()
        review_preds = Prediction.query.filter_by(label="review").count()

        # Disagreements
        predictions = Prediction.query.all()
        disagreements = 0
        total_conf = 0.0
        for p in predictions:
            total_conf += p.confidence or 0.0
            if p.features_used:
                try:
                    feat = json.loads(p.features_used)
                    lr_pred = feat.get("logistic_regression", {}).get("prediction")
                    nb_pred = feat.get("naive_bayes", {}).get("prediction")
                    if lr_pred and nb_pred and lr_pred.lower() != nb_pred.lower():
                        disagreements += 1
                except Exception:
                    pass

        disagree_rate = round((disagreements / total_preds * 100), 2) if total_preds > 0 else 0.0
        avg_confidence = round((total_conf / total_preds), 4) if total_preds > 0 else 0.0

        # Feedback corrections
        total_feedback = Feedback.query.count()
        corrections = Feedback.query.filter_by(is_correction=True).count()
        correction_rate = round((corrections / total_feedback * 100), 2) if total_feedback > 0 else 0.0

        # Health alerts
        alerts = []
        if disagree_rate > 15.0:
            alerts.append({
                "type": "warning",
                "code": "HIGH_DISAGREEMENT",
                "message": f"High model disagreement rate ({disagree_rate}%). Models diverge on significant inbox samples.",
            })
        if correction_rate > 10.0 and total_feedback >= 5:
            alerts.append({
                "type": "warning",
                "code": "HIGH_CORRECTION_RATE",
                "message": f"User correction rate is elevated ({correction_rate}%). Consider triggering model retraining.",
            })
        if avg_confidence < 0.75 and total_preds > 0:
            alerts.append({
                "type": "info",
                "code": "LOW_CONFIDENCE",
                "message": f"Average model confidence is below 75% ({avg_confidence * 100:.1f}%).",
            })
        if not alerts:
            alerts.append({
                "type": "healthy",
                "code": "OPTIMAL",
                "message": "Both models are operating within nominal disagreement and confidence thresholds.",
            })

        manifest = RetrainingService.get_manifest()

        return success_response(
            data={
                "active_version": manifest.get("active_version", "v1"),
                "total_predictions": total_preds,
                "distribution": {
                    "spam": spam_preds,
                    "safe": ham_preds,
                    "review": review_preds,
                },
                "disagreement_count": disagreements,
                "disagreement_rate": disagree_rate,
                "user_correction_rate": correction_rate,
                "average_confidence": avg_confidence,
                "alerts": alerts,
            },
            message="Model monitoring metrics retrieved successfully",
        )
    except Exception as exc:
        return error_response(f"Failed to get model monitoring metrics: {str(exc)}", status_code=500)
