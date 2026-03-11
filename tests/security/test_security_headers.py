"""Security Tests - Security Headers & Best Practices"""
import pytest
import requests
import allure


BASE_URL = "http://localhost:8080"


@allure.feature("Security Testing")
@allure.story("Security Headers")
@allure.severity(allure.severity_level.NORMAL)
class TestSecurityHeaders:
    """Test suite for security headers and best practices"""

    @allure.title("Security Headers Presence")
    @allure.description("Test presence of essential security headers")
    @pytest.mark.security
    def test_security_headers_presence(self):
        """Test essential security headers"""
        response = requests.get(f"{BASE_URL}/")
        
        # Essential security headers
        expected_headers = {
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "X-Content-Type-Options": ["nosniff"],
            "X-XSS-Protection": ["1; mode=block", "0"],  # 0 is also acceptable (modern approach)
            "Strict-Transport-Security": None,  # Should contain max-age
            "Content-Security-Policy": None,
            "Referrer-Policy": ["strict-origin-when-cross-origin", "strict-origin", "no-referrer"],
        }
        
        missing_headers = []
        weak_headers = []
        
        for header, expected_values in expected_headers.items():
            header_value = response.headers.get(header)
            
            with allure.step(f"Checking {header}"):
                if header_value is None:
                    missing_headers.append(header)
                    allure.attach(f"Missing header: {header}", 
                                 name="Missing Security Header", attachment_type=allure.attachment_type.TEXT)
                else:
                    if expected_values and header_value not in expected_values:
                        if header == "Strict-Transport-Security" and "max-age=" not in header_value:
                            weak_headers.append(f"{header}: {header_value}")
                        elif header != "Strict-Transport-Security":
                            weak_headers.append(f"{header}: {header_value}")
                    
                    allure.attach(f"{header}: {header_value}", 
                                 name="Security Header Found", attachment_type=allure.attachment_type.TEXT)
        
        # Document findings
        if missing_headers:
            allure.attach(f"Missing headers: {missing_headers}", 
                         name="Security Headers Missing", attachment_type=allure.attachment_type.TEXT)
        
        if weak_headers:
            allure.attach(f"Weak headers: {weak_headers}", 
                         name="Weak Security Headers", attachment_type=allure.attachment_type.TEXT)

    @allure.title("Content Security Policy")
    @allure.description("Test Content Security Policy configuration")
    @pytest.mark.security
    def test_content_security_policy(self):
        """Test CSP configuration"""
        response = requests.get(f"{BASE_URL}/")
        csp_header = response.headers.get("Content-Security-Policy")
        
        if csp_header:
            with allure.step("Analyzing CSP directives"):
                # Check for dangerous CSP configurations
                dangerous_patterns = [
                    "'unsafe-inline'",
                    "'unsafe-eval'",
                    "data:",
                    "*",
                    "http:",
                ]
                
                csp_issues = []
                for pattern in dangerous_patterns:
                    if pattern in csp_header:
                        csp_issues.append(f"Dangerous CSP directive: {pattern}")
                
                if csp_issues:
                    allure.attach(f"CSP issues: {csp_issues}", 
                                 name="CSP Security Issues", attachment_type=allure.attachment_type.TEXT)
                
                allure.attach(f"CSP: {csp_header}", 
                             name="Content Security Policy", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach("No Content Security Policy found", 
                         name="CSP Missing", attachment_type=allure.attachment_type.TEXT)

    @allure.title("HTTPS Enforcement")
    @allure.description("Test HTTPS enforcement and HSTS")
    @pytest.mark.security
    def test_https_enforcement(self):
        """Test HTTPS enforcement"""
        # Test if HTTP redirects to HTTPS (if applicable)
        try:
            http_response = requests.get("http://localhost:8080/", allow_redirects=False)
            
            if http_response.status_code in [301, 302, 307, 308]:
                location = http_response.headers.get("Location", "")
                if location.startswith("https://"):
                    allure.attach("HTTP redirects to HTTPS", 
                                 name="HTTPS Redirect", attachment_type=allure.attachment_type.TEXT)
                else:
                    allure.attach("HTTP redirect but not to HTTPS", 
                                 name="Weak HTTPS Redirect", attachment_type=allure.attachment_type.TEXT)
            else:
                allure.attach("No HTTPS redirect found", 
                             name="No HTTPS Enforcement", attachment_type=allure.attachment_type.TEXT)
        
        except requests.exceptions.RequestException:
            allure.attach("Could not test HTTP endpoint", 
                         name="HTTPS Test Skipped", attachment_type=allure.attachment_type.TEXT)
        
        # Test HSTS header
        response = requests.get(f"{BASE_URL}/")
        hsts_header = response.headers.get("Strict-Transport-Security")
        
        if hsts_header:
            # Check HSTS configuration
            if "max-age=" in hsts_header:
                # Extract max-age value
                import re
                max_age_match = re.search(r'max-age=(\d+)', hsts_header)
                if max_age_match:
                    max_age = int(max_age_match.group(1))
                    if max_age < 31536000:  # Less than 1 year
                        allure.attach(f"HSTS max-age too short: {max_age} seconds", 
                                     name="Weak HSTS", attachment_type=allure.attachment_type.TEXT)
            
            allure.attach(f"HSTS: {hsts_header}", 
                         name="HSTS Configuration", attachment_type=allure.attachment_type.TEXT)

    @allure.title("Clickjacking Protection")
    @allure.description("Test clickjacking protection")
    @pytest.mark.security
    def test_clickjacking_protection(self):
        """Test clickjacking protection"""
        response = requests.get(f"{BASE_URL}/")
        
        # Check X-Frame-Options
        x_frame_options = response.headers.get("X-Frame-Options")
        
        if x_frame_options:
            if x_frame_options.upper() in ["DENY", "SAMEORIGIN"]:
                allure.attach(f"Good X-Frame-Options: {x_frame_options}", 
                             name="Clickjacking Protection", attachment_type=allure.attachment_type.TEXT)
            else:
                allure.attach(f"Weak X-Frame-Options: {x_frame_options}", 
                             name="Weak Clickjacking Protection", attachment_type=allure.attachment_type.TEXT)
        else:
            # Check if CSP has frame-ancestors directive
            csp_header = response.headers.get("Content-Security-Policy", "")
            if "frame-ancestors" in csp_header:
                allure.attach("CSP frame-ancestors found (alternative to X-Frame-Options)", 
                             name="CSP Clickjacking Protection", attachment_type=allure.attachment_type.TEXT)
            else:
                allure.attach("No clickjacking protection found", 
                             name="Missing Clickjacking Protection", attachment_type=allure.attachment_type.TEXT)

    @allure.title("Information Disclosure")
    @allure.description("Test for information disclosure in headers")
    @pytest.mark.security
    def test_information_disclosure(self):
        """Test information disclosure in headers"""
        response = requests.get(f"{BASE_URL}/")
        
        # Headers that might disclose sensitive information
        sensitive_headers = [
            "Server",
            "X-Powered-By",
            "X-AspNet-Version",
            "X-AspNetMvc-Version",
            "X-Generator",
        ]
        
        disclosed_info = []
        
        for header in sensitive_headers:
            value = response.headers.get(header)
            if value:
                disclosed_info.append(f"{header}: {value}")
        
        if disclosed_info:
            allure.attach(f"Information disclosure: {disclosed_info}", 
                         name="Information Disclosure", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach("No sensitive information disclosed in headers", 
                         name="Good Information Hiding", attachment_type=allure.attachment_type.TEXT)

    @allure.title("MIME Type Sniffing Protection")
    @allure.description("Test MIME type sniffing protection")
    @pytest.mark.security
    def test_mime_sniffing_protection(self):
        """Test MIME type sniffing protection"""
        response = requests.get(f"{BASE_URL}/")
        
        x_content_type_options = response.headers.get("X-Content-Type-Options")
        
        if x_content_type_options == "nosniff":
            allure.attach("MIME sniffing protection enabled", 
                         name="MIME Protection", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach("No MIME sniffing protection", 
                         name="Missing MIME Protection", attachment_type=allure.attachment_type.TEXT)

    @allure.title("Referrer Policy")
    @allure.description("Test referrer policy configuration")
    @pytest.mark.security
    def test_referrer_policy(self):
        """Test referrer policy"""
        response = requests.get(f"{BASE_URL}/")
        
        referrer_policy = response.headers.get("Referrer-Policy")
        
        if referrer_policy:
            # Check for secure referrer policies
            secure_policies = [
                "no-referrer",
                "strict-origin",
                "strict-origin-when-cross-origin",
                "same-origin",
            ]
            
            if referrer_policy in secure_policies:
                allure.attach(f"Secure referrer policy: {referrer_policy}", 
                             name="Good Referrer Policy", attachment_type=allure.attachment_type.TEXT)
            else:
                allure.attach(f"Potentially weak referrer policy: {referrer_policy}", 
                             name="Weak Referrer Policy", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach("No referrer policy set", 
                         name="Missing Referrer Policy", attachment_type=allure.attachment_type.TEXT)

    @allure.title("API Security Headers")
    @allure.description("Test security headers on API endpoints")
    @pytest.mark.security
    def test_api_security_headers(self, auth_token):
        """Test security headers on API endpoints"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/guestbook", headers=headers)
        
        # API endpoints should also have security headers
        api_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": ["DENY", "SAMEORIGIN"],
            "Cache-Control": None,  # Should control caching
        }
        
        api_security_issues = []
        
        for header, expected in api_headers.items():
            value = response.headers.get(header)
            
            if value is None:
                api_security_issues.append(f"Missing {header}")
            elif expected and isinstance(expected, list) and value not in expected:
                api_security_issues.append(f"Weak {header}: {value}")
        
        # Check cache control for sensitive data
        cache_control = response.headers.get("Cache-Control", "")
        if "no-store" not in cache_control and "private" not in cache_control:
            api_security_issues.append("API response may be cached")
        
        if api_security_issues:
            allure.attach(f"API security issues: {api_security_issues}", 
                         name="API Security Headers", attachment_type=allure.attachment_type.TEXT)
        else:
            allure.attach("API security headers look good", 
                         name="Good API Security", attachment_type=allure.attachment_type.TEXT)

    @allure.title("Error Page Information Disclosure")
    @allure.description("Test error pages for information disclosure")
    @pytest.mark.security
    def test_error_page_disclosure(self):
        """Test error pages for information disclosure"""
        # Test various error conditions
        error_endpoints = [
            "/nonexistent",
            "/api/nonexistent",
            "/admin",
            "/.env",
            "/config.php",
            "/wp-admin",
        ]
        
        for endpoint in error_endpoints:
            with allure.step(f"Testing error page: {endpoint}"):
                response = requests.get(f"{BASE_URL}{endpoint}")
                
                # Check for information disclosure in error pages
                sensitive_patterns = [
                    "traceback",
                    "stack trace",
                    "debug",
                    "exception",
                    "error",
                    "flask",
                    "python",
                    "werkzeug",
                ]
                
                response_text = response.text.lower()
                disclosed_info = []
                
                for pattern in sensitive_patterns:
                    if pattern in response_text:
                        disclosed_info.append(pattern)
                
                if disclosed_info:
                    allure.attach(f"Error page disclosure in {endpoint}: {disclosed_info}", 
                                 name="Error Page Disclosure", attachment_type=allure.attachment_type.TEXT)