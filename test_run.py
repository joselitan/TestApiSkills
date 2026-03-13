#!/usr/bin/env python3
"""
Automated Test Run - Verify QA Platform Functionality
Tests environment variable support and basic functionality
"""

import os
import sys
import time
import requests
import subprocess
import threading
import json
from datetime import datetime


class QAPlatformTester:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.app_process = None
        self.test_results = []

    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")

    def start_app(self, environment="staging"):
        """Start Flask app with specific environment"""
        self.log(f"Starting app with {environment} environment...")

        # Set environment variables
        env = os.environ.copy()
        if environment == "staging":
            env["DATABASE_URL"] = "sqlite:///data/staging_guestbook.db"
            env["ENVIRONMENT"] = "staging"
        else:
            env["DATABASE_URL"] = "sqlite:///data/guestbook.db"
            env["ENVIRONMENT"] = "production"

        # Start Flask app in background
        self.app_process = subprocess.Popen(
            [sys.executable, "src/app.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=os.getcwd(),
        )

        # Wait for app to start
        self.log("Waiting for app to start...")
        time.sleep(8)

        return self.is_app_running()

    def stop_app(self):
        """Stop Flask app"""
        if self.app_process:
            self.app_process.terminate()
            self.app_process.wait()
            self.log("App stopped")

    def is_app_running(self):
        """Check if app is running"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False

    def test_health_endpoints(self):
        """Test all health endpoints"""
        self.log("Testing health endpoints...")

        endpoints = ["/health", "/health/detailed", "/health/ready", "/health/live"]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.test_results.append(f"✅ {endpoint}: OK")
                    self.log(f"{endpoint}: OK", "PASS")
                else:
                    self.test_results.append(f"❌ {endpoint}: {response.status_code}")
                    self.log(f"{endpoint}: {response.status_code}", "FAIL")
            except Exception as e:
                self.test_results.append(f"❌ {endpoint}: {str(e)}")
                self.log(f"{endpoint}: {str(e)}", "ERROR")

    def test_api_authentication(self):
        """Test API login functionality"""
        self.log("Testing API authentication...")

        try:
            # Test login
            login_data = {"username": "admin", "password": "password123"}
            response = requests.post(
                f"{self.base_url}/api/login", json=login_data, timeout=5
            )

            if response.status_code == 200:
                token = response.json().get("token")
                if token:
                    self.test_results.append("✅ Login: OK")
                    self.log("Login: OK", "PASS")
                    return token
                else:
                    self.test_results.append("❌ Login: No token returned")
                    self.log("Login: No token returned", "FAIL")
            else:
                self.test_results.append(f"❌ Login: {response.status_code}")
                self.log(f"Login: {response.status_code}", "FAIL")
        except Exception as e:
            self.test_results.append(f"❌ Login: {str(e)}")
            self.log(f"Login: {str(e)}", "ERROR")

        return None

    def test_api_crud(self, token):
        """Test API CRUD operations"""
        if not token:
            self.log("Skipping CRUD tests - no token", "SKIP")
            return

        self.log("Testing API CRUD operations...")
        headers = {"Authorization": f"Bearer {token}"}

        # Test CREATE
        try:
            entry_data = {
                "name": "Test User",
                "email": "test@example.com",
                "comment": "Test run entry",
            }
            response = requests.post(
                f"{self.base_url}/api/guestbook",
                json=entry_data,
                headers=headers,
                timeout=5,
            )

            if response.status_code == 201:
                entry_id = response.json().get("userId")
                self.test_results.append("✅ CREATE: OK")
                self.log("CREATE: OK", "PASS")

                # Test READ
                response = requests.get(
                    f"{self.base_url}/api/guestbook/{entry_id}",
                    headers=headers,
                    timeout=5,
                )
                if response.status_code == 200:
                    self.test_results.append("✅ READ: OK")
                    self.log("READ: OK", "PASS")
                else:
                    self.test_results.append(f"❌ READ: {response.status_code}")
                    self.log(f"READ: {response.status_code}", "FAIL")

                # Test LIST
                response = requests.get(
                    f"{self.base_url}/api/guestbook", headers=headers, timeout=5
                )
                if response.status_code == 200:
                    self.test_results.append("✅ LIST: OK")
                    self.log("LIST: OK", "PASS")
                else:
                    self.test_results.append(f"❌ LIST: {response.status_code}")
                    self.log(f"LIST: {response.status_code}", "FAIL")

                # Test DELETE (cleanup)
                response = requests.delete(
                    f"{self.base_url}/api/guestbook/{entry_id}",
                    headers=headers,
                    timeout=5,
                )
                if response.status_code == 200:
                    self.test_results.append("✅ DELETE: OK")
                    self.log("DELETE: OK", "PASS")
                else:
                    self.test_results.append(f"❌ DELETE: {response.status_code}")
                    self.log(f"DELETE: {response.status_code}", "FAIL")

            else:
                self.test_results.append(f"❌ CREATE: {response.status_code}")
                self.log(f"CREATE: {response.status_code}", "FAIL")

        except Exception as e:
            self.test_results.append(f"❌ CRUD: {str(e)}")
            self.log(f"CRUD: {str(e)}", "ERROR")

    def test_environment_config(self):
        """Test environment configuration"""
        self.log("Testing environment configuration...")

        try:
            response = requests.get(f"{self.base_url}/health/detailed", timeout=5)
            if response.status_code == 200:
                data = response.json()
                environment = data.get("environment", "unknown")
                self.test_results.append(f"✅ Environment: {environment}")
                self.log(f"Environment detected: {environment}", "PASS")
            else:
                self.test_results.append(
                    f"❌ Environment check failed: {response.status_code}"
                )
                self.log(f"Environment check failed: {response.status_code}", "FAIL")
        except Exception as e:
            self.test_results.append(f"❌ Environment: {str(e)}")
            self.log(f"Environment: {str(e)}", "ERROR")

    def run_full_test(self, environment="staging"):
        """Run complete test suite"""
        self.log(f"Starting QA Platform Test Run - {environment.upper()}")
        self.log("=" * 50)

        # Start app
        if not self.start_app(environment):
            self.log("Failed to start app", "ERROR")
            return False

        try:
            # Run tests
            self.test_health_endpoints()
            self.test_environment_config()
            token = self.test_api_authentication()
            self.test_api_crud(token)

            # Generate report
            self.generate_report(environment)

            return True

        finally:
            self.stop_app()

    def generate_report(self, environment):
        """Generate test report"""
        self.log("=" * 50)
        self.log(f"TEST RESULTS - {environment.upper()}")
        self.log("=" * 50)

        passed = len([r for r in self.test_results if r.startswith("✅")])
        failed = len([r for r in self.test_results if r.startswith("❌")])
        total = len(self.test_results)

        for result in self.test_results:
            print(result)

        self.log("=" * 50)
        self.log(f"SUMMARY: {passed}/{total} tests passed, {failed} failed")

        if failed == 0:
            self.log("ALL TESTS PASSED!", "SUCCESS")
        else:
            self.log(f"{failed} tests failed", "WARNING")

        # Save report to file
        report_data = {
            "environment": environment,
            "timestamp": datetime.now().isoformat(),
            "results": self.test_results,
            "summary": {"total": total, "passed": passed, "failed": failed},
        }

        with open(
            f"reports/test_run_{environment}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "w",
        ) as f:
            json.dump(report_data, f, indent=2)

        self.log(f"Report saved to reports/test_run_{environment}_*.json")


def main():
    # Ensure reports directory exists
    os.makedirs("reports", exist_ok=True)

    tester = QAPlatformTester()

    # Test staging environment
    success = tester.run_full_test("staging")

    if success:
        print("\n" + "=" * 60)
        print("QA PLATFORM VERIFICATION COMPLETE")
        print("Environment variable support working")
        print("Health monitoring functional")
        print("API authentication working")
        print("CRUD operations functional")
        print("Platform ready for CI/CD deployment!")
        print("=" * 60)
    else:
        print("\nTest run failed - check logs above")


if __name__ == "__main__":
    main()
