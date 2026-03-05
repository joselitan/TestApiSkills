import pytest
import os
import sys
from database import init_db, clear_test_db, get_db_path

# Sätt test mode environment variable
os.environ['TEST_MODE'] = '1'

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database before all tests"""
    print("\n🔧 Setting up test database...")
    init_db(test_mode=True)
    print(f"✅ Test database created: {get_db_path(test_mode=True)}")
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
