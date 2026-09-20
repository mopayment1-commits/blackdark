"""
Launch-57 B1 isolation helpers — zero legacy/PARKED runtime dependencies.

Freshness (#41) and evidence-class (#6) owners are NOT implemented here.
"""

from __future__ import annotations

from typing import Any

TEMPORAL_DEPENDENCY_PENDING_41: dict[str, Any] = {
    "launch_number": 41,
    "capability_name": "Freshness assurance + delayed explicit",
    "status": "TEMPORAL_DEPENDENCY_PENDING",
    "missing_contract": "canonical #41 freshness semantics owner",
    "consumer_impact": "B1 cannot assert LIVE/DELAYED/STALE or presented_as_live until B1_TO_41_TARGETED_RECONCILIATION",
    "reconciliation_contract": "B1_TO_41_TARGETED_RECONCILIATION",
    "auto_activate_on_b2_pass": False,
}

TEMPORAL_DEPENDENCY_PENDING_6: dict[str, Any] = {
    "launch_number": 6,
    "capability_name": "Evidence class visible (LIVE/DELAYED/SIM)",
    "status": "TEMPORAL_DEPENDENCY_PENDING",
    "missing_contract": "canonical #6 user-visible evidence-class owner",
    "consumer_impact": "B1 cannot attach evidence-class metadata until #6 PASS_ENGINEERING + targeted reconciliation",
    "reconciliation_contract": "B6_TARGETED_RECONCILIATION",
    "auto_activate_on_b3_pass": False,
}

B1_TO_41_TARGETED_RECONCILIATION_CONTRACT: dict[str, Any] = {
    "contract_id": "B1_TO_41_TARGETED_RECONCILIATION",
    "trigger_batch": "B2",
    "trigger_sequence": "#40 → #41 → #39",
    "activation": "explicit_only_after_41_pass_engineering",
    "auto_activate": False,
    "required_steps": [
        "verify #41 final tested SHA",
        "identify only B1 paths whose semantics genuinely require freshness",
        "replace TEMPORAL_DEPENDENCY_PENDING=#41 with canonical Launch-57 #41 contract",
        "run targeted B1↔#41 integration/regression tests",
        "verify no change to unaffected B1 behavior",
        "remove #41 pending dependency only after successful reconciliation",
    ],
    "reopen_rule": "REOPEN_REASON=DEPENDENCY_CONTRACT_CHANGE only if #41 causes material B1 contract/behavior change",
    "rebuild_b1_forbidden": True,
}


def _merge_pending(body: dict[str, Any], *items: dict[str, Any]) -> list[dict[str, Any]]:
    pending = list(body.get("temporal_dependency_pending") or [])
    existing = {p.get("launch_number") for p in pending}
    for item in items:
        if item["launch_number"] not in existing:
            pending.append(item)
            existing.add(item["launch_number"])
    return pending


def finalize_b1_response(body: dict[str, Any], *, require_freshness_owner: bool = False) -> dict[str, Any]:
    out = dict(body)
    pending_items = [TEMPORAL_DEPENDENCY_PENDING_6]
    if require_freshness_owner:
        pending_items.append(TEMPORAL_DEPENDENCY_PENDING_41)
    out["temporal_dependency_pending"] = _merge_pending(out, *pending_items)
    if require_freshness_owner:
        out["freshness_semantics"] = "BLOCKED_BY_DEPENDENCY_ORDER"
        out["presented_as_live"] = False
    out["launch57_isolation_boundary"] = True
    out["legacy_runtime_dependencies"] = 0
    out["b1_isolation_leakage"] = 0
    from launch57.b3_evidence_bridge import apply_b3_evidence_reconciliation

    return apply_b3_evidence_reconciliation(out)
