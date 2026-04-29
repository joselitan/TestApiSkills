"""Authentication routes Blueprint (v1)."""

import datetime
import json
import uuid

import jwt
from flask import Blueprint, current_app, jsonify, request
from itsdangerous import BadSignature, SignatureExpired
from werkzeug.security import check_password_hash, generate_password_hash

from auth_helpers import (
    get_serializer,
    get_user_by_email_or_username,
    send_password_reset_email,
    send_verification_email,
    token_required,
)
from database import get_db
from utils import is_valid_email, normalize_email, sanitize_html, validate_json_payload
from webhooks import dispatch

bp = Blueprint("auth_v1", __name__)


@bp.route("/login", methods=["POST"])
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
        current_app.logger.warning(f"Invalid JSON in login request: {str(e)}")
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
    current_app.logger.info(
        f"Login attempt for identifier: {identifier} from IP: {request.remote_addr}"
    )

    user = get_user_by_email_or_username(identifier)
    if not user:
        current_app.logger.warning(
            f"Login failed for identifier: {identifier} - Invalid credentials"
        )
        return jsonify({"message": "Invalid credentials"}), 401

    if not check_password_hash(user["password"], password):
        current_app.logger.warning(
            f"Login failed for identifier: {identifier} - Invalid credentials"
        )
        return jsonify({"message": "Invalid credentials"}), 401

    if not user["is_active"]:
        current_app.logger.warning(
            f"Login rejected for identifier: {identifier} - account inactive"
        )
        return jsonify({"message": "Account not active. Verify your email."}), 403

    token = jwt.encode(
        {
            "user": user["email"] or user["username"],
            "role": user["role"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        },
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )
    current_app.logger.info(f"Login successful for identifier: {identifier}")
    return jsonify({"token": token})


@bp.route("/register", methods=["POST"])
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
    if not current_app.config["ENABLE_SELF_REGISTRATION"]:
        return jsonify({"message": "Self registration is disabled."}), 403

    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"message": "Invalid JSON payload"}), 400

        is_valid, message = validate_json_payload(data)
        if not is_valid:
            return jsonify({"message": message}), 400
    except (json.JSONDecodeError, Exception) as e:
        current_app.logger.warning(f"Invalid JSON in register request: {str(e)}")
        return jsonify({"message": "Invalid JSON payload"}), 400

    email = normalize_email(data.get("email"))
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    role = data.get("role", current_app.config["DEFAULT_ROLE"])
    username = data.get("username")

    if username:
        username = sanitize_html(username.strip())

    if not username and email:
        base_username = email.split("@")[0] or "user"
        username = sanitize_html(base_username)

    if not email or not password or not confirm_password:
        return (
            jsonify({"message": "Email, password and confirm_password are required"}),
            400,
        )
    if not is_valid_email(email):
        return jsonify({"message": "Invalid email address"}), 400
    if password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400
    if role not in current_app.config["ALLOWED_ROLES"]:
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
    serializer = get_serializer()
    verification_token = serializer.dumps(email, salt="email-confirm")
    verification_expires_at = datetime.datetime.utcnow() + datetime.timedelta(
        hours=current_app.config["VERIFICATION_TOKEN_EXPIRATION_HOURS"]
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
    dispatch("user.registered", {"email": email, "username": username})
    return jsonify({"message": message}), 201


@bp.route("/verify-email")
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

    serializer = get_serializer()
    try:
        email = serializer.loads(
            token,
            salt="email-confirm",
            max_age=current_app.config["VERIFICATION_TOKEN_EXPIRATION_HOURS"] * 3600,
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


@bp.route("/password-reset-request", methods=["POST"])
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
        current_app.logger.warning(
            f"Invalid JSON in password reset request: {str(e)}"
        )
        return jsonify({"message": "Invalid JSON payload"}), 400

    email = normalize_email(data.get("email"))
    if not email or not is_valid_email(email):
        return jsonify({"message": "Invalid email address"}), 400

    serializer = get_serializer()
    conn = get_db()
    user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if user:
        reset_token = serializer.dumps(email, salt="password-reset")
        reset_expires = datetime.datetime.utcnow() + datetime.timedelta(
            hours=current_app.config["PASSWORD_RESET_TOKEN_EXPIRATION_HOURS"]
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
        return (
            jsonify(
                {
                    "message": (
                        "Password reset requested, but email could not be sent. "
                        "Check email SMTP configuration."
                    )
                }
            ),
            200,
        )

    return jsonify({"message": "Password reset email sent."}), 200


@bp.route("/password-reset", methods=["POST"])
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
        current_app.logger.warning(
            f"Invalid JSON in password reset request: {str(e)}"
        )
        return jsonify({"message": "Invalid JSON payload"}), 400

    token = data.get("token")
    password = data.get("password")
    confirm_password = data.get("confirm_password")

    if not token or not password or not confirm_password:
        return (
            jsonify({"message": "Token, password and confirm_password are required"}),
            400,
        )
    if password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400
    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters"}), 400

    serializer = get_serializer()
    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=current_app.config["PASSWORD_RESET_TOKEN_EXPIRATION_HOURS"] * 3600,
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
