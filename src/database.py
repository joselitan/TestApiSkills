import os
import sqlite3
from datetime import datetime

from werkzeug.security import generate_password_hash


def get_db_path(test_mode=False):
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Support environment variables for database configuration
    if test_mode:
        db_path = os.getenv("TEST_DATABASE_URL", "sqlite:///data/guestbook_test.db")
    else:
        db_path = os.getenv("DATABASE_URL", "sqlite:///data/guestbook.db")

    # Extract path from sqlite:/// URL format
    if db_path.startswith("sqlite:///"):
        db_path = db_path[10:]  # Remove 'sqlite:///' prefix

    # Handle relative paths
    if not os.path.isabs(db_path):
        db_path = os.path.join(basedir, db_path)

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    return db_path


def init_db(test_mode=False):
    conn = sqlite3.connect(get_db_path(test_mode))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS guestbook (
            userId INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        hashed_password = generate_password_hash("password123")
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            ("admin", hashed_password),
        )

    conn.commit()
    conn.close()


def get_db(test_mode=False):
    conn = sqlite3.connect(get_db_path(test_mode))
    conn.row_factory = sqlite3.Row
    return conn


def clear_test_db():
    """Clear all data from test database"""
    test_db_path = get_db_path(test_mode=True)
    if os.path.exists(test_db_path):
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM guestbook")
        conn.commit()
        conn.close()
        return True
    return False
