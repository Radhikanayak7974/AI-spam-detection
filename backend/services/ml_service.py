"""
SpamGuard AI - Machine Learning Service (Phase 2)
Provides text preprocessing, TF-IDF vectorization, model training,
evaluation metrics, and inference for Logistic Regression and Multinomial Naive Bayes.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Tuple, List

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

logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELS_DIR = os.path.join(BASE_DIR, "ml_models")
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
DATASET_PATH = os.path.join(DATASET_DIR, "spam_dataset.csv")

METRICS_FILE = os.path.join(MODELS_DIR, "metrics.json")
VECTORIZER_FILE = os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib")
LR_MODEL_FILE = os.path.join(MODELS_DIR, "logistic_regression.joblib")
NB_MODEL_FILE = os.path.join(MODELS_DIR, "naive_bayes.joblib")

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATASET_DIR, exist_ok=True)


def clean_text(text: str) -> str:
    """Preprocess email/SMS text: lowercasing, url/email replacement, symbol cleanup."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Replace URLs with token
    text = re.sub(r"https?://\S+|www\.\S+", " httpaddr ", text)
    # Replace email addresses with token
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", " emailaddr ", text)
    # Replace currency symbols and numbers
    text = re.sub(r"[$£€¥₹]", " currencysym ", text)
    text = re.sub(r"\b\d+\b", " number ", text)
    # Remove HTML tags
    text = re.sub(r"<.*?>", " ", text)
    # Remove special punctuation and extra whitespace
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class MLService:
    """Singleton service for model management, evaluation, and inference."""

    _vectorizer = None
    _lr_model = None
    _nb_model = None
    _metrics = None

    @classmethod
    def is_trained(cls) -> bool:
        """Check if models and vectorizer exist on disk."""
        return (
            os.path.exists(VECTORIZER_FILE)
            and os.path.exists(LR_MODEL_FILE)
            and os.path.exists(NB_MODEL_FILE)
        )

    @classmethod
    def load_models(cls, force_reload: bool = False):
        """Load trained models from disk into memory."""
        if cls.is_trained():
            if cls._vectorizer is None or force_reload:
                cls._vectorizer = joblib.load(VECTORIZER_FILE)
                cls._lr_model = joblib.load(LR_MODEL_FILE)
                cls._nb_model = joblib.load(NB_MODEL_FILE)
            if os.path.exists(METRICS_FILE):
                with open(METRICS_FILE, "r", encoding="utf-8") as f:
                    cls._metrics = json.load(f)
            return True
        return False

    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        """Return cached evaluation metrics."""
        if cls._metrics is None and os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                cls._metrics = json.load(f)
        return cls._metrics or {}

    @classmethod
    def train_models(cls) -> Dict[str, Any]:
        """Train both Logistic Regression and Multinomial Naive Bayes models."""
        if not os.path.exists(DATASET_PATH):
            raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")

        # Load dataset
        df = pd.read_csv(DATASET_PATH)
        if "label" not in df.columns or "text" not in df.columns:
            raise ValueError("Dataset must contain 'label' and 'text' columns")

        # Map labels: ham -> 0, spam -> 1
        df["label_num"] = df["label"].map({"ham": 0, "spam": 1})
        df["cleaned_text"] = df["text"].apply(clean_text)

        X_train_raw, X_test_raw, y_train, y_test = train_test_split(
            df["cleaned_text"],
            df["label_num"],
            test_size=0.2,
            random_state=42,
            stratify=df["label_num"],
        )

        # TF-IDF Feature Extraction
        vectorizer = TfidfVectorizer(
            max_features=3000,
            ngram_range=(1, 2),
            stop_words="english",
            sublinear_tf=True,
        )
        X_train = vectorizer.fit_transform(X_train_raw)
        X_test = vectorizer.transform(X_test_raw)

        # 1. Train Logistic Regression
        lr = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
        lr.fit(X_train, y_train)
        lr_preds = lr.predict(X_test)
        lr_probs = lr.predict_proba(X_test)[:, 1]

        # 2. Train Multinomial Naive Bayes
        nb = MultinomialNB(alpha=0.1)
        nb.fit(X_train, y_train)
        nb_preds = nb.predict(X_test)
        nb_probs = nb.predict_proba(X_test)[:, 1]

        # Calculate metrics for Logistic Regression
        lr_cm = confusion_matrix(y_test, lr_preds).tolist()
        lr_fpr, lr_tpr, _ = roc_curve(y_test, lr_probs)
        lr_roc = [{"fpr": round(float(f), 4), "tpr": round(float(t), 4)} for f, t in zip(lr_fpr[::max(1, len(lr_fpr)//20)], lr_tpr[::max(1, len(lr_tpr)//20)])]

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

        # Calculate metrics for Naive Bayes
        nb_cm = confusion_matrix(y_test, nb_preds).tolist()
        nb_fpr, nb_tpr, _ = roc_curve(y_test, nb_probs)
        nb_roc = [{"fpr": round(float(f), 4), "tpr": round(float(t), 4)} for f, t in zip(nb_fpr[::max(1, len(nb_fpr)//20)], nb_tpr[::max(1, len(nb_tpr)//20)])]

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

        dataset_stats = {
            "total_samples": len(df),
            "spam_samples": int((df["label"] == "spam").sum()),
            "ham_samples": int((df["label"] == "ham").sum()),
            "vocab_size": len(vectorizer.vocabulary_),
            "train_samples": len(X_train_raw),
            "test_samples": len(X_test_raw),
        }

        full_metrics = {
            "logistic_regression": lr_metrics,
            "naive_bayes": nb_metrics,
            "dataset": dataset_stats,
            "trained_at": pd.Timestamp.now().isoformat(),
        }

        # Save artifacts
        joblib.dump(vectorizer, VECTORIZER_FILE)
        joblib.dump(lr, LR_MODEL_FILE)
        joblib.dump(nb, NB_MODEL_FILE)
        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(full_metrics, f, indent=2)

        # Update loaded memory references
        cls._vectorizer = vectorizer
        cls._lr_model = lr
        cls._nb_model = nb
        cls._metrics = full_metrics

        return full_metrics

    @classmethod
    def predict(cls, text: str, model_name: str = "logistic_regression") -> Dict[str, Any]:
        """Classify single email text using chosen model."""
        if not cls.load_models():
            return {
                "is_spam": False,
                "confidence": 0.0,
                "label": "unknown",
                "status": "not_trained",
                "message": "Models are not trained yet.",
            }

        cleaned = clean_text(text)
        features = cls._vectorizer.transform([cleaned])

        if model_name == "naive_bayes":
            model = cls._nb_model
            name = "Multinomial Naive Bayes"
        else:
            model = cls._lr_model
            name = "Logistic Regression"

        proba = model.predict_proba(features)[0]
        spam_prob = float(proba[1])
        ham_prob = float(proba[0])
        is_spam = bool(spam_prob >= 0.5)

        # Extract top keywords contributing to classification
        feature_names = np.array(cls._vectorizer.get_feature_names_out())
        non_zero_indices = features.nonzero()[1]
        feature_weights = []

        if len(non_zero_indices) > 0:
            if model_name == "logistic_regression":
                coefs = cls._lr_model.coef_[0]
                for idx in non_zero_indices:
                    word = feature_names[idx]
                    weight = float(coefs[idx]) * float(features[0, idx])
                    feature_weights.append({"word": word, "score": round(weight, 4)})
            else:
                log_probs = cls._nb_model.feature_log_prob_
                for idx in non_zero_indices:
                    word = feature_names[idx]
                    weight = float(log_probs[1, idx] - log_probs[0, idx]) * float(features[0, idx])
                    feature_weights.append({"word": word, "score": round(weight, 4)})

            # Sort descending by score (highest spam indicator first)
            feature_weights.sort(key=lambda x: x["score"], reverse=True)

        return {
            "is_spam": is_spam,
            "label": "spam" if is_spam else "ham",
            "confidence": round(spam_prob if is_spam else ham_prob, 4),
            "spam_probability": round(spam_prob, 4),
            "ham_probability": round(ham_prob, 4),
            "model_used": name,
            "model_id": model_name,
            "top_signals": feature_weights[:8],
        }
