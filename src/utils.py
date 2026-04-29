"""Shared utility functions with no Flask app-context dependency."""

import html
import os
import re

from werkzeug.utils import secure_filename

VALID_REACTIONS = {"like", "love", "laugh"}


def sanitize_html(text):
    """Sanitize HTML content to prevent XSS attacks"""
    if not text:
        return text
    return html.escape(str(text))


def validate_filename(filename):
    """Validate and sanitize filename to prevent command injection"""
    if not filename:
        return False, "Filename is required"

    # Remove path traversal attempts
    filename = os.path.basename(filename)

    # Use werkzeug's secure_filename
    secure_name = secure_filename(filename)

    # Additional checks for malicious patterns
    dangerous_patterns = [
        r"[;&|`$(){}\\[\\]<>]",  # Command injection characters
        r"\\.\\./",  # Path traversal
        r"^\\.",  # Hidden files
        r"\\.(bat|cmd|exe|sh|ps1)$",  # Executable files
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, secure_name, re.IGNORECASE):
            return False, f"Filename contains invalid characters: {filename}"

    # Check file extension whitelist
    allowed_extensions = {".xlsx", ".xls", ".csv"}
    file_ext = os.path.splitext(secure_name)[1].lower()
    if file_ext not in allowed_extensions:
        return False, f"File type not allowed: {file_ext}"

    return True, secure_name


def validate_json_payload(data):
    """Validate JSON payload structure and content"""
    if not isinstance(data, dict):
        return False, "Invalid JSON structure"

    # Check for NoSQL injection patterns
    def check_nosql_injection(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check for MongoDB operators
                if isinstance(key, str) and key.startswith("$"):
                    return True
                if check_nosql_injection(value):
                    return True
        elif isinstance(obj, list):
            for item in obj:
                if check_nosql_injection(item):
                    return True
        return False

    if check_nosql_injection(data):
        return False, "Invalid JSON content detected"

    return True, "Valid"


def is_valid_email(email):
    if not isinstance(email, str):
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def normalize_email(email):
    if not email or not isinstance(email, str):
        return None
    return sanitize_html(email.strip().lower())
