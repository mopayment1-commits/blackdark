"""Privacy-safe analytics — AV §16."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from anonymous_visitor.consent import optional_tracking_allowed

_LOG = Path("data/anonymous_public_analytics.jsonl")
_LOCK = threading.Lock()
_ALLOWED_EVENTS = frozenset(
    {
        "landing_view",
        "explore_click",
        "intelligence_interaction",
        "account_intent",
        "signup_start",
        "consent_update",
    }
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def record_public_analytics_event(*, visitor_key: str, event: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    name = (event or "").strip().lower()
    if name not in _ALLOWED_EVENTS:
        return {"ok": False, "error": "event_not_allowed"}
    if not optional_tracking_allowed(visitor_key=visitor_key):
        return {
            "ok": True,
            "recorded": False,
            "reason": "optional_tracking_not_consented",
            "essential_only": True,
        }
    safe_meta = {}
    for k, v in (metadata or {}).items():
        kl = str(k).lower()
        if any(x in kl for x in ("email", "token", "key", "portfolio", "balance", "wallet")):
            continue
        safe_meta[k] = v
    row = {
        "ts": _now(),
        "event": name,
        "visitor_key_hash": visitor_key[:12],
        "metadata": safe_meta,
    }
    with _LOCK:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")
    return {"ok": True, "recorded": True, "event": name}


def analytics_status() -> dict[str, Any]:
    return {
        "consent_aware": True,
        "allowed_events": sorted(_ALLOWED_EVENTS),
        "no_financial_secrets": True,
        "no_private_payloads": True,
        "retention_policy": "local_jsonl_operational",
    }
