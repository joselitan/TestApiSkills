#!/usr/bin/env python3
"""
Fix database schema for test cases API
"""
import sqlite3
import os
import json
from datetime import datetime

def fix_database():
    """Fix database schema issues"""
    db_paths = [
        "dashboard/database/test_results.db",
        "dashboard/backend/dashboard/database/test_results.db",
        "dashboard/dashboard/database/test_results.db"
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Fixing database: {db_path}")
            fix_single_database(db_path)

def fix_single_database(db_path):
    """Fix a single database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if test_cases table exists and get its structure
    cursor.execute("PRAGMA table_info(test_cases)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    print(f"Current columns in test_cases: {column_names}")
    
    # If test_cases table doesn't exist or is missing columns, recreate it
    if not columns or 'created_at' not in column_names:
        print("Recreating test_cases table with proper structure...")
        
        # Drop existing table if it exists
        cursor.execute("DROP TABLE IF EXISTS test_cases_old")
        if columns:
            cursor.execute("ALTER TABLE test_cases RENAME TO test_cases_old")
        
        # Create new table with proper structure
        cursor.execute("""
            CREATE TABLE test_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                test_type TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'active',
                tags TEXT DEFAULT '[]',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT DEFAULT 'system'
            )
        """)
        
        # Migrate data if old table exists
        if columns:
            try:
                # Get old data
                cursor.execute("SELECT * FROM test_cases_old")
                old_data = cursor.fetchall()
                
                # Insert into new table
                for row in old_data:
                    # Map old columns to new structure
                    if len(row) >= 4:  # Minimum required columns
                        cursor.execute("""
                            INSERT INTO test_cases (id, name, test_type, status, description)
                            VALUES (?, ?, ?, ?, ?)
                        """, (row[0], row[1] if len(row) > 1 else 'Unknown', 
                             row[2] if len(row) > 2 else 'unit',
                             row[3] if len(row) > 3 else 'active',
                             row[4] if len(row) > 4 else ''))
                
                print(f"Migrated {len(old_data)} records")
                cursor.execute("DROP TABLE test_cases_old")
            except Exception as e:
                print(f"Error migrating data: {e}")
    
    # Ensure other required tables exist
    create_other_tables(cursor)
    
    # Add some sample data if table is empty
    cursor.execute("SELECT COUNT(*) FROM test_cases")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("Adding sample test cases...")
        sample_data = [
            ("Login Test", "Test user login functionality", "ui", "high", "active", '["login", "authentication"]'),
            ("API Response Test", "Test API response times", "api", "medium", "active", '["api", "performance"]'),
            ("Database Connection Test", "Test database connectivity", "integration", "critical", "active", '["database", "integration"]'),
            ("Unit Test Example", "Example unit test", "unit", "low", "active", '["unit", "example"]'),
            ("Performance Load Test", "Test system under load", "performance", "high", "active", '["performance", "load"]')
        ]
        
        for name, desc, test_type, priority, status, tags in sample_data:
            cursor.execute("""
                INSERT INTO test_cases (name, description, test_type, priority, status, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, desc, test_type, priority, status, tags))
        
        print(f"Added {len(sample_data)} sample test cases")
    
    conn.commit()
    conn.close()
    print(f"Database {db_path} fixed successfully!")

def create_other_tables(cursor):
    """Create other required tables"""
    
    # Bug Reports Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bug_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            severity TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            test_case_id INTEGER,
            github_issue_url TEXT,
            jira_ticket_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            assigned_to TEXT,
            FOREIGN KEY (test_case_id) REFERENCES test_cases (id)
        )
    """)
    
    # AI Test Suggestions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_test_suggestions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT NOT NULL,
            test_code TEXT NOT NULL,
            confidence_score REAL DEFAULT 0.0,
            test_type TEXT,
            generated_from TEXT,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Integration Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS integration_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT NOT NULL UNIQUE,
            config_data TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

if __name__ == "__main__":
    fix_database()
    print("Database fix completed!")