"""Unusual access / bulk export / audit-bypass detectors (FDS-17 / SDG-09)."""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Any

from security_events import record_security_event

_EXPORT_WINDOW_SEC = 3600
_DENIED_WINDOW_SEC = 300


def _export_threshold() -> int:
    return int(os.getenv("BULK_FINANCIAL_EXPORT_THRESHOLD", "3"))


def _denied_threshold() -> int:
    return int(os.getenv("FINANCIAL_DENIED_THRESHOLD", "5"))

_export_counts: dict[str, list[float]] = defaultdict(list)
_denied_counts: dict[str, list[float]] = defaultdict(list)


def _prune(bucket: dict[str, list[float]], key: str, window: float) -> list[float]:
    now = time.time()
    bucket[key] = [t for t in bucket[key] if now - t < window]
    return bucket[key]


def detect_bulk_financial_export(*, actor: str, resource_class: str, correlation_id: str | None = None) -> dict[str, Any] | None:
    key = f"{actor}:{resource_class}"
    events = _prune(_export_counts, key, _EXPORT_WINDOW_SEC)
    events.append(time.time())
    _export_counts[key] = events
    if len(events) < _export_threshold():
        return None
    detail = {
        "detector": "bulk_financial_export",
        "actor": actor,
        "resource_class": resource_class,
        "count": len(events),
        "window_sec": _EXPORT_WINDOW_SEC,
        "correlation_id": correlation_id,
        "severity": "high",
    }
    record_security_event("bulk_financial_export", severity="high", actor=actor, detail=detail)
    return detail


def detect_repeated_denied_financial_access(*, actor: str, operation: str) -> dict[str, Any] | None:
    key = f"{actor}:{operation}"
    events = _prune(_denied_counts, key, _DENIED_WINDOW_SEC)
    events.append(time.time())
    _denied_counts[key] = events
    if len(events) < _denied_threshold():
        return None
    detail = {
        "detector": "repeated_denied_financial_access",
        "actor": actor,
        "operation": operation,
        "count": len(events),
        "window_sec": _DENIED_WINDOW_SEC,
        "severity": "medium",
    }
    record_security_event("unusual_financial_access", severity="warning", actor=actor, detail=detail)
    return detail


def detect_audit_bypass_attempt(*, actor: str | None, flag: str) -> dict[str, Any]:
    forbidden = {
        "AUDIT_DISABLE",
        "SKIP_AUDIT",
        "AUDIT_BYPASS",
        "DISABLE_SECURITY_EVENTS",
    }
    if flag not in forbidden and not os.getenv(flag, "").strip():
        return {"detected": False}
    detail = {
        "detector": "audit_bypass_attempt",
        "actor": actor,
        "flag": flag,
        "severity": "critical",
    }
    record_security_event("audit_bypass_attempt", severity="critical", actor=actor, detail=detail)
    return {"detected": True, **detail}


def check_audit_bypass_env() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for flag in ("AUDIT_DISABLE", "SKIP_AUDIT", "AUDIT_BYPASS", "DISABLE_SECURITY_EVENTS"):
        if os.getenv(flag, "").strip().lower() in {"1", "true", "yes", "on"}:
            findings.append(detect_audit_bypass_attempt(actor="system", flag=flag))
    return findings
