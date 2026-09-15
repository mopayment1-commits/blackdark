"""Production privileged access audit contract (SDG-13)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from transport_webhook_env.environment import environment_identity


def _ledger_path() -> Path:
    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root / "production_access_audit.jsonl"


def record_production_access_event(
    *,
    actor: str,
    action: str,
    target: str,
    outcome: str,
    correlation_id: str | None = None,
    auth_strength: str | None = None,
    authorization_result: str | None = None,
    reason: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "ts": time.time(),
        "environment": environment_identity(),
        "actor": (actor or "system").strip().lower()[:256],
        "action": (action or "unknown").strip()[:256],
        "target": (target or "").strip()[:512],
        "outcome": (outcome or "unknown").strip()[:64],
        "correlation_id": correlation_id,
        "auth_strength": auth_strength,
        "authorization_result": authorization_result,
        "reason": (reason or "")[:512],
        "detail": detail or {},
    }
    with _ledger_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event) + "\n")
    try:
        from security_events import record_security_event

        record_security_event(
            "production_access",
            severity="info" if outcome == "success" else "warning",
            actor=event["actor"],
            detail={
                "action": event["action"],
                "target": event["target"],
                "environment": event["environment"],
                "correlation_id": correlation_id,
                "authorization_result": authorization_result,
            },
        )
    except Exception:
        pass
    return event


def recent_production_access_events(limit: int = 50) -> list[dict[str, Any]]:
    path = _ledger_path()
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(raw))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]
