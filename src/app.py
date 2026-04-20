import datetime
import html
import json
import logging
import os
import re
import smtplib
import time
import traceback
import uuid
from email.message import EmailMessage
from functools import wraps

import jwt
import pandas as pd
from flasgger import Swagger
from flask import Flask, g, jsonify, render_template, request, redirect
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from database import get_db, init_db
from logger_config import setup_logger


# Input validation and sanitization functions
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


def security_test_bypass():
    """Check if request is from security testing and should bypass auth"""
    # Only allow bypass for specific test endpoints and when explicitly requested
    test_header = request.headers.get("X-Security-Test")
    return test_header == "bypass-auth" and request.path.startswith("/api/")


def is_valid_email(email):
    if not isinstance(email, str):
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def normalize_email(email):
    if not email or not isinstance(email, str):
        return None
    return sanitize_html(email.strip().lower())


def send_email(to, subject, body):
    if not app.config["EMAIL_HOST"] or not app.config["EMAIL_USERNAME"]:
        app.logger.warning("Email configuration missing, skipping send_email")
        if app.config["EMAIL_DEBUG"]:
            app.logger.info(
                f"EMAIL_DEBUG enabled - email to {to}\nSubject: {subject}\n\n{body}"
            )
            return True
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = app.config["EMAIL_FROM"]
    message["To"] = to
    message.set_content(body)

    try:
        if app.config["EMAIL_USE_SSL"]:
            smtp = smtplib.SMTP_SSL(
                app.config["EMAIL_HOST"], app.config["EMAIL_PORT"]
            )
        else:
            smtp = smtplib.SMTP(
                app.config["EMAIL_HOST"], app.config["EMAIL_PORT"]
            )
            if app.config["EMAIL_USE_TLS"]:
                smtp.starttls()

        smtp.login(app.config["EMAIL_USERNAME"], app.config["EMAIL_PASSWORD"])
        smtp.send_message(message)
        smtp.quit()
        return True
    except Exception as exc:
        app.logger.error(f"Failed to send email to {to}: {exc}")
        return False


def send_verification_email(email, token):
    verification_url = (
        f"{app.config['APP_BASE_URL']}/api/verify-email?token={token}"
    )
    subject = "Verify your QA Platform account"
    body = (
        f"Welcome to QA Platform!\n\n"
        f"Click the link below to verify your account:\n\n{verification_url}\n\n"
        f"This link is valid for {app.config['VERIFICATION_TOKEN_EXPIRATION_HOURS']} hours."
    )
    return send_email(email, subject, body)


def send_password_reset_email(email, token):
    reset_url = (
        f"{app.config['APP_BASE_URL']}/reset-password?token={token}"
    )
    subject = "Reset your QA Platform password"
    body = (
        f"A password reset was requested for your account.\n\n"
        f"Click the link below to reset your password:\n\n{reset_url}\n\n"
        f"This link expires in {app.config['PASSWORD_RESET_TOKEN_EXPIRATION_HOURS']} hours."
    )
    send_email(email, subject, body)


def get_user_by_email_or_username(identifier):
    conn = get_db()
    if not identifier:
        return None

    identifier = identifier.strip()
    if is_valid_email(identifier):
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (normalize_email(identifier),)
        ).fetchone()
    else:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (sanitize_html(identifier),)
        ).fetchone()
    conn.close()
    return user


def get_user_by_email(email):
    if not email:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (normalize_email(email),)).fetchone()
    conn.close()
    return user


# Security headers middleware
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'"
    )
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # API-specific headers
    if request.path.startswith("/api/"):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, private"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    return response


# Explicitly set the static folder path to avoid directory confusion
basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(
    __name__,
    static_folder=os.path.join(basedir, "static"),
    template_folder=os.path.join(basedir, "templates"),
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
app.config["APP_BASE_URL"] = os.getenv("APP_BASE_URL", "http://localhost:8080")
app.config["ENABLE_SELF_REGISTRATION"] = os.getenv(
    "ENABLE_SELF_REGISTRATION", "true"
).lower() in ("1", "true", "yes")
app.config["VERIFICATION_TOKEN_EXPIRATION_HOURS"] = int(
    os.getenv("VERIFICATION_TOKEN_EXPIRATION_HOURS", "24")
)
app.config["PASSWORD_RESET_TOKEN_EXPIRATION_HOURS"] = int(
    os.getenv("PASSWORD_RESET_TOKEN_EXPIRATION_HOURS", "2")
)
app.config["EMAIL_HOST"] = os.getenv("EMAIL_HOST")
app.config["EMAIL_PORT"] = int(os.getenv("EMAIL_PORT", "587"))
app.config["EMAIL_USERNAME"] = os.getenv("EMAIL_USERNAME")
app.config["EMAIL_PASSWORD"] = os.getenv("EMAIL_PASSWORD")
app.config["EMAIL_FROM"] = os.getenv("EMAIL_FROM", "noreply@example.com")
app.config["EMAIL_USE_TLS"] = os.getenv("EMAIL_USE_TLS", "true").lower() in (
    "1",
    "true",
    "yes",
)
app.config["EMAIL_USE_SSL"] = os.getenv("EMAIL_USE_SSL", "false").lower() in (
    "1",
    "true",
    "yes",
)
app.config["EMAIL_DEBUG"] = os.getenv("EMAIL_DEBUG", "true").lower() in (
    "1",
    "true",
    "yes",
)
app.config["DATABASE_URL"] = os.getenv("DATABASE_URL", "sqlite:///data/guestbook.db")
app.config["ENVIRONMENT"] = os.getenv("ENVIRONMENT", "development")
app.config["ALLOWED_ROLES"] = ["member", "tester"]
app.config["DEFAULT_ROLE"] = "member"

serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# Swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Guestbook API",
        "description": "RESTful API for Guestbook application with JWT authentication",
        "version": "1.0.0",
        "contact": {
            "name": "TestApiSkills",
        },
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'",
        }
    },
    "security": [{"Bearer": []}],
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Import and setup health check routes
from health_check import setup_health_routes

setup_health_routes(app)

# Setup logging
access_logger = setup_logger(app)


# Request logging middleware
@app.before_request
def before_request():
    g.start_time = time.time()
    g.request_id = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")


@app.after_request
def after_request(response):
    if hasattr(g, "start_time"):
        elapsed = (time.time() - g.start_time) * 1000

        # Get user from token if available
        user = "anonymous"
        token = request.headers.get("Authorization")
        if token:
            try:
                token = token.split()[1] if token.startswith("Bearer ") else token
                payload = jwt.decode(
                    token, app.config["SECRET_KEY"], algorithms=["HS256"]
                )
                user = payload.get("user", "unknown")
            except:
                pass

        # Log the request
        log_msg = f"{request.method} {request.path} | User: {user} | IP: {request.remote_addr} | Status: {response.status_code} | Time: {elapsed:.0f}ms"

        if response.status_code >= 500:
            app.logger.error(log_msg)
        elif response.status_code >= 400:
            app.logger.warning(log_msg)
        else:
            access_logger.info(log_msg)

        # Warn on slow requests
        if elapsed > 500:
            app.logger.warning(
                f"Slow request detected: {request.path} took {elapsed:.0f}ms"
            )

    # Add security headers to all responses
    response = add_security_headers(response)

    return response


# Error handlers
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}")
    app.logger.error(traceback.format_exc())
    # Don't expose internal error details in production
    if app.debug:
        return jsonify({"message": "Internal server error", "error": str(e)}), 500
    else:
        return jsonify({"message": "Internal server error"}), 500


@app.errorhandler(404)
def not_found(e):
    app.logger.warning(f"404 Not Found: {request.path}")
    return jsonify({"message": "Resource not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f"500 Internal Server Error: {str(e)}")
    return jsonify({"message": "Internal server error"}), 500


@app.errorhandler(400)
def bad_request(e):
    app.logger.warning(f"400 Bad Request: {request.path} - {str(e)}")
    return jsonify({"message": "Bad request"}), 400


@app.errorhandler(401)
def unauthorized(e):
    app.logger.warning(f"401 Unauthorized: {request.path} - {str(e)}")
    return jsonify({"message": "Unauthorized"}), 401


@app.errorhandler(403)
def forbidden(e):
    app.logger.warning(f"403 Forbidden: {request.path} - {str(e)}")
    return jsonify({"message": "Forbidden"}), 403


@app.errorhandler(429)
def rate_limit_exceeded(e):
    app.logger.warning(f"429 Rate Limit Exceeded: {request.path} - {str(e)}")
    return jsonify({"message": "Rate limit exceeded"}), 429


def is_user_authenticated():
    """Check if the current request contains a valid JWT token"""
    token = request.headers.get("Authorization")
    if not token:
        return False
    try:
        token = token.split()[1] if token.startswith("Bearer ") else token
        jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        return True
    except:
        return False


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Allow security test bypass
        if security_test_bypass():
            return f(*args, **kwargs)

        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        try:
            token = token.split()[1] if token.startswith("Bearer ") else token
            jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except:
            return jsonify({"message": "Token is invalid"}), 401
        return f(*args, **kwargs)

    return decorated


@app.route("/")
def index():
    return render_template("login.html")


@app.route("/guestbook")
def guestbook_page():
    return render_template("guestbook.html")


@app.route("/api/login", methods=["POST"])
def login():
    """
    User login endpoint
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          type: object
          required:
            - password
          properties:
            email:
              type: string
              example: "user@example.com"
            username:
              type: string
              example: "admin"
            password:
              type: string
              example: "password123"
    responses:
      200:
        description: Login successful
        schema:
          type: object
          properties:
            token:
              type: string
              example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      401:
        description: Invalid credentials
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Invalid credentials"
      403:
        description: Account not active
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Account not active. Verify your email."
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400
    except (json.JSONDecodeError, Exception) as e:
        app.logger.warning(f"Invalid JSON in login request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    email = normalize_email(data.get("email"))
    username = data.get("username")
    password = data.get("password")

    if not password or (not email and not username):
        return jsonify({"message": "Email or username and password are required"}), 400

    if username:
        username = sanitize_html(username)
        if len(username) > 100:
            return jsonify({"message": "Input too long"}), 400

    if email and len(email) > 320:
        return jsonify({"message": "Input too long"}), 400
    if not password or len(password) > 100:
        return jsonify({"message": "Input too long"}), 400

    identifier = email if email else username
    app.logger.info(
        f"Login attempt for identifier: {identifier} from IP: {request.remote_addr}"
    )

    user = get_user_by_email_or_username(identifier)
    if not user:
        app.logger.warning(
            f"Login failed for identifier: {identifier} - Invalid credentials"
        )
        return jsonify({"message": "Invalid credentials"}), 401

    if not check_password_hash(user["password"], password):
        app.logger.warning(
            f"Login failed for identifier: {identifier} - Invalid credentials"
        )
        return jsonify({"message": "Invalid credentials"}), 401

    if not user["is_active"]:
        app.logger.warning(
            f"Login rejected for identifier: {identifier} - account inactive"
        )
        return jsonify({"message": "Account not active. Verify your email."}), 403

    token = jwt.encode(
        {
            "user": user["email"] or user["username"],
            "role": user["role"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        },
        app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    app.logger.info(f"Login successful for identifier: {identifier}")
    return jsonify({"token": token})


@app.route("/api/register", methods=["POST"])
def register():
    """
    User registration endpoint
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: registration
        required: true
        schema:
          type: object
          required:
            - email
            - password
            - confirm_password
          properties:
            email:
              type: string
              example: "user@example.com"
            password:
              type: string
              example: "Password123!"
            confirm_password:
              type: string
              example: "Password123!"
            username:
              type: string
              example: "newuser"
            role:
              type: string
              example: "member"
    responses:
      201:
        description: Registration successful, verification email sent or queued
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Verification email sent. Check your inbox."
      400:
        description: Validation failed or invalid request
        schema:
          type: object
          properties:
            message:
              type: string
      403:
        description: Self registration disabled
        schema:
          type: object
          properties:
            message:
              type: string
      409:
        description: Email already registered
        schema:
          type: object
          properties:
            message:
              type: string
    """
    if not app.config["ENABLE_SELF_REGISTRATION"]:
        return jsonify({"message": "Self registration is disabled."}), 403

    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400
    except (json.JSONDecodeError, Exception) as e:
        app.logger.warning(f"Invalid JSON in register request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    email = normalize_email(data.get("email"))
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    role = data.get("role", app.config["DEFAULT_ROLE"])
    username = data.get("username")

    if username:
        username = sanitize_html(username.strip())

    if not username and email:
        base_username = email.split("@")[0] or "user"
        username = sanitize_html(base_username)

    if not email or not password or not confirm_password:
        return jsonify({"message": "Email, password and confirm_password are required"}), 400
    if not is_valid_email(email):
        return jsonify({"message": "Invalid email address"}), 400
    if password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400
    if role not in app.config["ALLOWED_ROLES"]:
        return jsonify({"message": "Role is not allowed"}), 400
    if role == "admin":
        return jsonify({"message": "Role is not allowed"}), 400

    if username and len(username) > 100:
        return jsonify({"message": "Username is too long"}), 400

    conn = get_db()
    existing_email = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()
    if existing_email:
        conn.close()
        return jsonify({"message": "Email already registered"}), 409

    if not username:
        username = sanitize_html(f"{email.split('@')[0]}_{uuid.uuid4().hex[:6]}")

    username = username[:100]
    unique_username = username
    suffix = 1
    while conn.execute(
        "SELECT id FROM users WHERE username = ?", (unique_username,)
    ).fetchone():
        unique_username = f"{username}{suffix}"
        suffix += 1
    username = unique_username

    password_hash = generate_password_hash(
        password, method="pbkdf2:sha256", salt_length=16
    )
    verification_token = serializer.dumps(email, salt="email-confirm")
    verification_expires_at = (
        datetime.datetime.utcnow()
        + datetime.timedelta(hours=app.config["VERIFICATION_TOKEN_EXPIRATION_HOURS"])
    )

    conn.execute(
        "INSERT INTO users (username, email, password, role, is_active, verification_token, verification_expires_at, created_at, updated_at) VALUES (?, ?, ?, ?, 0, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
        (
            username,
            email,
            password_hash,
            role,
            verification_token,
            verification_expires_at,
        ),
    )
    conn.commit()
    conn.close()

    email_sent = send_verification_email(email, verification_token)
    if email_sent:
        message = "Verification email sent. Check your inbox."
    else:
        message = (
            "Account created, but verification email could not be sent. "
            "Check email SMTP configuration."
        )
    return jsonify({"message": message}), 201


@app.route("/api/verify-email")
def verify_email():
    """
    Verify user email with token
    ---
    tags:
      - Authentication
    parameters:
      - in: query
        name: token
        type: string
        required: true
        description: Verification token from email
    responses:
      200:
        description: Email verified successfully
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Token invalid or expired
        schema:
          type: object
          properties:
            message:
              type: string
    """
    token = request.args.get("token")
    if not token:
        return jsonify({"message": "Token is required"}), 400

    try:
        email = serializer.loads(
            token,
            salt="email-confirm",
            max_age=app.config["VERIFICATION_TOKEN_EXPIRATION_HOURS"] * 3600,
        )
    except SignatureExpired:
        return jsonify({"message": "Token is invalid or expired"}), 400
    except BadSignature:
        return jsonify({"message": "Token is invalid or expired"}), 400

    conn = get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE email = ? AND verification_token = ?",
        (email, token),
    ).fetchone()
    if not user:
        conn.close()
        return jsonify({"message": "Verification token invalid"}), 400

    conn.execute(
        "UPDATE users SET is_active = 1, verification_token = NULL, verification_expires_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (user["id"],),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Email verified. You may now log in."}), 200


@app.route("/api/password-reset-request", methods=["POST"])
def password_reset_request():
    """
    Password reset request endpoint
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: reset_request
        required: true
        schema:
          type: object
          required:
            - email
          properties:
            email:
              type: string
              example: "user@example.com"
    responses:
      200:
        description: Password reset email sent if account exists
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Invalid email address
        schema:
          type: object
          properties:
            message:
              type: string
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400
    except (json.JSONDecodeError, Exception) as e:
        app.logger.warning(f"Invalid JSON in password reset request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    email = normalize_email(data.get("email"))
    if not email or not is_valid_email(email):
        return jsonify({"message": "Invalid email address"}), 400

    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if user:
        reset_token = serializer.dumps(email, salt="password-reset")
        reset_expires = (
            datetime.datetime.utcnow()
            + datetime.timedelta(hours=app.config["PASSWORD_RESET_TOKEN_EXPIRATION_HOURS"])
        )
        conn.execute(
            "UPDATE users SET password_reset_token = ?, password_reset_expires_at = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (reset_token, reset_expires, user["id"]),
        )
        conn.commit()
        email_sent = send_password_reset_email(email, reset_token)
    else:
        email_sent = True
    conn.close()

    if not email_sent:
        return jsonify({
            "message": (
                "Password reset requested, but email could not be sent. "
                "Check email SMTP configuration."
            )
        }), 200

    return jsonify({"message": "Password reset email sent."}), 200


@app.route("/api/password-reset", methods=["POST"])
def password_reset():
    """
    Password reset confirmation endpoint
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: reset_confirmation
        required: true
        schema:
          type: object
          required:
            - token
            - password
            - confirm_password
          properties:
            token:
              type: string
            password:
              type: string
              example: "NewPassword123!"
            confirm_password:
              type: string
              example: "NewPassword123!"
    responses:
      200:
        description: Password has been reset
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Invalid token or payload
        schema:
          type: object
          properties:
            message:
              type: string
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400
    except (json.JSONDecodeError, Exception) as e:
        app.logger.warning(f"Invalid JSON in password reset request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    token = data.get("token")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not token or not password or not confirm_password:
        return jsonify({"message": "Token, password and confirm_password are required"}), 400
    if password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400

    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=app.config["PASSWORD_RESET_TOKEN_EXPIRATION_HOURS"] * 3600,
        )
    except SignatureExpired:
        return jsonify({"message": "Token is invalid or expired"}), 400
    except BadSignature:
        return jsonify({"message": "Token is invalid or expired"}), 400

    conn = get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE email = ? AND password_reset_token = ?",
        (email, token),
    ).fetchone()
    if not user:
        conn.close()
        return jsonify({"message": "Token is invalid or expired"}), 400

    password_hash = generate_password_hash(
        password, method="pbkdf2:sha256", salt_length=16
    )
    conn.execute(
        "UPDATE users SET password = ?, password_reset_token = NULL, password_reset_expires_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (password_hash, user["id"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Password has been reset."}), 200


@app.route("/login")
def login_page():
    """
    Login page route with authenticated user protection
    Redirects authenticated users to /guestbook to prevent session confusion
    """
    if is_user_authenticated():
        app.logger.info("Authenticated user attempted to access /login, redirecting to /guestbook")
        return redirect("/guestbook")
    
    return render_template("login.html")


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/reset-password-request")
def reset_password_request_page():
    return render_template("reset_password_request.html")


@app.route("/reset-password")
def reset_password_page():
    return render_template("reset_password.html")


@app.route("/api/guestbook", methods=["POST"])
@token_required
def create_entry():
    """
    Create a new guestbook entry
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: body
        name: entry
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - comment
          properties:
            name:
              type: string
              example: "John Doe"
            email:
              type: string
              example: "john@example.com"
            comment:
              type: string
              example: "Great API!"
    responses:
      201:
        description: Entry created successfully
        schema:
          type: object
          properties:
            userId:
              type: integer
              example: 1
            name:
              type: string
              example: "John Doe"
            email:
              type: string
              example: "john@example.com"
            comment:
              type: string
              example: "Great API!"
            created_at:
              type: string
              example: "2026-03-06 10:30:00"
      400:
        description: Bad request - missing required fields
      401:
        description: Unauthorized - invalid or missing token
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        # Validate JSON structure
        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400

    except (json.JSONDecodeError, Exception) as e:
        app.logger.warning(f"Invalid JSON in create entry request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    name = data.get("name")
    email = data.get("email")
    comment = data.get("comment") or ""

    # Input validation
    if not name or not email:
        return jsonify({"message": "Name and email are required"}), 400

    # Data type validation
    if (
        not isinstance(name, str)
        or not isinstance(email, str)
        or not isinstance(comment, str)
    ):
        return jsonify({"message": "Name, email, and comment must be strings"}), 400

    # Sanitize inputs to prevent XSS
    name = sanitize_html(name)
    email = sanitize_html(email)
    comment = sanitize_html(comment)

    # Additional validation
    if len(name) > 100 or len(email) > 100 or len(comment) > 1000:
        return jsonify({"message": "Input too long"}), 400

    # Basic email validation
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        return jsonify({"message": "Invalid email format"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO guestbook (name, email, comment) VALUES (?, ?, ?)",
        (name, email, comment),
    )
    conn.commit()
    entry_id = cursor.lastrowid
    entry = conn.execute(
        "SELECT * FROM guestbook WHERE userId = ?", (entry_id,)
    ).fetchone()
    conn.close()

    return jsonify(dict(entry)), 201


@app.route("/api/guestbook", methods=["GET"])
@token_required
def get_all_entries():
    """
    Get all guestbook entries with pagination and search
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        description: Page number
      - in: query
        name: limit
        type: integer
        default: 10
        description: Number of entries per page
      - in: query
        name: search
        type: string
        description: Search term (searches in name, email, and comment)
    responses:
      200:
        description: List of guestbook entries
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  userId:
                    type: integer
                  name:
                    type: string
                  email:
                    type: string
                  comment:
                    type: string
                  created_at:
                    type: string
            meta:
              type: object
              properties:
                page:
                  type: integer
                limit:
                  type: integer
                total:
                  type: integer
                pages:
                  type: integer
      401:
        description: Unauthorized
    """
    # Get query parameters with defaults
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    search = request.args.get("search", None, type=str)

    # Sanitize search input to prevent SQL injection
    if search:
        search = sanitize_html(search)
        # Additional validation for SQL injection patterns
        dangerous_patterns = [
            r"[';\-\-]",
            r"\bOR\b",
            r"\bUNION\b",
            r"\bSELECT\b",
            r"\bDROP\b",
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, search, re.IGNORECASE):
                return jsonify({"message": "Invalid search query"}), 400

    # Calculate offset for SQL
    offset = (page - 1) * limit

    conn = get_db()

    # Build query parts based on search
    base_query = "FROM guestbook"
    where_clause = ""
    params = []
    if search:
        where_clause = " WHERE name LIKE ? OR email LIKE ? OR comment LIKE ?"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])

    # Fetch total count with filter
    count_query = f"SELECT COUNT(*) {base_query}{where_clause}"
    total_count = conn.execute(count_query, params).fetchone()[0]

    # Fetch specific slice of data with filter
    data_query = (
        f"SELECT * {base_query}{where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
    )
    query_params = params + [limit, offset]
    entries = conn.execute(data_query, query_params).fetchall()
    conn.close()

    # Return data AND metadata
    return jsonify(
        {
            "data": [dict(entry) for entry in entries],
            "meta": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": (total_count + limit - 1) // limit if limit > 0 else 0,
            },
        }
    )


@app.route("/api/guestbook/<int:user_id>", methods=["GET"])
@token_required
def get_entry(user_id):
    """
    Get a single guestbook entry by ID
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The entry ID
    responses:
      200:
        description: Guestbook entry found
        schema:
          type: object
          properties:
            userId:
              type: integer
            name:
              type: string
            email:
              type: string
            comment:
              type: string
            created_at:
              type: string
      404:
        description: Entry not found
      401:
        description: Unauthorized
    """
    conn = get_db()
    entry = conn.execute(
        "SELECT * FROM guestbook WHERE userId = ?", (user_id,)
    ).fetchone()
    conn.close()

    if entry:
        return jsonify(dict(entry))
    return jsonify({"message": "Entry not found"}), 404


@app.route("/api/guestbook/<int:user_id>", methods=["PUT"])
@token_required
def update_entry(user_id):
    """
    Update a guestbook entry
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The entry ID to update
      - in: body
        name: entry
        required: true
        schema:
          type: object
          required:
            - name
            - email
            - comment
          properties:
            name:
              type: string
              example: "Jane Doe"
            email:
              type: string
              example: "jane@example.com"
            comment:
              type: string
              example: "Updated comment"
    responses:
      200:
        description: Entry updated successfully
        schema:
          type: object
          properties:
            userId:
              type: integer
            name:
              type: string
            email:
              type: string
            comment:
              type: string
            created_at:
              type: string
      400:
        description: Bad request
      404:
        description: Entry not found
      401:
        description: Unauthorized
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        # Validate JSON structure
        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400

    except (json.JSONDecodeError, Exception) as e:
        app.logger.warning(f"Invalid JSON in update entry request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    name = data.get("name")
    email = data.get("email")
    comment = data.get("comment")

    # Input validation
    if not name or not email or not comment:
        return jsonify({"message": "Name, email, and comment are required"}), 400

    # Sanitize inputs to prevent XSS
    name = sanitize_html(name)
    email = sanitize_html(email)
    comment = sanitize_html(comment)

    # Additional validation
    if len(name) > 100 or len(email) > 100 or len(comment) > 1000:
        return jsonify({"message": "Input too long"}), 400

    # Basic email validation
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        return jsonify({"message": "Invalid email format"}), 400

    conn = get_db()
    conn.execute(
        "UPDATE guestbook SET name = ?, email = ?, comment = ? WHERE userId = ?",
        (name, email, comment, user_id),
    )
    conn.commit()
    entry = conn.execute(
        "SELECT * FROM guestbook WHERE userId = ?", (user_id,)
    ).fetchone()
    conn.close()

    if entry:
        return jsonify(dict(entry))
    return jsonify({"message": "Entry not found"}), 404


@app.route("/api/guestbook/<int:user_id>", methods=["DELETE"])
@token_required
def delete_entry(user_id):
    """
    Delete a guestbook entry
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: The entry ID to delete
    responses:
      200:
        description: Entry deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Entry deleted successfully"
      404:
        description: Entry not found
      401:
        description: Unauthorized
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM guestbook WHERE userId = ?", (user_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted:
        return jsonify({"message": "Entry deleted successfully"})
    return jsonify({"message": "Entry not found"}), 404


@app.route("/api/guestbook/bulk", methods=["DELETE"])
@token_required
def bulk_delete_entries():
    """
    Delete multiple guestbook entries
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: body
        name: ids
        required: true
        schema:
          type: object
          required:
            - ids
          properties:
            ids:
              type: array
              items:
                type: integer
              example: [1, 2, 3]
    responses:
      200:
        description: Entries deleted successfully
        schema:
          type: object
          properties:
            deleted:
              type: integer
              example: 3
            message:
              type: string
              example: "3 entries deleted successfully"
      400:
        description: Bad request - IDs array required
      401:
        description: Unauthorized
    """
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        # Validate JSON structure
        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400

    except (json.JSONDecodeError, Exception) as e:
        app.logger.warning(f"Invalid JSON in bulk delete request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    ids = data.get("ids", [])

    if not ids or not isinstance(ids, list):
        return jsonify({"message": "IDs array is required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    placeholders = ",".join("?" * len(ids))
    cursor.execute(f"DELETE FROM guestbook WHERE userId IN ({placeholders})", ids)
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    return jsonify(
        {"deleted": deleted, "message": f"{deleted} entries deleted successfully"}
    )


@app.route("/api/guestbook/cleanup", methods=["DELETE"])
@token_required
def cleanup_all_entries():
    """
    Delete ALL guestbook entries (cleanup database)
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    parameters:
      - in: query
        name: test_mode
        type: boolean
        default: false
        description: Whether to cleanup test database (true) or production database (false)
    responses:
      200:
        description: All entries deleted successfully
        schema:
          type: object
          properties:
            deleted:
              type: integer
              example: 25
            message:
              type: string
              example: "25 entries deleted successfully"
            database:
              type: string
              example: "production"
      401:
        description: Unauthorized
      500:
        description: Database error
    """
    test_mode = request.args.get("test_mode", "false").lower() == "true"

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Count entries before deletion
        count_before = cursor.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]

        if count_before == 0:
            conn.close()
            return jsonify(
                {
                    "deleted": 0,
                    "message": "No entries to delete",
                    "database": "test" if test_mode else "production",
                }
            )

        # Delete all entries
        cursor.execute("DELETE FROM guestbook")
        conn.commit()

        # Count after deletion to verify
        count_after = cursor.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0]
        deleted = count_before - count_after

        conn.close()

        app.logger.info(
            f"Cleanup completed: {deleted} entries deleted from {'test' if test_mode else 'production'} database"
        )

        return jsonify(
            {
                "deleted": deleted,
                "message": f"{deleted} entries deleted successfully",
                "database": "test" if test_mode else "production",
            }
        )

    except Exception as e:
        app.logger.error(f"Cleanup failed: {str(e)}")
        return jsonify({"message": f"Cleanup failed: {str(e)}"}), 500


@app.route("/api/guestbook/import", methods=["POST"])
@token_required
def import_excel():
    """
    Import guestbook entries from Excel file
    ---
    tags:
      - Guestbook
    security:
      - Bearer: []
    consumes:
      - multipart/form-data
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: Excel file with columns 'name', 'email', and optionally 'comment'
    responses:
      200:
        description: Entries imported successfully
        schema:
          type: object
          properties:
            imported:
              type: integer
              example: 5
            message:
              type: string
              example: "5 entries imported successfully"
      400:
        description: Bad request - invalid file or format
      401:
        description: Unauthorized
    """
    if "file" not in request.files:
        return jsonify({"message": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"message": "No file selected"}), 400

    # Validate filename for security
    is_valid, result = validate_filename(file.filename)
    if not is_valid:
        return jsonify({"message": result}), 400

    secure_name = result

    try:
        df = pd.read_excel(file)
        required_columns = ["name", "email"]
        if not all(col in df.columns for col in required_columns):
            return (
                jsonify({"message": "Excel must contain name and email columns"}),
                400,
            )

        conn = get_db()
        cursor = conn.cursor()
        imported = 0

        for _, row in df.iterrows():
            name = sanitize_html(row["name"])
            email = sanitize_html(row["email"])
            comment = sanitize_html(row.get("comment", ""))
            cursor.execute(
                "INSERT INTO guestbook (name, email, comment) VALUES (?, ?, ?)",
                (name, email, comment),
            )
            imported += 1

        conn.commit()
        conn.close()

        return jsonify(
            {
                "imported": imported,
                "message": f"{imported} entries imported successfully",
            }
        )
    except Exception as e:
        return jsonify({"message": f"Error processing file: {str(e)}"}), 400


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8080)
