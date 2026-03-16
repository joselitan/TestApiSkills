from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import os

# Import new API blueprints
from test_cases_api import test_cases_bp
from bug_tracking_api import bug_tracking_bp
from ai_testing_api import ai_testing_bp
from models import DatabaseManager

app = Flask(__name__)
CORS(app)

# Register API blueprints
app.register_blueprint(test_cases_bp, url_prefix='/api')
app.register_blueprint(bug_tracking_bp, url_prefix='/api')
app.register_blueprint(ai_testing_bp, url_prefix='/api')

#DATABASE_PATH = "dashboard/database/test_dashboard.db"
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "../database/test_dashboard.db")
db_manager = DatabaseManager("dashboard/database/test_dashboard.db")


@app.route('/')
def serve_frontend():
    """Serve the frontend HTML dashboard"""
    return send_from_directory('../frontend', 'index.html')


def init_db():
    """Initialize the test results database"""
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:  # Only create directory if path has a directory component
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Test runs table
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

    # Test cases table
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

    # Performance metrics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            endpoint TEXT NOT NULL,
            response_time REAL,
            status_code INTEGER,
            users INTEGER DEFAULT 1
        )
    """)

    conn.commit()

    # Ensure schema is compatible (migrations)
    cursor.execute("PRAGMA table_info(test_cases)")
    columns = {row[1] for row in cursor.fetchall()}

    # Add missing columns if needed (backward-compatibility)
    required_columns = {
        "run_id": "INTEGER",
        "test_name": "TEXT",
        "test_file": "TEXT",
        "status": "TEXT",
        "duration": "REAL",
        "error_message": "TEXT",
    }

    for col, col_type in required_columns.items():
        if col not in columns:
            cursor.execute(f"ALTER TABLE test_cases ADD COLUMN {col} {col_type}")
            conn.commit()

    conn.close()


@app.route("/api/dashboard/summary")
def get_dashboard_summary():
    """Get overall test summary for dashboard"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Get latest test run stats
    cursor.execute("""
        SELECT 
            SUM(total_tests) as total,
            SUM(passed_tests) as passed,
            SUM(failed_tests) as failed,
            AVG(coverage_percentage) as coverage
        FROM test_runs 
        WHERE DATE(timestamp) = DATE('now')
    """)

    today_stats = cursor.fetchone()

    # Get test trends (last 7 days)
    cursor.execute("""
        SELECT 
            DATE(timestamp) as date,
            SUM(passed_tests) as passed,
            SUM(failed_tests) as failed
        FROM test_runs 
        WHERE timestamp >= DATE('now', '-7 days')
        GROUP BY DATE(timestamp)
        ORDER BY date
    """)

    trends = cursor.fetchall()

    conn.close()

    return jsonify(
        {
            "today": {
                "total_tests": today_stats[0] or 0,
                "passed_tests": today_stats[1] or 0,
                "failed_tests": today_stats[2] or 0,
                "coverage": round(today_stats[3] or 0, 2),
            },
            "trends": [
                {"date": row[0], "passed": row[1], "failed": row[2]} for row in trends
            ],
        }
    )


@app.route("/api/dashboard/test-types")
def get_test_types_breakdown():
    """Get breakdown by test type"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            test_type,
            COUNT(*) as runs,
            AVG(passed_tests * 100.0 / total_tests) as success_rate,
            AVG(duration) as avg_duration
        FROM test_runs 
        WHERE timestamp >= DATE('now', '-30 days')
        GROUP BY test_type
    """)

    results = cursor.fetchall()
    conn.close()

    return jsonify(
        [
            {
                "type": row[0],
                "runs": row[1],
                "success_rate": round(row[2] or 0, 2),
                "avg_duration": round(row[3] or 0, 2),
            }
            for row in results
        ]
    )


@app.route("/api/dashboard/performance")
def get_performance_metrics():
    """Get performance metrics for dashboard"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            endpoint,
            AVG(response_time) as avg_response,
            COUNT(*) as requests,
            AVG(CASE WHEN status_code < 400 THEN 1.0 ELSE 0.0 END) * 100 as success_rate
        FROM performance_metrics 
        WHERE timestamp >= DATE('now', '-7 days')
        GROUP BY endpoint
        ORDER BY avg_response DESC
    """)

    results = cursor.fetchall()
    conn.close()

    return jsonify(
        [
            {
                "endpoint": row[0],
                "avg_response_time": round(row[1], 3),
                "total_requests": row[2],
                "success_rate": round(row[3], 2),
            }
            for row in results
        ]
    )


@app.route("/api/test-runs", methods=["POST"])
def add_test_run():
    """Add a new test run result"""
    data = request.json
    
    # Check if this is a partial update (real-time individual test)
    if data.get('is_partial'):
        # For partial updates, just update the latest run or create a temporary one
        # This gives real-time feedback without creating duplicate runs
        return jsonify({"success": True, "partial": True})

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO test_runs 
        (test_type, total_tests, passed_tests, failed_tests, skipped_tests, duration, coverage_percentage, branch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """,
        (
            data.get("test_type"),
            data.get("total_tests"),
            data.get("passed_tests"),
            data.get("failed_tests"),
            data.get("skipped_tests", 0),
            data.get("duration"),
            data.get("coverage_percentage"),
            data.get("branch", "main"),
        ),
    )

    run_id = cursor.lastrowid

    # Add individual test cases if provided
    if "test_cases" in data:
        for test_case in data["test_cases"]:
            cursor.execute(
                """
                INSERT INTO test_cases (run_id, test_name, test_file, status, duration, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    run_id,
                    test_case.get("name"),
                    test_case.get("file"),
                    test_case.get("status"),
                    test_case.get("duration"),
                    test_case.get("error_message"),
                ),
            )

    conn.commit()
    conn.close()

    return jsonify({"success": True, "run_id": run_id})


@app.route("/api/dashboard/enhanced-summary")
def get_enhanced_dashboard_summary():
    """Get enhanced dashboard summary with Fas 6 features"""
    try:
        analytics = db_manager.get_dashboard_analytics()
        
        # Get original summary
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(total_tests) as total,
                SUM(passed_tests) as passed,
                SUM(failed_tests) as failed,
                AVG(coverage_percentage) as coverage
            FROM test_runs 
            WHERE DATE(timestamp) = DATE('now')
        """)
        
        today_stats = cursor.fetchone()
        conn.close()
        
        return jsonify({
            "test_execution": {
                "total_tests": today_stats[0] or 0,
                "passed_tests": today_stats[1] or 0,
                "failed_tests": today_stats[2] or 0,
                "coverage": round(today_stats[3] or 0, 2),
            },
            "test_management": analytics["test_cases"],
            "bug_tracking": analytics["bugs"],
            "ai_insights": analytics["ai_suggestions"]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/api/integrations/settings", methods=["GET", "POST"])
def manage_integration_settings():
    """Manage integration settings"""
    if request.method == "GET":
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT service_name, config_data, is_active FROM integration_settings")
            settings = cursor.fetchall()
            conn.close()
            
            return jsonify([
                {
                    "service": row[0],
                    "config": json.loads(row[1]),
                    "active": bool(row[2])
                } for row in settings
            ])
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == "POST":
        data = request.json
        
        if not data.get('service_name') or not data.get('config'):
            return jsonify({'error': 'Service name and config are required'}), 400
        
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO integration_settings (service_name, config_data, is_active)
                VALUES (?, ?, ?)
            """, (
                data['service_name'],
                json.dumps(data['config']),
                data.get('is_active', True)
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    init_db()
    # Initialize enhanced database
    db_manager.init_enhanced_db()
    app.run(debug=True, port=6001)
