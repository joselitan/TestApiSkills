"""
Contract tests for API v1 endpoints (DEV-28).

These tests assert response *shape* only — status codes and required fields.
They act as a specification: if a future change silently renames a field or
drops a required key, exactly this file will fail and CI will catch it.
"""

import pytest
import requests

BASE_URL = "http://127.0.0.1:8080"
V1 = f"{BASE_URL}/api/v1"


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def token():
    resp = requests.post(
        f"{V1}/login", json={"username": "admin", "password": "password123"}
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def entry_id(auth_headers):
    """Create a guestbook entry and return its userId for use in tests."""
    resp = requests.post(
        f"{V1}/guestbook",
        json={
            "name": "Contract Tester",
            "email": "contract@example.com",
            "comment": "contract test entry",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()["userId"]


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------


def test_login_returns_token():
    resp = requests.post(
        f"{V1}/login", json={"username": "admin", "password": "password123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "token" in body
    assert isinstance(body["token"], str)
    assert len(body["token"]) > 10


def test_login_wrong_password_returns_401():
    resp = requests.post(
        f"{V1}/login", json={"username": "admin", "password": "wrong"}
    )
    assert resp.status_code == 401
    assert "message" in resp.json()


def test_login_missing_fields_returns_400():
    resp = requests.post(f"{V1}/login", json={"username": "admin"})
    assert resp.status_code == 400
    assert "message" in resp.json()


def test_register_duplicate_returns_409_or_400():
    resp = requests.post(
        f"{V1}/register",
        json={
            "username": "admin",
            "email": "admin@example.com",
            "password": "password123",
        },
    )
    assert resp.status_code in (400, 409)
    assert "message" in resp.json()


# ---------------------------------------------------------------------------
# Guestbook endpoints
# ---------------------------------------------------------------------------


def test_get_guestbook_requires_auth():
    resp = requests.get(f"{V1}/guestbook")
    assert resp.status_code == 401


def test_get_guestbook_shape(auth_headers):
    resp = requests.get(f"{V1}/guestbook", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    assert "meta" in body
    assert isinstance(body["data"], list)
    meta = body["meta"]
    assert "total" in meta
    assert "page" in meta
    assert "limit" in meta
    assert isinstance(meta["total"], int)
    assert isinstance(meta["page"], int)
    assert isinstance(meta["limit"], int)


def test_get_guestbook_entry_shape(auth_headers, entry_id):
    resp = requests.get(f"{V1}/guestbook/{entry_id}", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    for field in ("userId", "name", "email", "comment"):
        assert field in body, f"Missing field: {field}"
    assert isinstance(body["userId"], int)
    assert isinstance(body["name"], str)
    assert isinstance(body["email"], str)
    assert isinstance(body["comment"], str)


def test_create_guestbook_entry_shape(auth_headers):
    resp = requests.post(
        f"{V1}/guestbook",
        json={
            "name": "Shape Tester",
            "email": "shape@example.com",
            "comment": "shape test",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    for field in ("userId", "name", "email", "comment"):
        assert field in body, f"Missing field: {field}"


def test_create_guestbook_missing_fields_returns_400(auth_headers):
    resp = requests.post(
        f"{V1}/guestbook", json={"name": "No Email"}, headers=auth_headers
    )
    assert resp.status_code == 400
    assert "message" in resp.json()


def test_get_nonexistent_entry_returns_404(auth_headers):
    resp = requests.get(f"{V1}/guestbook/999999999", headers=auth_headers)
    assert resp.status_code == 404
    assert "message" in resp.json()


def test_update_guestbook_entry_shape(auth_headers, entry_id):
    resp = requests.put(
        f"{V1}/guestbook/{entry_id}",
        json={
            "name": "Contract Tester",
            "email": "contract@example.com",
            "comment": "updated comment",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    for field in ("userId", "name", "email", "comment"):
        assert field in body, f"Missing field: {field}"


def test_delete_nonexistent_entry_returns_404(auth_headers):
    resp = requests.delete(f"{V1}/guestbook/999999999", headers=auth_headers)
    assert resp.status_code == 404
    assert "message" in resp.json()


# ---------------------------------------------------------------------------
# Webhook endpoints
# ---------------------------------------------------------------------------


def test_get_webhooks_requires_auth():
    resp = requests.get(f"{V1}/webhooks")
    assert resp.status_code == 401


def test_get_webhooks_shape(auth_headers):
    resp = requests.get(f"{V1}/webhooks", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "webhooks" in body
    assert isinstance(body["webhooks"], list)


def test_register_webhook_missing_url_returns_400(auth_headers):
    resp = requests.post(f"{V1}/webhooks", json={}, headers=auth_headers)
    assert resp.status_code == 400
    assert "message" in resp.json()


# ---------------------------------------------------------------------------
# Reactions endpoints
# ---------------------------------------------------------------------------


def test_get_reactions_shape(entry_id):
    resp = requests.get(f"{V1}/entries/{entry_id}/reactions")
    assert resp.status_code == 200
    body = resp.json()
    # Response contains reaction counts as top-level keys
    for field in ("like", "love", "laugh"):
        assert field in body, f"Missing reaction field: {field}"
        assert isinstance(body[field], int)


def test_get_reactions_nonexistent_entry_returns_404():
    resp = requests.get(f"{V1}/entries/999999999/reactions")
    assert resp.status_code == 404
    assert "message" in resp.json()


def test_post_reaction_requires_auth(entry_id):
    resp = requests.post(
        f"{V1}/entries/{entry_id}/reactions", json={"reaction": "like"}
    )
    assert resp.status_code == 401


def test_post_invalid_reaction_returns_400(auth_headers, entry_id):
    resp = requests.post(
        f"{V1}/entries/{entry_id}/reactions",
        json={"reaction": "invalid_type"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "message" in resp.json()
