import json
import os

import pytest
import requests

BASE_URL = "http://localhost:8080"
token = None


@pytest.fixture(scope="module")
def auth_token():
    response = requests.post(
        f"{BASE_URL}/api/login", json={"username": "admin", "password": "password123"}
    )
    assert response.status_code == 200
    return response.json()["token"]


def test_login_success():
    response = requests.post(
        f"{BASE_URL}/api/login", json={"username": "admin", "password": "password123"}
    )
    assert response.status_code == 200
    assert "token" in response.json()


def test_login_invalid():
    response = requests.post(
        f"{BASE_URL}/api/login", json={"username": "admin", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_protected_without_token():
    response = requests.get(f"{BASE_URL}/api/guestbook")
    assert response.status_code == 401


def test_create_entry(auth_token):
    print("\n--- Test: Create a new guestbook entry")
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "name": "Emelie User",
        "email": "emelie@example.com",
        "comment": "Helping my mom",
    }
    print(f"POST /api/guestbook")
    print(f"    Payload: {json.dumps(payload, indent=2)}")

    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)

    print(f"Response Status Code: {response.status_code}")
    print(f"    Response JSON: {json.dumps(response.json(), indent=2)}")
    assert response.status_code == 201
    data = response.json()

    print("Verifying response content...")
    assert data["name"] == "Emelie User"
    assert data["email"] == "emelie@example.com"
    assert data["comment"] == "Helping my mom"
    assert "userId" in data
    print(f"Entry created with ID: {data['userId']}")


def test_read_all_entries(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{BASE_URL}/api/guestbook", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # Response is now a dict with 'data' and 'meta' keys due to pagination
    assert isinstance(data, dict)
    assert "data" in data
    assert isinstance(data["data"], list)


def test_read_all_with_search(auth_token):
    print("\n--- Test: Search/filter guestbook entries ---")
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Create two entries for testing search
    payload1 = {
        "name": "Search Test User One",
        "email": "search1@example.com",
        "comment": "This entry contains the unique keyword 'XYZ_UNIQUE'",
    }
    payload2 = {
        "name": "Search Test User Two",
        "email": "search2@example.com",
        "comment": "This is just another entry",
    }

    create_resp1 = requests.post(
        f"{BASE_URL}/api/guestbook", json=payload1, headers=headers
    )
    assert create_resp1.status_code == 201
    entry_id1 = create_resp1.json()["userId"]
    print(f"Created entry 1 with ID: {entry_id1}")

    create_resp2 = requests.post(
        f"{BASE_URL}/api/guestbook", json=payload2, headers=headers
    )
    assert create_resp2.status_code == 201
    entry_id2 = create_resp2.json()["userId"]
    print(f"Created entry 2 with ID: {entry_id2}")

    search_term = "XYZ_UNIQUE"
    print(f"GET /api/guestbook?search={search_term}")
    response = requests.get(
        f"{BASE_URL}/api/guestbook?search={search_term}", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    print(f"Response JSON: {json.dumps(data, indent=2)}")

    print("Verifying search results...")
    assert len(data["data"]) == 1, "Should only find one entry"
    assert data["data"][0]["name"] == "Search Test User One"
    assert data["meta"]["total"] == 1, "Metadata total should be 1"
    print("Search verification successful")


def test_read_single_entry(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    payload = {
        "name": "Single Test",
        "email": "single@example.com",
        "comment": "Single entry test",
    }
    create_response = requests.post(
        f"{BASE_URL}/api/guestbook", json=payload, headers=headers
    )
    entry_id = create_response.json()["userId"]

    response = requests.get(f"{BASE_URL}/api/guestbook/{entry_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Single Test"
    assert data["email"] == "single@example.com"


def test_update_entry(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    payload = {
        "name": "Update Test",
        "email": "update@example.com",
        "comment": "Original comment",
    }
    create_response = requests.post(
        f"{BASE_URL}/api/guestbook", json=payload, headers=headers
    )
    entry_id = create_response.json()["userId"]

    update_payload = {
        "name": "Updated Name",
        "email": "updated@example.com",
        "comment": "Updated comment",
    }
    response = requests.put(
        f"{BASE_URL}/api/guestbook/{entry_id}", json=update_payload, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["email"] == "updated@example.com"
    assert data["comment"] == "Updated comment"


def test_delete_entry(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    payload = {
        "name": "Delete Test",
        "email": "delete@example.com",
        "comment": "To be deleted",
    }
    create_response = requests.post(
        f"{BASE_URL}/api/guestbook", json=payload, headers=headers
    )
    entry_id = create_response.json()["userId"]

    response = requests.delete(f"{BASE_URL}/api/guestbook/{entry_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Entry deleted successfully"

    get_response = requests.get(f"{BASE_URL}/api/guestbook/{entry_id}", headers=headers)
    assert get_response.status_code == 404


def test_delete_nonexistent(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.delete(f"{BASE_URL}/api/guestbook/99999", headers=headers)
    assert response.status_code == 404


def test_import_excel(auth_token):
    import pandas as pd

    df = pd.DataFrame(
        {
            "name": ["Excel User 1", "Excel User 2"],
            "email": ["excel1@example.com", "excel2@example.com"],
            "comment": ["Excel comment 1", "Excel comment 2"],
        }
    )

    excel_file = "test_import.xlsx"
    df.to_excel(excel_file, index=False)

    headers = {"Authorization": f"Bearer {auth_token}"}
    with open(excel_file, "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{BASE_URL}/api/guestbook/import", files=files, headers=headers
        )

    os.remove(excel_file)

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2


def test_import_invalid_file(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}

    with open("test_invalid.txt", "w") as f:
        f.write("invalid content")

    with open("test_invalid.txt", "rb") as f:
        files = {"file": f}
        response = requests.post(
            f"{BASE_URL}/api/guestbook/import", files=files, headers=headers
        )

    os.remove("test_invalid.txt")

    assert response.status_code == 400


def test_zzz_cleanup_all_test_data(auth_token):
    """Cleanup method - runs last (alphabetically) to remove all test data"""
    print("\n--- CLEANUP: Removing all test data from database ---")
    headers = {"Authorization": f"Bearer {auth_token}"}

    # Get all entries
    # simple comment
    response = requests.get(f"{BASE_URL}/api/guestbook?limit=1000", headers=headers)
    if response.status_code == 200:
        data = response.json()
        entries = data.get("data", [])

        if entries:
            print(f"Found {len(entries)} entries to clean up")
            for entry in entries:
                entry_id = entry["userId"]
                delete_resp = requests.delete(
                    f"{BASE_URL}/api/guestbook/{entry_id}", headers=headers
                )
                if delete_resp.status_code == 200:
                    print(f"   Deleted entry ID: {entry_id}")
            print("Cleanup completed - Database is clean")
        else:
            print("No entries to clean up")
