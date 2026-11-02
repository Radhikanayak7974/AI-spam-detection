"""
SpamGuard AI - Phase 4 Integration Tests
Tests for:
- Feedback submission, validation, duplicate updates, listing, stats, patching, deleting.
- Advanced Analytics: overview (with date filters), trends, senders, patterns, model comparison.
- Controlled Retraining Pipeline: feedback collection, validation, training, acceptance criteria,
  version promotion, version audit trail in TrainingHistory, model monitoring & alerts.
"""

import os
import sys
import json
import unittest
from datetime import datetime, timezone, timedelta

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from app import create_app
from database import db
from models import User, Email, Prediction, Feedback, TrainingHistory
from services.ml_service import MLService
from services.retraining_service import RetrainingService


def utcnow():
    return datetime.now(timezone.utc)


class Phase4IntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure app for testing with in-memory SQLite
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db.create_all()

    def setUp(self):
        with self.app.app_context():
            db.session.query(Feedback).delete()
            db.session.query(TrainingHistory).delete()
            db.session.query(Prediction).delete()
            db.session.query(Email).delete()
            db.session.query(User).delete()
            db.session.commit()

            # Seed a test user
            user = User(
                email="testuser@example.com",
                name="Test User",
                google_id="google-user-12345",
            )
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

            # Seed 5 test emails with predictions
            emails_data = [
                {
                    "subject": "Urgent: Wire money to claim your lottery prize",
                    "sender": "Lottery Office <scam@lottery-winner.xyz>",
                    "sender_email": "scam@lottery-winner.xyz",
                    "label": "spam",
                    "confidence": 0.98,
                    "lr_pred": "SPAM",
                    "nb_pred": "SPAM",
                },
                {
                    "subject": "Chase Bank Account Verification Required",
                    "sender": "Security Team <security@bank-verify.xyz>",
                    "sender_email": "security@bank-verify.xyz",
                    "label": "spam",
                    "confidence": 0.95,
                    "lr_pred": "SPAM",
                    "nb_pred": "SPAM",
                },
                {
                    "subject": "Quarterly Financial Engineering Review",
                    "sender": "Sarah Jenkins <sarah@acme-corp.com>",
                    "sender_email": "sarah@acme-corp.com",
                    "label": "ham",
                    "confidence": 0.99,
                    "lr_pred": "HAM",
                    "nb_pred": "HAM",
                },
                {
                    "subject": "Family dinner this Sunday at 7 PM",
                    "sender": "Mom <mom@family.org>",
                    "sender_email": "mom@family.org",
                    "label": "ham",
                    "confidence": 0.97,
                    "lr_pred": "HAM",
                    "nb_pred": "HAM",
                },
                {
                    "subject": "Special Offer: 50% discount on conference pass",
                    "sender": "Tech Summit <info@techsummit.io>",
                    "sender_email": "info@techsummit.io",
                    "label": "review",
                    "confidence": 0.65,
                    "lr_pred": "SPAM",
                    "nb_pred": "HAM",  # Disagreement!
                },
            ]

            self.email_ids = []
            for item in emails_data:
                em = Email(
                    user_id=self.user_id,
                    gmail_message_id=f"msg-{len(self.email_ids)+1}",
                    subject=item["subject"],
                    sender=item["sender"],
                    sender_email=item["sender_email"],
                    body_plain=item["subject"] + " This is the email content body.",
                    received_at=utcnow() - timedelta(days=len(self.email_ids)),
                )
                db.session.add(em)
                db.session.flush()

                pred = Prediction(
                    email_id=em.id,
                    model_name="ensemble_lr_nb",
                    label=item["label"],
                    confidence=item["confidence"],
                    spam_probability=item["confidence"] if item["label"] == "spam" else 1.0 - item["confidence"],
                    ham_probability=1.0 - item["confidence"] if item["label"] == "spam" else item["confidence"],
                    features_used=json.dumps({
                        "logistic_regression": {"prediction": item["lr_pred"], "confidence": item["confidence"]},
                        "naive_bayes": {"prediction": item["nb_pred"], "confidence": item["confidence"]},
                        "top_signals": [
                            {"word": "urgent", "score": 1.45},
                            {"word": "verify", "score": 1.20},
                        ],
                    }),
                )
                db.session.add(pred)
                self.email_ids.append(em.id)

            db.session.commit()

    # ── Feedback Tests ────────────────────────────────────────────────────────

    def test_01_submit_feedback_confirmation(self):
        """Test submitting feedback confirming a model prediction."""
        res = self.client.post(
            "/api/feedback",
            json={
                "email_id": self.email_ids[0],  # spam email
                "user_label": "spam",
                "notes": "Indeed an obvious lottery scam",
            },
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["data"]
        self.assertEqual(data["user_label"], "spam")
        self.assertFalse(data["is_correction"])
        self.assertEqual(data["status"], "approved")

    def test_02_submit_feedback_correction(self):
        """Test submitting feedback overriding a model prediction."""
        res = self.client.post(
            "/api/feedback",
            json={
                "email_id": self.email_ids[1],  # spam email
                "user_label": "ham",            # user marks as false positive!
                "notes": "Legitimate security alert, false alarm",
            },
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()["data"]
        self.assertEqual(data["user_label"], "ham")
        self.assertTrue(data["is_correction"])

    def test_03_submit_feedback_duplicate_prevention(self):
        """Test that submitting feedback twice for the same email updates the existing record."""
        email_id = self.email_ids[2]
        res1 = self.client.post(
            "/api/feedback",
            json={"email_id": email_id, "user_label": "ham", "notes": "Initial note"},
        )
        self.assertEqual(res1.status_code, 201)
        fb_id = res1.get_json()["data"]["id"]

        # Submit again with updated note and label
        res2 = self.client.post(
            "/api/feedback",
            json={"email_id": email_id, "user_label": "spam", "notes": "Updated note"},
        )
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()["data"]
        self.assertEqual(data2["id"], fb_id)  # Same ID!
        self.assertEqual(data2["user_label"], "spam")
        self.assertEqual(data2["notes"], "Updated note")

    def test_04_list_and_stats_feedback(self):
        """Test listing feedback records and retrieving summary stats."""
        # Submit two feedbacks
        self.client.post("/api/feedback", json={"email_id": self.email_ids[0], "user_label": "spam"})
        self.client.post("/api/feedback", json={"email_id": self.email_ids[1], "user_label": "ham"})

        # List
        res_list = self.client.get("/api/feedback?status=all")
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(len(res_list.get_json()["data"]), 2)

        # Stats
        res_stats = self.client.get("/api/feedback/stats")
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.get_json()["data"]
        self.assertEqual(stats["total_feedback"], 2)
        self.assertEqual(stats["corrections_count"], 1)

    def test_05_update_and_delete_feedback(self):
        """Test PATCH and DELETE feedback."""
        res_create = self.client.post(
            "/api/feedback", json={"email_id": self.email_ids[0], "user_label": "spam"}
        )
        fb_id = res_create.get_json()["data"]["id"]

        # Patch
        res_patch = self.client.patch(f"/api/feedback/{fb_id}", json={"status": "rejected"})
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.get_json()["data"]["status"], "rejected")

        # Delete
        res_del = self.client.delete(f"/api/feedback/{fb_id}")
        self.assertEqual(res_del.status_code, 200)

    # ── Analytics Tests ───────────────────────────────────────────────────────

    def test_06_analytics_overview(self):
        """Test GET /api/analytics/overview."""
        res = self.client.get("/api/analytics/overview?filter=all")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertEqual(data["total_predictions"], 5)
        self.assertEqual(data["spam_detected"], 2)
        self.assertEqual(data["safe_emails"], 2)
        self.assertEqual(data["review_required"], 1)
        self.assertEqual(data["disagreement_count"], 1)

    def test_07_analytics_trends(self):
        """Test GET /api/analytics/trends."""
        res = self.client.get("/api/analytics/trends?filter=all&interval=daily")
        self.assertEqual(res.status_code, 200)
        trends = res.get_json()["data"]["trends"]
        self.assertTrue(len(trends) > 0)
        self.assertIn("spam", trends[0])
        self.assertIn("safe", trends[0])

    def test_08_analytics_senders(self):
        """Test GET /api/analytics/senders."""
        res = self.client.get("/api/analytics/senders?filter=all")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("top_senders", data)
        self.assertIn("top_spam_senders", data)
        self.assertTrue(len(data["top_spam_senders"]) > 0)

    def test_09_analytics_patterns(self):
        """Test GET /api/analytics/patterns."""
        res = self.client.get("/api/analytics/patterns")
        self.assertEqual(res.status_code, 200)
        patterns = res.get_json()["data"]["patterns"]
        self.assertTrue(len(patterns) > 0)
        words = [p["word"] for p in patterns]
        self.assertTrue("urgent" in words or "verify" in words)

    def test_10_analytics_model_comparison(self):
        """Test GET /api/analytics/model-comparison."""
        res = self.client.get("/api/analytics/model-comparison")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()["data"]
        self.assertIn("test_dataset_benchmarks", data)
        self.assertIn("live_gmail_statistics", data)
        live = data["live_gmail_statistics"]
        self.assertEqual(live["disagreement_count"], 1)

    # ── Retraining & Monitoring Tests ─────────────────────────────────────────

    def test_11_model_versions_and_monitoring(self):
        """Test /api/models/versions and /api/models/monitoring endpoints."""
        res_v = self.client.get("/api/models/versions")
        self.assertEqual(res_v.status_code, 200)
        self.assertIn("active_version", res_v.get_json()["data"])

        res_m = self.client.get("/api/models/monitoring")
        self.assertEqual(res_m.status_code, 200)
        m_data = res_m.get_json()["data"]
        self.assertIn("distribution", m_data)
        self.assertIn("alerts", m_data)

    def test_12_controlled_retraining_pipeline(self):
        """Test running the controlled retraining pipeline with feedback records."""
        with self.app.app_context():
            # Seed 2 approved feedback records
            fb1 = Feedback(
                email_id=self.email_ids[0],
                user_label="spam",
                status="approved",
                is_correction=False,
            )
            fb2 = Feedback(
                email_id=self.email_ids[2],
                user_label="ham",
                status="approved",
                is_correction=False,
            )
            db.session.add(fb1)
            db.session.add(fb2)
            db.session.commit()

            result = RetrainingService.retrain_pipeline(
                acceptance_threshold_margin=0.10,
                created_by="test_suite",
            )

            self.assertTrue(result["success"])
            self.assertIn("promoted", result)
            self.assertIn("version", result)

            # Check TrainingHistory record was created
            history = TrainingHistory.query.order_by(TrainingHistory.id.desc()).first()
            self.assertIsNotNone(history)
            self.assertEqual(history.created_by, "test_suite")


if __name__ == "__main__":
    unittest.main()

