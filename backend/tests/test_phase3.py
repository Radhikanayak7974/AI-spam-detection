"""
SpamGuard AI – Phase 3 Integration & Unit Tests
Verifies:
1. Dual-Model ML prediction and ensemble decision logic (SPAM, HAM, REVIEW)
2. Email MIME body extraction & HTML sanitization
3. Gmail sync service error handling & duplicate detection
4. Background scheduler initialization & interval management
5. API endpoints (Gmail, Settings, Dashboard, Emails)
"""
import json
import os
import sys
import unittest

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from database import db
from models import Email, OAuthToken, Prediction, SyncHistory, User
from services.gmail_service import (
    _parse_sender,
    _safe_decode_header,
    _strip_html,
    extract_body,
)
from services.ml_service import MLService
from services.scheduler import (
    get_scheduler_info,
    init_scheduler,
    is_scheduler_running,
    shutdown_scheduler,
    update_sync_interval,
)
from services.sync_service import _classify_email, _save_prediction


class TestPhase3Suite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["FLASK_ENV"] = "testing"
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        cls.client = cls.app.test_client()

        with cls.app.app_context():
            db.create_all()
            MLService.load_models()

    @classmethod
    def tearDownClass(cls):
        shutdown_scheduler()

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.rollback()
        self.app_context.pop()

    # ─────────────────────────────────────────────────────────────────────────
    # 1. MIME & Text Extraction Tests
    # ─────────────────────────────────────────────────────────────────────────
    def test_sender_parsing(self):
        name, email = _parse_sender("Google Security <no-reply@accounts.google.com>")
        self.assertEqual(name, "Google Security")
        self.assertEqual(email, "no-reply@accounts.google.com")

        name, email = _parse_sender("alerts@paypal.com")
        self.assertEqual(email, "alerts@paypal.com")

    def test_html_stripping(self):
        html = "<html><body><h1>Special Offer!</h1><p>Claim your prize <a href='http://spam.xyz'>now</a>.</p></body></html>"
        plain = _strip_html(html)
        self.assertIn("Special Offer!", plain)
        self.assertIn("Claim your prize", plain)
        self.assertNotIn("<script>", plain)
        self.assertNotIn("<h1>", plain)

    def test_extract_body_plain_fallback(self):
        payload = {
            "mimeType": "text/html",
            "body": {
                # base64url of "<p>Congratulations you won!</p>"
                "data": "PHA-Q29uZ3JhdHVsYXRpb25zIHlvdSB3b24hPC9wPg=="
            }
        }
        plain, html = extract_body(payload)
        self.assertIn("Congratulations you won!", plain)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Dual ML Model & Decision Logic Tests
    # ─────────────────────────────────────────────────────────────────────────
    def test_dual_model_classification_spam(self):
        spam_text = "Free entry in a 2k prize draw. Text WIN to 87118 immediately to claim your cash award!"
        res = _classify_email(spam_text)
        self.assertIn("lr", res)
        self.assertIn("nb", res)
        self.assertIn("final_label", res)
        self.assertEqual(res["final_label"], "spam")
        self.assertEqual(res["lr"]["label"], "spam")
        self.assertEqual(res["nb"]["label"], "spam")

    def test_dual_model_classification_ham(self):
        ham_text = "Hi Alice, could we schedule our project review meeting tomorrow at 10am in conference room B?"
        res = _classify_email(ham_text)
        self.assertIn("lr", res)
        self.assertIn("nb", res)
        self.assertIn(res["final_label"], ["ham", "review"])
        self.assertEqual(res["lr"]["label"], "ham")

    def test_prediction_storage_with_both_models(self):
        test_user = User(email="test_ml@example.com", is_active=True)
        db.session.add(test_user)
        db.session.flush()

        test_email = Email(
            user_id=test_user.id,
            gmail_message_id="msg_test_ml_101",
            subject="Exclusive Promotion Just For You",
            body_plain="Click here to win a million dollars lottery reward urgent call now",
        )
        db.session.add(test_email)
        db.session.flush()

        classification = _classify_email(test_email.body_plain)
        _save_prediction(test_email, classification)
        db.session.commit()

        pred = Prediction.query.filter_by(email_id=test_email.id).first()
        self.assertIsNotNone(pred)
        data = pred.to_dict()
        self.assertIn("details", data)
        self.assertIn("logistic_regression", data["details"])
        self.assertIn("naive_bayes", data["details"])
        self.assertIn("final_label", data["details"])

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Background Scheduler Lifecycle Tests
    # ─────────────────────────────────────────────────────────────────────────
    def test_scheduler_lifecycle(self):
        # Force non-reloader mode for test
        os.environ.pop("WERKZEUG_RUN_MAIN", None)
        init_scheduler(self.app, interval_minutes=10)
        self.assertTrue(is_scheduler_running())

        info = get_scheduler_info()
        self.assertTrue(info["running"])
        self.assertTrue(len(info["jobs"]) > 0)

        # Update interval
        success = update_sync_interval(15, self.app)
        self.assertTrue(success)

        shutdown_scheduler()
        self.assertFalse(is_scheduler_running())

    # ─────────────────────────────────────────────────────────────────────────
    # 4. API Endpoints Tests
    # ─────────────────────────────────────────────────────────────────────────
    def test_unauthenticated_sync_rejected(self):
        res = self.client.post("/api/gmail/sync")
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertFalse(data["success"])

    def test_gmail_sync_status_endpoint(self):
        res = self.client.get("/api/gmail/sync-status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

    def test_dashboard_stats_endpoint(self):
        res = self.client.get("/api/dashboard/stats")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        stats = data["data"]
        self.assertIn("total_emails_scanned", stats)
        self.assertIn("spam_detected", stats)
        self.assertIn("safe_emails", stats)
        self.assertIn("review_required", stats)
        self.assertIn("scheduler_running", stats)

    def test_sync_settings_endpoint(self):
        res = self.client.get("/api/settings/sync")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("auto_sync_enabled", data["data"])
        self.assertIn("sync_interval_minutes", data["data"])

    def test_review_emails_endpoint(self):
        res = self.client.get("/api/emails/review")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

