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


def security_log_retention_days() -> int:
    """CISA Secure by Demand: SaaS security logs ≥ 6 months (default 180 days)."""
    return max(180, int(os.getenv("SECURITY_LOG_RETENTION_DAYS", "180")))


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
            prune_expired_events()
        except Exception:
            logger.debug("security event persist failed", exc_info=True)
    return event


def prune_expired_events() -> int:
    """Drop JSONL lines older than retention window (best-effort, in-process lock)."""
    path = _log_path()
    if not path.is_file():
        return 0
    cutoff = time.time() - security_log_retention_days() * 86400
    removed = 0
    with _LOCK:
        try:
            kept: list[str] = []
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    ts = float(row.get("ts") or 0)
                except (json.JSONDecodeError, TypeError, ValueError):
                    kept.append(line)
                    continue
                if ts >= cutoff:
                    kept.append(line)
                else:
                    removed += 1
            if removed:
                path.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
        except Exception:
            logger.debug("security event prune failed", exc_info=True)
            return 0
    return removed


def fetch_security_events(
    *,
    limit: int = 1000,
    kinds: frozenset[str] | None = None,
) -> list[dict[str, Any]]:
    """Load recent events from JSONL (durable store), newest last."""
    path = _log_path()
    rows: list[dict[str, Any]] = []
    if path.is_file():
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rows.append(json.loads(line))
        except Exception:
            logger.debug("security event read failed", exc_info=True)
    if kinds:
        rows = [r for r in rows if str(r.get("kind") or "") in kinds]
    return rows[-limit:]


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
        "retention_days": security_log_retention_days(),
        "by_kind": by_kind,
        "recent": rows[-10:],
    }
