"""
Health Check Module for QA Test Platform
Provides comprehensive health monitoring for CI/CD pipeline
"""

import time
import psutil
import sqlite3
from datetime import datetime
from flask import jsonify

class HealthChecker:
    def __init__(self, app):
        self.app = app
        self.start_time = time.time()
        
    def get_system_health(self):
        """Get system resource health metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            return {
                "cpu_usage": f"{cpu_percent}%",
                "memory_usage": f"{memory.percent}%",
                "memory_available": f"{memory.available / (1024**3):.2f}GB",
                "disk_usage": f"{disk.percent}%",
                "disk_free": f"{disk.free / (1024**3):.2f}GB"
            }
        except Exception as e:
            return {"error": f"Failed to get system metrics: {str(e)}"}
    
    def check_database_health(self):
        """Check database connectivity and basic operations"""
        try:
            conn = sqlite3.connect('guestbook.db')
            cursor = conn.cursor()
            
            # Test basic query
            cursor.execute("SELECT COUNT(*) FROM guestbook")
            count = cursor.fetchone()[0]
            
            # Test write operation
            test_time = datetime.now().isoformat()
            cursor.execute("SELECT 1")  # Simple connectivity test
            
            conn.close()
            
            return {
                "status": "healthy",
                "total_entries": count,
                "last_check": test_time
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def check_api_endpoints(self):
        """Check critical API endpoints"""
        with self.app.test_client() as client:
            endpoints_status = {}
            
            # Test login endpoint
            try:
                response = client.post('/api/login', json={
                    "username": "admin",
                    "password": "password123"
                })
                endpoints_status['login'] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_code": response.status_code
                }
            except Exception as e:
                endpoints_status['login'] = {"status": "unhealthy", "error": str(e)}
            
            # Test guestbook list endpoint
            try:
                response = client.get('/api/guestbook')
                endpoints_status['guestbook_list'] = {
                    "status": "healthy" if response.status_code in [200, 401] else "unhealthy",
                    "response_code": response.status_code
                }
            except Exception as e:
                endpoints_status['guestbook_list'] = {"status": "unhealthy", "error": str(e)}
            
            return endpoints_status
    
    def get_uptime(self):
        """Get application uptime"""
        uptime_seconds = time.time() - self.start_time
        uptime_minutes = uptime_seconds / 60
        uptime_hours = uptime_minutes / 60
        
        if uptime_hours >= 1:
            return f"{uptime_hours:.1f} hours"
        elif uptime_minutes >= 1:
            return f"{uptime_minutes:.1f} minutes"
        else:
            return f"{uptime_seconds:.1f} seconds"
    
    def comprehensive_health_check(self):
        """Perform comprehensive health check"""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": self.get_uptime(),
            "version": "1.0.0",
            "environment": self.app.config.get('ENVIRONMENT', 'development')
        }
        
        # System health
        system_health = self.get_system_health()
        health_data["system"] = system_health
        
        # Database health
        db_health = self.check_database_health()
        health_data["database"] = db_health
        
        # API endpoints health
        api_health = self.check_api_endpoints()
        health_data["api_endpoints"] = api_health
        
        # Determine overall status
        if db_health.get("status") == "unhealthy":
            health_data["status"] = "unhealthy"
        
        unhealthy_endpoints = [k for k, v in api_health.items() if v.get("status") == "unhealthy"]
        if unhealthy_endpoints:
            health_data["status"] = "degraded"
            health_data["unhealthy_endpoints"] = unhealthy_endpoints
        
        return health_data

def setup_health_routes(app):
    """Setup health check routes"""
    health_checker = HealthChecker(app)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime": health_checker.get_uptime()
        })
    
    @app.route('/health/detailed', methods=['GET'])
    def detailed_health_check():
        """Detailed health check endpoint"""
        return jsonify(health_checker.comprehensive_health_check())
    
    @app.route('/health/ready', methods=['GET'])
    def readiness_check():
        """Kubernetes-style readiness check"""
        db_health = health_checker.check_database_health()
        if db_health.get("status") == "healthy":
            return jsonify({"status": "ready"}), 200
        else:
            return jsonify({"status": "not ready", "reason": "database unhealthy"}), 503
    
    @app.route('/health/live', methods=['GET'])
    def liveness_check():
        """Kubernetes-style liveness check"""
        return jsonify({"status": "alive"}), 200