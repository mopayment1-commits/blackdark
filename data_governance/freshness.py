"""Data freshness evaluation (DIG-012)."""

from __future__ import annotations

import time
from typing import Any


def evaluate_freshness(*, observed_at: float | None, max_age_seconds: float) -> dict[str, Any]:
    now = time.time()
    if observed_at is None:
        return {"ok": False, "reason": "missing_timestamp", "age_seconds": None}
    age = max(0.0, now - observed_at)
    return {
        "ok": age <= max_age_seconds,
        "age_seconds": age,
        "max_age_seconds": max_age_seconds,
        "observed_at": observed_at,
    }


def gate_admission(payload: dict[str, Any], *, max_age_seconds: float = 300.0) -> dict[str, Any]:
    observed = payload.get("observed_at") or payload.get("timestamp")
    try:
        observed_at = float(observed) if observed is not None else None
    except (TypeError, ValueError):
        observed_at = None
    freshness = evaluate_freshness(observed_at=observed_at, max_age_seconds=max_age_seconds)
    rights_source = str(payload.get("source_id") or "internal_cache")
    from data_governance.rights import assert_usage_allowed

    rights = assert_usage_allowed(rights_source, purpose=str(payload.get("purpose") or "analytics"))
    admitted = freshness["ok"] and rights["allowed"]
    return {
        "admitted": admitted,
        "freshness": freshness,
        "rights": rights,
        "decision_truth_admission_gate": admitted,
    }
