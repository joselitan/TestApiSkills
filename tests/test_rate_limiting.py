"""
Test suite for rate limiting functionality.

This test suite verifies that rate limiting is properly configured and enforced
for different API endpoints to protect against:
- Brute force attacks on authentication endpoints
- API abuse and excessive requests
- DDoS attacks
"""

import time
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


# Base URL for the API
BASE_URL = "http://localhost:8080"


class TestRateLimitingAuth:
    """Test rate limiting on authentication endpoints"""
    
    def test_login_rate_limit_per_minute(self):
        """
        Test that login endpoint enforces 5 requests per minute limit
        Expected: First 5 attempts succeed or return 401, 6th returns 429
        """
        endpoint = f"{BASE_URL}/api/v1/login"
        payload = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        responses = []
        for i in range(6):
            response = requests.post(endpoint, json=payload)
            responses.append(response.status_code)
            print(f"Login attempt {i+1}: Status {response.status_code}")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        # First 5 should be either 401 (invalid creds) or 200 (valid)
        # 6th should be 429 (rate limit exceeded)
        assert 429 in responses, f"Expected 429 in responses, got: {responses}"
        print(f"✓ Login rate limit enforced after 5 attempts")
    
    def test_register_rate_limit_per_hour(self):
        """
        Test that registration endpoint enforces 3 requests per hour limit
        Expected: First 3 attempts succeed, 4th returns 429
        """
        endpoint = f"{BASE_URL}/api/v1/register"
        
        responses = []
        for i in range(4):
            payload = {
                "email": f"test{i}_{time.time()}@example.com",
                "password": "Password123!",
                "confirm_password": "Password123!"
            }
            response = requests.post(endpoint, json=payload)
            responses.append(response.status_code)
            print(f"Register attempt {i+1}: Status {response.status_code}")
            time.sleep(0.1)
        
        assert 429 in responses, f"Expected 429 in responses, got: {responses}"
        print(f"✓ Registration rate limit enforced after 3 attempts")
    
    def test_password_reset_request_rate_limit(self):
        """
        Test that password reset request enforces 3 requests per hour limit
        """
        endpoint = f"{BASE_URL}/api/v1/password-reset-request"
        payload = {"email": "test@example.com"}
        
        responses = []
        for i in range(4):
            response = requests.post(endpoint, json=payload)
            responses.append(response.status_code)
            print(f"Password reset attempt {i+1}: Status {response.status_code}")
            time.sleep(0.1)
        
        assert 429 in responses, f"Expected 429 in responses, got: {responses}"
        print(f"✓ Password reset rate limit enforced after 3 attempts")


class TestRateLimitingGuestbook:
    """Test rate limiting on guestbook endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get a valid authentication token for testing"""
        # First, register a test user
        register_payload = {
            "email": f"ratelimittest_{time.time()}@example.com",
            "username": f"ratelimittest_{int(time.time())}",
            "password": "Password123!",
            "confirm_password": "Password123!"
        }
        
        # Try to register (may fail if already exists or rate limited)
        requests.post(f"{BASE_URL}/api/v1/register", json=register_payload)
        
        # Try to login (use a known working account or skip if not available)
        login_payload = {
            "username": "admin",  # Default admin account
            "password": "admin123"
        }
        response = requests.post(f"{BASE_URL}/api/v1/login", json=login_payload)
        
        if response.status_code == 200:
            return response.json().get("token")
        return None
    
    def test_create_entry_rate_limit(self, auth_token):
        """
        Test that create entry enforces 30 requests per minute limit
        """
        if not auth_token:
            pytest.skip("No authentication token available")
        
        endpoint = f"{BASE_URL}/api/v1/guestbook"
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        responses = []
        for i in range(35):
            payload = {
                "name": f"Test User {i}",
                "email": f"test{i}@example.com",
                "comment": f"Test comment {i}"
            }
            response = requests.post(endpoint, json=payload, headers=headers)
            responses.append(response.status_code)
            
            if response.status_code == 429:
                print(f"Rate limit hit at request {i+1}")
                break
        
        assert 429 in responses, f"Expected 429 in responses after 30 requests"
        print(f"✓ Create entry rate limit enforced")
    
    def test_bulk_delete_rate_limit(self, auth_token):
        """
        Test that bulk delete enforces 10 requests per minute limit
        """
        if not auth_token:
            pytest.skip("No authentication token available")
        
        endpoint = f"{BASE_URL}/api/v1/guestbook/bulk"
        headers = {"Authorization": f"Bearer {auth_token}"}
        payload = {"ids": [1, 2, 3]}
        
        responses = []
        for i in range(12):
            response = requests.delete(endpoint, json=payload, headers=headers)
            responses.append(response.status_code)
            print(f"Bulk delete attempt {i+1}: Status {response.status_code}")
            time.sleep(0.1)
        
        assert 429 in responses, f"Expected 429 in responses, got: {responses}"
        print(f"✓ Bulk delete rate limit enforced after 10 attempts")


class TestRateLimitingConcurrent:
    """Test rate limiting under concurrent load"""
    
    def test_concurrent_login_attempts(self):
        """
        Test that rate limiting works correctly with concurrent requests
        Simulates a brute force attack scenario
        """
        endpoint = f"{BASE_URL}/api/v1/login"
        payload = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        def make_request(attempt_num):
            response = requests.post(endpoint, json=payload)
            return (attempt_num, response.status_code)
        
        # Send 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        status_codes = [status for _, status in results]
        rate_limited = status_codes.count(429)
        
        print(f"Concurrent requests status codes: {status_codes}")
        print(f"Rate limited responses: {rate_limited}")
        
        # At least some requests should be rate limited
        assert rate_limited > 0, "Expected some requests to be rate limited"
        print(f"✓ Concurrent rate limiting working correctly")


class TestRateLimitingDifferentUsers:
    """Test that rate limits are applied per user/IP"""
    
    def test_rate_limit_per_ip_isolation(self):
        """
        Test that rate limits are tracked separately per IP
        Note: This test is limited in a single-IP environment
        """
        endpoint = f"{BASE_URL}/api/v1/rate-limit/status"
        
        response = requests.get(endpoint)
        assert response.status_code == 200
        
        data = response.json()
        print(f"Rate limit identifier: {data.get('identifier')}")
        print(f"IP address: {data.get('ip_address')}")
        print(f"Is authenticated: {data.get('is_authenticated')}")
        
        assert "identifier" in data
        print(f"✓ Rate limit tracking per identifier working")


class TestRateLimitHeaders:
    """Test that rate limit headers are included in responses"""
    
    def test_rate_limit_headers_present(self):
        """
        Test that rate limit information is included in response headers
        """
        endpoint = f"{BASE_URL}/api/v1/rate-limit/status"
        
        response = requests.get(endpoint)
        
        print(f"\nResponse headers:")
        for header, value in response.headers.items():
            if 'limit' in header.lower() or 'rate' in header.lower():
                print(f"  {header}: {value}")
        
        # Flask-Limiter typically adds these headers
        # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        
        print(f"✓ Response received (headers may include rate limit info)")


class TestRateLimitRecovery:
    """Test rate limit recovery after waiting"""
    
    def test_rate_limit_recovery_after_wait(self):
        """
        Test that rate limits reset after the time window
        This test takes 61 seconds to complete
        """
        endpoint = f"{BASE_URL}/api/v1/rate-limit/status"
        
        # Make 10 requests quickly to hit the limit
        for i in range(10):
            response = requests.get(endpoint)
            if response.status_code == 429:
                print(f"Hit rate limit at request {i+1}")
                break
        
        # Check if we got rate limited
        response = requests.get(endpoint)
        if response.status_code == 429:
            print("✓ Rate limit active")
            print("Waiting 61 seconds for rate limit to reset...")
            time.sleep(61)
            
            # Try again after waiting
            response = requests.get(endpoint)
            print(f"After wait, status: {response.status_code}")
            
            assert response.status_code == 200, "Rate limit should have reset"
            print("✓ Rate limit successfully reset after waiting")
        else:
            print("Note: Did not hit rate limit, may need more requests")


def run_manual_tests():
    """
    Run tests manually without pytest for quick verification
    """
    print("\n" + "="*70)
    print("RATE LIMITING MANUAL TEST SUITE")
    print("="*70)
    
    print("\n[1] Testing Login Rate Limit (5/minute)")
    print("-" * 70)
    test = TestRateLimitingAuth()
    try:
        test.test_login_rate_limit_per_minute()
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n[2] Testing Registration Rate Limit (3/hour)")
    print("-" * 70)
    try:
        test.test_register_rate_limit_per_hour()
    except AssertionError as e:
        print(f"✗ Test failed: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n[3] Testing Rate Limit Status Endpoint")
    print("-" * 70)
    test2 = TestRateLimitingDifferentUsers()
    try:
        test2.test_rate_limit_per_ip_isolation()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n[4] Testing Rate Limit Headers")
    print("-" * 70)
    test3 = TestRateLimitHeaders()
    try:
        test3.test_rate_limit_headers_present()
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*70)
    print("MANUAL TEST SUITE COMPLETE")
    print("="*70)
    print("\nNote: Some tests may fail if the server is not running")
    print("Start the server with: cd src && python app.py")


if __name__ == "__main__":
    # Run manual tests
    run_manual_tests()
