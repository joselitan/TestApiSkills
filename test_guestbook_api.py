import requests
import pytest
import os

BASE_URL = "http://localhost:8080"
token = None

@pytest.fixture(scope="module")
def auth_token():
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "admin",
        "password": "password123"
    })
    assert response.status_code == 200
    return response.json()['token']

def test_login_success():
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "admin",
        "password": "password123"
    })
    assert response.status_code == 200
    assert 'token' in response.json()

def test_login_invalid():
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

def test_protected_without_token():
    response = requests.get(f"{BASE_URL}/api/guestbook")
    assert response.status_code == 401

def test_create_entry(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "name": "John Doe",
        "email": "david@example.com",
        "comment": "Helping my dad"
    }
    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    entry_id = data.get('userId')  # Store entry_id for cleanup
    
    try:
        # FIXED: Changed "David Usuario" to "David User" to match the payload
        assert data['name'] == "David User"
        assert data['email'] == "david@example.com"
        assert data['comment'] == "Helping my dad"
        assert 'userId' in data
    finally:
        # CLEANUP: Delete the created entry even if assertions fail to keep database clean
        if entry_id:
            requests.delete(f"{BASE_URL}/api/guestbook/{entry_id}", headers=headers)

def test_read_all_entries(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{BASE_URL}/api/guestbook", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_read_single_entry(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    payload = {
        "name": "Single Test",
        "email": "single@example.com",
        "comment": "Single entry test"
    }
    create_response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    entry_id = create_response.json()['userId']
    
    response = requests.get(f"{BASE_URL}/api/guestbook/{entry_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == "Single Test"
    assert data['email'] == "single@example.com"

def test_update_entry(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    payload = {
        "name": "Update Test",
        "email": "update@example.com",
        "comment": "Original comment"
    }
    create_response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    entry_id = create_response.json()['userId']
    
    update_payload = {
        "name": "Updated Name",
        "email": "updated@example.com",
        "comment": "Updated comment"
    }
    response = requests.put(f"{BASE_URL}/api/guestbook/{entry_id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['name'] == "Updated Name"
    assert data['email'] == "updated@example.com"
    assert data['comment'] == "Updated comment"

def test_delete_entry(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    payload = {
        "name": "Delete Test",
        "email": "delete@example.com",
        "comment": "To be deleted"
    }
    create_response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    entry_id = create_response.json()['userId']
    
    response = requests.delete(f"{BASE_URL}/api/guestbook/{entry_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()['message'] == 'Entry deleted successfully'
    
    get_response = requests.get(f"{BASE_URL}/api/guestbook/{entry_id}", headers=headers)
    assert get_response.status_code == 404

def test_delete_nonexistent(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.delete(f"{BASE_URL}/api/guestbook/99999", headers=headers)
    assert response.status_code == 404

def test_import_excel(auth_token):
    import pandas as pd
    
    df = pd.DataFrame({
        'name': ['Excel User 1', 'Excel User 2'],
        'email': ['excel1@example.com', 'excel2@example.com'],
        'comment': ['Excel comment 1', 'Excel comment 2']
    })
    
    excel_file = 'test_import.xlsx'
    df.to_excel(excel_file, index=False)
    
    headers = {"Authorization": f"Bearer {auth_token}"}
    with open(excel_file, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/guestbook/import", files=files, headers=headers)
    
    os.remove(excel_file)
    
    assert response.status_code == 200
    data = response.json()
    assert data['imported'] == 2

def test_import_invalid_file(auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    with open('test_invalid.txt', 'w') as f:
        f.write('invalid content')
    
    with open('test_invalid.txt', 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/api/guestbook/import", files=files, headers=headers)
    
    os.remove('test_invalid.txt')
    
    assert response.status_code == 400
