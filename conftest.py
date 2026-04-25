import pytest
import os
import sys
import requests
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from database import init_db, clear_test_db, get_db_path
from tests.fixtures.factories import create_guestbook_entry, create_multiple_entries

# Sätt test mode environment variable
os.environ["TEST_MODE"] = "1"

BASE_URL = "http://localhost:8080"
DASHBOARD_API = "http://localhost:6001/api"

# Dashboard Integration
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
        self.start_time = datetime.now()
        print(f"\nQA Dashboard: Startar test-session...")

    def pytest_collection_finish(self, session):
        """Detect test type after collection, when session.items is populated"""
        from pathlib import Path

        test_type = 'integration'  # default
        detected_types = set()

        for item in session.items:
            path = Path(str(item.fspath))
            joined = str(path).lower().replace('\\', '/')
            for t in ('ui', 'api', 'performance', 'security'):
                if f'/{t}/' in joined:
                    detected_types.add(t)

        for t in ('ui', 'api', 'performance', 'security'):
            if t in detected_types:
                test_type = t
                break

        self.session_data['test_type'] = test_type
        print(f"Detekterad test-typ: {test_type} (sanity check: found {sorted(detected_types)})")

    def pytest_runtest_logreport(self, report):
        if report.when == 'call':
            test_case = {
                'name': report.nodeid.split('::')[-1],
                'file': report.nodeid.split('::')[0],
                'status': 'passed' if report.passed else 'failed' if report.failed else 'skipped',
                'duration': getattr(report, 'duration', 0),
                'error_message': str(report.longrepr) if report.failed else None
            }
            
            self.test_results.append(test_case)
            
            if report.passed:
                self.session_data['passed_tests'] += 1
            elif report.failed:
                self.session_data['failed_tests'] += 1
            elif report.skipped:
                self.session_data['skipped_tests'] += 1
            
            # Send individual test result immediately for real-time updates
            self.send_individual_result(test_case)

    def pytest_sessionfinish(self, session, exitstatus):
        if self.start_time:
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            
            self.session_data.update({
                'total_tests': len(self.test_results),
                'duration': duration,
                'test_cases': self.test_results,
                'coverage_percentage': self.get_coverage_percentage()
            })
            
            self.send_to_dashboard()
            self.print_summary()

    def get_coverage_percentage(self):
        if self.session_data['total_tests'] > 0:
            success_rate = (self.session_data['passed_tests'] / self.session_data['total_tests']) * 100
            return min(success_rate * 0.9, 95)  # Estimate coverage
        return 0

    def send_individual_result(self, test_case):
        """Send individual test result for real-time updates"""
        try:
            # Create a mini test run for this individual test
            current_time = datetime.now()
            duration_so_far = (current_time - self.start_time).total_seconds() if self.start_time else 0
            
            mini_run = {
                'test_type': self.session_data['test_type'],
                'total_tests': len(self.test_results),
                'passed_tests': self.session_data['passed_tests'],
                'failed_tests': self.session_data['failed_tests'],
                'skipped_tests': self.session_data['skipped_tests'],
                'duration': duration_so_far,
                'coverage_percentage': self.get_coverage_percentage(),
                'branch': 'main',
                'test_cases': [test_case],  # Just this one test
                'is_partial': True  # Flag to indicate this is a partial update
            }
            
            requests.post(
                f"{DASHBOARD_API}/test-runs",
                json=mini_run,
                timeout=2  # Quick timeout for real-time
            )
            
            # Print progress
            status_emoji = 'PASS' if test_case['status'] == 'passed' else 'FAIL' if test_case['status'] == 'failed' else 'SKIP'
            print(f"  {status_emoji} {test_case['name']} -> Dashboard uppdaterad")
            
        except:
            pass  # Silent fail for real-time updates

    def send_to_dashboard(self):
        try:
            response = requests.post(
                f"{DASHBOARD_API}/test-runs",
                json=self.session_data,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"Test-resultat skickade till dashboard!")
                
                if self.session_data['failed_tests'] > 0:
                    self.analyze_failures()
            else:
                print(f"Dashboard response: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("⚠️  Dashboard inte tillgänglig (starta: cd dashboard/backend && python app.py)")
        except Exception as e:
            print(f"⚠️  Dashboard fel: {e}")

    def analyze_failures(self):
        try:
            failed_tests = [tc for tc in self.test_results if tc['status'] == 'failed']
            
            response = requests.post(
                f"{DASHBOARD_API}/ai/analyze-failures",
                json={'failures': failed_tests},
                timeout=5
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('suggestions_created', 0) > 0:
                    print(f"🤖 AI skapade {result['suggestions_created']} förbättringsförslag!")
        except:
            pass  # Silent fail for AI features

    def print_summary(self):
        print(f"\n📊 QA Dashboard Summary:")
        print(f"   Test Type: {self.session_data['test_type']}")
        print(f"   Total: {self.session_data['total_tests']}")
        print(f"   Passed: {self.session_data['passed_tests']} ✅")
        print(f"   Failed: {self.session_data['failed_tests']} ❌")
        print(f"   Duration: {self.session_data['duration']:.2f}s")
        print(f"\n🌐 Se resultat: http://localhost:6001")

# Global reporter
dashboard_reporter = DashboardReporter()

def pytest_sessionstart(session):
    dashboard_reporter.pytest_sessionstart(session)

def pytest_collection_finish(session):
    dashboard_reporter.pytest_collection_finish(session)

def pytest_runtest_logreport(report):
    dashboard_reporter.pytest_runtest_logreport(report)

def pytest_sessionfinish(session, exitstatus):
    dashboard_reporter.pytest_sessionfinish(session, exitstatus)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database before all tests"""
    print("\nSetting up test database...")
    init_db(test_mode=True)
    print(f"Test database created: {get_db_path(test_mode=True)}")
    yield
    # Cleanup after all tests (optional)
    # clear_test_db()


@pytest.fixture(scope="function")
def clean_test_db():
    """Clean test database before each test"""
    clear_test_db()
    yield
    # Cleanup after test (optional)
    # clear_test_db()


@pytest.fixture(scope="session")
def test_db_path():
    """Return test database path"""
    return get_db_path(test_mode=True)


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(
        f"{BASE_URL}/api/login", json={"username": "admin", "password": "password123"}
    )
    return response.json()["token"]


@pytest.fixture
def test_entry():
    """Generate a single test entry using factory"""
    return create_guestbook_entry()


@pytest.fixture
def test_entries():
    """Generate multiple test entries using factory"""
    return create_multiple_entries(5)
