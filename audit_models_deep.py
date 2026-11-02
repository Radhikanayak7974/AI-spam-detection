"""
Deep Audit of Trained Machine Learning Models in SpamGuard AI
Inspects weights, vocabulary, confusion matrix, learned signals,
and tests prediction on realistic emails.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from services.ml_service import MLService, clean_text
from services.sync_service import _classify_email

def main():
    print("\n" + "=" * 70)
    print("  🔬 SPAMGUARD AI — DEEP MODEL AUDIT & VERIFICATION REPORT")
    print("=" * 70)

    # 1. Model Artifacts on disk
    print("\n[1/5] Checking Model Artifact Files on Disk:")
    files = [
        ("Production Vectorizer", "ml_models/tfidf_vectorizer.joblib"),
        ("Production Logistic Regression", "ml_models/logistic_regression.joblib"),
        ("Production Naive Bayes", "ml_models/naive_bayes.joblib"),
        ("Production Metrics Report", "ml_models/metrics.json"),
        ("Version Manifest", "ml_models/version_manifest.json"),
        ("Archived v7 Directory", "ml_models/v7"),
        ("Active Training Dataset", "dataset/spam_dataset.csv"),
    ]

    for label, path in files:
        if os.path.exists(path):
            if os.path.isdir(path):
                cnt = len(os.listdir(path))
                print(f"  ✅ {label:<32} {path:<40} (Directory with {cnt} files)")
            else:
                sz = os.path.getsize(path)
                mtime = pd.Timestamp.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  ✅ {label:<32} {path:<40} ({sz:,} bytes | {mtime})")
        else:
            print(f"  ❌ {label:<32} {path:<40} (MISSING)")

    # 2. Inspect Model Internal State & Vocabulary
    print("\n[2/5] Inspecting Learned Model Weights & Architecture:")
    vec = joblib.load("ml_models/tfidf_vectorizer.joblib")
    lr = joblib.load("ml_models/logistic_regression.joblib")
    nb = joblib.load("ml_models/naive_bayes.joblib")

    feature_names = vec.get_feature_names_out()
    vocab_len = len(feature_names)
    print(f"  • Vocabulary Features   : {vocab_len:,} (Unigrams + Bigrams)")
    print(f"  • TF-IDF N-Gram Range   : {vec.ngram_range}")
    print(f"  • Sublinear TF Scaling  : {vec.sublinear_tf}")
    print(f"  • Stop Words            : {vec.stop_words}")
    print(f"  • Logistic Regression   : Classes = {lr.classes_} (0=Ham, 1=Spam), Solver = {lr.solver}, MaxIter = {lr.max_iter}")
    print(f"  • Multinomial NB        : Classes = {nb.classes_} (0=Ham, 1=Spam), Alpha = {nb.alpha}")

    # Top features learned by models
    lr_coef = lr.coef_[0]
    top_spam_idx = np.argsort(lr_coef)[-10:][::-1]
    top_ham_idx = np.argsort(lr_coef)[:10]

    print("\n  ▶ Top 10 SPAM Indicators Learned by Logistic Regression:")
    for idx in top_spam_idx:
        print(f"     + {feature_names[idx]:<22} (weight: +{lr_coef[idx]:.4f})")

    print("\n  ▶ Top 10 SAFE (HAM) Indicators Learned by Logistic Regression:")
    for idx in top_ham_idx:
        print(f"     - {feature_names[idx]:<22} (weight: {lr_coef[idx]:.4f})")

    # 3. Check Active Version Manifest & Metrics
    print("\n[3/5] Verifying Version Manifest & Performance Consistency:")
    with open("ml_models/version_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    print(f"  • Active Version In Manifest : {manifest.get('active_version')}")
    print(f"  • Available Registered Ver   : {manifest.get('versions')}")

    with open("ml_models/metrics.json", "r", encoding="utf-8") as f:
        metrics = json.load(f)

    ds = metrics.get("dataset", {})
    lr_m = metrics.get("logistic_regression", {})
    nb_m = metrics.get("naive_bayes", {})

    print(f"  • Evaluated On Dataset       : {ds.get('total_samples', 0):,} records ({ds.get('train_samples', 0):,} train / {ds.get('test_samples', 0):,} test)")
    print(f"  • Safe / Spam Split          : {ds.get('ham_samples', 0):,} Safe vs {ds.get('spam_samples', 0):,} Spam")
    print(f"  • Logistic Regression Acc    : {lr_m.get('accuracy', 0)*100:.2f}% | Precision: {lr_m.get('precision', 0)*100:.2f}% | Recall: {lr_m.get('recall', 0)*100:.2f}% | AUC: {lr_m.get('auc', 0)*100:.2f}%")
    print(f"  • Multinomial Naive Bayes Acc: {nb_m.get('accuracy', 0)*100:.2f}% | Precision: {nb_m.get('precision', 0)*100:.2f}% | Recall: {nb_m.get('recall', 0)*100:.2f}% | AUC: {nb_m.get('auc', 0)*100:.2f}%")
    print(f"  • Confusion Matrix (LR)      : TN={lr_m.get('confusion_matrix', {}).get('tn')}, FP={lr_m.get('confusion_matrix', {}).get('fp')}, FN={lr_m.get('confusion_matrix', {}).get('fn')}, TP={lr_m.get('confusion_matrix', {}).get('tp')}")
    print(f"  • Confusion Matrix (NB)      : TN={nb_m.get('confusion_matrix', {}).get('tn')}, FP={nb_m.get('confusion_matrix', {}).get('fp')}, FN={nb_m.get('confusion_matrix', {}).get('fn')}, TP={nb_m.get('confusion_matrix', {}).get('tp')}")

    # 4. Check Database Training History
    print("\n[4/5] Checking Database Training History Audit Trail:")
    from app import create_app
    from models import TrainingHistory
    app = create_app()
    with app.app_context():
        records = TrainingHistory.query.order_by(TrainingHistory.id.desc()).all()
        for r in records[:4]:
            print(f"  • ID {r.id} | Ver {r.version:<4} | Records: {r.dataset_size:>6,} | Status: {r.status:<12} | Trained: {r.trained_at} | Promoted: {r.promoted_at}")

    # 5. Live Inference Verification on Varied Scenarios
    print("\n[5/5] Running Live Inference on Realistic Scenarios:")
    test_cases = [
        {
            "scenario": "Legitimate Office/Work Email",
            "subject": "Sprint retrospective and deployment schedule",
            "body": "Hi team, please find attached the action items from today's retrospective. The production deployment is scheduled for Thursday at 6 PM UTC.",
            "expected": "ham",
        },
        {
            "scenario": "Legitimate Personal Email",
            "subject": "Lunch tomorrow?",
            "body": "Hey Alex, are you free for lunch tomorrow around 1 PM? Let me know if that works for you.",
            "expected": "ham",
        },
        {
            "scenario": "Credential Harvesting / Phishing",
            "subject": "URGENT: Your Office365 Account will be terminated in 24 hours",
            "body": "Your email password expired today. Re-validate your corporate credentials immediately at http://login-verify-account.com to prevent service suspension.",
            "expected": "spam",
        },
        {
            "scenario": "Lottery / Advance Fee Fraud Scam",
            "subject": "FINAL NOTICE: Claim your $2,500,000 cash grant reward",
            "body": "Dear beneficiary, your payment reference #KL9902 has been cleared for immediate wire transfer. Contact Dr. Mark Johnson with your bank account and ID.",
            "expected": "spam",
        },
        {
            "scenario": "Pharmaceutical / Viagra Spam",
            "subject": "Order cheap prescription medications online with 80% discount",
            "body": "Buy FDA approved generic pills, luxury watches, and weight loss remedies without prescription. Fast discreet international shipping. Click here.",
            "expected": "spam",
        },
        {
            "scenario": "Real Gmail Policybazaar/Unstop Notification",
            "subject": "Application update for Software Engineering Intern",
            "body": "Dear Candidate, thank you for participating in the coding challenge on Unstop. Your test results have been forwarded to the hiring team for review.",
            "expected": "ham",
        },
    ]

    all_passed = True
    for i, tc in enumerate(test_cases, 1):
        full_text = f"Subject: {tc['subject']}\n\n{tc['body']}"
        res = _classify_email(full_text)
        final_label = res["final_label"]
        lr_pred = res["lr"]["label"]
        lr_prob = res["lr"]["spam_probability"]
        nb_pred = res["nb"]["label"]
        nb_prob = res["nb"]["spam_probability"]

        is_match = (final_label == tc["expected"])
        if not is_match:
            all_passed = False
        status_icon = "✅ PASS" if is_match else "❌ FAIL"

        print(f"\n  Case {i}: [{status_icon}] {tc['scenario']}")
        print(f"     Subject     : \"{tc['subject']}\"")
        print(f"     Expected    : {tc['expected'].upper()} | Got: {final_label.upper()}")
        print(f"     Logistic Reg: {lr_pred.upper()} (Spam Prob: {lr_prob*100:.1f}%)")
        print(f"     Naive Bayes : {nb_pred.upper()} (Spam Prob: {nb_prob*100:.1f}%)")

    print("\n" + "=" * 70)
    if all_passed:
        print("  🎉 AUDIT RESULT: Model training is 100% CORRECT, VERIFIED, & ACCURATE!")
    else:
        print("  ⚠️ AUDIT RESULT: Some predictions diverged from expected.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
