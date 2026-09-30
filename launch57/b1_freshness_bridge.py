"""
B1 → #41 targeted reconciliation bridge.

Post-verification activation binds B1 #22/#21 to canonical launch57.freshness_common (#41).
"""

from __future__ import annotations

from typing import Any

from launch57.batch1_isolation import TEMPORAL_DEPENDENCY_PENDING_6, TEMPORAL_DEPENDENCY_PENDING_41
from launch57.b3_evidence_bridge import apply_b3_evidence_reconciliation
from launch57.freshness_common import assess_freshness

# Activated after independent B2:#41 PASS_ENGINEERING @ 6ad4ae4c (REOPEN_REASON=DEPENDENCY_CONTRACT_CHANGE).
B1_TO_41_RECONCILIATION_ACTIVATED: bool = True
VERIFIED_HASH41_IMPLEMENTATION_SHA = "6ad4ae4c"


def b1_to_41_reconciliation_state() -> dict[str, Any]:
    base = {
        "contract": "B1_TO_41_TARGETED_RECONCILIATION",
        "auto_activate": False,
        "activated": B1_TO_41_RECONCILIATION_ACTIVATED,
        "verified_hash41_sha": VERIFIED_HASH41_IMPLEMENTATION_SHA,
        "affected_launch_items": [22, 21],
        "reopen_reason": "DEPENDENCY_CONTRACT_CHANGE",
    }
    if B1_TO_41_RECONCILIATION_ACTIVATED:
        return {
            **base,
            "status": "PENDING_VERIFICATION",
            "binding_status": "ACTIVATED_BOUND_TO_LAUNCH57_41",
        }
    return {
        **base,
        "status": "PREPARED_NOT_ACTIVATED",
        "required_verdict": "B2:#41=PASS_ENGINEERING",
    }


def prepare_b1_freshness_path(body: dict[str, Any]) -> dict[str, Any]:
    """Keep #41 dependency pending; bridge prepared but inert."""
    out = dict(body)
    pending = list(out.get("temporal_dependency_pending") or [])
    for item in (TEMPORAL_DEPENDENCY_PENDING_6, TEMPORAL_DEPENDENCY_PENDING_41):
        if not any(p.get("launch_number") == item["launch_number"] for p in pending):
            pending.append(item)
    out["temporal_dependency_pending"] = pending
    out["freshness_semantics"] = "BLOCKED_BY_DEPENDENCY_ORDER"
    out["presented_as_live"] = False
    out["b1_to_41_reconciliation"] = {
        **b1_to_41_reconciliation_state(),
        "status": "PREPARED_NOT_ACTIVATED",
        "activated": False,
    }
    out["launch57_isolation_boundary"] = True
    out["legacy_runtime_dependencies"] = 0
    out["b1_isolation_leakage"] = 0
    return out


def apply_b1_freshness_reconciliation(
    body: dict[str, Any],
    *,
    age_sec: float | None,
    source_time: Any = None,
    temporal: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind B1 freshness path to #41 only when reconciliation is explicitly activated."""
    if not B1_TO_41_RECONCILIATION_ACTIVATED:
        return prepare_b1_freshness_path(body)

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
    out["b1_to_41_reconciliation"] = b1_to_41_reconciliation_state()
    out["launch57_isolation_boundary"] = True
    out["legacy_runtime_dependencies"] = 0
    out["b1_isolation_leakage"] = 0
    if assessment.success:
        out["success"] = body.get("price_data_available", body.get("success", False))
    else:
        out["success"] = False
    return apply_b3_evidence_reconciliation(out)
