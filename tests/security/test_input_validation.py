"""Security Tests - Data Integrity Failures (OWASP A08)"""
import pytest
import requests
import allure
import json
from tests.fixtures.factories import create_guestbook_entry


BASE_URL = "http://localhost:8080"


@allure.feature("Security Testing")
@allure.story("Data Integrity Failures")
@allure.severity(allure.severity_level.NORMAL)
class TestDataIntegrity:
    """Test suite for input validation and data integrity"""

    @pytest.fixture(autouse=True)
    def setup(self, auth_token):
        """Setup for each test"""
        self.headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

    @allure.title("Oversized Payload Attack")
    @allure.description("Test handling of oversized payloads")
    @pytest.mark.security
    def test_oversized_payload(self):
        """Test oversized payload handling"""
        # Test very large strings
        large_string = "A" * 10000  # 10KB string
        very_large_string = "B" * 100000  # 100KB string
        
        oversized_payloads = [
            {"name": large_string, "email": "test@example.com", "comment": "test"},
            {"name": "test", "email": large_string, "comment": "test"},
            {"name": "test", "email": "test@example.com", "comment": large_string},
            {"name": very_large_string, "email": "test@example.com", "comment": "test"},
        ]
        
        for payload in oversized_payloads:
            with allure.step(f"Testing oversized field: {list(payload.keys())[0]}"):
                response = requests.post(f"{BASE_URL}/api/guestbook", 
                                       json=payload, headers=self.headers)
                
                # Should handle large payloads gracefully
                assert response.status_code in [400, 413, 422], \
                       f"Oversized payload should be rejected"

    @allure.title("Invalid Data Types")
    @allure.description("Test handling of invalid data types")
    @pytest.mark.security
    def test_invalid_data_types(self):
        """Test invalid data type handling"""
        invalid_payloads = [
            # Integer instead of string
            {"name": 12345, "email": "test@example.com", "comment": "test"},
            {"name": "test", "email": 12345, "comment": "test"},
            {"name": "test", "email": "test@example.com", "comment": 12345},
            
            # Boolean instead of string
            {"name": True, "email": "test@example.com", "comment": "test"},
            {"name": "test", "email": False, "comment": "test"},
            
            # Array instead of string
            {"name": ["test"], "email": "test@example.com", "comment": "test"},
            {"name": "test", "email": ["test@example.com"], "comment": "test"},
            
            # Object instead of string
            {"name": {"value": "test"}, "email": "test@example.com", "comment": "test"},
            
            # Null values
            {"name": None, "email": "test@example.com", "comment": "test"},
            {"name": "test", "email": None, "comment": "test"},
            {"name": "test", "email": "test@example.com", "comment": None},
        ]
        
        for payload in invalid_payloads:
            with allure.step(f"Testing invalid payload: {payload}"):
                response = requests.post(f"{BASE_URL}/api/guestbook", 
                                       json=payload, headers=self.headers)
                
                # Should reject invalid data types
                assert response.status_code in [400, 422], \
                       f"Invalid data type should be rejected: {payload}"

    @allure.title("Email Validation")
    @allure.description("Test email format validation")
    @pytest.mark.security
    def test_email_validation(self):
        """Test email validation"""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            "test@.com",
            "test@example..com",
            "test@-example.com",
            "test@example-.com",
            "test@example.c",
            "test@example.toolongdomainextension",
            "test space@example.com",
            "test@exam ple.com",
            "test@example.com.",
            ".test@example.com",
            "test.@example.com",
            "test@exam_ple.com",
            "test@[192.168.1.1",
            "test@192.168.1.1]",
        ]
        
        for email in invalid_emails:
            with allure.step(f"Testing invalid email: {email}"):
                payload = {"name": "Test User", "email": email, "comment": "Test comment"}
                response = requests.post(f"{BASE_URL}/api/guestbook", 
                                       json=payload, headers=self.headers)
                
                # Should validate email format
                if response.status_code == 201:
                    allure.attach(f"Invalid email accepted: {email}", 
                                 name="Email Validation Issue", attachment_type=allure.attachment_type.TEXT)

    @allure.title("Special Characters Handling")
    @allure.description("Test handling of special characters")
    @pytest.mark.security
    def test_special_characters(self):
        """Test special character handling"""
        special_char_payloads = [
            # Unicode characters
            {"name": "Test 测试 🚀", "email": "test@example.com", "comment": "Unicode test"},
            {"name": "Test", "email": "测试@example.com", "comment": "Unicode email"},
            
            # Control characters
            {"name": "Test\x00User", "email": "test@example.com", "comment": "Null byte"},
            {"name": "Test\r\nUser", "email": "test@example.com", "comment": "CRLF injection"},
            {"name": "Test\tUser", "email": "test@example.com", "comment": "Tab character"},
            
            # HTML entities
            {"name": "&lt;script&gt;", "email": "test@example.com", "comment": "HTML entities"},
            {"name": "&#60;script&#62;", "email": "test@example.com", "comment": "Numeric entities"},
            
            # URL encoding
            {"name": "%3Cscript%3E", "email": "test@example.com", "comment": "URL encoded"},
            
            # Double encoding
            {"name": "%253Cscript%253E", "email": "test@example.com", "comment": "Double encoded"},
        ]
        
        for payload in special_char_payloads:
            with allure.step(f"Testing special characters: {payload['name'][:20]}..."):
                response = requests.post(f"{BASE_URL}/api/guestbook", 
                                       json=payload, headers=self.headers)
                
                # Should handle special characters safely
                if response.status_code == 201:
                    # Verify data is stored safely
                    entry_id = response.json()["userId"]
                    get_response = requests.get(f"{BASE_URL}/api/guestbook/{entry_id}", 
                                              headers=self.headers)
                    
                    if get_response.status_code == 200:
                        stored_data = get_response.json()
                        # Check for proper encoding/escaping
                        allure.attach(f"Stored data: {stored_data}", 
                                     name="Special Character Storage", attachment_type=allure.attachment_type.TEXT)

    @allure.title("JSON Structure Manipulation")
    @allure.description("Test JSON structure manipulation attacks")
    @pytest.mark.security
    def test_json_structure_manipulation(self):
        """Test JSON structure manipulation"""
        malicious_payloads = [
            # Extra fields (mass assignment)
            {"name": "test", "email": "test@example.com", "comment": "test", "admin": True},
            {"name": "test", "email": "test@example.com", "comment": "test", "role": "admin"},
            {"name": "test", "email": "test@example.com", "comment": "test", "userId": 999},
            
            # Nested objects
            {"name": "test", "email": "test@example.com", "comment": "test", "nested": {"admin": True}},
            
            # Array injection
            {"name": "test", "email": "test@example.com", "comment": "test", "permissions": ["admin", "delete"]},
            
            # Prototype pollution attempts
            {"name": "test", "email": "test@example.com", "comment": "test", "__proto__": {"admin": True}},
            {"name": "test", "email": "test@example.com", "comment": "test", "constructor": {"prototype": {"admin": True}}},
        ]
        
        for payload in malicious_payloads:
            with allure.step(f"Testing JSON manipulation: {list(payload.keys())}"):
                response = requests.post(f"{BASE_URL}/api/guestbook", 
                                       json=payload, headers=self.headers)
                
                # Should ignore extra fields or reject payload
                if response.status_code == 201:
                    # Check if extra fields were processed
                    entry_data = response.json()
                    extra_fields = set(payload.keys()) - {"name", "email", "comment"}
                    
                    for field in extra_fields:
                        if field in entry_data:
                            allure.attach(f"Extra field processed: {field} = {entry_data[field]}", 
                                         name="Mass Assignment Risk", attachment_type=allure.attachment_type.TEXT)

    @allure.title("Content-Type Manipulation")
    @allure.description("Test content-type manipulation attacks")
    @pytest.mark.security
    def test_content_type_manipulation(self):
        """Test content-type manipulation"""
        payload = {"name": "test", "email": "test@example.com", "comment": "test"}
        
        malicious_content_types = [
            "application/x-www-form-urlencoded",
            "text/plain",
            "application/xml",
            "multipart/form-data",
            "text/html",
            "application/javascript",
        ]
        
        for content_type in malicious_content_types:
            with allure.step(f"Testing content-type: {content_type}"):
                headers = self.headers.copy()
                headers["Content-Type"] = content_type
                
                response = requests.post(f"{BASE_URL}/api/guestbook", 
                                       json=payload, headers=headers)
                
                # Should validate content-type
                if content_type != "application/json" and response.status_code == 201:
                    allure.attach(f"Unexpected content-type accepted: {content_type}", 
                                 name="Content-Type Issue", attachment_type=allure.attachment_type.TEXT)

    @allure.title("Encoding Attacks")
    @allure.description("Test various encoding attacks")
    @pytest.mark.security
    def test_encoding_attacks(self):
        """Test encoding-based attacks"""
        # Test different encodings
        encoding_payloads = [
            # Base64 encoded script
            {"name": "PHNjcmlwdD5hbGVydCgnWFNTJyk8L3NjcmlwdD4=", "email": "test@example.com", "comment": "base64"},
            
            # Hex encoded
            {"name": "\\x3cscript\\x3ealert('XSS')\\x3c/script\\x3e", "email": "test@example.com", "comment": "hex"},
            
            # Unicode escape
            {"name": "\\u003cscript\\u003ealert('XSS')\\u003c/script\\u003e", "email": "test@example.com", "comment": "unicode"},
            
            # HTML numeric entities
            {"name": "&#60;script&#62;alert('XSS')&#60;/script&#62;", "email": "test@example.com", "comment": "numeric"},
        ]
        
        for payload in encoding_payloads:
            with allure.step(f"Testing encoding attack: {payload['comment']}"):
                response = requests.post(f"{BASE_URL}/api/guestbook", 
                                       json=payload, headers=self.headers)
                
                if response.status_code == 201:
                    # Check if encoding was decoded
                    entry_id = response.json()["userId"]
                    get_response = requests.get(f"{BASE_URL}/api/guestbook/{entry_id}", 
                                              headers=self.headers)
                    
                    if get_response.status_code == 200:
                        stored_name = get_response.json().get("name", "")
                        if "<script>" in stored_name.lower():
                            allure.attach(f"Encoding bypass detected: {payload['comment']}", 
                                         name="Encoding Bypass", attachment_type=allure.attachment_type.TEXT)

    @allure.title("Integer Overflow/Underflow")
    @allure.description("Test integer overflow and underflow")
    @pytest.mark.security
    def test_integer_overflow(self):
        """Test integer overflow/underflow in numeric fields"""
        # Test with entry IDs (if any numeric processing)
        overflow_values = [
            2147483647,    # Max 32-bit signed int
            2147483648,    # Max 32-bit signed int + 1
            4294967295,    # Max 32-bit unsigned int
            4294967296,    # Max 32-bit unsigned int + 1
            9223372036854775807,   # Max 64-bit signed int
            -2147483648,   # Min 32-bit signed int
            -2147483649,   # Min 32-bit signed int - 1
        ]
        
        for value in overflow_values:
            with allure.step(f"Testing integer overflow: {value}"):
                # Test in URL path
                response = requests.get(f"{BASE_URL}/api/guestbook/{value}", 
                                      headers=self.headers)
                
                # Should handle large integers gracefully
                assert response.status_code in [400, 404], \
                       f"Large integer should be handled safely: {value}"