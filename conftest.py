import pytest
import os
import sys
import requests

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import init_db, clear_test_db, get_db_path
from tests.fixtures.factories import create_guestbook_entry, create_multiple_entries

# Sätt test mode environment variable
os.environ['TEST_MODE'] = '1'

BASE_URL = "http://localhost:8080"

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
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "admin",
        "password": "password123"
    })
    return response.json()['token']

@pytest.fixture
def test_entry():
    """Generate a single test entry using factory"""
    return create_guestbook_entry()

@pytest.fixture
def test_entries():
    """Generate multiple test entries using factory"""
    return create_multiple_entries(5)
