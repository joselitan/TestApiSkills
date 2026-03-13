"""Security Tests - Penetration Testing Scenarios"""

import base64
import json
import time

import allure
import jwt
import pytest
import requests

from tests.fixtures.factories import create_guestbook_entry

BASE_URL = "http://localhost:8080"


@allure.feature("Security Testing")
@allure.story("Penetration Testing")
@allure.severity(allure.severity_level.CRITICAL)
class TestPenetrationScenarios:
    """Test suite for penetration testing scenarios"""

    @allure.title("Advanced Brute Force Attack")
    @allure.description("Simulate advanced brute force attack with various techniques")
    @pytest.mark.security
    def test_advanced_brute_force(self):
        """Test advanced brute force techniques"""
        # Common passwords list
        common_passwords = [
            "password123",  # Current password (should work)
            "admin",
            "password",
            "123456",
            "admin123",
            "root",
            "toor",
            "pass",
            "test",
            "guest",
        ]

        successful_logins = []
        failed_attempts = 0
        rate_limited = False

        with allure.step("Executing brute force attack"):
            for password in common_passwords:
                response = requests.post(
                    f"{BASE_URL}/api/login",
                    json={"username": "admin", "password": password},
                )

                if response.status_code == 200:
                    successful_logins.append(password)
                    allure.attach(
                        f"Successful login with password: {password}",
                        name="Brute Force Success",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                elif response.status_code == 429:
                    rate_limited = True
                    allure.attach(
                        f"Rate limited after {failed_attempts} attempts",
                        name="Rate Limiting",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                    break
                else:
                    failed_attempts += 1

                time.sleep(0.1)  # Small delay

        # Analysis
        if not rate_limited and failed_attempts > 5:
            allure.attach(
                "No rate limiting detected - brute force possible",
                name="Brute Force Vulnerability",
                attachment_type=allure.attachment_type.TEXT,
            )

        if len(successful_logins) > 1:
            allure.attach(
                f"Multiple weak passwords found: {successful_logins}",
                name="Weak Password Issue",
                attachment_type=allure.attachment_type.TEXT,
            )

    @allure.title("JWT Token Manipulation")
    @allure.description("Test JWT token manipulation attacks")
    @pytest.mark.security
    def test_jwt_token_manipulation(self, auth_token):
        """Test JWT token manipulation"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        # First verify token works
        response = requests.get(f"{BASE_URL}/api/guestbook", headers=headers)
        assert response.status_code == 200, "Valid token should work"

        # Decode token to understand structure
        try:
            # JWT tokens have 3 parts: header.payload.signature
            parts = auth_token.split(".")
            if len(parts) == 3:
                header = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))
                payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))

                allure.attach(
                    f"JWT Header: {header}",
                    name="JWT Structure",
                    attachment_type=allure.attachment_type.TEXT,
                )
                allure.attach(
                    f"JWT Payload: {payload}",
                    name="JWT Payload",
                    attachment_type=allure.attachment_type.TEXT,
                )

                # Test algorithm confusion attack
                with allure.step("Testing algorithm confusion"):
                    # Try to change algorithm to 'none'
                    modified_header = header.copy()
                    modified_header["alg"] = "none"

                    new_header = (
                        base64.urlsafe_b64encode(json.dumps(modified_header).encode())
                        .decode()
                        .rstrip("=")
                    )

                    # Create token with no signature
                    none_token = f"{new_header}.{parts[1]}."

                    test_headers = {
                        "Authorization": f"Bearer {none_token}",
                        "Content-Type": "application/json",
                    }
                    response = requests.get(
                        f"{BASE_URL}/api/guestbook", headers=test_headers
                    )

                    if response.status_code == 200:
                        allure.attach(
                            "Algorithm confusion attack successful!",
                            name="Critical JWT Vulnerability",
                            attachment_type=allure.attachment_type.TEXT,
                        )

                # Test payload manipulation
                with allure.step("Testing payload manipulation"):
                    modified_payload = payload.copy()
                    modified_payload["user"] = "superadmin"

                    new_payload = (
                        base64.urlsafe_b64encode(json.dumps(modified_payload).encode())
                        .decode()
                        .rstrip("=")
                    )

                    # Keep original signature (should fail)
                    manipulated_token = f"{parts[0]}.{new_payload}.{parts[2]}"

                    test_headers = {
                        "Authorization": f"Bearer {manipulated_token}",
                        "Content-Type": "application/json",
                    }
                    response = requests.get(
                        f"{BASE_URL}/api/guestbook", headers=test_headers
                    )

                    if response.status_code == 200:
                        allure.attach(
                            "Payload manipulation successful - signature not verified!",
                            name="JWT Signature Bypass",
                            attachment_type=allure.attachment_type.TEXT,
                        )
                    else:
                        allure.attach(
                            "Payload manipulation blocked - good signature verification",
                            name="Good JWT Security",
                            attachment_type=allure.attachment_type.TEXT,
                        )

        except Exception as e:
            allure.attach(
                f"JWT manipulation test failed: {str(e)}",
                name="JWT Test Error",
                attachment_type=allure.attachment_type.TEXT,
            )

    @allure.title("Advanced IDOR Attack")
    @allure.description("Test advanced Insecure Direct Object Reference attacks")
    @pytest.mark.security
    def test_advanced_idor(self, auth_token):
        """Test advanced IDOR attacks"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        # Create multiple test entries
        created_entries = []
        for i in range(3):
            entry_data = create_guestbook_entry()
            response = requests.post(
                f"{BASE_URL}/api/guestbook", json=entry_data, headers=headers
            )
            if response.status_code == 201:
                created_entries.append(response.json()["userId"])

        if created_entries:
            # Test sequential ID enumeration
            with allure.step("Testing ID enumeration"):
                min_id = min(created_entries)
                max_id = max(created_entries)

                accessible_entries = []
                for test_id in range(min_id - 10, max_id + 10):
                    response = requests.get(
                        f"{BASE_URL}/api/guestbook/{test_id}", headers=headers
                    )
                    if response.status_code == 200:
                        accessible_entries.append(test_id)

                if len(accessible_entries) > len(created_entries):
                    allure.attach(
                        f"ID enumeration possible: {len(accessible_entries)} entries accessible",
                        name="IDOR Enumeration",
                        attachment_type=allure.attachment_type.TEXT,
                    )

            # Test IDOR with different HTTP methods
            with allure.step("Testing IDOR with different methods"):
                test_id = created_entries[0]

                # Try to modify entry with PUT
                modified_data = {
                    "name": "Hacker",
                    "email": "hacker@evil.com",
                    "comment": "Pwned!",
                }
                response = requests.put(
                    f"{BASE_URL}/api/guestbook/{test_id}",
                    json=modified_data,
                    headers=headers,
                )

                if response.status_code == 200:
                    # Verify modification
                    get_response = requests.get(
                        f"{BASE_URL}/api/guestbook/{test_id}", headers=headers
                    )
                    if get_response.status_code == 200:
                        entry_data = get_response.json()
                        if entry_data.get("name") == "Hacker":
                            allure.attach(
                                "IDOR modification successful",
                                name="IDOR Write Access",
                                attachment_type=allure.attachment_type.TEXT,
                            )

                # Try to delete entry
                response = requests.delete(
                    f"{BASE_URL}/api/guestbook/{test_id}", headers=headers
                )
                if response.status_code == 200:
                    allure.attach(
                        "IDOR deletion successful",
                        name="IDOR Delete Access",
                        attachment_type=allure.attachment_type.TEXT,
                    )

    @allure.title("Mass Assignment Attack")
    @allure.description("Test mass assignment vulnerabilities")
    @pytest.mark.security
    def test_mass_assignment(self, auth_token):
        """Test mass assignment attacks"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        # Test mass assignment in entry creation
        mass_assignment_payloads = [
            # Try to set admin fields
            {
                "name": "Test User",
                "email": "test@example.com",
                "comment": "Test comment",
                "admin": True,
                "role": "administrator",
                "permissions": ["read", "write", "delete"],
                "userId": 999999,
                "created_at": "2020-01-01 00:00:00",
                "is_verified": True,
                "priority": "high",
            },
            # Try to inject database fields
            {
                "name": "Test User",
                "email": "test@example.com",
                "comment": "Test comment",
                "id": 1,
                "password": "hacked",
                "token": "fake_token",
                "secret_key": "stolen",
            },
            # Try nested object injection
            {
                "name": "Test User",
                "email": "test@example.com",
                "comment": "Test comment",
                "user": {"admin": True, "role": "superuser"},
                "metadata": {"bypass": True, "elevated": True},
            },
        ]

        for payload in mass_assignment_payloads:
            with allure.step(f"Testing mass assignment with {len(payload)} fields"):
                response = requests.post(
                    f"{BASE_URL}/api/guestbook", json=payload, headers=headers
                )

                if response.status_code == 201:
                    entry_data = response.json()

                    # Check if extra fields were processed
                    extra_fields = []
                    expected_fields = {
                        "userId",
                        "name",
                        "email",
                        "comment",
                        "created_at",
                    }

                    for field in entry_data:
                        if field not in expected_fields:
                            extra_fields.append(field)

                    if extra_fields:
                        allure.attach(
                            f"Mass assignment successful: {extra_fields}",
                            name="Mass Assignment Vulnerability",
                            attachment_type=allure.attachment_type.TEXT,
                        )

                    # Check if any dangerous values were set
                    dangerous_values = []
                    for key, value in entry_data.items():
                        if key in ["admin", "role", "permissions"] and value:
                            dangerous_values.append(f"{key}: {value}")

                    if dangerous_values:
                        allure.attach(
                            f"Dangerous mass assignment: {dangerous_values}",
                            name="Critical Mass Assignment",
                            attachment_type=allure.attachment_type.TEXT,
                        )

    @allure.title("File Upload Attack")
    @allure.description("Test malicious file upload attacks")
    @pytest.mark.security
    def test_file_upload_attack(self, auth_token):
        """Test file upload attacks"""
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Test various malicious file types
        malicious_files = [
            # Web shells
            ("shell.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            (
                "shell.jsp",
                b'<% Runtime.getRuntime().exec(request.getParameter("cmd")); %>',
                "text/plain",
            ),
            (
                "shell.aspx",
                b'<%@ Page Language="C#" %><%System.Diagnostics.Process.Start(Request["cmd"]);%>',
                "text/plain",
            ),
            # Executable files
            ("malware.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/octet-stream"),
            ("script.bat", b"@echo off\nformat c: /y", "text/plain"),
            ("script.sh", b"#!/bin/bash\nrm -rf /", "text/plain"),
            # Archive bombs
            ("bomb.zip", b"PK\x03\x04" + b"A" * 1000, "application/zip"),
            # Image with embedded script
            (
                "image.jpg",
                b"\xff\xd8\xff\xe0" + b"<script>alert('XSS')</script>",
                "image/jpeg",
            ),
        ]

        for filename, content, content_type in malicious_files:
            with allure.step(f"Testing malicious file: {filename}"):
                import io

                files = {"file": (filename, io.BytesIO(content), content_type)}

                response = requests.post(
                    f"{BASE_URL}/api/guestbook/import", files=files, headers=headers
                )

                if response.status_code == 200:
                    allure.attach(
                        f"Malicious file upload successful: {filename}",
                        name="File Upload Vulnerability",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                elif response.status_code in [400, 415, 422]:
                    allure.attach(
                        f"Malicious file rejected: {filename}",
                        name="Good File Validation",
                        attachment_type=allure.attachment_type.TEXT,
                    )

    @allure.title("CORS Attack Simulation")
    @allure.description("Test CORS misconfiguration attacks")
    @pytest.mark.security
    def test_cors_attack(self, auth_token):
        """Test CORS attack scenarios"""
        # Simulate malicious website trying to access API
        malicious_origins = [
            "https://evil.com",
            "http://attacker.local",
            "null",
            "file://",
        ]

        for origin in malicious_origins:
            with allure.step(f"Testing CORS with malicious origin: {origin}"):
                # Preflight request
                headers = {
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Authorization",
                }

                response = requests.options(
                    f"{BASE_URL}/api/guestbook", headers=headers
                )

                # Check if CORS allows the malicious origin
                allowed_origin = response.headers.get("Access-Control-Allow-Origin")
                allow_credentials = response.headers.get(
                    "Access-Control-Allow-Credentials"
                )

                if allowed_origin == origin or allowed_origin == "*":
                    if allow_credentials and allow_credentials.lower() == "true":
                        allure.attach(
                            f"Dangerous CORS: {origin} allowed with credentials",
                            name="CORS Vulnerability",
                            attachment_type=allure.attachment_type.TEXT,
                        )
                    else:
                        allure.attach(
                            f"CORS allows {origin} but no credentials",
                            name="CORS Risk",
                            attachment_type=allure.attachment_type.TEXT,
                        )

                # Try actual request with malicious origin
                if allowed_origin:
                    actual_headers = {
                        "Origin": origin,
                        "Authorization": f"Bearer {auth_token}",
                    }

                    actual_response = requests.get(
                        f"{BASE_URL}/api/guestbook", headers=actual_headers
                    )

                    if actual_response.status_code == 200:
                        allure.attach(
                            f"Cross-origin request successful from {origin}",
                            name="CORS Attack Success",
                            attachment_type=allure.attachment_type.TEXT,
                        )

    @allure.title("Session Fixation Attack")
    @allure.description("Test session fixation vulnerabilities")
    @pytest.mark.security
    def test_session_fixation(self):
        """Test session fixation attacks"""
        # Since JWT is stateless, traditional session fixation doesn't apply
        # But we can test token reuse scenarios

        with allure.step("Testing token reuse scenarios"):
            # Get initial token
            response1 = requests.post(
                f"{BASE_URL}/api/login",
                json={"username": "admin", "password": "password123"},
            )

            if response1.status_code == 200:
                token1 = response1.json()["token"]

                # Get another token (simulate new login)
                response2 = requests.post(
                    f"{BASE_URL}/api/login",
                    json={"username": "admin", "password": "password123"},
                )

                if response2.status_code == 200:
                    token2 = response2.json()["token"]

                    # Both tokens should work (JWT is stateless)
                    headers1 = {"Authorization": f"Bearer {token1}"}
                    headers2 = {"Authorization": f"Bearer {token2}"}

                    test1 = requests.get(f"{BASE_URL}/api/guestbook", headers=headers1)
                    test2 = requests.get(f"{BASE_URL}/api/guestbook", headers=headers2)

                    if test1.status_code == 200 and test2.status_code == 200:
                        allure.attach(
                            "Multiple concurrent tokens allowed (JWT stateless behavior)",
                            name="Token Behavior",
                            attachment_type=allure.attachment_type.TEXT,
                        )

                        # Check if tokens are identical (would be bad)
                        if token1 == token2:
                            allure.attach(
                                "Identical tokens generated - potential security issue",
                                name="Token Generation Issue",
                                attachment_type=allure.attachment_type.TEXT,
                            )
