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
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'member',
            is_active INTEGER NOT NULL DEFAULT 0,
            verification_token TEXT,
            verification_expires_at TIMESTAMP,
            password_reset_token TEXT,
            password_reset_expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    cursor.execute("PRAGMA table_info(users)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    migration_statements = []

    if "email" not in existing_columns:
        migration_statements.append("ALTER TABLE users ADD COLUMN email TEXT")
    if "role" not in existing_columns:
        migration_statements.append(
            "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'member'"
        )
    if "is_active" not in existing_columns:
        migration_statements.append(
            "ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 0"
        )
    if "verification_token" not in existing_columns:
        migration_statements.append(
            "ALTER TABLE users ADD COLUMN verification_token TEXT"
        )
    if "verification_expires_at" not in existing_columns:
        migration_statements.append(
            "ALTER TABLE users ADD COLUMN verification_expires_at TIMESTAMP"
        )
    if "password_reset_token" not in existing_columns:
        migration_statements.append(
            "ALTER TABLE users ADD COLUMN password_reset_token TEXT"
        )
    if "password_reset_expires_at" not in existing_columns:
        migration_statements.append(
            "ALTER TABLE users ADD COLUMN password_reset_expires_at TIMESTAMP"
        )
    if "created_at" not in existing_columns:
        migration_statements.append("ALTER TABLE users ADD COLUMN created_at TIMESTAMP")
    if "updated_at" not in existing_columns:
        migration_statements.append("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")

    for statement in migration_statements:
        cursor.execute(statement)

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        hashed_password = generate_password_hash("password123")
        cursor.execute(
            "INSERT INTO users (username, password, role, is_active) VALUES (?, ?, 'admin', 1)",
            ("admin", hashed_password),
        )
    else:
        cursor.execute(
            "UPDATE users SET role = COALESCE(role, 'admin'), is_active = 1 WHERE username = 'admin'"
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
