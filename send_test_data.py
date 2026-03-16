import sqlite3
import requests
import json
from datetime import datetime

# Create a fresh database
DB_PATH = "test_dashboard.db"

def create_fresh_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create test_runs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            test_type TEXT NOT NULL,
            total_tests INTEGER,
            passed_tests INTEGER,
            failed_tests INTEGER,
            skipped_tests INTEGER,
            duration REAL,
            coverage_percentage REAL,
            branch TEXT DEFAULT 'main'
        )
    """)
    
    # Create test_cases table with correct structure
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            test_name TEXT NOT NULL,
            test_file TEXT,
            status TEXT NOT NULL,
            duration REAL,
            error_message TEXT,
            FOREIGN KEY (run_id) REFERENCES test_runs (id)
        )
    """)
    
    # Add sample data
    cursor.execute("""
        INSERT INTO test_runs 
        (test_type, total_tests, passed_tests, failed_tests, duration, coverage_percentage)
        VALUES ('ui', 5, 4, 1, 25.3, 80.0)
    """)
    
    conn.commit()
    conn.close()
    print(f"Created fresh database: {DB_PATH}")

def send_test_data():
    # Send current test data
    test_data = {
        "test_type": "ui",
        "total_tests": 8,
        "passed_tests": 6,
        "failed_tests": 2,
        "duration": 45.2,
        "coverage_percentage": 75.0,
        "test_cases": [
            {"name": "test_guestbook_page_loads", "status": "passed", "duration": 2.1},
            {"name": "test_create_entry", "status": "passed", "duration": 3.5},
            {"name": "test_edit_entry", "status": "failed", "duration": 8.2, "error_message": "Modal not found"},
            {"name": "test_delete_entry", "status": "passed", "duration": 4.1},
            {"name": "test_delete_entry_cancel", "status": "passed", "duration": 3.8},
            {"name": "test_delete_modal_close_x", "status": "passed", "duration": 2.9},
            {"name": "test_form_validation", "status": "failed", "duration": 1.2, "error_message": "Validation failed"},
            {"name": "test_login_ui", "status": "passed", "duration": 5.4}
        ]
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:6001/api/test-runs",
            json=test_data,
            timeout=5
        )
        print(f"Response: {response.status_code}")
        if response.status_code == 200:
            print("Test data sent successfully!")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Failed to send data: {e}")

if __name__ == "__main__":
    create_fresh_db()
    send_test_data()