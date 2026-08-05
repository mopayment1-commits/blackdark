"""
BLACKDARK — In-app alert inbox (works without Telegram/SMTP).

Every dispatch_alert writes here so Free/Pro users always see signals
in the product even when external channels are unavailable.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

_LOCK = threading.Lock()
_INBOX: list[dict[str, Any]] = []
_MAX = 300
_PATH = Path("data/in_app_alerts.jsonl")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def push_in_app_alert(
    title: str,
    body: str,
    *,
    payload: dict[str, Any] | None = None,
    user_email: str | None = None,
    level: str = "info",
) -> dict[str, Any]:
    row = {
        "id": f"ina_{uuid4().hex[:12]}",
        "title": title,
        "body": body,
        "level": level,
        "payload": payload or {},
        "user_email": (user_email or "").lower() or None,
        "read": False,
        "created_at": _utcnow(),
        "ts": time.time(),
    }
    with _LOCK:
        _INBOX.insert(0, row)
        del _INBOX[_MAX:]
        try:
            _PATH.parent.mkdir(parents=True, exist_ok=True)
            with _PATH.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, separators=(",", ":"), default=str) + "\n")
        except Exception:
            pass
    return dict(row)


def list_in_app_alerts(
    *,
    limit: int = 30,
    user_email: str | None = None,
    unread_only: bool = False,
) -> list[dict[str, Any]]:
    with _LOCK:
        rows = list(_INBOX)
    email = (user_email or "").lower().strip()
    if email:
        rows = [r for r in rows if not r.get("user_email") or r.get("user_email") == email]
    else:
        # Public/guest: only broadcast (no user_email) alerts
        rows = [r for r in rows if not r.get("user_email")]
    if unread_only:
        rows = [r for r in rows if not r.get("read")]
    return rows[: max(1, min(limit, 100))]


def mark_read(alert_id: str) -> dict[str, Any] | None:
    with _LOCK:
        for row in _INBOX:
            if row.get("id") == alert_id:
                row["read"] = True
                return dict(row)
    return None


def inbox_stats(*, user_email: str | None = None) -> dict[str, Any]:
    rows = list_in_app_alerts(limit=200, user_email=user_email)
    unread = sum(1 for r in rows if not r.get("read"))
    return {
        "total": len(rows),
        "unread": unread,
        "channels_note": "In-app inbox works without Telegram or SMTP",
        "generosity_note": (
            "No TradingView-style 15-alerts-per-3-minutes hard cap on the in-app inbox. "
            "Only Truth + Half-Life survivors are alertable."
        ),
        "timestamp": _utcnow(),
    }
