"""Negative Testing - Test error handling and security"""
import requests
import pytest
import allure

BASE_URL = "http://localhost:8080"

@pytest.fixture(scope="module")
def auth_token():
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "admin",
        "password": "password123"
    })
    return response.json()['token']

# Authentication Tests
@allure.feature('Security')
@allure.story('Authentication')
@allure.severity(allure.severity_level.CRITICAL)
def test_login_missing_username():
    """Test login with missing username"""
    response = requests.post(f"{BASE_URL}/api/login", json={"password": "password123"})
    assert response.status_code == 400

@allure.feature('Security')
@allure.story('Authentication')
@allure.severity(allure.severity_level.CRITICAL)
def test_login_missing_password():
    """Test login with missing password"""
    response = requests.post(f"{BASE_URL}/api/login", json={"username": "admin"})
    assert response.status_code == 400

@allure.feature('Security')
@allure.story('Authentication')
@allure.severity(allure.severity_level.CRITICAL)
def test_login_wrong_credentials():
    """Test login with wrong credentials"""
    response = requests.post(f"{BASE_URL}/api/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401

@allure.feature('Security')
@allure.story('Authorization')
@allure.severity(allure.severity_level.CRITICAL)
def test_access_without_token():
    """Test accessing protected endpoint without token"""
    response = requests.get(f"{BASE_URL}/api/guestbook")
    assert response.status_code == 401

@allure.feature('Security')
@allure.story('Authorization')
@allure.severity(allure.severity_level.CRITICAL)
def test_access_with_invalid_token():
    """Test accessing with invalid token"""
    headers = {"Authorization": "Bearer invalid_token_12345"}
    response = requests.get(f"{BASE_URL}/api/guestbook", headers=headers)
    assert response.status_code == 401

# Input Validation Tests
@allure.feature('Input Validation')
@allure.story('Required Fields')
@allure.severity(allure.severity_level.NORMAL)
def test_create_entry_missing_name(auth_token):
    """Test creating entry without name"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {"email": "test@test.com", "comment": "Test"}
    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    assert response.status_code == 400

@allure.feature('Input Validation')
@allure.story('Required Fields')
@allure.severity(allure.severity_level.NORMAL)
def test_create_entry_missing_email(auth_token):
    """Test creating entry without email"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {"name": "Test", "comment": "Test"}
    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    assert response.status_code == 400

@allure.feature('Input Validation')
@allure.story('Email Format')
@allure.severity(allure.severity_level.NORMAL)
def test_create_entry_invalid_email(auth_token):
    """Test creating entry with invalid email format"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {"name": "Test", "email": "not-an-email", "comment": "Test"}
    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    assert response.status_code == 400

@allure.feature('Input Validation')
@allure.story('Empty Values')
@allure.severity(allure.severity_level.NORMAL)
def test_create_entry_empty_strings(auth_token):
    """Test creating entry with empty strings"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {"name": "", "email": "", "comment": ""}
    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    assert response.status_code == 400

# SQL Injection Tests
@allure.feature('Security')
@allure.story('SQL Injection')
@allure.severity(allure.severity_level.CRITICAL)
def test_sql_injection_in_name(auth_token):
    """Test SQL injection attempt in name field"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "name": "'; DROP TABLE guestbook; --",
        "email": "test@test.com",
        "comment": "SQL injection test"
    }
    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    assert response.status_code in [201, 400]

@allure.feature('Security')
@allure.story('SQL Injection')
@allure.severity(allure.severity_level.CRITICAL)
def test_sql_injection_in_search(auth_token):
    """Test SQL injection in search parameter"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{BASE_URL}/api/guestbook?search=' OR '1'='1", headers=headers)
    assert response.status_code == 400, "Should reject SQL injection in search"

# XSS Tests
@allure.feature('Security')
@allure.story('XSS Protection')
@allure.severity(allure.severity_level.CRITICAL)
def test_xss_in_comment(auth_token):
    """Test XSS attempt in comment field"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "name": "XSS Test",
        "email": "xss@test.com",
        "comment": "<script>alert('XSS')</script>"
    }
    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    assert response.status_code in [201, 400]

# Resource Tests
@allure.feature('Error Handling')
@allure.story('404 Errors')
@allure.severity(allure.severity_level.NORMAL)
def test_get_nonexistent_entry(auth_token):
    """Test getting non-existent entry"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{BASE_URL}/api/guestbook/999999", headers=headers)
    assert response.status_code == 404

@allure.feature('Error Handling')
@allure.story('404 Errors')
@allure.severity(allure.severity_level.NORMAL)
def test_update_nonexistent_entry(auth_token):
    """Test updating non-existent entry"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {"name": "Test", "email": "test@test.com", "comment": "Test"}
    response = requests.put(f"{BASE_URL}/api/guestbook/999999", json=payload, headers=headers)
    assert response.status_code == 404

@allure.feature('Error Handling')
@allure.story('404 Errors')
@allure.severity(allure.severity_level.NORMAL)
def test_delete_nonexistent_entry(auth_token):
    """Test deleting non-existent entry"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.delete(f"{BASE_URL}/api/guestbook/999999", headers=headers)
    assert response.status_code == 404

# Type Tests
@allure.feature('Input Validation')
@allure.story('Data Types')
@allure.severity(allure.severity_level.NORMAL)
def test_create_entry_wrong_types(auth_token):
    """Test creating entry with wrong data types"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "name": 12345,
        "email": True,
        "comment": ["array"]
    }
    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    assert response.status_code == 400

# Oversized Payload Tests
@allure.feature('Input Validation')
@allure.story('Payload Size')
@allure.severity(allure.severity_level.MINOR)
def test_oversized_comment(auth_token):
    """Test creating entry with very large comment"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "name": "Test",
        "email": "test@test.com",
        "comment": "A" * 10000
    }
    response = requests.post(f"{BASE_URL}/api/guestbook", json=payload, headers=headers)
    assert response.status_code in [201, 400, 413]
