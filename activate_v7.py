"""
SpamGuard AI - Phase 4: Promotion & Activation of Model Version v7
Executes ONLY upon user approval.
Promotes v7 artifacts to production, updates manifest, training_history,
and active dataset, and reloads models in memory.
"""

import os
import sys
import json
import shutil
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

MODELS_DIR = "ml_models"
V7_DIR = os.path.join(MODELS_DIR, "v7")
MANIFEST_FILE = os.path.join(MODELS_DIR, "version_manifest.json")
CLEANED_DATASET = "dataset/processed/enron_spam_cleaned.csv"
ACTIVE_DATASET = "dataset/spam_dataset.csv"

def activate_v7():
    print("\n" + "=" * 65)
    print("  🚀 SpamGuard AI — Activating & Promoting Model Version v7")
    print("=" * 65)

    if not os.path.exists(V7_DIR):
        raise FileNotFoundError(f"Candidate v7 directory missing at {V7_DIR}")

    # 1. Copy candidate artifacts to root ml_models/
    print("\n[1/5] Promoting v7 artifacts to production ml_models/ ...")
    for fname in ["tfidf_vectorizer.joblib", "logistic_regression.joblib", "naive_bayes.joblib", "metrics.json"]:
        src = os.path.join(V7_DIR, fname)
        dst = os.path.join(MODELS_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  ✅ Promoted: {fname}")

    # 2. Update version_manifest.json
    print("\n[2/5] Updating version_manifest.json ...")
    manifest = {}
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    
    manifest["current_version"] = "v7"
    manifest["active_version"] = "v7"
    if "v7" not in manifest.get("versions", []):
        manifest.setdefault("versions", []).append("v7")
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("  ✅ version_manifest.json set to active_version='v7'")

    # 3. Update active dataset to Enron cleaned dataset
    print("\n[3/5] Updating active dataset (dataset/spam_dataset.csv) ...")
    if os.path.exists(CLEANED_DATASET):
        shutil.copy2(CLEANED_DATASET, ACTIVE_DATASET)
        print(f"  ✅ Copied {CLEANED_DATASET} to {ACTIVE_DATASET}")

    # 4. Update training_history status in database to 'promoted'
    print("\n[4/5] Updating database TrainingHistory record to 'promoted' ...")
    from app import create_app
    from database import db
    from models import TrainingHistory

    app = create_app()
    with app.app_context():
        record = TrainingHistory.query.filter_by(version="v7").first()
        if record:
            record.status = "promoted"
            record.promoted_at = datetime.now(timezone.utc)
            record.notes = (record.notes or "") + " [Promoted to production upon user approval]"
            db.session.commit()
            print(f"  ✅ TrainingHistory ID {record.id} updated: status='promoted'")
        else:
            print("  ⚠️ TrainingHistory record for v7 not found, creating one...")
            with open(os.path.join(V7_DIR, "metrics.json"), "r", encoding="utf-8") as f:
                v7_metrics = f.read()
            record = TrainingHistory(
                version="v7",
                model_type="ensemble_lr_nb",
                dataset_size=30462,
                feedback_samples=0,
                metrics=v7_metrics,
                status="promoted",
                trained_at=datetime.now(timezone.utc),
                promoted_at=datetime.now(timezone.utc),
                created_by="admin_training",
                notes="Trained on Enron email corpus (30,462 records). Promoted to production.",
            )
            db.session.add(record)
            db.session.commit()
            print(f"  ✅ Created new TrainingHistory record ID {record.id}")

    # 5. Reload models in MLService
    print("\n[5/5] Reloading models into MLService memory ...")
    from services.ml_service import MLService
    with app.app_context():
        MLService.load_models(force_reload=True)
        print("  ✅ MLService successfully reloaded v7 models")

    print("\n" + "=" * 65)
    print("  🎉 VERSION v7 ACTIVATION COMPLETE!")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    activate_v7()

