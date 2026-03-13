"""Security Tests - Authentication Failures (OWASP A07)"""

import pytest
import requests
import allure
import time
from tests.fixtures.factories import create_user_credentials

BASE_URL = "http://localhost:8080"


@allure.feature("Security Testing")
@allure.story("Authentication Failures")
@allure.severity(allure.severity_level.NORMAL)
class TestAuthenticationFailures:
    """Test suite for authentication vulnerabilities"""

    @allure.title("Brute Force Protection")
    @allure.description("Test protection against brute force attacks")
    @pytest.mark.security
    def test_brute_force_protection(self):
        """Test brute force protection on login endpoint"""
        failed_attempts = 0
        max_attempts = 10

        with allure.step("Attempting multiple failed logins"):
            for i in range(max_attempts):
                response = requests.post(
                    f"{BASE_URL}/api/login",
                    json={"username": "admin", "password": f"wrong_password_{i}"},
                )

                if response.status_code == 401:
                    failed_attempts += 1
                elif response.status_code == 429:  # Rate limited
                    allure.attach(
                        f"Rate limiting triggered after {failed_attempts} attempts",
                        name="Rate Limiting",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                    break

                time.sleep(0.1)  # Small delay between attempts

        # Should implement some form of rate limiting or account lockout
        # This test documents current behavior - ideally should be rate limited
        allure.attach(
            f"Total failed attempts before rate limiting: {failed_attempts}",
            name="Brute Force Results",
            attachment_type=allure.attachment_type.TEXT,
        )

    @allure.title("Weak Password Acceptance")
    @allure.description("Test if system accepts weak passwords")
    @pytest.mark.security
    def test_weak_password_acceptance(self):
        """Test weak password patterns"""
        weak_passwords = [
            "123456",
            "password",
            "admin",
            "qwerty",
            "abc123",
            "password123",
            "admin123",
            "12345678",
            "1234567890",
            "password1",
        ]

        # Note: This test assumes we can create users, but current API only has fixed admin user
        # Testing with login to see if weak passwords are rejected
        for weak_password in weak_passwords:
            with allure.step(f"Testing weak password: {weak_password}"):
                response = requests.post(
                    f"{BASE_URL}/api/login",
                    json={"username": "admin", "password": weak_password},
                )

                # Document if weak password works (current admin password is password123)
                if response.status_code == 200 and weak_password == "password123":
                    allure.attach(
                        "System uses weak default password",
                        name="Weak Password Found",
                        attachment_type=allure.attachment_type.TEXT,
                    )

    @allure.title("JWT Token Security")
    @allure.description("Test JWT token security and validation")
    @pytest.mark.security
    def test_jwt_token_security(self, auth_token):
        """Test JWT token security"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        # Test with valid token first
        with allure.step("Testing valid token"):
            response = requests.get(f"{BASE_URL}/api/guestbook", headers=headers)
            assert response.status_code == 200, "Valid token should work"

        # Test with malformed tokens
        malformed_tokens = [
            "invalid_token",
            "Bearer invalid_token",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
            auth_token[:-5] + "XXXXX",  # Modified signature
            auth_token.replace(".", "X"),  # Corrupted token
            "",  # Empty token
        ]

        for token in malformed_tokens:
            with allure.step(f"Testing malformed token: {token[:20]}..."):
                test_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                }
                response = requests.get(
                    f"{BASE_URL}/api/guestbook", headers=test_headers
                )
                assert (
                    response.status_code == 401
                ), f"Malformed token should be rejected: {token[:20]}..."

    @allure.title("Token Expiration")
    @allure.description("Test JWT token expiration handling")
    @pytest.mark.security
    def test_token_expiration(self):
        """Test token expiration (simulated)"""
        # Get a fresh token
        login_response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": "admin", "password": "password123"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]

        # Test immediate use (should work)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = requests.get(f"{BASE_URL}/api/guestbook", headers=headers)
        assert response.status_code == 200, "Fresh token should work"

        # Note: Real expiration test would require waiting 24 hours or manipulating system time
        # This documents the current token lifetime (24 hours as per app.py)
        allure.attach(
            "Token lifetime: 24 hours",
            name="Token Configuration",
            attachment_type=allure.attachment_type.TEXT,
        )

    @allure.title("Session Management")
    @allure.description("Test session management security")
    @pytest.mark.security
    def test_session_management(self, auth_token):
        """Test session management"""
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }

        # Test concurrent sessions (multiple tokens)
        with allure.step("Testing concurrent sessions"):
            # Get another token
            login_response = requests.post(
                f"{BASE_URL}/api/login",
                json={"username": "admin", "password": "password123"},
            )
            assert login_response.status_code == 200
            token2 = login_response.json()["token"]

            headers2 = {
                "Authorization": f"Bearer {token2}",
                "Content-Type": "application/json",
            }

            # Both tokens should work (stateless JWT)
            response1 = requests.get(f"{BASE_URL}/api/guestbook", headers=headers)
            response2 = requests.get(f"{BASE_URL}/api/guestbook", headers=headers2)

            assert response1.status_code == 200, "First token should work"
            assert response2.status_code == 200, "Second token should work"

            # Note: JWT is stateless, so multiple tokens will work until expiration
            allure.attach(
                "Multiple concurrent sessions allowed (JWT stateless)",
                name="Session Behavior",
                attachment_type=allure.attachment_type.TEXT,
            )

    @allure.title("Password Reset Security")
    @allure.description("Test password reset functionality (if available)")
    @pytest.mark.security
    def test_password_reset_security(self):
        """Test password reset security"""
        # Current API doesn't have password reset, but test for endpoint existence
        reset_endpoints = [
            "/api/password-reset",
            "/api/forgot-password",
            "/api/reset-password",
            "/password-reset",
            "/forgot-password",
        ]

        for endpoint in reset_endpoints:
            with allure.step(f"Testing password reset endpoint: {endpoint}"):
                response = requests.post(
                    f"{BASE_URL}{endpoint}", json={"email": "admin@example.com"}
                )

                # Should return 404 if not implemented
                if response.status_code != 404:
                    allure.attach(
                        f"Password reset endpoint found: {endpoint}",
                        name="Password Reset Discovery",
                        attachment_type=allure.attachment_type.TEXT,
                    )

    @allure.title("Account Enumeration")
    @allure.description("Test for username enumeration vulnerabilities")
    @pytest.mark.security
    def test_account_enumeration(self):
        """Test account enumeration through login responses"""
        test_users = [
            "admin",  # Valid user
            "nonexistent",  # Invalid user
            "user",
            "test",
            "administrator",
        ]

        response_times = {}
        response_messages = {}

        for username in test_users:
            with allure.step(f"Testing username: {username}"):
                start_time = time.time()
                response = requests.post(
                    f"{BASE_URL}/api/login",
                    json={"username": username, "password": "wrong_password"},
                )
                end_time = time.time()

                response_times[username] = end_time - start_time
                response_messages[username] = response.json().get("message", "")

        # Check for timing differences that could indicate user enumeration
        admin_time = response_times.get("admin", 0)
        nonexistent_time = response_times.get("nonexistent", 0)

        time_difference = abs(admin_time - nonexistent_time)

        allure.attach(
            f"Response times: {response_times}",
            name="Timing Analysis",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            f"Response messages: {response_messages}",
            name="Message Analysis",
            attachment_type=allure.attachment_type.TEXT,
        )

        # Significant timing difference could indicate enumeration vulnerability
        if time_difference > 0.1:  # 100ms difference
            allure.attach(
                f"Potential timing-based enumeration: {time_difference:.3f}s difference",
                name="Enumeration Risk",
                attachment_type=allure.attachment_type.TEXT,
            )

    @allure.title("Multi-Factor Authentication")
    @allure.description("Test MFA implementation (if available)")
    @pytest.mark.security
    def test_mfa_implementation(self):
        """Test multi-factor authentication"""
        # Current API doesn't have MFA, document this gap
        with allure.step("Checking for MFA implementation"):
            # Test if login requires additional factors
            response = requests.post(
                f"{BASE_URL}/api/login",
                json={"username": "admin", "password": "password123"},
            )

            if response.status_code == 200:
                # Login successful without MFA
                allure.attach(
                    "No MFA implementation detected",
                    name="MFA Status",
                    attachment_type=allure.attachment_type.TEXT,
                )
            elif "mfa" in response.json().get("message", "").lower():
                allure.attach(
                    "MFA implementation detected",
                    name="MFA Status",
                    attachment_type=allure.attachment_type.TEXT,
                )
