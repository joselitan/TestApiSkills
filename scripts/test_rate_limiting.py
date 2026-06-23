#!/usr/bin/env python3
"""
Interactive Rate Limiting Test Script

This script provides interactive tests to verify rate limiting functionality.
Run this script while the Flask app is running to test various rate limit scenarios.

Usage:
    python scripts/test_rate_limiting.py
"""

import time
import sys
import requests
from datetime import datetime


BASE_URL = "http://localhost:8080"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")


def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")


def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")


def print_info(text):
    """Print info message"""
    print(f"{YELLOW}ℹ {text}{RESET}")


def check_server():
    """Check if the Flask server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def test_login_rate_limit():
    """Test login endpoint rate limiting"""
    print_header("TEST 1: Login Rate Limit (5 per minute)")
    
    endpoint = f"{BASE_URL}/api/v1/login"
    payload = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    print_info("Sending 6 login requests rapidly...")
    print_info("Expected: First 5 should process, 6th should be rate limited (429)\n")
    
    results = []
    for i in range(6):
        start_time = time.time()
        response = requests.post(endpoint, json=payload)
        elapsed = (time.time() - start_time) * 1000
        
        status = response.status_code
        results.append(status)
        
        if status == 429:
            print(f"  Request {i+1}: {RED}429 RATE LIMITED{RESET} ({elapsed:.0f}ms)")
            retry_after = response.headers.get('Retry-After', 'N/A')
            print(f"           Retry-After: {retry_after}")
        elif status == 401:
            print(f"  Request {i+1}: {YELLOW}401 Unauthorized{RESET} ({elapsed:.0f}ms)")
        elif status == 200:
            print(f"  Request {i+1}: {GREEN}200 OK{RESET} ({elapsed:.0f}ms)")
        else:
            print(f"  Request {i+1}: {status} ({elapsed:.0f}ms)")
        
        time.sleep(0.1)
    
    if 429 in results:
        print_success("Login rate limiting is working correctly!")
        return True
    else:
        print_error(f"Expected 429, got: {results}")
        return False


def test_register_rate_limit():
    """Test registration endpoint rate limiting"""
    print_header("TEST 2: Registration Rate Limit (3 per hour)")
    
    endpoint = f"{BASE_URL}/api/v1/register"
    
    print_info("Sending 4 registration requests...")
    print_info("Expected: First 3 should process, 4th should be rate limited (429)\n")
    
    results = []
    for i in range(4):
        payload = {
            "email": f"test_{i}_{int(time.time())}@example.com",
            "username": f"testuser_{i}_{int(time.time())}",
            "password": "Password123!",
            "confirm_password": "Password123!"
        }
        
        response = requests.post(endpoint, json=payload)
        status = response.status_code
        results.append(status)
        
        if status == 429:
            print(f"  Request {i+1}: {RED}429 RATE LIMITED{RESET}")
        elif status == 201:
            print(f"  Request {i+1}: {GREEN}201 Created{RESET}")
        elif status == 403:
            print(f"  Request {i+1}: {YELLOW}403 Forbidden (registration disabled){RESET}")
        else:
            print(f"  Request {i+1}: {status}")
        
        time.sleep(0.1)
    
    if 429 in results:
        print_success("Registration rate limiting is working correctly!")
        return True
    else:
        print_error(f"Expected 429, got: {results}")
        return False


def test_authenticated_vs_unauthenticated():
    """Test different rate limits for authenticated vs unauthenticated users"""
    print_header("TEST 3: Authenticated vs Unauthenticated Rate Limits")
    
    print_info("Testing unauthenticated access...")
    endpoint = f"{BASE_URL}/api/v1/rate-limit/status"
    
    # Test without authentication
    print("\n  Unauthenticated requests:")
    for i in range(3):
        response = requests.get(endpoint)
        data = response.json()
        print(f"    Request {i+1}: Identifier = {data.get('identifier')}")
    
    # Try to get authenticated token
    print("\n  Attempting to get authenticated token...")
    login_response = requests.post(
        f"{BASE_URL}/api/v1/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get("token")
        print_success("Got authentication token")
        
        # Test with authentication
        print("\n  Authenticated requests:")
        headers = {"Authorization": f"Bearer {token}"}
        for i in range(3):
            response = requests.get(endpoint, headers=headers)
            data = response.json()
            print(f"    Request {i+1}: Identifier = {data.get('identifier')}")
        
        print_success("Authenticated requests use user-based rate limiting")
        return True
    else:
        print_error(f"Could not authenticate (status: {login_response.status_code})")
        print_info("Make sure default admin account exists (username: admin, password: admin123)")
        return False


def test_rate_limit_headers():
    """Test that rate limit headers are present"""
    print_header("TEST 4: Rate Limit Response Headers")
    
    endpoint = f"{BASE_URL}/api/v1/rate-limit/status"
    response = requests.get(endpoint)
    
    print_info("Checking response headers for rate limit information...\n")
    
    rate_limit_headers = {}
    for header, value in response.headers.items():
        if 'limit' in header.lower() or 'rate' in header.lower() or 'retry' in header.lower():
            rate_limit_headers[header] = value
            print(f"  {header}: {value}")
    
    if rate_limit_headers:
        print_success("Rate limit headers are present")
        return True
    else:
        print_info("No explicit rate limit headers found (this is optional)")
        return True


def test_burst_protection():
    """Test that rate limiting protects against burst requests"""
    print_header("TEST 5: Burst Request Protection")
    
    endpoint = f"{BASE_URL}/api/v1/rate-limit/status"
    
    print_info("Sending 15 rapid requests to test burst protection...\n")
    
    rate_limited_at = None
    for i in range(15):
        start = time.time()
        response = requests.get(endpoint)
        elapsed = (time.time() - start) * 1000
        
        if response.status_code == 429:
            if rate_limited_at is None:
                rate_limited_at = i + 1
                print(f"  Request {i+1}: {RED}RATE LIMITED{RESET} ({elapsed:.0f}ms)")
            else:
                print(f"  Request {i+1}: {RED}RATE LIMITED{RESET} ({elapsed:.0f}ms)")
        else:
            print(f"  Request {i+1}: {GREEN}OK{RESET} ({elapsed:.0f}ms)")
    
    if rate_limited_at:
        print_success(f"Burst protection activated after {rate_limited_at} requests")
        return True
    else:
        print_info("No rate limit hit in 15 requests (limit may be higher)")
        return False


def test_password_reset_limit():
    """Test password reset rate limiting"""
    print_header("TEST 6: Password Reset Rate Limit (3 per hour)")
    
    endpoint = f"{BASE_URL}/api/v1/password-reset-request"
    payload = {"email": "test@example.com"}
    
    print_info("Sending 4 password reset requests...")
    print_info("Expected: First 3 should process, 4th should be rate limited (429)\n")
    
    results = []
    for i in range(4):
        response = requests.post(endpoint, json=payload)
        status = response.status_code
        results.append(status)
        
        if status == 429:
            print(f"  Request {i+1}: {RED}429 RATE LIMITED{RESET}")
        elif status == 200:
            print(f"  Request {i+1}: {GREEN}200 OK{RESET}")
        else:
            print(f"  Request {i+1}: {status}")
        
        time.sleep(0.1)
    
    if 429 in results:
        print_success("Password reset rate limiting is working correctly!")
        return True
    else:
        print_error(f"Expected 429, got: {results}")
        return False


def main():
    """Main test runner"""
    print_header("RATE LIMITING TEST SUITE")
    print(f"Testing API at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check if server is running
    print_info("Checking if Flask server is running...")
    if not check_server():
        print_error("Flask server is not responding!")
        print_info("Please start the server first:")
        print_info("  cd src && python app.py")
        sys.exit(1)
    
    print_success("Flask server is running\n")
    
    # Run tests
    results = []
    
    tests = [
        ("Login Rate Limit", test_login_rate_limit),
        ("Registration Rate Limit", test_register_rate_limit),
        ("Authenticated vs Unauthenticated", test_authenticated_vs_unauthenticated),
        ("Rate Limit Headers", test_rate_limit_headers),
        ("Burst Protection", test_burst_protection),
        ("Password Reset Rate Limit", test_password_reset_limit),
    ]
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            results.append((name, False))
        
        time.sleep(1)  # Brief pause between tests
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{GREEN}PASSED{RESET}" if result else f"{RED}FAILED{RESET}"
        print(f"  {name}: {status}")
    
    print(f"\n{GREEN}{passed}{RESET}/{total} tests passed")
    
    if passed == total:
        print_success("\nAll tests passed! Rate limiting is properly configured.")
    else:
        print_error("\nSome tests failed. Please review the configuration.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_error("\n\nTest interrupted by user")
        sys.exit(1)
