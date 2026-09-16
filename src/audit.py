"""
Audit logging — spårar användaråtgärder i applikationen.

Användning i routes:
    from audit import log_action

    log_action("CREATE", "guestbook_entry", {"id": 5, "name": "John"})
    log_action("DELETE", "guestbook_entry", {"id": 5})
    log_action("BULK_DELETE", "guestbook_entries", {"count": 3, "ids": [1, 2, 3]})

Resulterar i en rad i logs/audit.log:
    2026-09-06T13:45:22 | USER=admin@test.com | IP=127.0.0.1 | ACTION=DELETE | RESOURCE=guestbook_entry | DETAILS={'id': 5}
"""

import logging

import jwt
from flask import current_app, request

# Separat logger enbart för audit-händelser — skriver till logs/audit.log
audit_logger = logging.getLogger("audit")


def _get_current_user() -> str:
    """Extrahera användarnamn från JWT-token i requesten. Returnerar 'anonymous' vid fel."""
    try:
        token = request.headers.get("Authorization", "")
        token = token.split()[1] if token.startswith("Bearer ") else token
        if not token:
            return "anonymous"
        payload = jwt.decode(
            token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
        )
        return payload.get("user", "anonymous")
    except Exception:
        return "anonymous"


def log_action(action: str, resource: str, details: dict = None) -> None:
    """
    Logga en användaråtgärd till logs/audit.log.

    Args:
        action:   Vad som gjordes, t.ex. "CREATE", "DELETE", "BULK_DELETE", "CLEANUP"
        resource: Vilket objekt som påverkades, t.ex. "guestbook_entry"
        details:  Valfri dict med extra info, t.ex. {"id": 5, "name": "John"}
    """
    from datetime import datetime, timezone

    user = _get_current_user()
    ip = request.remote_addr or "unknown"
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    msg = f"{timestamp} | USER={user} | IP={ip} | ACTION={action} | RESOURCE={resource}"
    if details:
        msg += f" | DETAILS={details}"

    audit_logger.info(msg)
