"""Source reliability engineering (DIG-003, DIG-023, DIG-048)."""

from __future__ import annotations

from typing import Any

_UNTRUSTED = frozenset({"unknown_vendor", "mock", "stub"})


def source_reliability_score(source_id: str) -> float:
    sid = str(source_id or "internal_cache").lower()
    if sid in _UNTRUSTED:
        return 0.0
    from data_governance.registry import get_source

    rec = get_source(sid)
    if rec:
        return 85.0 if rec.live_allowed else 50.0
    return 60.0


def assert_source_reliability(payload: dict[str, Any]) -> None:
    sid = str(payload.get("source_id") or payload.get("source") or "internal_cache")
    score = source_reliability_score(sid)
    if score < 30.0:
        from blackdark.data_governance.runtime import GovernanceViolationError

        raise GovernanceViolationError(f"source_reliability_too_low:{sid}")
