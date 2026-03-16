"""
Demo Data Population Script for Fas 6 Dashboard
Kör detta script för att fylla dashboard med exempel-data
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from models import DatabaseManager, TestCase, BugReport, AITestSuggestion
import json
from datetime import datetime, timedelta
import random

def populate_demo_data():
    """Populera dashboard med demo-data"""
    db = DatabaseManager()
    
    # Initialize original tables first
    from app import init_db
    init_db()
    
    print("Skapar demo-data for Fas 6 Dashboard...")
    
    # Test Cases
    test_cases = [
        TestCase(
            name="test_user_authentication",
            description="Testar användarautentisering med olika scenarier",
            test_type="integration",
            priority="high",
            status="active",
            tags='["auth", "security", "login"]',
            created_by="demo_user"
        ),
        TestCase(
            name="test_api_rate_limiting",
            description="Verifierar att API rate limiting fungerar korrekt",
            test_type="api",
            priority="medium",
            status="active",
            tags='["api", "performance", "security"]',
            created_by="demo_user"
        ),
        TestCase(
            name="test_database_connection_pool",
            description="Testar databasanslutningspool under hög belastning",
            test_type="performance",
            priority="high",
            status="active",
            tags='["database", "performance", "connection"]',
            created_by="demo_user"
        ),
        TestCase(
            name="test_ui_responsive_design",
            description="Kontrollerar att UI fungerar på olika skärmstorlekar",
            test_type="ui",
            priority="medium",
            status="active",
            tags='["ui", "responsive", "mobile"]',
            created_by="demo_user"
        ),
        TestCase(
            name="test_data_validation",
            description="Testar input-validering för alla formulär",
            test_type="unit",
            priority="critical",
            status="active",
            tags='["validation", "security", "forms"]',
            created_by="demo_user"
        )
    ]
    
    print("Skapar test cases...")
    for tc in test_cases:
        try:
            db.create_test_case(tc)
            print(f"  OK {tc.name}")
        except Exception as e:
            print(f"  ERROR {tc.name}: {e}")
    
    # Bug Reports
    bug_reports = [
        BugReport(
            title="Login form inte responsiv pa mobil",
            description="Login-formuläret visas inte korrekt på mobila enheter under 768px bredd",
            severity="medium",
            status="open",
            test_case_id=4,  # UI test case
            assigned_to="frontend_team"
        ),
        BugReport(
            title="API timeout vid hog belastning",
            description="API:et får timeout-fel när fler än 100 samtidiga användare är aktiva",
            severity="high",
            status="in_progress",
            test_case_id=2,  # API rate limiting test
            assigned_to="backend_team"
        ),
        BugReport(
            title="Sakerhetslucka i input-validering",
            description="SQL injection möjlig genom sökfältet på huvudsidan",
            severity="critical",
            status="open",
            test_case_id=5,  # Data validation test
            assigned_to="security_team"
        ),
        BugReport(
            title="Minneslacka i databasanslutningar",
            description="Databasanslutningar stängs inte korrekt vilket leder till minnesläcka",
            severity="high",
            status="resolved",
            test_case_id=3,  # Database connection test
            assigned_to="backend_team"
        )
    ]
    
    print("Skapar bug reports...")
    for bug in bug_reports:
        try:
            db.create_bug_report(bug)
            print(f"  OK {bug.title}")
        except Exception as e:
            print(f"  ERROR {bug.title}: {e}")
    
    # AI Test Suggestions
    ai_suggestions = [
        AITestSuggestion(
            test_name="test_password_strength_validation",
            test_code='''def test_password_strength_validation():
    """Test password strength validation"""
    weak_passwords = ["123", "password", "abc"]
    strong_passwords = ["MyStr0ng!Pass", "C0mpl3x#2023"]
    
    for pwd in weak_passwords:
        assert not validate_password_strength(pwd)
    
    for pwd in strong_passwords:
        assert validate_password_strength(pwd)''',
            confidence_score=0.85,
            test_type="unit",
            generated_from="failure_analysis",
            status="pending"
        ),
        AITestSuggestion(
            test_name="test_concurrent_user_sessions",
            test_code='''def test_concurrent_user_sessions():
    """Test handling of concurrent user sessions"""
    import threading
    import time
    
    def create_session():
        return create_user_session("test_user")
    
    threads = []
    for i in range(10):
        t = threading.Thread(target=create_session)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    assert get_active_sessions_count() <= 10''',
            confidence_score=0.72,
            test_type="integration",
            generated_from="code_analysis",
            status="pending"
        ),
        AITestSuggestion(
            test_name="test_error_handling_edge_cases",
            test_code='''def test_error_handling_edge_cases():
    """Test error handling for edge cases"""
    # Test null inputs
    with pytest.raises(ValueError):
        process_user_input(None)
    
    # Test empty strings
    with pytest.raises(ValueError):
        process_user_input("")
    
    # Test extremely long inputs
    long_input = "x" * 10000
    result = process_user_input(long_input)
    assert result is not None''',
            confidence_score=0.91,
            test_type="unit",
            generated_from="pattern_detection",
            status="approved"
        ),
        AITestSuggestion(
            test_name="test_api_response_time_sla",
            test_code='''def test_api_response_time_sla():
    """Test API response time meets SLA requirements"""
    import time
    
    endpoints = ["/api/users", "/api/data", "/api/reports"]
    
    for endpoint in endpoints:
        start_time = time.time()
        response = api_client.get(endpoint)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 2.0, f"{endpoint} took {response_time}s"
        assert response.status_code == 200''',
            confidence_score=0.78,
            test_type="performance",
            generated_from="coverage_analysis",
            status="pending"
        )
    ]
    
    print("Skapar AI test-forslag...")
    for suggestion in ai_suggestions:
        try:
            db.create_ai_suggestion(suggestion)
            print(f"  OK {suggestion.test_name}")
        except Exception as e:
            print(f"  ERROR {suggestion.test_name}: {e}")
    
    # Lägg till några test runs för att visa trends
    print("Skapar test run historik...")
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    
    # Simulera test runs för de senaste 7 dagarna
    for i in range(7):
        date = datetime.now() - timedelta(days=i)
        
        # Unit tests
        cursor.execute("""
            INSERT INTO test_runs 
            (timestamp, test_type, total_tests, passed_tests, failed_tests, skipped_tests, duration, coverage_percentage, branch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date.isoformat(),
            "unit",
            random.randint(45, 55),
            random.randint(40, 50),
            random.randint(0, 5),
            random.randint(0, 2),
            random.uniform(30, 60),
            random.uniform(85, 95),
            "main"
        ))
        
        # Integration tests
        cursor.execute("""
            INSERT INTO test_runs 
            (timestamp, test_type, total_tests, passed_tests, failed_tests, skipped_tests, duration, coverage_percentage, branch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date.isoformat(),
            "integration",
            random.randint(15, 25),
            random.randint(12, 20),
            random.randint(0, 3),
            random.randint(0, 1),
            random.uniform(120, 180),
            random.uniform(70, 85),
            "main"
        ))
        
        # UI tests
        cursor.execute("""
            INSERT INTO test_runs 
            (timestamp, test_type, total_tests, passed_tests, failed_tests, skipped_tests, duration, coverage_percentage, branch)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            date.isoformat(),
            "ui",
            random.randint(8, 15),
            random.randint(6, 12),
            random.randint(0, 2),
            random.randint(0, 1),
            random.uniform(300, 600),
            random.uniform(60, 80),
            "main"
        ))
    
    conn.commit()
    conn.close()
    
    print("Demo-data skapad framgangsrikt!")
    print("\nStatistik:")
    analytics = db.get_dashboard_analytics()
    print(f"  Test Cases: {analytics['test_cases']['total']}")
    print(f"  Bug Reports: {analytics['bugs']['total']}")
    print(f"  AI Suggestions: {analytics['ai_suggestions']['total']}")
    
    print("\nStarta dashboard:")
    print("  1. cd dashboard/backend")
    print("  2. python app.py")
    print("  3. Oppna http://localhost:6001")
    print("\nEller for React frontend:")
    print("  1. cd dashboard/frontend-react")
    print("  2. npm install")
    print("  3. npm start")

if __name__ == "__main__":
    populate_demo_data()