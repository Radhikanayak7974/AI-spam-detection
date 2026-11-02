"""
SpamGuard AI - Phase 3: Machine Learning Model Training (Enron Dataset)
Trains Logistic Regression & Multinomial Naive Bayes on Enron cleaned dataset.
Saves candidate artifacts in ml_models/v7/ without overwriting active production models.
"""

import os
import sys
import time
import json
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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
    classification_report,
    roc_curve,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from services.ml_service import clean_text

DATASET_PATH = "dataset/processed/enron_spam_cleaned.csv"
OUTPUT_DIR = "ml_models/v7"
VERSION = "v7"

def main():
    print("\n" + "=" * 70)
    print("  🚀 SpamGuard AI — PHASE 3: Machine Learning Model Training (Enron)")
    print("=" * 70)

    # ── 1. Load Dataset ───────────────────────────────────────────────
    print(f"\n[1/7] Loading cleaned Enron dataset from: {DATASET_PATH}")
    if not os.path.exists(DATASET_PATH):
        raise FileNotFoundError(f"Dataset missing at {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    total_records = len(df)
    print(f"  ✅ Records loaded: {total_records:,}")

    # ── 2. Verify Spam & Ham Labels ───────────────────────────────────
    print("\n[2/7] Verifying labels and distributions...")
    df["label_clean"] = df["label"].astype(str).str.strip().str.lower()
    df = df[df["label_clean"].isin(["ham", "spam"])].copy()
    df["label_num"] = df["label_clean"].map({"ham": 0, "spam": 1})

    spam_count = int((df["label_num"] == 1).sum())
    ham_count = int((df["label_num"] == 0).sum())
    print(f"  • Total verified: {len(df):,}")
    print(f"  • Ham (Safe = 0): {ham_count:,} ({ham_count / len(df) * 100:.2f}%)")
    print(f"  • Spam (Spam = 1): {spam_count:,} ({spam_count / len(df) * 100:.2f}%)")

    # Check leakage / duplicates
    exact_dups = df["text"].duplicated().sum()
    print(f"  • Exact duplicate text checks: {exact_dups} (Zero duplicates expected)")

    # ── 3. Clean Text & Train-Test Split ──────────────────────────────
    print("\n[3/7] Preprocessing text and performing 80:20 Stratified Split...")
    start_prep = time.time()
    df["cleaned_text"] = df["text"].astype(str).apply(clean_text)
    print(f"  • Text preprocessing completed in {time.time() - start_prep:.2f}s")

    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        df["cleaned_text"],
        df["label_num"],
        test_size=0.20,
        random_state=42,
        stratify=df["label_num"],
    )

    n_train = len(X_train_raw)
    n_test = len(X_test_raw)
    train_spam = int((y_train == 1).sum())
    train_ham = int((y_train == 0).sum())
    test_spam = int((y_test == 1).sum())
    test_ham = int((y_test == 0).sum())

    print(f"  • Training samples: {n_train:,} (Spam: {train_spam:,}, Ham: {train_ham:,})")
    print(f"  • Testing samples : {n_test:,} (Spam: {test_spam:,}, Ham: {test_ham:,})")

    # ── 4. TF-IDF Feature Extraction (Fit on Training ONLY) ───────────
    print("\n[4/7] Fitting TF-IDF Vectorizer on training data ONLY...")
    tfidf_start = time.time()
    vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
    )

    X_train = vectorizer.fit_transform(X_train_raw)
    X_test = vectorizer.transform(X_test_raw)
    tfidf_time = time.time() - tfidf_start

    vocab_size = len(vectorizer.vocabulary_)
    print(f"  ✅ TF-IDF fitted in {tfidf_time:.2f}s")
    print(f"  • Vocabulary size: {vocab_size:,} features (max 10,000 unigrams + bigrams)")
    print(f"  • X_train shape  : {X_train.shape}")
    print(f"  • X_test shape   : {X_test.shape}")

    # ── 5. Model Training ─────────────────────────────────────────────
    print("\n[5/7] Training Models independently...")

    # Model A: Logistic Regression
    print("  ▶ Training Model 1: Logistic Regression (max_iter=1000, C=1.0)...")
    lr_start = time.time()
    lr_model = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    lr_model.fit(X_train, y_train)
    lr_duration = time.time() - lr_start
    print(f"    ✅ Logistic Regression trained in {lr_duration:.2f}s")

    # Model B: Multinomial Naive Bayes
    print("  ▶ Training Model 2: Multinomial Naive Bayes (alpha=0.1)...")
    nb_start = time.time()
    nb_model = MultinomialNB(alpha=0.1)
    nb_model.fit(X_train, y_train)
    nb_duration = time.time() - nb_start
    print(f"    ✅ Multinomial Naive Bayes trained in {nb_duration:.2f}s")

    # ── 6. Comprehensive Evaluation on Unseen Test Set ────────────────
    print("\n[6/7] Evaluating Models on separate Test Set (6,093 samples)...")

    # Evaluate LR
    lr_preds = lr_model.predict(X_test)
    lr_probs = lr_model.predict_proba(X_test)[:, 1]
    lr_acc = float(accuracy_score(y_test, lr_preds))
    lr_prec = float(precision_score(y_test, lr_preds, zero_division=0))
    lr_rec = float(recall_score(y_test, lr_preds, zero_division=0))
    lr_f1 = float(f1_score(y_test, lr_preds, zero_division=0))
    lr_auc = float(roc_auc_score(y_test, lr_probs))
    lr_cm = confusion_matrix(y_test, lr_preds).tolist()
    lr_report = classification_report(y_test, lr_preds, target_names=["Safe (Ham)", "Spam"], digits=4)

    lr_fpr, lr_tpr, _ = roc_curve(y_test, lr_probs)
    lr_step = max(1, len(lr_fpr) // 25)
    lr_roc = [{"fpr": round(float(f), 4), "tpr": round(float(t), 4)} for f, t in zip(lr_fpr[::lr_step], lr_tpr[::lr_step])]

    # Evaluate NB
    nb_preds = nb_model.predict(X_test)
    nb_probs = nb_model.predict_proba(X_test)[:, 1]
    nb_acc = float(accuracy_score(y_test, nb_preds))
    nb_prec = float(precision_score(y_test, nb_preds, zero_division=0))
    nb_rec = float(recall_score(y_test, nb_preds, zero_division=0))
    nb_f1 = float(f1_score(y_test, nb_preds, zero_division=0))
    nb_auc = float(roc_auc_score(y_test, nb_probs))
    nb_cm = confusion_matrix(y_test, nb_preds).tolist()
    nb_report = classification_report(y_test, nb_preds, target_names=["Safe (Ham)", "Spam"], digits=4)

    nb_fpr, nb_tpr, _ = roc_curve(y_test, nb_probs)
    nb_step = max(1, len(nb_fpr) // 25)
    nb_roc = [{"fpr": round(float(f), 4), "tpr": round(float(t), 4)} for f, t in zip(nb_fpr[::nb_step], nb_tpr[::nb_step])]

    print("\n" + "-" * 70)
    print("  📊 EVALUATION RESULTS SUMMARY")
    print("-" * 70)
    print(f"  {'Metric':<20} {'Logistic Regression':<22} {'Naive Bayes'}")
    print("-" * 70)
    print(f"  {'Accuracy':<20} {lr_acc * 100:.2f}%{'':<16} {nb_acc * 100:.2f}%")
    print(f"  {'Precision':<20} {lr_prec * 100:.2f}%{'':<16} {nb_prec * 100:.2f}%")
    print(f"  {'Recall':<20} {lr_rec * 100:.2f}%{'':<16} {nb_rec * 100:.2f}%")
    print(f"  {'F1-Score':<20} {lr_f1 * 100:.2f}%{'':<16} {nb_f1 * 100:.2f}%")
    print(f"  {'ROC-AUC':<20} {lr_auc * 100:.2f}%{'':<16} {nb_auc * 100:.2f}%")
    print(f"  {'Training Time':<20} {lr_duration:.2f}s{'':<17} {nb_duration:.2f}s")
    print("-" * 70)
    print(f"  Confusion Matrix (LR): TN={lr_cm[0][0]}, FP={lr_cm[0][1]}, FN={lr_cm[1][0]}, TP={lr_cm[1][1]}")
    print(f"  Confusion Matrix (NB): TN={nb_cm[0][0]}, FP={nb_cm[0][1]}, FN={nb_cm[1][0]}, TP={nb_cm[1][1]}")
    print("\n  Classification Report - Logistic Regression:")
    print(lr_report)
    print("  Classification Report - Multinomial Naive Bayes:")
    print(nb_report)

    # ── 7. Save Candidate Model Artifacts in ml_models/v7 ─────────────
    print(f"\n[7/7] Saving Candidate Artifacts to: {OUTPUT_DIR} (without overwriting production)...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    joblib.dump(vectorizer, os.path.join(OUTPUT_DIR, "tfidf_vectorizer.joblib"))
    joblib.dump(lr_model, os.path.join(OUTPUT_DIR, "logistic_regression.joblib"))
    joblib.dump(nb_model, os.path.join(OUTPUT_DIR, "naive_bayes.joblib"))

    full_metrics = {
        "version": VERSION,
        "dataset_source": "Enron Spam Email Corpus (Cleaned)",
        "logistic_regression": {
            "accuracy": round(lr_acc, 4),
            "precision": round(lr_prec, 4),
            "recall": round(lr_rec, 4),
            "f1": round(lr_f1, 4),
            "auc": round(lr_auc, 4),
            "training_duration_seconds": round(lr_duration, 2),
            "confusion_matrix": {
                "tn": lr_cm[0][0],
                "fp": lr_cm[0][1],
                "fn": lr_cm[1][0],
                "tp": lr_cm[1][1],
            },
            "roc_curve": lr_roc,
        },
        "naive_bayes": {
            "accuracy": round(nb_acc, 4),
            "precision": round(nb_prec, 4),
            "recall": round(nb_rec, 4),
            "f1": round(nb_f1, 4),
            "auc": round(nb_auc, 4),
            "training_duration_seconds": round(nb_duration, 2),
            "confusion_matrix": {
                "tn": nb_cm[0][0],
                "fp": nb_cm[0][1],
                "fn": nb_cm[1][0],
                "tp": nb_cm[1][1],
            },
            "roc_curve": nb_roc,
        },
        "dataset": {
            "total_samples": total_records,
            "spam_samples": spam_count,
            "ham_samples": ham_count,
            "vocab_size": vocab_size,
            "train_samples": n_train,
            "test_samples": n_test,
        },
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "status": "candidate_ready",
        "acceptance": {
            "promoted": False,
            "lr_accuracy": round(lr_acc, 4),
            "nb_accuracy": round(nb_acc, 4),
            "benchmark_passed": bool(lr_acc >= 0.90 and nb_acc >= 0.90),
        },
    }

    with open(os.path.join(OUTPUT_DIR, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(full_metrics, f, indent=2)

    print(f"  ✅ Candidate files saved in {OUTPUT_DIR}/:")
    print("     • tfidf_vectorizer.joblib")
    print("     • logistic_regression.joblib")
    print("     • naive_bayes.joblib")
    print("     • metrics.json")

    # Record in TrainingHistory table as 'candidate_ready'
    try:
        from app import create_app
        from database import db
        from models import TrainingHistory

        app = create_app()
        with app.app_context():
            # Check if record for v7 already exists
            existing_v7 = TrainingHistory.query.filter_by(version=VERSION).first()
            if not existing_v7:
                hist = TrainingHistory(
                    version=VERSION,
                    model_type="ensemble_lr_nb",
                    dataset_size=total_records,
                    feedback_samples=0,
                    metrics=json.dumps(full_metrics),
                    status="candidate_ready",
                    trained_at=datetime.now(timezone.utc),
                    promoted_at=None,
                    created_by="admin_training",
                    notes=f"Trained on Enron email corpus (30,462 records). LR Acc: {lr_acc*100:.2f}%, NB Acc: {nb_acc*100:.2f}%. Candidate status awaiting user approval.",
                )
                db.session.add(hist)
                db.session.commit()
                print(f"  ✅ Audit record created in TrainingHistory table (ID: {hist.id}, Status: candidate_ready)")
            else:
                existing_v7.dataset_size = total_records
                existing_v7.metrics = json.dumps(full_metrics)
                existing_v7.notes = f"Updated Enron candidate training: LR Acc {lr_acc*100:.2f}%, NB Acc {nb_acc*100:.2f}%"
                db.session.commit()
                print(f"  ✅ Existing audit record for {VERSION} updated in TrainingHistory")
    except Exception as exc:
        print(f"  ⚠️ Note: Could not record to database table: {exc}")

    # ── 8. Test on Unseen Diverse Email Samples ───────────────────────
    print("\n" + "=" * 70)
    print("  🧪 TESTING CANDIDATE MODELS ON UNSEEN REPRESENTATIVE SAMPLES")
    print("=" * 70)

    unseen_tests = [
        {
            "category": "Normal Professional Email",
            "subject": "Q4 Financial Review & Strategy Sync",
            "body": "Hi team, please find attached the preliminary revenue figures for Q4. We will review variances during Tuesday's strategy call at 10:00 AM.",
            "expected": "Safe (Ham)",
        },
        {
            "category": "Promotional Email",
            "subject": "Weekend Flash Sale: 40% Off Premium Software Licenses",
            "body": "Exclusive subscriber discount! Upgrade your workstation subscription today with discount code SAVE40. Offer valid until Sunday midnight.",
            "expected": "Promotional / Ham",
        },
        {
            "category": "Lottery & Prize Scam",
            "subject": "URGENT NOTIFICATION: You have won $1,500,000 in International Sweepstakes",
            "body": "Congratulations Valued Winner! Your email address was selected in the annual global lucky draw. Contact claims agent Mr. David Cole with your bank info immediately.",
            "expected": "Spam",
        },
        {
            "category": "Phishing-Style Email",
            "subject": "Critical Security Alert: Suspicious login attempt on your account",
            "body": "Your email credentials have expired. Unauthorized login detected from IP 192.168.1.1. Click http://verify-secure-login-portal.net/auth to confirm password within 12 hours.",
            "expected": "Spam",
        },
        {
            "category": "Genuine Personal Email",
            "subject": "Dinner this Friday?",
            "body": "Hey, it was great catching up last week. Let me know if you are free for dinner at the bistro downtown around 7 PM. Let me know what works!",
            "expected": "Safe (Ham)",
        },
    ]

    for idx, test in enumerate(unseen_tests, 1):
        full_text = f"{test['subject']} {test['body']}"
        cleaned = clean_text(full_text)
        vec = vectorizer.transform([cleaned])

        lr_p = lr_model.predict_proba(vec)[0]
        lr_pred_label = "Spam" if lr_p[1] >= 0.5 else "Safe"
        lr_conf = max(lr_p) * 100

        nb_p = nb_model.predict_proba(vec)[0]
        nb_pred_label = "Spam" if nb_p[1] >= 0.5 else "Safe"
        nb_conf = max(nb_p) * 100

        print(f"\n[{idx}] Category : {test['category']}")
        print(f"    Subject  : \"{test['subject']}\"")
        print(f"    Expected : {test['expected']}")
        print(f"    → Logistic Regression : {lr_pred_label.upper():<5} (Confidence: {lr_conf:.1f}% | Spam Prob: {lr_p[1]*100:.1f}%)")
        print(f"    → Naive Bayes         : {nb_pred_label.upper():<5} (Confidence: {nb_conf:.1f}% | Spam Prob: {nb_p[1]*100:.1f}%)")

    print("\n" + "=" * 70)
    print("  PHASE 3 COMPLETE: Candidate v7 Models Successfully Trained & Evaluated")
    print("  Active production models in ml_models/ remain unchanged (Safe staging).")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()

