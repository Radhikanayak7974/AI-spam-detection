"""
AI Email Spam Detection – Flask Application Entry Point
Phase 1: Foundation

Run with:
    cd backend
    python app.py
"""
import os
import sys

# Make sure the backend directory is on sys.path so local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from config import get_config
from database import db
from routes import health_bp, auth_bp, dashboard_bp, emails_bp, models_bp, gmail_bp, settings_bp, feedback_bp, analytics_bp


def create_app(config_class=None):
    """Application factory."""
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["FRONTEND_URL"]}},
        supports_credentials=True,
    )

    # ── Database ──────────────────────────────────────────────────────────────
    db.init_app(app)

    with app.app_context():
        # Import models so SQLAlchemy knows about them before create_all
        from models import User, OAuthToken, Email, Prediction, SyncHistory, Feedback, TrainingHistory  # noqa: F401
        db.create_all()
        print("[DB] Tables created / verified.")

    # ── Blueprints ────────────────────────────────────────────────────────────
    api_prefix = "/api"
    app.register_blueprint(health_bp,    url_prefix=api_prefix)
    app.register_blueprint(auth_bp,      url_prefix=api_prefix)
    app.register_blueprint(dashboard_bp, url_prefix=api_prefix)
    app.register_blueprint(emails_bp,    url_prefix=api_prefix)
    app.register_blueprint(models_bp,    url_prefix=api_prefix)
    app.register_blueprint(gmail_bp,     url_prefix=api_prefix)   # Phase 3
    app.register_blueprint(settings_bp,  url_prefix=api_prefix)   # Phase 3
    app.register_blueprint(feedback_bp,  url_prefix=api_prefix)   # Phase 4
    app.register_blueprint(analytics_bp, url_prefix=api_prefix)   # Phase 4

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(exc):
        return jsonify({"success": False, "message": "Endpoint not found", "data": None}), 404

    @app.errorhandler(405)
    def method_not_allowed(exc):
        return jsonify({"success": False, "message": "Method not allowed", "data": None}), 405

    @app.errorhandler(500)
    def internal_error(exc):
        return jsonify({"success": False, "message": "Internal server error", "data": None}), 500

    @app.errorhandler(Exception)
    def handle_exception(exc):
        app.logger.exception("Unhandled exception: %s", exc)
        return jsonify({"success": False, "message": str(exc), "data": None}), 500

    # ── Phase 3: ML pre-load + Background Scheduler ───────────────────────────
    with app.app_context():
        try:
            from services.ml_service import MLService
            MLService.load_models()
            print("[ML] Models loaded into memory.")
        except Exception as exc:
            print(f"[ML] Warning: Could not pre-load models: {exc}")

    from services.scheduler import init_scheduler, shutdown_scheduler
    init_scheduler(app, interval_minutes=5)

    import atexit
    atexit.register(shutdown_scheduler)

    return app


# ── Entry point ───────────────────────────────────────────────────────────────
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n{'=' * 60}")
    print("  SpamGuard AI – Flask Backend (Phase 4)")
    print(f"  Gmail Sync + Retraining + Analytics | http://localhost:{port}")
    print(f"  API Base                       | http://localhost:{port}/api")
    print(f"  Health Check                   | http://localhost:{port}/api/health")
    print(f"{'=' * 60}\n")
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", True))
