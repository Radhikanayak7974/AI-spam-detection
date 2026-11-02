"""
SpamGuard AI – Background Scheduler (Phase 3)
APScheduler-based background sync. Runs incremental Gmail sync for all
connected users at a configurable interval. Prevents duplicate scheduler
instances when Flask debug/reloader is active.
"""

import logging
import os
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler = None
_scheduler_lock = threading.Lock()
DEFAULT_SYNC_INTERVAL_MINUTES = 5

# ─────────────────────────────────────────────────────────────────────────────
# Internal sync job
# ─────────────────────────────────────────────────────────────────────────────

def _run_scheduled_sync(app):
    """
    Job function executed by APScheduler.
    Runs inside the Flask application context so DB operations work correctly.
    """
    try:
        with app.app_context():
            from models import OAuthToken, User
            from services.sync_service import run_incremental_sync

            # Find all connected, active users with valid OAuth tokens
            active_tokens = (
                OAuthToken.query.join(User)
                .filter(User.is_active == True)  # noqa: E712
                .all()
            )

            if not active_tokens:
                logger.debug("Scheduler: no active Gmail accounts to sync")
                return

            for token in active_tokens:
                if not token.refresh_token and token.is_expired:
                    logger.info("Scheduler: skipping user %d — token expired, no refresh", token.user_id)
                    continue
                logger.info("Scheduler: running incremental sync for user %d", token.user_id)
                try:
                    result = run_incremental_sync(token.user_id)
                    if result.get("success"):
                        stats = result.get("stats", {})
                        logger.info(
                            "Scheduler sync user %d: %d new, %d classified, %d spam",
                            token.user_id,
                            stats.get("emails_fetched", 0),
                            stats.get("emails_classified", 0),
                            stats.get("spam_detected", 0),
                        )
                    else:
                        logger.warning(
                            "Scheduler sync user %d failed: %s",
                            token.user_id,
                            result.get("message"),
                        )
                except Exception as exc:
                    logger.error(
                        "Scheduler: unhandled error syncing user %d: %s",
                        token.user_id, exc, exc_info=True,
                    )

    except Exception as exc:
        logger.error("Scheduler job crashed: %s", exc, exc_info=True)


# ─────────────────────────────────────────────────────────────────────────────
# Public scheduler lifecycle
# ─────────────────────────────────────────────────────────────────────────────

def init_scheduler(app, interval_minutes: int = DEFAULT_SYNC_INTERVAL_MINUTES):
    """
    Initialize and start the background scheduler.
    IMPORTANT: Only starts in the parent process (not in Flask's reloader child)
    to prevent duplicate scheduler instances in debug mode.
    """
    global _scheduler

    # When Flask debug mode is on, Werkzeug spawns a child reloader process.
    # WERKZEUG_RUN_MAIN=true only in the child.  Start the scheduler only in
    # the parent (where WERKZEUG_RUN_MAIN is absent) or when not using the
    # reloader at all.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        logger.debug("Scheduler: skipping init in Werkzeug reloader child process")
        return

    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            logger.debug("Scheduler already running — skipping re-init")
            return

        jobstores = {"default": MemoryJobStore()}
        executors = {"default": ThreadPoolExecutor(max_workers=2)}
        job_defaults = {"coalesce": True, "max_instances": 1, "misfire_grace_time": 60}

        _scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone="UTC",
        )

        _scheduler.add_job(
            func=_run_scheduled_sync,
            args=[app],
            trigger="interval",
            minutes=interval_minutes,
            id="gmail_sync",
            replace_existing=True,
        )

        try:
            _scheduler.start()
            logger.info(
                "Background scheduler started — Gmail sync every %d minute(s)",
                interval_minutes,
            )
        except Exception as exc:
            logger.error("Failed to start scheduler: %s", exc)
            _scheduler = None


def shutdown_scheduler():
    """Gracefully shut down the background scheduler."""
    global _scheduler
    with _scheduler_lock:
        if _scheduler and _scheduler.running:
            try:
                _scheduler.shutdown(wait=False)
                logger.info("Background scheduler shut down")
            except Exception as exc:
                logger.error("Error shutting down scheduler: %s", exc)
            finally:
                _scheduler = None


def update_sync_interval(interval_minutes: int, app) -> bool:
    """
    Dynamically update the sync interval without restarting the scheduler.
    Returns True if successful.
    """
    global _scheduler
    with _scheduler_lock:
        if _scheduler is None or not _scheduler.running:
            # Scheduler not running — restart with new interval
            init_scheduler(app, interval_minutes)
            return True
        try:
            _scheduler.reschedule_job(
                "gmail_sync",
                trigger="interval",
                minutes=interval_minutes,
            )
            logger.info("Sync interval updated to %d minute(s)", interval_minutes)
            return True
        except Exception as exc:
            logger.error("Failed to update sync interval: %s", exc)
            return False


def is_scheduler_running() -> bool:
    """Return True if the background scheduler is active."""
    return _scheduler is not None and _scheduler.running


def get_scheduler_info() -> dict:
    """Return scheduler status and next run time for the sync job."""
    if not is_scheduler_running():
        return {"running": False, "next_run": None, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger),
        })

    return {
        "running": True,
        "next_run": jobs[0]["next_run"] if jobs else None,
        "jobs": jobs,
    }

