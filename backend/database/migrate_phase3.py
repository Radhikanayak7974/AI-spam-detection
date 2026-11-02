"""
Database schema verification and Phase 3 migration.
Adds missing columns to existing SQLite database tables safely.
"""
import os
import sqlite3

def migrate():
    # Database path (backend/instance/spam_detection.db or backend/spam_detection.db)
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "..", "instance", "spam_detection.db"),
        os.path.join(os.path.dirname(__file__), "..", "spam_detection.db"),
    ]

    migrated = 0
    for path in possible_paths:
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            print(f"Checking database at: {abs_path}")
            conn = sqlite3.connect(abs_path)
            cur = conn.cursor()

            # 1. oauth_tokens table
            cur.execute("PRAGMA table_info(oauth_tokens)")
            cols = [r[1] for r in cur.fetchall()]
            if "gmail_history_id" not in cols:
                print("Adding column gmail_history_id to oauth_tokens...")
                cur.execute("ALTER TABLE oauth_tokens ADD COLUMN gmail_history_id VARCHAR(128)")
                migrated += 1
            if "sync_settings" not in cols:
                print("Adding column sync_settings to oauth_tokens...")
                cur.execute("ALTER TABLE oauth_tokens ADD COLUMN sync_settings TEXT")
                migrated += 1

            # 2. emails table
            cur.execute("PRAGMA table_info(emails)")
            email_cols = [r[1] for r in cur.fetchall()]
            if "labels" not in email_cols:
                print("Adding column labels to emails...")
                cur.execute("ALTER TABLE emails ADD COLUMN labels TEXT")
                migrated += 1

            # 3. users table
            cur.execute("PRAGMA table_info(users)")
            user_cols = [r[1] for r in cur.fetchall()]
            print(f"User columns: {user_cols}")

            conn.commit()
            conn.close()
            print(f"Migration completed for {abs_path}. Applied {migrated} changes.")

if __name__ == "__main__":
    migrate()

