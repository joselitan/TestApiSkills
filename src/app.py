import datetime
import os
import time
import traceback

import jwt
from flasgger import Swagger
from flask import Flask, g, jsonify, redirect, render_template, request

from auth_helpers import is_user_authenticated
from database import get_db, init_db
from logger_config import setup_logger
from webhooks import dispatch, list_webhooks, register_webhook, unregister_webhook




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
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY", "your-secret-key-change-in-production"
)
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

# ---------------------------------------------------------------------------
# Blueprint registrations â€” DEV-26 (Flask Blueprints) + DEV-27 (/api/v1/ aliases)
# ---------------------------------------------------------------------------

from blueprints.v1.auth import bp as auth_v1_bp
from blueprints.v1.guestbook import bp as guestbook_v1_bp
from blueprints.v1.reactions import bp as reactions_v1_bp
from blueprints.v1.webhooks import bp as webhooks_v1_bp

# Versioned /api/v1/ routes (DEV-27)
app.register_blueprint(auth_v1_bp, url_prefix="/api/v1")
app.register_blueprint(guestbook_v1_bp, url_prefix="/api/v1")
app.register_blueprint(webhooks_v1_bp, url_prefix="/api/v1")
app.register_blueprint(reactions_v1_bp, url_prefix="/api/v1")

# Backward-compatible /api/ aliases â€” keeps existing tests green (DEV-27)
app.register_blueprint(auth_v1_bp, url_prefix="/api", name="auth_legacy")
app.register_blueprint(guestbook_v1_bp, url_prefix="/api", name="guestbook_legacy")
app.register_blueprint(webhooks_v1_bp, url_prefix="/api", name="webhooks_legacy")
app.register_blueprint(reactions_v1_bp, url_prefix="/api", name="reactions_legacy")

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



@app.route("/")
def index():
    return render_template("login.html")


@app.route("/guestbook")
def guestbook_page():
    return render_template("guestbook.html")


@app.route("/login")
def login_page():
    """
    Login page route with authenticated user protection
    Redirects authenticated users to /guestbook to prevent session confusion
    """
    if is_user_authenticated():
        app.logger.info(
            "Authenticated user attempted to access /login, redirecting to /guestbook"
        )
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


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=8080)

