"""
Shared fixtures for all API tests.

A single session-scoped auth_token is obtained here so that every test
module can reuse it without triggering additional login requests.  Without
this the login endpoint's rate-limit (5/min) is exhausted almost immediately
when the full suite runs, causing every fixture that calls /api/v1/login
to receive 429 and all dependent tests to ERROR.
"""

import time

import pytest
import requests

BASE_URL = "http://127.0.0.1:8080"


@pytest.fixture(scope="session")
def auth_token():
    """JWT token for the admin user, shared across the entire test session.

    Retries with back-off if the login endpoint returns 429 (rate limited).
    This can happen when test files that call /login directly run before this
    fixture and exhaust the 5-per-minute quota.
    """
    for attempt in range(6):
        response = requests.post(
            f"{BASE_URL}/api/v1/login",
            json={"username": "admin", "password": "password123"},
        )
        if response.status_code == 200:
            return response.json()["token"]
        if response.status_code == 429:
            wait = 12 * (attempt + 1)  # 12s, 24s, 36s … up to 72s
            print(f"\n[conftest] Login rate-limited (429), waiting {wait}s before retry {attempt + 1}/6…")
            time.sleep(wait)
        else:
            pytest.fail(
                f"Login failed during test setup: {response.status_code} {response.text}"
            )
    pytest.fail("Login still rate-limited after 6 retries — restart the server to reset.")


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    """Authorization header dict, shared across the entire test session."""
    return {"Authorization": f"Bearer {auth_token}"}
