"""
SpamGuard AI - Comprehensive System Verification Suite
Tests database, ML models, API endpoints, classification pipeline, and configuration.
"""

import os
import sys
import json
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app import create_app
from database import db
from models import User, OAuthToken, Email, Prediction, SyncHistory, Feedback, TrainingHistory
from services.ml_service import MLService
from services.sync_service import _classify_email
from services.retraining_service import RetrainingService

def run_tests():
    print("\n" + "=" * 70)
    print("  🔍 SpamGuard AI — Complete System Diagnostic & Health Check")
    print("=" * 70)

    passed_count = 0
    total_tests = 0

    def record_test(name, success, details=""):
        nonlocal passed_count, total_tests
        total_tests += 1
        status = "✅ PASS" if success else "❌ FAIL"
        if success:
            passed_count += 1
        print(f"  [{status}] {name}")
        if details:
            print(f"         {details}")

    app = create_app()
    client = app.test_client()

    with app.app_context():
        # ── Test 1: Database Tables & Records ────────────────────────
        print("\n[Section 1: Database & Persistence Layer]")
        try:
            users_c = User.query.count()
            emails_c = Email.query.count()
            preds_c = Prediction.query.count()
            tokens_c = OAuthToken.query.count()
            sync_c = SyncHistory.query.count()
            fb_c = Feedback.query.count()
            th_c = TrainingHistory.query.count()
            record_test(
                "SQLite Database Tables Connection",
                True,
                f"Users={users_c}, Emails={emails_c}, Preds={preds_c}, Tokens={tokens_c}, Sync={sync_c}, Feedback={fb_c}, TrainingHist={th_c}"
            )
        except Exception as e:
            record_test("SQLite Database Tables Connection", False, str(e))

        # ── Test 2: OAuth Token Verification ─────────────────────────
        try:
            token = OAuthToken.query.first()
            if token and token.access_token:
                record_test(
                    "Google OAuth Token Integrity",
                    True,
                    f"User ID={token.user_id}, Has refresh_token={bool(token.refresh_token)}, Expires={token.expires_at}"
                )
            else:
                record_test("Google OAuth Token Integrity", False, "No active token found")
        except Exception as e:
            record_test("Google OAuth Token Integrity", False, str(e))

        # ── Test 3: ML Models & Version Manifest ─────────────────────
        print("\n[Section 2: Machine Learning Models & Pipeline]")
        try:
            is_trained = MLService.is_trained()
            record_test("ML Model Artifacts on Disk", is_trained, "lr, nb, tfidf present in ml_models/")
        except Exception as e:
            record_test("ML Model Artifacts on Disk", False, str(e))

        try:
            manifest = RetrainingService.get_manifest()
            act_ver = manifest.get("active_version")
            record_test(
                "Version Manifest Check",
                act_ver == "v7",
                f"Active Version={act_ver}, Available Versions={manifest.get('versions')}"
            )
        except Exception as e:
            record_test("Version Manifest Check", False, str(e))

        try:
            metrics = MLService.get_metrics()
            lr_acc = metrics.get("logistic_regression", {}).get("accuracy")
            nb_acc = metrics.get("naive_bayes", {}).get("accuracy")
            ds_size = metrics.get("dataset", {}).get("total_samples")
            record_test(
                "Model Performance Metrics Consistency",
                bool(lr_acc and nb_acc and ds_size == 30462),
                f"Dataset={ds_size}, LR Accuracy={lr_acc*100:.2f}%, NB Accuracy={nb_acc*100:.2f}%"
            )
        except Exception as e:
            record_test("Model Performance Metrics Consistency", False, str(e))

        # ── Test 4: Live Inference (Ham & Spam) ───────────────────────
        try:
            lr_res = MLService.predict("Hi team, please find the quarterly report attached for your review.", "logistic_regression")
            nb_res = MLService.predict("Congratulations! You won $1,000,000 in the UK Lottery! Claim now.", "naive_bayes")
            ham_ok = lr_res["label"].lower() == "ham"
            spam_ok = nb_res["label"].lower() == "spam"
            record_test(
                "ML Inference (Ham/Spam Discrimination)",
                ham_ok and spam_ok,
                f"Ham test -> {lr_res['label']} ({lr_res['confidence']*100:.1f}%), Spam test -> {nb_res['label']} ({nb_res['confidence']*100:.1f}%)"
            )
        except Exception as e:
            record_test("ML Inference (Ham/Spam Discrimination)", False, str(e))

        # ── Test 5: Gmail Sync Classifier ────────────────────────────
        try:
            clf_ham = _classify_email("Hi, let's meet tomorrow at 10 AM to discuss the product roadmap.")
            clf_spam = _classify_email("URGENT ACCOUNT VERIFICATION: Confirm your credit card details immediately.")
            sync_ok = clf_ham["final_label"] == "ham" and clf_spam["final_label"] == "spam"
            record_test(
                "Gmail Sync Classifier Integration",
                sync_ok,
                f"Meeting email -> {clf_ham['final_label']}, Phishing email -> {clf_spam['final_label']}"
            )
        except Exception as e:
            record_test("Gmail Sync Classifier Integration", False, str(e))

        # ── Section 3: REST API Endpoints ────────────────────────────
        print("\n[Section 3: Flask REST API Endpoints]")

        endpoints = [
            ("GET", "/api/health", None, 200),
            ("GET", "/api/auth/status", None, 200),
            ("GET", "/api/dashboard/stats", None, 200),
            ("GET", "/api/emails?page=1&per_page=5", None, 200),
            ("GET", "/api/models/performance", None, 200),
            ("GET", "/api/models/versions", None, 200),
            ("GET", "/api/models/monitoring", None, 200),
            ("GET", "/api/feedback/stats", None, 200),
            ("GET", "/api/settings/sync", None, 200),
            ("POST", "/api/models/predict", {"text": "Weekly status update meeting notes", "model": "logistic_regression"}, 200),
        ]

        for method, route, body, expected_status in endpoints:
            try:
                t0 = time.time()
                if method == "GET":
                    res = client.get(route)
                else:
                    res = client.post(route, json=body)
                elapsed = (time.time() - t0) * 1000
                is_ok = res.status_code == expected_status
                data = res.get_json(silent=True) or {}
                msg = data.get("message", "")
                record_test(
                    f"{method} {route}",
                    is_ok,
                    f"Status={res.status_code} ({elapsed:.1f}ms) | Response success={data.get('success', False)}"
                )
            except Exception as e:
                record_test(f"{method} {route}", False, str(e))

        # ── Section 4: Version Alignment Verification ────────────────
        print("\n[Section 4: Frontend / Backend Version Alignment]")
        try:
            perf_res = client.get("/api/models/performance").get_json()
            vers_res = client.get("/api/models/versions").get_json()

            perf_ver = perf_res.get("data", {}).get("active_version")
            vers_ver = vers_res.get("data", {}).get("active_version")
            latest_hist = vers_res.get("data", {}).get("history", [{}])[0]
            hist_ver = latest_hist.get("version")
            hist_size = latest_hist.get("dataset_size")

            aligned = (perf_ver == "v7" and vers_ver == "v7" and hist_ver == "v7" and hist_size == 30462)
            record_test(
                "Full Version & Count Alignment across APIs",
                aligned,
                f"Performance active_version={perf_ver}, Versions active_version={vers_ver}, History top version={hist_ver} (size={hist_size})"
            )
        except Exception as e:
            record_test("Full Version & Count Alignment across APIs", False, str(e))

    # ── Summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    pct = (passed_count / total_tests) * 100 if total_tests > 0 else 0
    print(f"  DIAGNOSTIC RESULT: {passed_count}/{total_tests} Tests Passed ({pct:.1f}%)")
    if passed_count == total_tests:
        print("  🎉 ALL SYSTEMS OPERATING NORMALLY AND ERROR-FREE!")
    else:
        print("  ⚠️ Some tests failed. Please inspect the details above.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_tests()
