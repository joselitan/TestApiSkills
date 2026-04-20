"""API tests for user registration and authentication."""

import allure
import pytest
import requests
import uuid

BASE_URL = "http://localhost:8080"


@allure.feature("Authentication")
@allure.story("Registration")
@allure.severity(allure.severity_level.NORMAL)
def test_register_missing_fields():
    response = requests.post(
        f"{BASE_URL}/api/register", json={"password": "Password123!"}
    )
    assert response.status_code == 400


@allure.feature("Authentication")
@allure.story("Registration")
@allure.severity(allure.severity_level.NORMAL)
def test_register_password_mismatch():
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={
            "email": f"user-{uuid.uuid4().hex[:8]}@example.com",
            "password": "Password123!",
            "confirm_password": "Password1234!",
        },
    )
    assert response.status_code == 400


@allure.feature("Authentication")
@allure.story("Registration")
@allure.severity(allure.severity_level.CRITICAL)
def test_register_new_user_success():
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={
            "email": email,
            "username": f"user_{uuid.uuid4().hex[:6]}",
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    assert response.status_code == 201
    assert "Verification email sent" in response.json().get("message", "")


@allure.feature("Authentication")
@allure.story("Login")
@allure.severity(allure.severity_level.CRITICAL)
def test_login_inactive_user_returns_403():
    email = f"inactive-{uuid.uuid4().hex[:8]}@example.com"
    requests.post(
        f"{BASE_URL}/api/register",
        json={
            "email": email,
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )

    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"email": email, "password": "Password123!"},
    )
    assert response.status_code == 403
    assert "Account not active" in response.json().get("message", "")


@allure.feature("Authentication")
@allure.story("Password Reset")
@allure.severity(allure.severity_level.NORMAL)
def test_password_reset_request_returns_200():
    response = requests.post(
        f"{BASE_URL}/api/password-reset-request",
        json={"email": f"user-{uuid.uuid4().hex[:8]}@example.com"},
    )
    assert response.status_code == 200
    assert "Password reset email sent" in response.json().get("message", "")
