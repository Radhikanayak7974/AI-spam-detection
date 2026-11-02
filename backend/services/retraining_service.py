"""
SpamGuard AI - Controlled Model Retraining Pipeline (Phase 4)
Handles feedback collection, label validation, dataset augmentation,
stratified train/test splitting, training of LR and NB models, evaluation,
comparison against current production models, versioning, and safe promotion.
"""

import os
import re
import json
import shutil
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
)

from services.ml_service import clean_text, BASE_DIR, MODELS_DIR, DATASET_PATH

logger = logging.getLogger(__name__)

MANIFEST_FILE = os.path.join(MODELS_DIR, "version_manifest.json")


def utcnow():
    return datetime.now(timezone.utc)


class RetrainingService:
    """Service to coordinate controlled model retraining with user feedback."""

    @staticmethod
    def get_manifest() -> Dict[str, Any]:
        """Return version manifest or initialize default v1."""
        if os.path.exists(MANIFEST_FILE):
            try:
                with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read manifest: {e}")

        # Default manifest if not found
        default_manifest = {
            "current_version": "v1",
            "active_version": "v1",
            "versions": ["v1"],
            "last_updated": utcnow().isoformat(),
        }
        RetrainingService._save_manifest(default_manifest)
        return default_manifest

    @staticmethod
    def _save_manifest(manifest: Dict[str, Any]):
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

    @classmethod
    def get_next_version(cls) -> str:
        """Calculate next version string like v2, v3, etc."""
        manifest = cls.get_manifest()
        versions = manifest.get("versions", ["v1"])
        nums = []
        for v in versions:
            match = re.search(r"v(\d+)", v)
            if match:
                nums.append(int(match.group(1)))
        next_num = max(nums, default=1) + 1
        return f"v{next_num}"

    @classmethod
    def initialize_v1_backup_if_needed(cls):
        """Ensure the initial production models are backed up as v1."""
        v1_dir = os.path.join(MODELS_DIR, "v1")
        if not os.path.exists(v1_dir):
            os.makedirs(v1_dir, exist_ok=True)
            for fname in ["logistic_regression.joblib", "naive_bayes.joblib", "tfidf_vectorizer.joblib", "metrics.json"]:
                src = os.path.join(MODELS_DIR, fname)
                dst = os.path.join(v1_dir, fname)
                if os.path.exists(src) and not os.path.exists(dst):
                    shutil.copy2(src, dst)

    @classmethod
    def get_approved_feedback_samples(cls) -> List[Dict[str, Any]]:
        """Fetch approved feedback from database."""
        from database import db
        from models import Feedback, Email

        records = (
            db.session.query(Feedback, Email)
            .join(Email, Feedback.email_id == Email.id)
            .filter(Feedback.status == "approved")
            .all()
        )

        samples = []
        seen_texts = set()

        for fb, em in records:
            # Validate label
            user_label = (fb.user_label or "").strip().lower()
            if user_label not in ("spam", "ham"):
                continue

            text = f"{em.subject or ''} {em.body_plain or em.snippet or ''}".strip()
            if not text:
                continue

            # Clean and deduplicate text
            cleaned = clean_text(text)
            if cleaned in seen_texts or len(cleaned) < 10:
                continue
            seen_texts.add(cleaned)

            samples.append({
                "feedback_id": fb.id,
                "email_id": em.id,
                "label": user_label,
                "text": text,
                "cleaned_text": cleaned,
            })

        return samples

    @classmethod
    def retrain_pipeline(
        cls,
        min_feedback_samples: int = 1,
        acceptance_threshold_margin: float = 0.05,
        created_by: str = "admin",
    ) -> Dict[str, Any]:
        """
        Controlled model retraining pipeline:
        1. Collect approved feedback records.
        2. Validate labels and remove duplicates.
        3. Check class balance.
        4. Combine approved feedback with original dataset.
        5. Split train/test.
        6. Rebuild TF-IDF features using training data only.
        7. Train Logistic Regression & Multinomial Naive Bayes.
        8. Evaluate both models.
        9. Compare new models with existing production models.
        10. Promote new models only if acceptance criteria met.
        11. Save versioned artifacts and record in TrainingHistory.
        """
        from database import db
        from models import TrainingHistory
        from services.ml_service import MLService

        cls.initialize_v1_backup_if_needed()

        # 1. Collect approved feedback
        feedback_samples = cls.get_approved_feedback_samples()
        feedback_count = len(feedback_samples)

        # 2. Check base dataset
        if not os.path.exists(DATASET_PATH):
            from services.build_dataset import generate_dataset
            generate_dataset()

        base_df = pd.read_csv(DATASET_PATH)
        if "label" not in base_df.columns or "text" not in base_df.columns:
            raise ValueError("Dataset must contain 'label' and 'text' columns")

        # 3. Combine with feedback samples
        if feedback_samples:
            fb_df = pd.DataFrame([{"label": s["label"], "text": s["text"]} for s in feedback_samples])
            combined_df = pd.concat([base_df, fb_df], ignore_index=True)
        else:
            combined_df = base_df.copy()

        # Deduplicate combined dataset
        combined_df = combined_df.drop_duplicates(subset=["text"]).dropna(subset=["text", "label"])

        # Label encoding
        combined_df["label_clean"] = combined_df["label"].str.strip().str.lower()
        combined_df = combined_df[combined_df["label_clean"].isin(["ham", "spam"])]
        combined_df["label_num"] = combined_df["label_clean"].map({"ham": 0, "spam": 1})
        combined_df["cleaned_text"] = combined_df["text"].apply(clean_text)

        total_samples = len(combined_df)
        spam_samples = int((combined_df["label_num"] == 1).sum())
        ham_samples = int((combined_df["label_num"] == 0).sum())

        # Check minimum class balance
        if spam_samples < 5 or ham_samples < 5:
            raise ValueError(f"Insufficient class balance: {spam_samples} spam, {ham_samples} ham")

        # 4. Train / validation split
        X_train_raw, X_test_raw, y_train, y_test = train_test_split(
            combined_df["cleaned_text"],
            combined_df["label_num"],
            test_size=0.2,
            random_state=42,
            stratify=combined_df["label_num"],
        )

        # 5. TF-IDF feature extraction on training data ONLY
        vectorizer = TfidfVectorizer(
            max_features=3500,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
        )
        X_train = vectorizer.fit_transform(X_train_raw)
        X_test = vectorizer.transform(X_test_raw)

        # 6. Train candidate models
        # A. Logistic Regression
        lr = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
        lr.fit(X_train, y_train)
        lr_preds = lr.predict(X_test)
        lr_probs = lr.predict_proba(X_test)[:, 1]

        # B. Multinomial Naive Bayes
        nb = MultinomialNB(alpha=0.1)
        nb.fit(X_train, y_train)
        nb_preds = nb.predict(X_test)
        nb_probs = nb.predict_proba(X_test)[:, 1]

        # 7. Evaluate candidate models
        lr_cm = confusion_matrix(y_test, lr_preds).tolist()
        lr_fpr, lr_tpr, _ = roc_curve(y_test, lr_probs)
        lr_roc = [
            {"fpr": round(float(f), 4), "tpr": round(float(t), 4)}
            for f, t in zip(lr_fpr[::max(1, len(lr_fpr) // 20)], lr_tpr[::max(1, len(lr_tpr) // 20)])
        ]

        lr_metrics = {
            "accuracy": round(float(accuracy_score(y_test, lr_preds)), 4),
            "precision": round(float(precision_score(y_test, lr_preds, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, lr_preds, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, lr_preds, zero_division=0)), 4),
            "auc": round(float(roc_auc_score(y_test, lr_probs)), 4),
            "confusion_matrix": {
                "tn": lr_cm[0][0],
                "fp": lr_cm[0][1],
                "fn": lr_cm[1][0],
                "tp": lr_cm[1][1],
            },
            "roc_curve": lr_roc,
        }

        nb_cm = confusion_matrix(y_test, nb_preds).tolist()
        nb_fpr, nb_tpr, _ = roc_curve(y_test, nb_probs)
        nb_roc = [
            {"fpr": round(float(f), 4), "tpr": round(float(t), 4)}
            for f, t in zip(nb_fpr[::max(1, len(nb_fpr) // 20)], nb_tpr[::max(1, len(nb_tpr) // 20)])
        ]

        nb_metrics = {
            "accuracy": round(float(accuracy_score(y_test, nb_preds)), 4),
            "precision": round(float(precision_score(y_test, nb_preds, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, nb_preds, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, nb_preds, zero_division=0)), 4),
            "auc": round(float(roc_auc_score(y_test, nb_probs)), 4),
            "confusion_matrix": {
                "tn": nb_cm[0][0],
                "fp": nb_cm[0][1],
                "fn": nb_cm[1][0],
                "tp": nb_cm[1][1],
            },
            "roc_curve": nb_roc,
        }

        # 8. Compare with current production metrics
        current_metrics = MLService.get_metrics()
        current_lr_acc = current_metrics.get("logistic_regression", {}).get("accuracy", 0.90)
        current_nb_acc = current_metrics.get("naive_bayes", {}).get("accuracy", 0.90)

        # Acceptance check: accuracy should not drop more than configured threshold
        lr_acceptable = lr_metrics["accuracy"] >= (current_lr_acc - acceptance_threshold_margin)
        nb_acceptable = nb_metrics["accuracy"] >= (current_nb_acc - acceptance_threshold_margin)
        is_promoted = bool(lr_acceptable and nb_acceptable and lr_metrics["accuracy"] >= 0.85 and nb_metrics["accuracy"] >= 0.85)

        next_version = cls.get_next_version()

        full_metrics = {
            "version": next_version if is_promoted else f"{next_version}-candidate",
            "logistic_regression": lr_metrics,
            "naive_bayes": nb_metrics,
            "dataset": {
                "total_samples": total_samples,
                "spam_samples": spam_samples,
                "ham_samples": ham_samples,
                "feedback_samples_used": feedback_count,
                "vocab_size": len(vectorizer.vocabulary_),
                "train_samples": len(X_train_raw),
                "test_samples": len(X_test_raw),
            },
            "trained_at": utcnow().isoformat(),
            "status": "promoted" if is_promoted else "rejected",
            "acceptance": {
                "promoted": is_promoted,
                "lr_acceptable": lr_acceptable,
                "nb_acceptable": nb_acceptable,
                "current_lr_accuracy": current_lr_acc,
                "candidate_lr_accuracy": lr_metrics["accuracy"],
                "current_nb_accuracy": current_nb_acc,
                "candidate_nb_accuracy": nb_metrics["accuracy"],
            },
        }

        # 9. Handle Promotion or Rejection
        version_dir = os.path.join(MODELS_DIR, next_version)
        os.makedirs(version_dir, exist_ok=True)

        # Always save candidate artifacts in version directory for audit trail
        joblib.dump(vectorizer, os.path.join(version_dir, "tfidf_vectorizer.joblib"))
        joblib.dump(lr, os.path.join(version_dir, "logistic_regression.joblib"))
        joblib.dump(nb, os.path.join(version_dir, "naive_bayes.joblib"))
        with open(os.path.join(version_dir, "metrics.json"), "w", encoding="utf-8") as f:
            json.dump(full_metrics, f, indent=2)

        if is_promoted:
            # Overwrite production model files
            joblib.dump(vectorizer, os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
            joblib.dump(lr, os.path.join(MODELS_DIR, "logistic_regression.joblib"))
            joblib.dump(nb, os.path.join(MODELS_DIR, "naive_bayes.joblib"))
            with open(os.path.join(MODELS_DIR, "metrics.json"), "w", encoding="utf-8") as f:
                json.dump(full_metrics, f, indent=2)

            # Update manifest
            manifest = cls.get_manifest()
            manifest["current_version"] = next_version
            manifest["active_version"] = next_version
            if next_version not in manifest.get("versions", []):
                manifest.setdefault("versions", []).append(next_version)
            manifest["last_updated"] = utcnow().isoformat()
            cls._save_manifest(manifest)

            # Reload models into memory in MLService
            MLService.load_models(force_reload=True)

        # 10. Record in TrainingHistory database table
        history_record = TrainingHistory(
            version=next_version,
            model_type="ensemble_lr_nb",
            dataset_size=total_samples,
            feedback_samples=feedback_count,
            metrics=json.dumps(full_metrics),
            status="promoted" if is_promoted else "rejected",
            trained_at=utcnow(),
            promoted_at=utcnow() if is_promoted else None,
            created_by=created_by,
            notes=f"Retrained with {feedback_count} feedback samples. LR Acc: {lr_metrics['accuracy']:.4f}, NB Acc: {nb_metrics['accuracy']:.4f}. Status: {'Promoted' if is_promoted else 'Rejected'}",
        )
        db.session.add(history_record)
        db.session.commit()

        return {
            "success": True,
            "promoted": is_promoted,
            "version": next_version,
            "metrics": full_metrics,
            "history_id": history_record.id,
            "message": (
                f"Model successfully retrained and promoted to {next_version}!"
                if is_promoted
                else f"Retrained model {next_version} rejected: validation criteria not satisfied."
            ),
        }

