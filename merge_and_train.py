"""
SpamGuard AI - Merge Kaggle Dataset + Retrain Model
Merges the new Kaggle email_spam dataset with existing dataset,
saves combined dataset, retrains models, and updates database.
"""

import os
import sys
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd

KAGGLE_CSV = r"C:/Users/91797/.gemini/antigravity/brain/7aaf19b8-9709-4998-8e97-122e03ee0e8d/.user_uploaded/media_1793626328419_ba29ccbf.csv"
EXISTING_CSV = "dataset/spam_dataset.csv"
COMBINED_CSV = "dataset/spam_dataset.csv"
BACKUP_CSV = "dataset/spam_dataset_backup_v1.csv"

def main():
    print("\n" + "=" * 65)
    print("  🔄 SpamGuard AI – Dataset Merge & Model Retraining")
    print("=" * 65)

    # Step 1: Read existing dataset
    print("\n[1/6] Reading existing dataset...")
    df_existing = pd.read_csv(EXISTING_CSV)
    print(f"  ✅ Existing: {len(df_existing)} emails ({(df_existing['label']=='ham').sum()} safe, {(df_existing['label']=='spam').sum()} spam)")

    # Step 2: Read Kaggle dataset
    print("\n[2/6] Reading Kaggle dataset (email_spam.csv)...")
    df_kaggle = pd.read_csv(KAGGLE_CSV, encoding="latin-1")
    # Normalize columns: v1 -> label, v2 -> text
    df_kaggle = df_kaggle[["v1", "v2"]].copy()
    df_kaggle.columns = ["label", "text"]
    # Clean: drop nulls, strip whitespace
    df_kaggle = df_kaggle.dropna(subset=["label", "text"])
    df_kaggle["label"] = df_kaggle["label"].str.strip().str.lower()
    df_kaggle["text"] = df_kaggle["text"].str.strip()
    # Keep only valid labels
    df_kaggle = df_kaggle[df_kaggle["label"].isin(["ham", "spam"])]
    print(f"  ✅ Kaggle:   {len(df_kaggle)} emails ({(df_kaggle['label']=='ham').sum()} safe, {(df_kaggle['label']=='spam').sum()} spam)")

    # Step 3: Merge and deduplicate
    print("\n[3/6] Merging datasets & removing duplicates...")
    df_combined = pd.concat([df_existing, df_kaggle], ignore_index=True)
    before_dedup = len(df_combined)
    df_combined = df_combined.drop_duplicates(subset=["text"], keep="first")
    removed = before_dedup - len(df_combined)
    print(f"  ✅ Combined: {len(df_combined)} unique emails (removed {removed} duplicates)")
    print(f"     → Safe (ham):  {(df_combined['label']=='ham').sum()}")
    print(f"     → Spam:        {(df_combined['label']=='spam').sum()}")

    # Step 4: Backup old dataset & save combined
    print("\n[4/6] Backing up old dataset & saving combined...")
    if not os.path.exists(BACKUP_CSV):
        shutil.copy2(EXISTING_CSV, BACKUP_CSV)
        print(f"  ✅ Backup saved: {BACKUP_CSV}")
    df_combined.to_csv(COMBINED_CSV, index=False)
    print(f"  ✅ Combined dataset saved: {COMBINED_CSV}")

    # Step 5: Retrain models
    print("\n[5/6] Training ML models on combined dataset...")
    from services.ml_service import MLService
    metrics = MLService.train_models()

    lr = metrics.get("logistic_regression", {})
    nb = metrics.get("naive_bayes", {})
    ds = metrics.get("dataset", {})

    print(f"  ✅ Training complete!")
    print(f"\n{'─'*65}")
    print(f"  📊 TRAINING RESULTS:")
    print(f"  • Total Emails:       {ds.get('total_samples')}")
    print(f"  • Safe (Ham):         {ds.get('ham_samples')}")
    print(f"  • Spam:               {ds.get('spam_samples')}")
    print(f"  • Vocabulary Size:    {ds.get('vocab_size')} features")
    print(f"  • Train/Test Split:   {ds.get('train_samples')} / {ds.get('test_samples')}")
    print(f"{'─'*65}")
    print(f"  {'Metric':<18} {'Logistic Regression':<22} {'Naive Bayes'}")
    print(f"  {'─'*55}")
    print(f"  {'Accuracy':<18} {lr.get('accuracy',0)*100:.2f}%{'':<16} {nb.get('accuracy',0)*100:.2f}%")
    print(f"  {'Precision':<18} {lr.get('precision',0)*100:.2f}%{'':<16} {nb.get('precision',0)*100:.2f}%")
    print(f"  {'Recall':<18} {lr.get('recall',0)*100:.2f}%{'':<16} {nb.get('recall',0)*100:.2f}%")
    print(f"  {'F1 Score':<18} {lr.get('f1',0)*100:.2f}%{'':<16} {nb.get('f1',0)*100:.2f}%")
    print(f"  {'ROC-AUC':<18} {lr.get('auc',0)*100:.2f}%{'':<16} {nb.get('auc',0)*100:.2f}%")

    # Step 6: Quick test
    print(f"\n{'─'*65}")
    print("  🧪 LIVE TEST (new model):")
    tests = [
        ("Free entry in 2 a wkly comp to win FA Cup final tkts. Text FA to 87121", "spam"),
        ("Hey, are you coming to the party tonight? Let me know!", "ham"),
        ("URGENT! You have won a prize of $1000. Call 09061701461 to claim", "spam"),
        ("Please find attached the quarterly report for your review.", "ham"),
    ]
    for text, expected in tests:
        pred = MLService.predict(text, "logistic_regression")
        status = "🔴 SPAM" if pred["is_spam"] else "🟢 SAFE"
        print(f"  {status} ({pred['confidence']*100:.1f}%) → \"{text[:55]}...\"")

    print(f"\n{'='*65}")
    print("  ✅ DONE! Model retrained with 6,700+ emails!")
    print("  📌 Backend server ko restart karein (Ctrl+C → python backend/app.py)")
    print("  📌 Phir browser mein http://localhost:5173/inbox refresh karein!")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()

