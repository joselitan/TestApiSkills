#!/usr/bin/env python3
"""
Test Data Populator for Dashboard
Populates the dashboard database with sample test data and real results from existing tests
"""

import sqlite3
import json
import subprocess
import os
import sys
from datetime import datetime, timedelta
import random

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

DATABASE_PATH = 'dashboard/database/test_results.db'

def init_database():
    """Initialize the database"""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Test runs table
    cursor.execute('''
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
    ''')
    
    # Test cases table
    cursor.execute('''
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
    ''')
    
    # Performance metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            endpoint TEXT NOT NULL,
            response_time REAL,
            status_code INTEGER,
            users INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized")

def run_actual_tests():
    """Run actual tests and capture results"""
    print("Running actual tests to get real data...")
    
    test_results = {}
    
    # Run API tests
    try:
        result = subprocess.run([
            'python', '-m', 'pytest', 'test_guestbook_api.py', '-v', '--tb=short'
        ], capture_output=True, text=True, cwd='.')
        
        # Parse pytest output
        lines = result.stdout.split('\n')
        passed = len([l for l in lines if '::' in l and 'PASSED' in l])
        failed = len([l for l in lines if '::' in l and 'FAILED' in l])
        
        test_results['api'] = {
            'total': passed + failed,
            'passed': passed,
            'failed': failed,
            'duration': 2.5 + random.uniform(-0.5, 1.0)
        }
        print(f"API Tests: {passed} passed, {failed} failed")
        
    except Exception as e:
        print(f"Could not run API tests: {e}")
        test_results['api'] = {'total': 13, 'passed': 12, 'failed': 1, 'duration': 2.8}
    
    # Simulate other test types with realistic data
    test_results.update({
        'ui': {'total': 16, 'passed': 15, 'failed': 1, 'duration': 45.2},
        'security': {'total': 38, 'passed': 36, 'failed': 2, 'duration': 12.7},
        'performance': {'total': 19, 'passed': 18, 'failed': 1, 'duration': 180.5},
        'unit': {'total': 25, 'passed': 24, 'failed': 1, 'duration': 1.2}
    })
    
    return test_results

def populate_historical_data():
    """Populate database with historical test data"""
    print("Populating historical test data...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get actual test results
    test_results = run_actual_tests()
    
    # Generate data for the last 30 days
    for days_ago in range(30, 0, -1):
        timestamp = datetime.now() - timedelta(days=days_ago)
        
        for test_type, base_results in test_results.items():
            # Add some variation to make it realistic
            variation = random.uniform(0.8, 1.2)
            total = int(base_results['total'] * variation)
            
            # Most tests should pass, but add some realistic failures
            if random.random() < 0.1:  # 10% chance of more failures
                failed = random.randint(1, max(1, total // 5))
            else:
                failed = random.randint(0, max(0, total // 10))
            
            passed = total - failed
            duration = base_results['duration'] * random.uniform(0.7, 1.3)
            coverage = random.uniform(75, 95)
            
            cursor.execute('''
                INSERT INTO test_runs 
                (timestamp, test_type, total_tests, passed_tests, failed_tests, skipped_tests, duration, coverage_percentage, branch)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp.isoformat(),
                test_type,
                total,
                passed,
                failed,
                0,
                duration,
                coverage,
                'main' if random.random() < 0.8 else 'develop'
            ))
    
    # Add today's data with current results
    for test_type, results in test_results.items():
        cursor.execute('''
            INSERT INTO test_runs 
            (test_type, total_tests, passed_tests, failed_tests, skipped_tests, duration, coverage_percentage, branch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_type,
            results['total'],
            results['passed'],
            results['failed'],
            0,
            results['duration'],
            random.uniform(80, 95),
            'main'
        ))
    
    conn.commit()
    conn.close()
    print("Historical data populated")

def populate_performance_data():
    """Populate performance metrics"""
    print("Populating performance data...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    endpoints = [
        '/api/login',
        '/api/guestbook',
        '/api/guestbook/search',
        '/api/guestbook/1',
        '/health',
        '/health/detailed'
    ]
    
    # Generate performance data for the last 7 days
    for days_ago in range(7, 0, -1):
        base_time = datetime.now() - timedelta(days=days_ago)
        
        # Generate multiple data points per day
        for hour in range(0, 24, 2):  # Every 2 hours
            timestamp = base_time.replace(hour=hour, minute=0, second=0)
            
            for endpoint in endpoints:
                # Different endpoints have different typical response times
                if endpoint == '/api/login':
                    base_response = 0.15
                elif endpoint == '/health':
                    base_response = 0.05
                elif 'search' in endpoint:
                    base_response = 0.25
                else:
                    base_response = 0.10
                
                response_time = base_response * random.uniform(0.5, 2.0)
                status_code = 200 if random.random() < 0.95 else random.choice([400, 401, 500])
                
                cursor.execute('''
                    INSERT INTO performance_metrics (timestamp, endpoint, response_time, status_code, users)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    timestamp.isoformat(),
                    endpoint,
                    response_time,
                    status_code,
                    random.randint(1, 5)
                ))
    
    conn.commit()
    conn.close()
    print("Performance data populated")

def show_dashboard_stats():
    """Show current dashboard statistics"""
    print("\nDashboard Statistics:")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Test runs summary
    cursor.execute('SELECT COUNT(*) FROM test_runs')
    total_runs = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT test_type) FROM test_runs')
    test_types = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM performance_metrics')
    perf_metrics = cursor.fetchone()[0]
    
    print(f"  • Total test runs: {total_runs}")
    print(f"  • Test types: {test_types}")
    print(f"  • Performance metrics: {perf_metrics}")
    
    # Today's summary
    cursor.execute('''
        SELECT 
            SUM(total_tests) as total,
            SUM(passed_tests) as passed,
            SUM(failed_tests) as failed,
            AVG(coverage_percentage) as coverage
        FROM test_runs 
        WHERE DATE(timestamp) = DATE('now')
    ''')
    
    today = cursor.fetchone()
    if today[0]:
        print(f"  • Today: {today[1]} passed, {today[2]} failed, {today[3]:.1f}% coverage")
    
    conn.close()

def main():
    """Main function"""
    print("QA Dashboard Data Populator")
    print("=" * 50)
    
    # Initialize database
    init_database()
    
    # Populate with data
    populate_historical_data()
    populate_performance_data()
    
    # Show stats
    show_dashboard_stats()
    
    print("\nDashboard data population complete!")
    print("\nNästa steg:")
    print("1. Starta backend: cd dashboard/backend && python app.py")
    print("2. Öppna dashboard: dashboard/frontend/index.html")
    print("3. Backend API: http://localhost:6001")

if __name__ == '__main__':
    main()