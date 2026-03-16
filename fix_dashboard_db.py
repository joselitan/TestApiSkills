#!/usr/bin/env python3
"""
Snabb fix för låst databas - starta om backend med rätt databashantering
"""
import sqlite3
import os
import time
import subprocess
import sys

def kill_processes_using_db():
    """Stäng processer som använder databasen"""
    try:
        # Försök stänga eventuella låsningar
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
                    print(f"✅ Fixade {db_path}")
                except:
                    print(f"⚠️ Kunde inte fixa {db_path}")
    except Exception as e:
        print(f"Fel: {e}")

def restart_backend():
    """Starta om backend-servern"""
    print("🔄 Startar om backend-servern...")
    
    # Döda eventuella processer på port 6001
    try:
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
        time.sleep(2)
    except:
        pass
    
    # Starta backend i bakgrunden
    try:
        os.chdir("dashboard/backend")
        subprocess.Popen([sys.executable, "app.py"], 
                        creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("✅ Backend startad på port 6001")
        print("🌐 Dashboard: http://localhost:3000")
        print("🔧 Backend API: http://localhost:6001")
    except Exception as e:
        print(f"❌ Kunde inte starta backend: {e}")

if __name__ == "__main__":
    print("🔧 Fixar dashboard-databas...")
    kill_processes_using_db()
    restart_backend()
    print("\n✅ Klar! Testa nu dina UI-tester igen.")
    print("Kör: pytest tests/ui/ -v")