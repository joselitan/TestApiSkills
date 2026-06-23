"""Rate limit testing endpoint Blueprint (v1)."""

from flask import Blueprint, jsonify, request

from rate_limiter import get_rate_limit_info

bp = Blueprint("rate_limit_test_v1", __name__)


@bp.route("/rate-limit/status", methods=["GET"])
def rate_limit_status():
    """
    Get current rate limit status
    ---
    tags:
      - Rate Limiting
    responses:
      200:
        description: Current rate limit status
        schema:
          type: object
          properties:
            identifier:
              type: string
              example: "ip:127.0.0.1"
            ip_address:
              type: string
              example: "127.0.0.1"
            is_authenticated:
              type: boolean
              example: false
            message:
              type: string
              example: "Rate limit status retrieved successfully"
    """
    info = get_rate_limit_info()
    info["message"] = "Rate limit status retrieved successfully"
    return jsonify(info), 200
