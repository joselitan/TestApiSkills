"""API tests for Entry Reactions endpoints (DEV-18).

Covers:
  GET  /api/entries/<id>/reactions  — public, no auth required
  POST /api/entries/<id>/reactions  — toggle reaction, auth required
"""

import pytest
import requests

BASE_URL = "http://localhost:8080"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def auth_token():
    """Obtain a JWT token for the admin user."""
    response = requests.post(
        f"{BASE_URL}/api/login", json={"username": "admin", "password": "password123"}
    )
    assert response.status_code == 200
    return response.json()["token"]


@pytest.fixture(scope="module")
def entry_id(auth_token):
    """Create a guestbook entry for reaction tests and return its ID."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(
        f"{BASE_URL}/api/guestbook",
        json={
            "name": "Reaction Tester",
            "email": "reactions@example.com",
            "comment": "Testing reactions",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["userId"]


# ---------------------------------------------------------------------------
# GET /api/entries/<id>/reactions — public access
# ---------------------------------------------------------------------------


def test_get_reactions_no_auth(entry_id):
    """GET reactions is publicly accessible without a token."""
    response = requests.get(f"{BASE_URL}/api/entries/{entry_id}/reactions")
    assert response.status_code == 200


def test_get_reactions_initial_counts(entry_id):
    """Freshly created entry has zero counts for all reaction types."""
    response = requests.get(f"{BASE_URL}/api/entries/{entry_id}/reactions")
    assert response.status_code == 200
    data = response.json()
    assert data["like"] == 0
    assert data["love"] == 0
    assert data["laugh"] == 0


def test_get_reactions_response_shape(entry_id):
    """Response includes like, love, laugh counts and user_reactions list."""
    response = requests.get(f"{BASE_URL}/api/entries/{entry_id}/reactions")
    data = response.json()
    assert "like" in data
    assert "love" in data
    assert "laugh" in data
    assert "user_reactions" in data
    assert isinstance(data["user_reactions"], list)


def test_get_reactions_nonexistent_entry():
    """GET on a non-existent entry ID returns 404."""
    response = requests.get(f"{BASE_URL}/api/entries/999999/reactions")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/entries/<id>/reactions — toggle, requires auth
# ---------------------------------------------------------------------------


def test_add_reaction_requires_auth(entry_id):
    """POST without a token is rejected with 401."""
    response = requests.post(
        f"{BASE_URL}/api/entries/{entry_id}/reactions",
        json={"reaction_type": "like"},
    )
    assert response.status_code == 401


def test_add_reaction_like(auth_token, entry_id):
    """POST adds a 'like' reaction and returns 201."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(
        f"{BASE_URL}/api/entries/{entry_id}/reactions",
        json={"reaction_type": "like"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["action"] == "added"


def test_get_reactions_after_like(auth_token, entry_id):
    """After adding 'like', the count reflects the new reaction."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(
        f"{BASE_URL}/api/entries/{entry_id}/reactions", headers=headers
    )
    data = response.json()
    assert data["like"] >= 1
    assert "like" in data["user_reactions"]


def test_toggle_removes_existing_reaction(auth_token, entry_id):
    """POSTing the same reaction a second time removes it (toggle off) → 200."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(
        f"{BASE_URL}/api/entries/{entry_id}/reactions",
        json={"reaction_type": "like"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["action"] == "removed"


def test_get_reactions_after_toggle_off(auth_token, entry_id):
    """After toggling 'like' off, the count is back to 0."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(
        f"{BASE_URL}/api/entries/{entry_id}/reactions", headers=headers
    )
    data = response.json()
    assert data["like"] == 0
    assert "like" not in data["user_reactions"]


def test_add_love_and_laugh_reactions(auth_token, entry_id):
    """Multiple reaction types can be added independently."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    for rt in ("love", "laugh"):
        resp = requests.post(
            f"{BASE_URL}/api/entries/{entry_id}/reactions",
            json={"reaction_type": rt},
            headers=headers,
        )
        assert resp.status_code == 201, f"Expected 201 for {rt}, got {resp.status_code}"


def test_counts_reflect_multiple_reactions(auth_token, entry_id):
    """Counts for love and laugh are now 1 each."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(
        f"{BASE_URL}/api/entries/{entry_id}/reactions", headers=headers
    )
    data = response.json()
    assert data["love"] == 1
    assert data["laugh"] == 1


def test_invalid_reaction_type_returns_400(auth_token, entry_id):
    """An unrecognised reaction_type returns 400 Bad Request."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(
        f"{BASE_URL}/api/entries/{entry_id}/reactions",
        json={"reaction_type": "angry"},
        headers=headers,
    )
    assert response.status_code == 400


def test_reaction_on_nonexistent_entry_returns_404(auth_token):
    """POSTing a reaction to a non-existent entry returns 404."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(
        f"{BASE_URL}/api/entries/999999/reactions",
        json={"reaction_type": "like"},
        headers=headers,
    )
    assert response.status_code == 404
