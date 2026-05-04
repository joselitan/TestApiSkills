"""Integration tests: webhook registration, inbound events, and dispatch."""

import hashlib
import hmac
import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer

import allure
import pytest
import requests

BASE_URL = "http://127.0.0.1:8080"
MOCK_PORT = 9876
MOCK_URL = f"http://127.0.0.1:{MOCK_PORT}/hook"

received_events: list[dict] = []


class _MockHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        received_events.append(
            {
                "event_type": self.headers.get("X-Event-Type"),
                "signature": self.headers.get("X-Signature"),
                "body": json.loads(body),
            }
        )
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def mock_server():
    server = HTTPServer(("127.0.0.1", MOCK_PORT), _MockHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    yield server
    server.shutdown()


@pytest.fixture(scope="module")
def auth_token():
    resp = requests.post(
        f"{BASE_URL}/api/v1/login", json={"username": "admin", "password": "password123"}
    )
    return resp.json()["token"]


@pytest.fixture(autouse=True)
def clear_events():
    received_events.clear()


# â”€â”€ Webhook Management â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@allure.feature("Integrations")
@allure.story("Webhook Registration")
@allure.severity(allure.severity_level.CRITICAL)
def test_register_webhook(auth_token, mock_server):
    resp = requests.post(
        f"{BASE_URL}/api/v1/webhooks",
        json={"url": MOCK_URL, "events": ["entry.created"]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["url"] == MOCK_URL
    assert "entry.created" in body["events"]


@allure.feature("Integrations")
@allure.story("Webhook Registration")
@allure.severity(allure.severity_level.NORMAL)
def test_register_webhook_missing_fields(auth_token, mock_server):
    resp = requests.post(
        f"{BASE_URL}/api/v1/webhooks",
        json={"url": MOCK_URL},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 400


@allure.feature("Integrations")
@allure.story("Webhook List")
@allure.severity(allure.severity_level.NORMAL)
def test_list_webhooks(auth_token, mock_server):
    requests.post(
        f"{BASE_URL}/api/v1/webhooks",
        json={"url": MOCK_URL, "events": ["entry.created"]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    resp = requests.get(
        f"{BASE_URL}/api/v1/webhooks",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200
    urls = [w["url"] for w in resp.json()["webhooks"]]
    assert MOCK_URL in urls


@allure.feature("Integrations")
@allure.story("Webhook Unregister")
@allure.severity(allure.severity_level.NORMAL)
def test_unregister_webhook(auth_token, mock_server):
    requests.post(
        f"{BASE_URL}/api/v1/webhooks",
        json={"url": MOCK_URL, "events": ["entry.created"]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    resp = requests.delete(
        f"{BASE_URL}/api/v1/webhooks",
        json={"url": MOCK_URL},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 200


@allure.feature("Integrations")
@allure.story("Webhook Unregister")
@allure.severity(allure.severity_level.NORMAL)
def test_unregister_nonexistent_webhook(auth_token, mock_server):
    resp = requests.delete(
        f"{BASE_URL}/api/v1/webhooks",
        json={"url": "http://does-not-exist.example.com/hook"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert resp.status_code == 404


# â”€â”€ Inbound Events â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@allure.feature("Integrations")
@allure.story("Inbound Events")
@allure.severity(allure.severity_level.CRITICAL)
def test_inbound_event_success():
    resp = requests.post(
        f"{BASE_URL}/api/v1/integrations/inbound",
        json={"event": "external.sync", "data": {"ref": "abc123"}},
    )
    assert resp.status_code == 200
    assert resp.json()["event"] == "external.sync"


@allure.feature("Integrations")
@allure.story("Inbound Events")
@allure.severity(allure.severity_level.NORMAL)
def test_inbound_event_missing_fields():
    resp = requests.post(
        f"{BASE_URL}/api/v1/integrations/inbound",
        json={"event": "external.sync"},
    )
    assert resp.status_code == 400


# â”€â”€ End-to-End Dispatch â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


@allure.feature("Integrations")
@allure.story("Webhook Dispatch")
@allure.severity(allure.severity_level.CRITICAL)
def test_entry_created_dispatches_webhook(auth_token, mock_server):
    """Creating a guestbook entry should fire the entry.created webhook."""
    requests.post(
        f"{BASE_URL}/api/v1/webhooks",
        json={"url": MOCK_URL, "events": ["entry.created"]},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    requests.post(
        f"{BASE_URL}/api/v1/guestbook",
        json={
            "name": "Integration Test",
            "email": "int@test.com",
            "comment": "hook test",
        },
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    time.sleep(1.0)  # allow async dispatch

    assert any(e["event_type"] == "entry.created" for e in received_events)


@allure.feature("Integrations")
@allure.story("Webhook Dispatch")
@allure.severity(allure.severity_level.CRITICAL)
def test_webhook_hmac_signature(auth_token, mock_server):
    """Webhook payload should carry a valid HMAC-SHA256 signature when secret is set."""
    secret = "test-secret-123"
    requests.post(
        f"{BASE_URL}/api/v1/webhooks",
        json={"url": MOCK_URL, "events": ["entry.created"], "secret": secret},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    requests.post(
        f"{BASE_URL}/api/v1/guestbook",
        json={"name": "HMAC Test", "email": "hmac@test.com", "comment": "sig check"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )

    time.sleep(1.0)

    signed = [e for e in received_events if e.get("signature")]
    assert signed, "Expected at least one signed webhook delivery"

    event = signed[0]
    raw = json.dumps(
        {"event": event["body"]["event"], "data": event["body"]["data"]}
    ).encode()
    expected_sig = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    assert event["signature"] == expected_sig
