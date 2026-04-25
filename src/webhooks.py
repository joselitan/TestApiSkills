"""Webhook dispatcher for outbound integration events."""

import hashlib
import hmac
import json
import logging
import threading

import requests

logger = logging.getLogger(__name__)

_subscribers: list[dict] = []
_lock = threading.Lock()


def register_webhook(url: str, events: list[str], secret: str = "") -> dict:
    with _lock:
        existing = next((s for s in _subscribers if s["url"] == url), None)
        if existing:
            existing["events"] = events
            existing["secret"] = secret
            return existing
        entry = {"url": url, "events": events, "secret": secret}
        _subscribers.append(entry)
        return entry


def unregister_webhook(url: str) -> bool:
    with _lock:
        before = len(_subscribers)
        _subscribers[:] = [s for s in _subscribers if s["url"] != url]
        return len(_subscribers) < before


def list_webhooks() -> list[dict]:
    with _lock:
        return [{"url": s["url"], "events": s["events"]} for s in _subscribers]


def _sign_payload(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def dispatch(event: str, data: dict) -> None:
    """Fire-and-forget dispatch to all subscribers for this event."""
    with _lock:
        targets = [s for s in _subscribers if event in s.get("events", [])]

    if not targets:
        return

    payload = json.dumps({"event": event, "data": data}).encode()

    def _send(subscriber):
        headers = {"Content-Type": "application/json", "X-Event-Type": event}
        if subscriber.get("secret"):
            headers["X-Signature"] = _sign_payload(subscriber["secret"], payload)
        try:
            requests.post(subscriber["url"], data=payload, headers=headers, timeout=5)
        except Exception as exc:
            logger.warning("Webhook delivery failed to %s: %s", subscriber["url"], exc)

    for target in targets:
        threading.Thread(target=_send, args=(target,), daemon=True).start()
