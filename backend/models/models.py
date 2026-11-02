"""
SQLAlchemy ORM Models for AI Email Spam Detection.

Models:
    - User: Application user account
    - OAuthToken: Stored Google OAuth 2.0 tokens (encrypted in production)
    - Email: Fetched email records from Gmail
    - Prediction: ML model prediction result per email
    - SyncHistory: Log of Gmail synchronization runs
    - Feedback: User feedback on predictions (for future retraining)
"""
from datetime import datetime, timezone
from database import db


def utcnow():
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


class User(db.Model):
    """Application user – created on first OAuth login."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(128), unique=True, nullable=True)  # set after OAuth
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    picture = db.Column(db.String(512), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    oauth_tokens = db.relationship("OAuthToken", back_populates="user", cascade="all, delete-orphan")
    emails = db.relationship("Email", back_populates="user", cascade="all, delete-orphan")
    sync_history = db.relationship("SyncHistory", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "is_active": self.is_active,
            "has_password": bool(self.password_hash),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.email}>"


class OAuthToken(db.Model):
    """
    Stored Google OAuth 2.0 tokens.
    SECURITY: In production, encrypt token fields at rest.
    Never expose these to the frontend.
    """
    __tablename__ = "oauth_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    token_type = db.Column(db.String(64), default="Bearer")
    scope = db.Column(db.Text, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Phase 3 additions
    gmail_history_id = db.Column(db.String(128), nullable=True)   # for incremental sync
    sync_settings = db.Column(db.Text, nullable=True)              # JSON string of user sync prefs

    # Relationships
    user = db.relationship("User", back_populates="oauth_tokens")

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        exp = self.expires_at
        if exp.tzinfo is not None:
            exp = exp.replace(tzinfo=None)
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        return now_utc >= exp

    def __repr__(self):
        return f"<OAuthToken user_id={self.user_id}>"


class Email(db.Model):
    """Email fetched from Gmail."""
    __tablename__ = "emails"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    gmail_message_id = db.Column(db.String(255), nullable=True, unique=True)
    thread_id = db.Column(db.String(255), nullable=True)
    subject = db.Column(db.Text, nullable=True)
    sender = db.Column(db.String(512), nullable=True)
    sender_email = db.Column(db.String(255), nullable=True)
    recipient = db.Column(db.String(512), nullable=True)
    body_plain = db.Column(db.Text, nullable=True)
    body_html = db.Column(db.Text, nullable=True)
    snippet = db.Column(db.Text, nullable=True)
    received_at = db.Column(db.DateTime, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    has_attachments = db.Column(db.Boolean, default=False)
    labels = db.Column(db.Text, nullable=True)  # JSON string of Gmail label IDs
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="emails")
    prediction = db.relationship("Prediction", back_populates="email", uselist=False, cascade="all, delete-orphan")
    feedback = db.relationship("Feedback", back_populates="email", uselist=False, cascade="all, delete-orphan")

    def to_dict(self, include_body=False):
        data = {
            "id": self.id,
            "gmail_message_id": self.gmail_message_id,
            "subject": self.subject,
            "sender": self.sender,
            "sender_email": self.sender_email,
            "snippet": self.snippet,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "is_read": self.is_read,
            "has_attachments": self.has_attachments,
            "prediction": self.prediction.to_dict() if self.prediction else None,
        }
        if include_body:
            data["body_plain"] = self.body_plain
        return data

    def __repr__(self):
        return f"<Email id={self.id} subject='{self.subject[:30] if self.subject else ''}'>"


class Prediction(db.Model):
    """ML model prediction result for an email."""
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey("emails.id"), nullable=False, unique=True)
    model_name = db.Column(db.String(128), nullable=False)  # e.g., "logistic_regression", "naive_bayes"
    label = db.Column(db.String(32), nullable=False)        # "spam" | "ham"
    confidence = db.Column(db.Float, nullable=False)        # 0.0 – 1.0
    spam_probability = db.Column(db.Float, nullable=True)
    ham_probability = db.Column(db.Float, nullable=True)
    features_used = db.Column(db.Text, nullable=True)       # JSON string of feature info
    processing_time_ms = db.Column(db.Float, nullable=True)
    model_version = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    # Relationships
    email = db.relationship("Email", back_populates="prediction")

    def to_dict(self):
        details = None
        if self.features_used:
            try:
                import json
                details = json.loads(self.features_used)
            except Exception:
                details = None

        return {
            "id": self.id,
            "model_name": self.model_name,
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "spam_probability": round(self.spam_probability, 4) if self.spam_probability is not None else None,
            "ham_probability": round(self.ham_probability, 4) if self.ham_probability is not None else None,
            "details": details,
            "processing_time_ms": self.processing_time_ms,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Prediction email_id={self.email_id} label={self.label} conf={self.confidence:.2f}>"


class SyncHistory(db.Model):
    """Record of each Gmail synchronization run."""
    __tablename__ = "sync_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending")
    # status values: "pending" | "running" | "completed" | "failed"
    emails_fetched = db.Column(db.Integer, default=0)
    emails_processed = db.Column(db.Integer, default=0)
    spam_detected = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    started_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Float, nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="sync_history")

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "emails_fetched": self.emails_fetched,
            "emails_processed": self.emails_processed,
            "spam_detected": self.spam_detected,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }

    def __repr__(self):
        return f"<SyncHistory id={self.id} status={self.status}>"


class Feedback(db.Model):
    """User feedback on a prediction (used for future model retraining)."""
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey("emails.id"), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user_label = db.Column(db.String(32), nullable=False)   # "spam" | "ham"
    model_label = db.Column(db.String(32), nullable=True)   # original model prediction
    is_correction = db.Column(db.Boolean, default=False)    # True if user overrides model
    status = db.Column(db.String(32), default="approved", nullable=False)  # "pending" | "approved" | "rejected"
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    email = db.relationship("Email", back_populates="feedback")
    user = db.relationship("User", backref="feedbacks", foreign_keys=[user_id])

    def to_dict(self):
        email_info = None
        if self.email:
            email_info = {
                "id": self.email.id,
                "subject": self.email.subject,
                "sender": self.email.sender,
                "sender_email": self.email.sender_email,
                "received_at": self.email.received_at.isoformat() if self.email.received_at else None,
                "snippet": self.email.snippet,
            }
        return {
            "id": self.id,
            "email_id": self.email_id,
            "user_id": self.user_id,
            "user_label": self.user_label,
            "model_label": self.model_label,
            "is_correction": self.is_correction,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "email": email_info,
        }

    def __repr__(self):
        return f"<Feedback email_id={self.email_id} user_label={self.user_label} status={self.status}>"


class TrainingHistory(db.Model):
    """Audit trail and metrics history of model retraining runs."""
    __tablename__ = "training_history"

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(64), nullable=False)       # e.g. "v1", "v2"
    model_type = db.Column(db.String(64), default="ensemble_lr_nb")
    dataset_size = db.Column(db.Integer, default=0)
    feedback_samples = db.Column(db.Integer, default=0)
    metrics = db.Column(db.Text, nullable=True)              # JSON string of evaluation metrics
    status = db.Column(db.String(32), default="promoted")    # "promoted" | "rejected" | "rolled_back"
    trained_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    promoted_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.String(255), default="system")
    notes = db.Column(db.Text, nullable=True)

    def to_dict(self):
        import json
        metrics_dict = None
        if self.metrics:
            try:
                metrics_dict = json.loads(self.metrics)
            except Exception:
                metrics_dict = None

        return {
            "id": self.id,
            "version": self.version,
            "model_type": self.model_type,
            "dataset_size": self.dataset_size,
            "feedback_samples": self.feedback_samples,
            "metrics": metrics_dict,
            "status": self.status,
            "trained_at": self.trained_at.isoformat() if self.trained_at else None,
            "promoted_at": self.promoted_at.isoformat() if self.promoted_at else None,
            "created_by": self.created_by,
            "notes": self.notes,
        }

    def __repr__(self):
        return f"<TrainingHistory version={self.version} status={self.status}>"
