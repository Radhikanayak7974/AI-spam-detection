"""
Database schema verification and Phase 4 migration.
Adds missing columns to feedback table and creates training_history table.
"""
import os
import sqlite3

def migrate():
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

            # 1. Check feedback table columns
            cur.execute("PRAGMA table_info(feedback)")
            cols = [r[1] for r in cur.fetchall()]
            if "user_id" not in cols:
                print("Adding column user_id to feedback...")
                cur.execute("ALTER TABLE feedback ADD COLUMN user_id INTEGER REFERENCES users(id)")
                migrated += 1
            if "status" not in cols:
                print("Adding column status to feedback...")
                cur.execute("ALTER TABLE feedback ADD COLUMN status VARCHAR(32) DEFAULT 'approved'")
                migrated += 1
            if "updated_at" not in cols:
                print("Adding column updated_at to feedback...")
                cur.execute("ALTER TABLE feedback ADD COLUMN updated_at DATETIME")
                migrated += 1

            # 2. Check training_history table
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='training_history'")
            if not cur.fetchone():
                print("Creating table training_history...")
                cur.execute("""
                    CREATE TABLE training_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version VARCHAR(64) NOT NULL,
                        model_type VARCHAR(64) DEFAULT 'ensemble_lr_nb',
                        dataset_size INTEGER DEFAULT 0,
                        feedback_samples INTEGER DEFAULT 0,
                        metrics TEXT,
                        status VARCHAR(32) DEFAULT 'promoted',
                        trained_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        promoted_at DATETIME,
                        created_by VARCHAR(255) DEFAULT 'system',
                        notes TEXT
                    )
                """)
                migrated += 1

            conn.commit()
            conn.close()
            print(f"Migration completed for {abs_path}. Applied {migrated} changes.")

if __name__ == "__main__":
    migrate()

