#!/usr/bin/env python3
"""
Snabb fix for last databas
"""
import sqlite3
import os
import time
import subprocess
import sys

def fix_database():
    """Fix database locks"""
    db_paths = [
        "dashboard/database/test_results.db",
        "dashboard/backend/dashboard/database/test_results.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path, timeout=1)
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.close()
                print(f"Fixed {db_path}")
            except:
                print(f"Could not fix {db_path}")

def restart_backend():
    """Restart backend server"""
    print("Restarting backend server...")
    
    # Kill processes on port 6001
    try:
        subprocess.run(["netstat", "-ano"], capture_output=True)
        subprocess.run(["taskkill", "/F", "/FI", "IMAGENAME eq python.exe"], capture_output=True)
        time.sleep(2)
    except:
        pass
    
    # Start backend
    try:
        os.chdir("dashboard/backend")
        subprocess.Popen([sys.executable, "app.py"])
        print("Backend started on port 6001")
    except Exception as e:
        print(f"Could not start backend: {e}")

if __name__ == "__main__":
    print("Fixing dashboard database...")
    fix_database()
    restart_backend()
    print("Done! Test your UI tests again with: pytest tests/ui/ -v")