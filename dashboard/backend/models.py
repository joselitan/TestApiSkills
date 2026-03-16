"""
Database Models for QA Dashboard - Fas 6 Implementation
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class TestCase:
    """Test Case Model"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    test_type: str = ""  # unit, integration, ui, api, performance
    priority: str = "medium"  # low, medium, high, critical
    status: str = "active"  # active, inactive, deprecated
    tags: str = ""  # JSON string of tags
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    created_by: str = "system"


@dataclass
class BugReport:
    """Bug Report Model"""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    severity: str = "medium"  # low, medium, high, critical
    status: str = "open"  # open, in_progress, resolved, closed
    test_case_id: Optional[int] = None
    github_issue_url: Optional[str] = None
    jira_ticket_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    assigned_to: str = ""


@dataclass
class AITestSuggestion:
    """AI-Generated Test Suggestions"""
    id: Optional[int] = None
    test_name: str = ""
    test_code: str = ""
    confidence_score: float = 0.0
    test_type: str = ""
    generated_from: str = ""  # failure_analysis, code_analysis, pattern_detection
    status: str = "pending"  # pending, approved, rejected
    created_at: Optional[str] = None


class DatabaseManager:
    """Enhanced Database Manager for Fas 6"""
    
    def __init__(self, db_path: str = "dashboard/database/test_results.db"):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_enhanced_db()
    
    def init_enhanced_db(self):
        """Initialize enhanced database with Fas 6 tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Test Cases Management Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS managed_test_cases (
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
                FOREIGN KEY (test_case_id) REFERENCES managed_test_cases (id)
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
        
        # Test Execution History (enhanced)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case_id INTEGER,
                run_id INTEGER,
                status TEXT NOT NULL,
                duration REAL,
                error_message TEXT,
                stack_trace TEXT,
                executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_case_id) REFERENCES managed_test_cases (id),
                FOREIGN KEY (run_id) REFERENCES test_runs (id)
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
        
        conn.commit()
        conn.close()
    
    def create_test_case(self, test_case: TestCase) -> int:
        """Create a new test case"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO manged_test_cases (name, description, test_type, priority, status, tags, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            test_case.name,
            test_case.description,
            test_case.test_type,
            test_case.priority,
            test_case.status,
            test_case.tags,
            test_case.created_by
        ))
        
        test_case_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return test_case_id
    
    def get_test_cases(self, filters: Dict = None) -> List[TestCase]:
        """Get test cases with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM manged_test_cases WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('test_type'):
                query += " AND test_type = ?"
                params.append(filters['test_type'])
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            if filters.get('priority'):
                query += " AND priority = ?"
                params.append(filters['priority'])
        
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [TestCase(*row) for row in rows]
    
    def update_test_case(self, test_case_id: int, updates: Dict) -> bool:
        """Update a test case"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE manged_test_cases SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        params = list(updates.values()) + [test_case_id]
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def delete_test_case(self, test_case_id: int) -> bool:
        """Delete a test case"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM managed_test_cases WHERE id = ?", (test_case_id,))
        success = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        return success
    
    def create_bug_report(self, bug: BugReport) -> int:
        """Create a new bug report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO bug_reports 
            (title, description, severity, status, test_case_id, github_issue_url, jira_ticket_id, assigned_to)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bug.title,
            bug.description,
            bug.severity,
            bug.status,
            bug.test_case_id,
            bug.github_issue_url,
            bug.jira_ticket_id,
            bug.assigned_to
        ))
        
        bug_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return bug_id
    
    def get_bug_reports(self, filters: Dict = None) -> List[BugReport]:
        """Get bug reports with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM bug_reports WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            if filters.get('severity'):
                query += " AND severity = ?"
                params.append(filters['severity'])
        
        query += " ORDER BY created_at DESC"
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [BugReport(*row) for row in rows]
    
    def create_ai_suggestion(self, suggestion: AITestSuggestion) -> int:
        """Create a new AI test suggestion"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ai_test_suggestions 
            (test_name, test_code, confidence_score, test_type, generated_from, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            suggestion.test_name,
            suggestion.test_code,
            suggestion.confidence_score,
            suggestion.test_type,
            suggestion.generated_from,
            suggestion.status
        ))
        
        suggestion_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return suggestion_id
    
    def get_ai_suggestions(self, status: str = None) -> List[AITestSuggestion]:
        """Get AI test suggestions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM ai_test_suggestions WHERE status = ? ORDER BY confidence_score DESC", (status,))
        else:
            cursor.execute("SELECT * FROM ai_test_suggestions ORDER BY confidence_score DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [AITestSuggestion(*row) for row in rows]
    
    def update_bug_report(self, bug_id: int, updates: Dict) -> bool:
        """Update a bug report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        query = f"UPDATE bug_reports SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        params = list(updates.values()) + [bug_id]
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_dashboard_analytics(self) -> Dict:
        """Get comprehensive dashboard analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Test case statistics
        try:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_cases,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_cases,
                    SUM(CASE WHEN priority = 'critical' THEN 1 ELSE 0 END) as critical_cases
                FROM managed_test_cases
            """)
            test_stats = cursor.fetchone()
        except sqlite3.OperationalError:
            # Fallback if priority column doesn't exist yet
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_cases,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_cases,
                    0 as critical_cases
                FROM test_cases
            """)
            test_stats = cursor.fetchone()
        
        # Bug statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_bugs,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_bugs,
                SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical_bugs
            FROM bug_reports
        """)
        bug_stats = cursor.fetchone()
        
        # AI suggestions statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_suggestions,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_suggestions,
                AVG(confidence_score) as avg_confidence
            FROM ai_test_suggestions
        """)
        ai_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "test_cases": {
                "total": test_stats[0] or 0,
                "active": test_stats[1] or 0,
                "critical": test_stats[2] or 0
            },
            "bugs": {
                "total": bug_stats[0] or 0,
                "open": bug_stats[1] or 0,
                "critical": bug_stats[2] or 0
            },
            "ai_suggestions": {
                "total": ai_stats[0] or 0,
                "pending": ai_stats[1] or 0,
                "avg_confidence": round(ai_stats[2] or 0, 2)
            }
        }