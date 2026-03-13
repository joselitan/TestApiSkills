"""API Contract Testing - Validate API responses against schemas"""

import allure
import pytest
import requests
from jsonschema import ValidationError, validate

BASE_URL = "http://localhost:8080"

# JSON Schemas
GUESTBOOK_ENTRY_SCHEMA = {
    "type": "object",
    "required": ["userId", "name", "email", "comment"],
    "properties": {
        "userId": {"type": "integer"},
        "name": {"type": "string", "minLength": 1},
        "email": {"type": "string", "format": "email"},
        "comment": {"type": "string"},
    },
}

GUESTBOOK_LIST_SCHEMA = {
    "type": "object",
    "required": ["data", "meta"],
    "properties": {
        "data": {"type": "array", "items": GUESTBOOK_ENTRY_SCHEMA},
        "meta": {
            "type": "object",
            "required": ["total", "page", "limit"],
            "properties": {
                "total": {"type": "integer"},
                "page": {"type": "integer"},
                "limit": {"type": "integer"},
            },
        },
    },
}

LOGIN_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["token"],
    "properties": {"token": {"type": "string", "minLength": 10}},
}


@pytest.fixture(scope="module")
def auth_token():
    response = requests.post(
        f"{BASE_URL}/api/login", json={"username": "admin", "password": "password123"}
    )
    return response.json()["token"]


@allure.feature("API Contract")
@allure.story("Authentication")
@allure.severity(allure.severity_level.CRITICAL)
def test_login_response_schema():
    """Validate login response matches schema"""
    with allure.step("Send login request"):
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "password123"},
        )
    with allure.step("Validate response status"):
        assert response.status_code == 200
    with allure.step("Validate response schema"):
        validate(instance=response.json(), schema=LOGIN_RESPONSE_SCHEMA)


@allure.feature("API Contract")
@allure.story("Guestbook List")
@allure.severity(allure.severity_level.CRITICAL)
def test_guestbook_list_schema(auth_token):
    """Validate guestbook list response matches schema"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    with allure.step("Request guestbook list"):
        response = requests.get(f"{BASE_URL}/api/guestbook", headers=headers)
    with allure.step("Validate response"):
        assert response.status_code == 200
        validate(instance=response.json(), schema=GUESTBOOK_LIST_SCHEMA)


@allure.feature("API Contract")
@allure.story("Create Entry")
@allure.severity(allure.severity_level.CRITICAL)
def test_create_entry_schema(auth_token):
    """Validate created entry matches schema"""
    headers = {"Authorization": f"Bearer {auth_token}"}
    payload = {
        "name": "Contract Test",
        "email": "contract@test.com",
        "comment": "Testing API contract",
    }
    with allure.step("Create new entry"):
        response = requests.post(
            f"{BASE_URL}/api/guestbook", json=payload, headers=headers
        )
    with allure.step("Validate response"):
        assert response.status_code == 201
        validate(instance=response.json(), schema=GUESTBOOK_ENTRY_SCHEMA)


@allure.feature("API Contract")
@allure.story("Single Entry")
@allure.severity(allure.severity_level.NORMAL)
def test_single_entry_schema(auth_token):
    """Validate single entry response matches schema"""
    headers = {"Authorization": f"Bearer {auth_token}"}

    with allure.step("Create test entry"):
        payload = {"name": "Schema Test", "email": "schema@test.com", "comment": "Test"}
        create_resp = requests.post(
            f"{BASE_URL}/api/guestbook", json=payload, headers=headers
        )
        entry_id = create_resp.json()["userId"]

    with allure.step("Get single entry"):
        response = requests.get(f"{BASE_URL}/api/guestbook/{entry_id}", headers=headers)

    with allure.step("Validate response"):
        assert response.status_code == 200
        validate(instance=response.json(), schema=GUESTBOOK_ENTRY_SCHEMA)
