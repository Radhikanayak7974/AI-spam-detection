"""
SpamGuard AI - Database Quick Viewer
Run with: python backend/view_db.py [table_name]
Example:
    python backend/view_db.py
    python backend/view_db.py emails
    python backend/view_db.py users
    python backend/view_db.py predictions
    python backend/view_db.py feedback
"""

import sys
import os
import sqlite3

# Set stdout encoding to utf-8 to prevent Windows terminal charmap errors
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DB_PATH = os.path.join(os.path.dirname(__file__), "instance", "spam_detection.db")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [r[0] for r in cursor.fetchall()]

    requested_table = sys.argv[1].strip() if len(sys.argv) > 1 else None

    if not requested_table:
        print("\n" + "=" * 55)
        print("  SpamGuard AI - SQLite Database (spam_detection.db)")
        print("=" * 55)
        print(f"File Path: {DB_PATH}\n")
        print(f"{'Table Name':<22} {'Total Records':<15}")
        print("-" * 40)
        for tbl in tables:
            cursor.execute(f"SELECT count(*) FROM {tbl}")
            count = cursor.fetchone()[0]
            print(f"{tbl:<22} {count:<15}")
        print("-" * 40)
        print("\nKisi bhi table ka data dekhne ke liye command run karein:")
        print("  python backend/view_db.py emails")
        print("  python backend/view_db.py users")
        print("  python backend/view_db.py predictions")
        print("  python backend/view_db.py feedback")
        print("=" * 55 + "\n")
        return

    if requested_table not in tables:
        print(f"\nTable '{requested_table}' nahi mila! Available tables: {', '.join(tables)}\n")
        return

    cursor.execute(f"PRAGMA table_info({requested_table});")
    cols = [c[1] for c in cursor.fetchall()]

    cursor.execute(f"SELECT * FROM {requested_table} ORDER BY 1 DESC LIMIT 10;")
    rows = cursor.fetchall()

    print(f"\n=== Table: {requested_table} (Latest 10 Rows) ===")
    print("Columns:", " | ".join(cols))
    print("-" * 75)
    for r in rows:
        row_str = " | ".join(str(val)[:40] if val is not None else "NULL" for val in r)
        print(row_str)
    print("=" * 75 + "\n")

if __name__ == "__main__":
    main()
