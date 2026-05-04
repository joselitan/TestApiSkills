import json

import pytest
import requests


def test_1_verify_invalid_login():
    """Description: Verify that login fails with invalid credentials"""
    payload = {"username": "invaliduser", "password": "invalidpassword"}
    response = requests.post("http://localhost:8080/api/v1/login", json=payload)
    print(response.status_code)
    print(response.json())
    assert (
        response.status_code == 401
    ), f"FÃ¶rvÃ¤ntade statuskod 401 fÃ¶r ogiltig inloggning"


def test_2_verify_login_fields():
    """Description: Authenticate user and receive JWT token"""
    payload = {"username": "admin", "password": "password123"}
    response = requests.post("http://localhost:8080/api/v1/login", json=payload)
    print(response.status_code)
    print(response.json())
    assert response.status_code == 200, f"FÃ¶rvÃ¤ntade statuskod 200"
    assert (
        "token" in response.json()
    ), f"FÃ¶rvÃ¤ntade token saknas i svaret. Hittade: {response.json()}"


def test_3_access_guestbook_endpoint():
    """Description: Access protected endpoint with valid JWT token"""
    # First, authenticate to get the token
    auth_payload = {"username": "admin", "password": "password123"}
    auth_response = requests.post("http://localhost:8080/api/v1/login", json=auth_payload)
    token = auth_response.json().get("token")

    # Now access the protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("http://localhost:8080/api/v1/guestbook", headers=headers)
    print(response.status_code)
    print(json.dumps(response.json(), indent=4))
    assert response.status_code == 200, f"FÃ¶rvÃ¤ntade statuskod 200 fÃ¶r skyddad resurs"


def test_4_create_guestbook_entry():
    """Description: Create a new guestbook entry with valid JWT token"""
    # First, authenticate to get the token
    auth_payload = {"username": "admin", "password": "password123"}
    auth_response = requests.post("http://localhost:8080/api/v1/login", json=auth_payload)
    token = auth_response.json().get("token")

    # Now create a new guestbook entry
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "name": "Jose User",
        "email": "jose.user@example.com",
        "comment": "HjÃ¤lper pappa att testa API:et",
    }
    response = requests.post(
        "http://localhost:8080/api/v1/guestbook", json=payload, headers=headers
    )
    print(response.status_code)
    print(response.json())
    assert (
        response.status_code == 201
    ), f"FÃ¶rvÃ¤ntade statuskod 201 fÃ¶r att skapa gÃ¤stboksinlÃ¤gg"


def test_5_delete_guestbook_entry():
    """Description: Delete a guestbook entry with valid JWT token"""
    # First, authenticate to get the token
    auth_payload = {"username": "admin", "password": "password123"}
    auth_response = requests.post("http://localhost:8080/api/v1/login", json=auth_payload)
    token = auth_response.json().get("token")

    # Now delete a guestbook entry
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.delete(
        "http://localhost:8080/api/v1/guestbook/27", headers=headers
    )
    print(response.status_code)
    print(response.json())
    assert (
        response.status_code == 200
    ), f"FÃ¶rvÃ¤ntade statuskod 200 fÃ¶r att ta bort gÃ¤stboksinlÃ¤gg"


def test_6_access_guestbook_without_token():
    """Description: Attempt to access protected endpoint without JWT token"""
    response = requests.get("http://localhost:8080/api/v1/guestbook")
    print(response.status_code)
    print(response.json())
    assert (
        response.status_code == 401
    ), f"FÃ¶rvÃ¤ntade statuskod 401 fÃ¶r att komma Ã¥t skyddad resurs utan token"


@pytest.mark.skip(
    reason="Only run this test if you have guestbook with several entries to delete"
)
def test_7_bulk_delete_guestbook_entries():
    """Description: Bulk delete guestbook entries with valid JWT token"""
    # First, authenticate to get the token
    auth_payload = {"username": "admin", "password": "password123"}
    auth_response = requests.post("http://localhost:8080/api/v1/login", json=auth_payload)
    token = auth_response.json().get("token")

    # Now bulk delete guestbook entries
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"ids": [8, 9, 10]}
    response = requests.delete(
        "http://localhost:8080/api/v1/guestbook/bulk", json=payload, headers=headers
    )
    print(response.status_code)
    print(response.json())
    assert (
        response.status_code == 200
    ), f"FÃ¶rvÃ¤ntade statuskod 200 fÃ¶r att bulk ta bort gÃ¤stboksinlÃ¤gg"
