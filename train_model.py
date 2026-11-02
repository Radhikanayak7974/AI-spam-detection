"""
SpamGuard AI - Standalone Model Training & Testing Script
Run with: python train_model.py
"""

import os
import sys

# Ensure backend modules can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.ml_service import MLService, clean_text

def main():
    print("\n" + "=" * 60)
    print("      🚀 SpamGuard AI – Machine Learning Model Training")
    print("=" * 60)
    print("1. Loading dataset (dataset/spam_dataset.csv)...")
    
    try:
        metrics = MLService.train_models()
        print("2. [OK] Text preprocessing completed (cleaned URLs, symbols, emails).")
        print("3. [OK] TF-IDF feature extraction completed (3,000 top n-grams).")
        print("4. [OK] Logistic Regression model trained & saved.")
        print("5. [OK] Multinomial Naive Bayes model trained & saved.")
        print("-" * 60)
        
        lr = metrics.get("logistic_regression", {})
        nb = metrics.get("naive_bayes", {})
        ds = metrics.get("dataset", {})
        
        print("\n📊 TRAINING RESULTS & EVALUATION METRICS:")
        print(f"  • Total Emails in Dataset: {ds.get('total_samples')} ({ds.get('ham_samples')} Safe, {ds.get('spam_samples')} Spam)")
        print(f"  • Vocabulary Features:     {ds.get('vocab_size')} keywords/phrases")
        print(f"  • Training Samples:        {ds.get('train_samples')}")
        print(f"  • Testing Samples:         {ds.get('test_samples')}")
        print("-" * 60)
        print(f"{'Metric':<18} {'Logistic Regression':<22} {'Naive Bayes':<15}")
        print("-" * 60)
        print(f"{'Accuracy':<18} {lr.get('accuracy', 0)*100:.2f}%{'':<16} {nb.get('accuracy', 0)*100:.2f}%")
        print(f"{'Precision':<18} {lr.get('precision', 0)*100:.2f}%{'':<16} {nb.get('precision', 0)*100:.2f}%")
        print(f"{'Recall':<18} {lr.get('recall', 0)*100:.2f}%{'':<16} {nb.get('recall', 0)*100:.2f}%")
        print(f"{'F1 Score':<18} {lr.get('f1', 0)*100:.2f}%{'':<16} {nb.get('f1', 0)*100:.2f}%")
        print(f"{'ROC-AUC':<18} {lr.get('auc', 0)*100:.2f}%{'':<16} {nb.get('auc', 0)*100:.2f}%")
        print("=" * 60)
        print("✅ Models trained and saved successfully to 'ml_models/' directory!")
        print("=" * 60)

        # Quick test examples
        print("\n🧪 TESTING WITH SAMPLE MESSAGES:")
        test_samples = [
            ("🚨 Urgent: Your bank account is locked. Click http://verify-bank.com to claim $5000", "spam"),
            ("Hi team, please find attached the updated project presentation for tomorrow's meeting.", "ham"),
            ("Congratulations! You won the UK international lottery. Wire $100 processing fee now.", "spam"),
            ("Hey Radhika, are you free for lunch today at 1 PM?", "ham"),
        ]

        for text, expected in test_samples:
            pred = MLService.predict(text, model_name="logistic_regression")
            status = "🔴 SPAM" if pred["is_spam"] else "🟢 SAFE"
            conf = pred["confidence"] * 100
            print(f"\nText: \"{text[:65]}...\"")
            print(f"  -> Prediction: {status} (Confidence: {conf:.1f}%)")
            signals = [s["word"] for s in pred.get("top_signals", [])[:3]]
            if signals:
                print(f"  -> Trigger keywords: {', '.join(signals)}")

        print("\n" + "=" * 60)
        print("Tip: Ab aap browser mein 'http://localhost:5173/inbox' par jakar")
        print("apne real emails par is model ka classification dekh sakte hain!")
        print("=" * 60 + "\n")

    except Exception as exc:
        print(f"Training failed: {exc}")

if __name__ == "__main__":
    main()

