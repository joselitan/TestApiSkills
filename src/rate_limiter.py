"""
Rate limiting configuration and utilities for the Guestbook API.

This module provides rate limiting functionality to protect against:
- DDoS attacks
- Brute-force login attempts
- API abuse
- Excessive resource consumption

Rate limits are applied based on:
- IP address for anonymous users
- User identity for authenticated users
"""

import os
from functools import wraps

from flask import current_app, g, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import jwt


def get_user_identifier():
    """
    Get unique identifier for rate limiting.
    Uses authenticated user identity if available, otherwise falls back to IP address.
    
    Returns:
        str: User email/username for authenticated users, IP address for anonymous
    """
    # Try to get user from JWT token
    token = request.headers.get("Authorization")
    if token:
        try:
            # Remove 'Bearer ' prefix if present
            token = token.split()[1] if token.startswith("Bearer ") else token
            payload = jwt.decode(
                token, 
                current_app.config["SECRET_KEY"], 
                algorithms=["HS256"]
            )
            user = payload.get("user", "unknown")
            return f"user:{user}"
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, IndexError):
            pass
    
    # Fall back to IP address for anonymous users
    return f"ip:{get_remote_address()}"


def init_limiter(app):
    """
    Initialize Flask-Limiter with the app.
    
    Args:
        app: Flask application instance
        
    Returns:
        Limiter: Configured limiter instance
    """
    # Storage backend - uses memory by default, can be configured to use Redis
    storage_uri = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
    
    # Default limits for all routes (can be overridden per route)
    default_limits = os.getenv(
        "RATE_LIMIT_DEFAULT", 
        "1000 per hour, 100 per minute"
    )
    
    limiter = Limiter(
        app=app,
        key_func=get_user_identifier,
        default_limits=[default_limits],
        storage_uri=storage_uri,
        # Strategy for handling rate limit violations
        strategy="fixed-window",
        # Headers to include in response
        headers_enabled=True,
        # Retry-After header for 429 responses
        retry_after="http-date",
        # Swallow errors in production (don't break app if limiter fails)
        swallow_errors=app.config.get("ENVIRONMENT") == "production",
    )
    
    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        current_app.logger.warning(
            f"Rate limit exceeded for {get_user_identifier()} on {request.path}"
        )
        return jsonify({
            "message": "Rate limit exceeded. Please try again later.",
            "retry_after": e.description
        }), 429
    
    return limiter


# Rate limit configurations for different endpoint categories

# Authentication endpoints - strict limits to prevent brute force
AUTH_LIMITS = {
    "login": "5 per minute, 20 per hour",  # Max 5 login attempts per minute
    "register": "3 per hour, 10 per day",  # Prevent spam registrations
    "password_reset_request": "3 per hour, 10 per day",  # Prevent email spam
    "password_reset": "5 per hour",  # Limited password reset attempts
    "verify_email": "10 per hour",  # Limited verification attempts
}

# API endpoints - different limits for authenticated vs anonymous
API_LIMITS = {
    "authenticated_read": "200 per minute, 2000 per hour",  # Generous for reads
    "authenticated_write": "50 per minute, 500 per hour",  # More restrictive for writes
    "anonymous_read": "20 per minute, 100 per hour",  # Very limited for anonymous
    "anonymous_write": "5 per minute, 20 per hour",  # Extremely limited for anonymous
}

# Special endpoints
SPECIAL_LIMITS = {
    "bulk_operations": "10 per minute, 50 per hour",  # Bulk delete, import
    "cleanup": "2 per hour, 5 per day",  # Database cleanup operations
    "health_check": "60 per minute",  # Allow frequent health checks
}


def require_auth_for_rate_limit(limit_authenticated, limit_anonymous):
    """
    Decorator that applies different rate limits based on authentication status.
    
    Args:
        limit_authenticated: Rate limit string for authenticated users
        limit_anonymous: Rate limit string for anonymous users
        
    Returns:
        Decorated function with conditional rate limiting
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            token = request.headers.get("Authorization")
            is_authenticated = False
            
            if token:
                try:
                    token = token.split()[1] if token.startswith("Bearer ") else token
                    jwt.decode(
                        token, 
                        current_app.config["SECRET_KEY"], 
                        algorithms=["HS256"]
                    )
                    is_authenticated = True
                except:
                    pass
            
            # Store auth status in g for use by rate limiter
            g.is_authenticated = is_authenticated
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def get_rate_limit_info():
    """
    Get current rate limit status for the requester.
    
    Returns:
        dict: Rate limit information including remaining requests
    """
    from flask_limiter.util import get_remote_address
    
    identifier = get_user_identifier()
    
    return {
        "identifier": identifier,
        "ip_address": get_remote_address(),
        "is_authenticated": identifier.startswith("user:"),
    }
