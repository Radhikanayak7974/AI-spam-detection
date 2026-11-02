"""
SpamGuard AI - Add Kaggle Dataset Emails to SQLite Database
Reads the Kaggle CSV, inserts emails into the 'emails' table,
runs ML classification on each, and saves predictions.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
from datetime import datetime, timezone

from app import create_app
from database import db
from models import Email, Prediction
from services.ml_service import MLService
from services.sync_service import _classify_email, _save_prediction

KAGGLE_CSV = r"C:/Users/91797/.gemini/antigravity/brain/7aaf19b8-9709-4998-8e97-122e03ee0e8d/.user_uploaded/media_1793626328419_ba29ccbf.csv"

def main():
    print("\n" + "=" * 65)
    print("  📥 SpamGuard AI – Adding Kaggle Dataset to Database")
    print("=" * 65)

    app = create_app()
    with app.app_context():
        # Load Kaggle dataset
        print("\n[1/4] Reading Kaggle dataset...")
        df = pd.read_csv(KAGGLE_CSV, encoding="latin-1")
        df = df[["v1", "v2"]].copy()
        df.columns = ["label", "text"]
        df = df.dropna(subset=["label", "text"])
        df["label"] = df["label"].str.strip().str.lower()
        df["text"] = df["text"].str.strip()
        df = df[df["label"].isin(["ham", "spam"])]
        print(f"  ✅ {len(df)} emails loaded ({(df['label']=='ham').sum()} safe, {(df['label']=='spam').sum()} spam)")

        # Load ML models
        print("\n[2/4] Loading ML models...")
        MLService.load_models(force_reload=True)
        print("  ✅ Models loaded")

        # Insert into database
        print("\n[3/4] Inserting emails into database with AI classification...")
        added = 0
        spam_count = 0
        skipped = 0

        # Use user_id = 1 (system/dataset user) for Kaggle data
        # Check if dataset user exists, create if not
        from models import User
        dataset_user = User.query.filter_by(email="kaggle-dataset@spamguard.local").first()
        if not dataset_user:
            dataset_user = User(
                email="kaggle-dataset@spamguard.local",
                google_id="kaggle-dataset",
                name="Kaggle Dataset",
                is_active=False,
            )
            db.session.add(dataset_user)
            db.session.flush()

        batch_size = 100
        total = len(df)

        for idx, row in df.iterrows():
            text = row["text"]
            original_label = row["label"]

            # Skip if already exists (by exact text match in subject)
            short_text = text[:200]
            existing = Email.query.filter_by(subject=short_text).first()
            if existing:
                skipped += 1
                continue

            # Determine sender based on label
            if original_label == "spam":
                sender = "Spam Source"
                sender_email = "spam@dataset.kaggle"
            else:
                sender = "Legitimate Sender"
                sender_email = "safe@dataset.kaggle"

            # Create email record
            email_obj = Email(
                user_id=dataset_user.id,
                subject=short_text,
                sender=sender,
                sender_email=sender_email,
                body_plain=text,
                snippet=text[:100],
                received_at=datetime(2026, 1, 1 + (idx % 28), 9, 0, 0),
                is_read=True,
                has_attachments=False,
            )
            db.session.add(email_obj)
            db.session.flush()

            # Run ML classification
            clf = _classify_email(text)
            _save_prediction(email_obj, clf)

            if clf["final_label"] == "spam":
                spam_count += 1

            added += 1

            # Commit in batches
            if added % batch_size == 0:
                db.session.commit()
                pct = int((added / total) * 100)
                print(f"  ... {added}/{total} emails processed ({pct}%)")

        # Final commit
        db.session.commit()

        print(f"\n  ✅ Done! {added} new emails added to database")
        print(f"  ✅ {spam_count} classified as SPAM")
        print(f"  ✅ {added - spam_count} classified as SAFE")
        if skipped:
            print(f"  ⏭️  {skipped} duplicates skipped")

        # Show updated counts
        total_emails = Email.query.count()
        total_preds = Prediction.query.count()
        print(f"\n{'─'*65}")
        print(f"  📊 DATABASE UPDATED TOTALS:")
        print(f"  • Total Emails:      {total_emails}")
        print(f"  • Total Predictions: {total_preds}")
        print(f"{'='*65}\n")


if __name__ == "__main__":
    main()

