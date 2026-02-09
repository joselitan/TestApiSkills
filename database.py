import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

def init_db():
    conn = sqlite3.connect('guestbook.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guestbook (
            userId INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        hashed_password = generate_password_hash('password123')
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_password))
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('guestbook.db')
    conn.row_factory = sqlite3.Row
    return conn
