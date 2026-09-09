"""Identity audit trail — ID-043."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_AUDIT_PATH = Path(os.getenv("IDENTITY_AUDIT_PATH", "data/identity_audit.jsonl"))
_SENSITIVE = frozenset({"password", "otp", "recovery_code", "token", "secret", "session"})


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in payload.items():
        if any(s in k.lower() for s in _SENSITIVE):
            out[k] = "[redacted]"
        else:
            out[k] = v
    return out


async def record_identity_event(
    *,
    event_type: str,
    user_id: int | None = None,
    actor: str | None = None,
    source: str | None = None,
    correlation_id: str | None = None,
    success: bool = True,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "id": f"idt_{uuid4().hex[:16]}",
        "event_type": event_type,
        "user_id": user_id,
        "actor": actor,
        "source": source or "identity",
        "correlation_id": correlation_id or uuid4().hex[:12],
        "success": success,
        "detail": _redact(detail or {}),
        "created_at": _utcnow(),
    }
    try:
        async with __import__("database").get_connection() as db:
            await db.execute(
                """
                INSERT INTO identity_audit_events
                (id, user_id, event_type, actor, source, correlation_id, success, detail_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    user_id,
                    event_type,
                    actor,
                    row["source"],
                    row["correlation_id"],
                    1 if success else 0,
                    json.dumps(row["detail"], default=str),
                    row["created_at"],
                ),
            )
            await db.commit()
    except Exception:
        _AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _AUDIT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
    return row
