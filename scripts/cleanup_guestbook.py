"""Cleanup script - Remove all guestbook entries"""

import os
import sqlite3
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from database import get_db_path


def cleanup_guestbook(test_mode=False):
    """Remove all entries from guestbook table"""
    db_path = get_db_path(test_mode)

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Count entries before deletion
    count_before = cursor.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]
    print(f"Found {count_before} entries in database: {db_path}")

    if count_before == 0:
        print("No entries to delete.")
        conn.close()
        return

    # Delete all entries
    cursor.execute("DELETE FROM guestbook")
    conn.commit()

    # Count after deletion
    count_after = cursor.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]
    deleted = count_before - count_after

    print(f"Deleted {deleted} entries successfully!")
    print(f"Remaining entries: {count_after}")

    conn.close()


if __name__ == "__main__":
    print("=== Guestbook Cleanup Script ===")
    print()

    # Cleanup production database
    print("Cleaning production database...")
    cleanup_guestbook(test_mode=False)

    print()
    print("=" * 40)
    print()

    # Cleanup test database
    print("Cleaning test database...")
    cleanup_guestbook(test_mode=True)

    print()
    print("Cleanup complete!")
