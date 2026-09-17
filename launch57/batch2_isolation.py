"""Launch-57 B2 isolation helpers — zero legacy/PARKED runtime dependencies."""

from __future__ import annotations

from typing import Any

TEMPORAL_DEPENDENCY_PENDING_6: dict[str, Any] = {
    "launch_number": 6,
    "capability_name": "Evidence class visible (LIVE/DELAYED/SIM)",
    "status": "TEMPORAL_DEPENDENCY_PENDING",
    "missing_contract": "canonical #6 user-visible evidence-class owner",
    "consumer_impact": "B2 cannot attach evidence-class metadata until #6 PASS_ENGINEERING",
    "reconciliation_contract": "B6_TARGETED_RECONCILIATION",
}


def finalize_b2_response(body: dict[str, Any]) -> dict[str, Any]:
    out = dict(body)
    pending = list(out.get("temporal_dependency_pending") or [])
    if not any(p.get("launch_number") == 6 for p in pending):
        pending.append(TEMPORAL_DEPENDENCY_PENDING_6)
    out["temporal_dependency_pending"] = pending
    out["launch57_isolation_boundary"] = True
    out["legacy_runtime_dependencies"] = 0
    out["b2_isolation_leakage"] = 0
    return out
