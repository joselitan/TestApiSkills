"""Webhook and integration routes Blueprint (v1)."""

from flask import Blueprint, current_app, jsonify, request

from auth_helpers import token_required
from webhooks import dispatch, list_webhooks, register_webhook, unregister_webhook

bp = Blueprint("webhooks_v1", __name__)


@bp.route("/webhooks", methods=["POST"])
@token_required
def webhook_subscribe():
    """
    Register a webhook subscriber
    ---
    tags:
      - Integrations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: webhook
        required: true
        schema:
          type: object
          required:
            - url
            - events
          properties:
            url:
              type: string
              example: "https://external-system.example.com/hook"
            events:
              type: array
              items:
                type: string
              example: ["entry.created", "user.registered"]
            secret:
              type: string
              example: "mysecret"
    responses:
      201:
        description: Webhook registered
      400:
        description: Missing url or events
    """
    data = request.get_json(force=True) or {}
    url = data.get("url")
    events = data.get("events")
    secret = data.get("secret", "")

    if not url or not events or not isinstance(events, list):
        return jsonify({"message": "url and events array are required"}), 400

    entry = register_webhook(url, events, secret)
    return (
        jsonify(
            {
                "message": "Webhook registered",
                "url": entry["url"],
                "events": entry["events"],
            }
        ),
        201,
    )


@bp.route("/webhooks", methods=["GET"])
@token_required
def webhook_list():
    """
    List registered webhooks
    ---
    tags:
      - Integrations
    security:
      - Bearer: []
    responses:
      200:
        description: List of webhooks
    """
    return jsonify({"webhooks": list_webhooks()})


@bp.route("/webhooks", methods=["DELETE"])
@token_required
def webhook_unsubscribe():
    """
    Unregister a webhook
    ---
    tags:
      - Integrations
    security:
      - Bearer: []
    parameters:
      - in: body
        name: webhook
        required: true
        schema:
          type: object
          required:
            - url
          properties:
            url:
              type: string
    responses:
      200:
        description: Webhook removed
      404:
        description: Webhook not found
    """
    data = request.get_json(force=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"message": "url is required"}), 400
    removed = unregister_webhook(url)
    if removed:
        return jsonify({"message": "Webhook removed"})
    return jsonify({"message": "Webhook not found"}), 404


@bp.route("/integrations/inbound", methods=["POST"])
def inbound_event():
    """
    Receive events from external systems
    ---
    tags:
      - Integrations
    parameters:
      - in: body
        name: event
        required: true
        schema:
          type: object
          required:
            - event
            - data
          properties:
            event:
              type: string
              example: "external.sync"
            data:
              type: object
    responses:
      200:
        description: Event received
      400:
        description: Invalid payload
    """
    data = request.get_json(force=True) or {}
    event = data.get("event")
    payload = data.get("data")

    if not event or payload is None:
        return jsonify({"message": "event and data are required"}), 400

    current_app.logger.info("Inbound integration event received: %s", event)
    return jsonify({"message": "Event received", "event": event}), 200
