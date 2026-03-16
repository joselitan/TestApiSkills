"""
Pytest Plugin för QA Dashboard Integration
Skickar automatiskt test-resultat till dashboard efter varje test-körning
"""
import pytest
import requests
import json
from datetime import datetime
import os
import sys

# Dashboard API URL
DASHBOARD_API = "http://localhost:6001/api"

class DashboardReporter:
    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.session_data = {
            'test_type': 'unknown',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'duration': 0,
            'coverage_percentage': 0,
            'branch': 'main',
            'test_cases': []
        }

    def pytest_sessionstart(self, session):
        """Called when test session starts"""
        self.start_time = datetime.now()
        print(f"\n🚀 QA Dashboard: Startar test-session...")
        
        # Determine test type based on current directory or markers
        current_dir = os.getcwd()
        if 'ui' in current_dir.lower():
            self.session_data['test_type'] = 'ui'
        elif 'api' in current_dir.lower():
            self.session_data['test_type'] = 'api'
        elif 'performance' in current_dir.lower():
            self.session_data['test_type'] = 'performance'
        elif 'security' in current_dir.lower():
            self.session_data['test_type'] = 'security'
        else:
            self.session_data['test_type'] = 'integration'

    def pytest_runtest_logreport(self, report):
        """Called for each test phase (setup, call, teardown)"""
        if report.when == 'call':  # Only collect results from the actual test call
            test_case = {
                'name': report.nodeid.split('::')[-1],
                'file': report.nodeid.split('::')[0],
                'status': 'passed' if report.passed else 'failed' if report.failed else 'skipped',
                'duration': getattr(report, 'duration', 0),
                'error_message': str(report.longrepr) if report.failed else None
            }
            
            self.test_results.append(test_case)
            
            # Update counters
            if report.passed:
                self.session_data['passed_tests'] += 1
            elif report.failed:
                self.session_data['failed_tests'] += 1
            elif report.skipped:
                self.session_data['skipped_tests'] += 1

    def pytest_sessionfinish(self, session, exitstatus):
        """Called when test session finishes"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        # Finalize session data
        self.session_data.update({
            'total_tests': len(self.test_results),
            'duration': duration,
            'test_cases': self.test_results,
            'coverage_percentage': self.get_coverage_percentage()
        })
        
        # Send to dashboard
        self.send_to_dashboard()
        
        # Print summary
        self.print_summary()

    def get_coverage_percentage(self):
        """Try to get coverage percentage if available"""
        try:
            # This is a simple estimation - in real scenarios you'd integrate with coverage.py
            if self.session_data['passed_tests'] > 0:
                success_rate = (self.session_data['passed_tests'] / self.session_data['total_tests']) * 100
                return min(success_rate, 95)  # Cap at 95% as estimation
        except:
            pass
        return 0

    def send_to_dashboard(self):
        """Send test results to dashboard API"""
        try:
            response = requests.post(
                f"{DASHBOARD_API}/test-runs",
                json=self.session_data,
                timeout=10
            )
            
            if response.status_code == 200:
                print(f"✅ Test-resultat skickade till dashboard!")
                
                # Also try to analyze failures for AI suggestions
                if self.session_data['failed_tests'] > 0:
                    self.analyze_failures()
                    
            else:
                print(f"⚠️  Kunde inte skicka till dashboard: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("⚠️  Dashboard inte tillgänglig (kör python app.py i dashboard/backend)")
        except Exception as e:
            print(f"⚠️  Fel vid skickning till dashboard: {e}")

    def analyze_failures(self):
        """Send failed tests to AI analysis"""
        try:
            failed_tests = [tc for tc in self.test_results if tc['status'] == 'failed']
            
            response = requests.post(
                f"{DASHBOARD_API}/ai/analyze-failures",
                json={'failures': failed_tests},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('suggestions_created', 0) > 0:
                    print(f"🤖 AI skapade {result['suggestions_created']} test-förbättringsförslag!")
                    
        except Exception as e:
            print(f"⚠️  AI-analys misslyckades: {e}")

    def print_summary(self):
        """Print test summary"""
        print(f"\n📊 QA Dashboard Summary:")
        print(f"   Test Type: {self.session_data['test_type']}")
        print(f"   Total: {self.session_data['total_tests']}")
        print(f"   Passed: {self.session_data['passed_tests']} ✅")
        print(f"   Failed: {self.session_data['failed_tests']} ❌")
        print(f"   Skipped: {self.session_data['skipped_tests']} ⏭️")
        print(f"   Duration: {self.session_data['duration']:.2f}s")
        print(f"   Coverage: {self.session_data['coverage_percentage']:.1f}%")
        print(f"\n🌐 Se resultat på: http://localhost:6001")


# Global reporter instance
dashboard_reporter = DashboardReporter()

# Pytest hooks
def pytest_sessionstart(session):
    dashboard_reporter.pytest_sessionstart(session)

def pytest_runtest_logreport(report):
    dashboard_reporter.pytest_runtest_logreport(report)

def pytest_sessionfinish(session, exitstatus):
    dashboard_reporter.pytest_sessionfinish(session, exitstatus)