"""
BLACKDARK — Persistent security event log (login failures, admin MFA, denials).

Append-only JSONL + optional DB row. Engineering audit trail — not SIEM/SOC2.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.SecurityEvents")

_LOCK = threading.Lock()
_BUFFER: list[dict[str, Any]] = []
_MAX_BUFFER = 1000


def _log_path() -> Path:
    root = Path(os.getenv("DATA_DIR") or "data")
    root.mkdir(parents=True, exist_ok=True)
    return root / "security_events.jsonl"


def record_security_event(
    kind: str,
    *,
    severity: str = "info",
    actor: str | None = None,
    ip: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = {
        "ts": time.time(),
        "iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": kind,
        "severity": severity,
        "actor": actor,
        "ip": ip,
        "detail": detail or {},
    }
    with _LOCK:
        _BUFFER.append(event)
        if len(_BUFFER) > _MAX_BUFFER:
            del _BUFFER[: len(_BUFFER) - _MAX_BUFFER]
        try:
            with _log_path().open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            logger.debug("security event persist failed", exc_info=True)
    return event


def recent_security_events(*, limit: int = 50, kind: str | None = None) -> list[dict[str, Any]]:
    with _LOCK:
        rows = list(_BUFFER)
    if kind:
        rows = [r for r in rows if r.get("kind") == kind]
    # Also tail file if buffer empty (process restart)
    if not rows:
        path = _log_path()
        if path.is_file():
            try:
                lines = path.read_text(encoding="utf-8").splitlines()[-limit:]
                rows = [json.loads(x) for x in lines if x.strip()]
            except Exception:
                rows = []
    return rows[-limit:]


def security_events_stats() -> dict[str, Any]:
    rows = recent_security_events(limit=500)
    by_kind: dict[str, int] = {}
    for r in rows:
        k = str(r.get("kind") or "unknown")
        by_kind[k] = by_kind.get(k, 0) + 1
    return {
        "buffered": len(_BUFFER),
        "path": str(_log_path()),
        "by_kind": by_kind,
        "recent": rows[-10:],
    }
