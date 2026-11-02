# SpamGuard AI – Email Spam Detection

A full-stack AI-powered email spam detection platform using **Logistic Regression** and **Multinomial Naive Bayes** ML models, with automated **Gmail OAuth 2.0 API synchronization** and background classification.

---

## Project Structure

```
ai-email-spam-detection/
├── frontend/              # React 18 + Vite + Tailwind CSS
│   └── src/
│       ├── components/    # Reusable UI components (EmailTable, StatusBadge, etc.)
│       ├── pages/         # Page-level components (GmailInbox, Overview, Settings, etc.)
│       ├── layouts/       # DashboardLayout
│       ├── services/      # Axios API client (api.js)
│       ├── hooks/         # Custom React hooks (useApi.js)
│       └── styles/        # Global CSS & Tailwind configuration
├── backend/               # Python Flask API
│   ├── app.py             # Application factory & APScheduler initialization
│   ├── config.py          # Environment config & Google credentials
│   ├── routes/            # Flask blueprints (health, auth, dashboard, emails, models, gmail, settings)
│   ├── models/            # SQLAlchemy ORM models (User, OAuthToken, Email, Prediction, SyncHistory)
│   ├── services/          # Business logic:
│   │   ├── gmail_service.py   # Gmail API client, MIME parser, token refresh
│   │   ├── sync_service.py    # Inbox sync, duplicate prevention, dual-model ML pipeline
│   │   ├── scheduler.py       # APScheduler background sync job runner
│   │   ├── oauth_service.py   # Google OAuth 2.0 flow & callback handler
│   │   └── ml_service.py      # Logistic Regression & Multinomial Naive Bayes models
│   ├── database/          # DB instance & migration scripts
│   └── tests/             # Unit and integration test suite (test_phase3.py)
├── dataset/               # Training datasets (spam_dataset.csv)
├── ml_models/             # Serialized joblib models & vectorizer (metrics.json)
├── requirements.txt       # Python dependencies (includes APScheduler & beautifulsoup4)
├── .env.example           # Environment template
└── README.md
```

---

## Development Phases

- ✅ **Phase 1** – Foundation & UI (Complete)
- ✅ **Phase 2** – ML Model Training (Logistic Regression & Naive Bayes) + Live Inference + Gmail OAuth 2.0 (Complete)
- ✅ **Phase 3** – Real Gmail Inbox Synchronization + Background Scheduler + Automatic ML Dual-Classification (Complete)
- ✅ **Phase 4** – Advanced Analytics, User Feedback Loop & Controlled Model Retraining (Complete)
- 🔲 **Phase 5** – Production Deployment & Containerization

---

## Phase 4 Features

1. **Advanced Analytics & Threat Intelligence**:
   - Filter by date: **Today**, **Last 7 Days**, **Last 30 Days**, **Last 90 Days**, **All Time**, or **Custom Range**.
   - All analytics computed directly from stored SQLite database records (no mock/fake statistics).
   - Time-series classification trends with **Daily**, **Weekly**, and **Monthly** grouping via responsive Recharts.
   - Top threat senders and email domain distribution.
   - Explainable AI discriminative spam keywords cloud extracted from prediction signal tokens.
   - Head-to-head comparison between Logistic Regression and Naive Bayes: test-set benchmarks vs live Gmail performance.

2. **User Feedback Loop**:
   - Interactive feedback controls in the Email Detail Modal:
     - **Mark as Spam**
     - **Mark as Safe (Not Spam)**
     - **Report Incorrect (Toggle Override)**
     - **Confirm Classification**
     - User audit notes field.
   - Records user feedback in the `feedback` table associated with `email_id` and `user_id`.
   - Automatic calculation of `is_correction` (flagging false positives and false negatives).
   - Safe upsert mechanism prevents duplicate records for the same email.

3. **Feedback Management & Data Curation Page (`/feedback`)**:
   - Comprehensive feedback audit dashboard with live KPI metrics: Total Feedback, User Disagreements, Approved for Training, and User Agreement Rate.
   - Full-text search across email subject, sender, and feedback notes.
   - Filtering by status (`approved`, `pending`, `rejected`), label (`spam`, `ham`), and `corrections_only`.
   - Curator action buttons to approve, reject, or delete feedback entries.

4. **Controlled Model Retraining Pipeline**:
   - Curates approved user feedback samples from the database (`status == 'approved'`).
   - Validates labels, deduplicates text, and enforces class balance.
   - Combines approved feedback with base dataset (`dataset/spam_dataset.csv`).
   - Trains new candidate **Logistic Regression** and **Multinomial Naive Bayes** models using stratified train/test splitting.
   - Strict validation acceptance policy: candidate models must satisfy performance thresholds (≥85% accuracy and no severe drop vs current production).
   - **Versioned Model Storage**:
     - `ml_models/v1/`, `ml_models/v2/`, etc., holding `logistic_regression.joblib`, `naive_bayes.joblib`, `tfidf_vectorizer.joblib`, and `metrics.json`.
     - Manifest management (`version_manifest.json`) tracking active version.
     - Automatically promotes accepted candidate models to production and reloads `MLService` memory without server restart.
     - Logs complete retraining metadata, metrics, and promotion decisions to `training_history` table.

5. **Real-Time Model Monitoring & Drift Alerts**:
   - Live prediction distribution breakdown (Spam vs Safe vs Disagreed Review).
   - Live inter-model disagreement rate tracking.
   - User correction rate tracking (frequency of human overrides).
   - Automatic health alerts: `HIGH_DISAGREEMENT` (if >15%), `HIGH_CORRECTION_RATE` (if >10%), or `OPTIMAL`.

---

## Phase 4 API Endpoints

### Feedback Endpoints
- `POST /api/feedback` – Submit or update email feedback (`email_id`, `user_label`, `notes`, `status`).
- `GET /api/feedback` – Paginated feedback list with search, status, and label filters.
- `GET /api/feedback/stats` – Summary feedback metrics (total, corrections, approved, agreement rate).
- `PATCH /api/feedback/<id>` – Update feedback status (`approved`, `pending`, `rejected`) or notes.
- `DELETE /api/feedback/<id>` – Remove a feedback record.

### Analytics Endpoints
- `GET /api/analytics/overview` – Aggregated email, spam, safe, review, disagreement, and correction metrics with date filters (`today`, `7d`, `30d`, `90d`, `all`, `custom`).
- `GET /api/analytics/trends` – Time-series email classification trends (`daily`, `weekly`, `monthly`).
- `GET /api/analytics/senders` – Top senders, top spam senders, and top sender domains.
- `GET /api/analytics/patterns` – Frequently detected spam keywords and feature signals.
- `GET /api/analytics/model-comparison` – Dual-model benchmark metrics vs live Gmail prediction stats.

### Model Retraining & Monitoring Endpoints
- `POST /api/models/retrain` – Execute controlled model retraining pipeline with approved feedback.
- `GET /api/models/versions` – Model version manifest, active version, and `training_history` audit log.
- `GET /api/models/monitoring` – Model prediction distribution, live disagreement rate, correction rate, and health alerts.

---

## Phase 3 Features

1. **Official Gmail API Integration**:
   - Authenticated client built with user OAuth tokens (`google-api-python-client`).
   - Automatic token refresh via Google OAuth2 credentials.
   - Handles rate limiting, quota errors (HTTP 429), and network failures with retry backoff.
2. **Robust MIME Parser**:
   - Recursively decodes `multipart/alternative`, `multipart/mixed`, and Base64URL-encoded parts.
   - Converts HTML to sanitized plain text using standard parser without executing unsafe scripts.
   - Extracts sender name, email address, subject, timestamps, snippets, read status, and label IDs.
3. **Full & Incremental Synchronization**:
   - Duplicate prevention via unique `gmail_message_id`.
   - Incremental synchronization powered by Gmail History API (`historyId`).
   - Automatic fallback to controlled full sync if historyId expires.
4. **Automatic Dual-Model ML Classification**:
   - Every fetched email text is passed into both **Logistic Regression** and **Multinomial Naive Bayes**.
   - Generates confidence scores and spam probabilities for both models.
   - **Ensemble Decision Logic**:
     - Both SPAM &rarr; `SPAM`
     - Both HAM &rarr; `SAFE`
     - Disagree &rarr; `REVIEW REQUIRED`
   - Detailed breakdown and top signal keywords saved to the `Prediction` table.
5. **Background Scheduler (APScheduler)**:
   - Configurable sync interval (default: 5 minutes).
   - Prevents duplicate scheduler instances under Flask debug/reloader.
   - Per-user sync locking prevents concurrent overlapping executions.
   - Skips inactive or unauthenticated accounts safely.
6. **Dashboard & Inbox UI Updates**:
   - Real-time sync triggers: **Sync New** (incremental) and **Full Sync**.
   - Interactive Email Detail Modal showing dual-model confidence breakdown and top signal keywords.
   - Live scheduler management in the Settings tab.

---

## Quick Start (Windows PowerShell)

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm 9+
- Google Cloud Project with Gmail API enabled (for live synchronization)

---

### 1. Environment Configuration

Create or update your `.env` file in the project root:

```powershell
cp .env.example .env
```

Edit `.env` and configure your Google OAuth 2.0 credentials:

```env
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-change-in-production

DATABASE_URL=sqlite:///spam_detection.db
FRONTEND_URL=http://localhost:5173

GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/auth/callback
```

> **Google Cloud Setup Instructions**:
> 1. Open [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
> 2. Enable the **Gmail API** in APIs & Services &rarr; Library.
> 3. Go to **Credentials &rarr; Create Credentials &rarr; OAuth client ID** (Web application).
> 4. Add Authorized redirect URI: `http://localhost:5000/api/auth/callback`.
> 5. Add Authorized JavaScript origin: `http://localhost:5173`.
> 6. Add Scopes: `openid`, `.../auth/userinfo.email`, `.../auth/gmail.readonly`.
> 7. Add your email address under **OAuth consent screen &rarr; Test users**.

---

### 2. Backend Setup & Startup

```powershell
# Navigate to project root
cd e:\AI-spam-detection

# Install Python requirements
pip install -r requirements.txt

# Run database schema migration
python backend\database\migrate_phase3.py

# Start Flask backend server
python backend\app.py
```

Backend will start at: **http://localhost:5000**
- API Base: `http://localhost:5000/api`
- Health Check: `http://localhost:5000/api/health`

---

### 3. Frontend Setup & Startup

In a separate terminal:

```powershell
cd e:\AI-spam-detection\frontend

# Install node dependencies
npm install

# Start Vite development server
npm run dev
```

Frontend runs at: **http://localhost:5173**

---

## Running the Automated Test Suites

Run the Phase 4 test suite covering the user feedback loop, duplicate prevention, analytics queries, controlled model retraining pipeline, versioning, and monitoring alerts:

```powershell
cd e:\AI-spam-detection
python backend\tests\test_phase4.py
```

Expected output:
```
Ran 12 tests in ~1.2s
OK
```

Run the Phase 3 test suite covering MIME parsing, ML dual-model inference, sync service, background scheduler, and API endpoints:

```powershell
cd e:\AI-spam-detection
python backend\tests\test_phase3.py
```

Expected output:
```
Ran 12 tests in ~0.3s
OK
```

---

## API Endpoints Reference

### Authentication & Gmail
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/status` | Gmail connection status and user details |
| GET | `/api/auth/login` | Initiates Google OAuth consent flow |
| GET | `/api/auth/callback` | OAuth redirect callback handler |
| POST | `/api/auth/logout` | Disconnects account and clears tokens |
| POST | `/api/gmail/sync` | Triggers inbox synchronization (`{ "full": true/false }`) |
| GET | `/api/gmail/sync-status` | Current sync state and last sync history |
| GET | `/api/gmail/messages` | Paginated messages with ML predictions |

### Dashboard & Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | Database statistics (total scanned, spam, safe, review required, scheduler status) |
| GET | `/api/dashboard/recent-activity` | 10 most recent email predictions |

### Emails
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/emails` | Paginated emails list (supports `?label=spam|ham|review`) |
| GET | `/api/emails/<id>` | Single email detail with prediction metadata |
| GET | `/api/emails/spam` | Paginated spam emails |
| GET | `/api/emails/safe` | Paginated safe/ham emails |
| GET | `/api/emails/review` | Emails where ML models disagreed |

### Settings & Scheduler
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings/sync` | Read auto-sync preferences and scheduler status |
| PUT | `/api/settings/sync` | Update sync interval and auto-sync toggle |

### Models & Training
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/models/performance` | Metrics for Logistic Regression & Naive Bayes |
| POST | `/api/models/predict` | Live single text inference endpoint |
| POST | `/api/models/train` | Retrain models against dataset |

---

## Troubleshooting

- **Google OAuth Consent Warning / 403 Access Not Configured**:
  Ensure your Google Cloud app is published or your Gmail account is added under **OAuth consent screen &rarr; Test users**.
- **Missing Columns in SQLite**:
  Run `python backend\database\migrate_phase3.py` to ensure `gmail_history_id` and `sync_settings` exist on `oauth_tokens`.
- **Token Expiry**:
  The system automatically uses the stored `refresh_token` to fetch a fresh `access_token` when connecting to Gmail. If refresh fails (e.g. access revoked by user), disconnect and reconnect via the UI.
