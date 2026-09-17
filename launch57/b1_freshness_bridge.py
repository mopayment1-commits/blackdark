"""
B1 → #41 targeted reconciliation bridge.

REOPEN_REASON=DEPENDENCY_CONTRACT_CHANGE for B1 #22/#21 only.
"""

from __future__ import annotations

from typing import Any

from launch57.batch1_isolation import TEMPORAL_DEPENDENCY_PENDING_6
from launch57.freshness_common import FreshnessAssessment, assess_freshness


def apply_b1_freshness_reconciliation(
    body: dict[str, Any],
    *,
    age_sec: float | None,
    source_time: Any = None,
    temporal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind B1 freshness-dependent path to canonical Launch-57 #41 owner."""
    temporal = temporal or body.get("temporal") or {}
    assessment = assess_freshness(
        age_sec=age_sec,
        source_time=source_time,
        observed_at=temporal.get("observed_time"),
        ingested_at=temporal.get("ingested_at"),
        available_at=temporal.get("available_at"),
        availability_state=temporal.get("availability_state"),
    )
    out = dict(body)
    out.update(assessment.to_payload())
    pending = [p for p in (out.get("temporal_dependency_pending") or []) if p.get("launch_number") != 41]
    if not any(p.get("launch_number") == 6 for p in pending):
        pending.append(TEMPORAL_DEPENDENCY_PENDING_6)
    out["temporal_dependency_pending"] = pending
    out.pop("freshness_semantics", None)
    out["b1_to_41_reconciliation"] = {
        "status": "BOUND_TO_LAUNCH57_41",
        "contract": "B1_TO_41_TARGETED_RECONCILIATION",
        "reopen_reason": "DEPENDENCY_CONTRACT_CHANGE",
        "auto_activate": False,
        "affected_launch_items": [22, 21],
    }
    out["launch57_isolation_boundary"] = True
    out["legacy_runtime_dependencies"] = 0
    out["b1_isolation_leakage"] = 0
    if assessment.success:
        out["success"] = body.get("price_data_available", body.get("success", False))
    else:
        out["success"] = False
    return out
