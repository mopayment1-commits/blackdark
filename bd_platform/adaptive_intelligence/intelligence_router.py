"""Intelligence Router v1 — deterministic 10-stage selection contract (spec §22, AIE-002/013)."""

from __future__ import annotations

import time
from typing import Any

from bd_platform.adaptive_intelligence.intent_contract import IntentContract, resolve_intent_contract
from bd_platform.adaptive_intelligence.performance_budgets import PerformanceBudget, check_budget
from bd_platform.adaptive_intelligence.safety_floor import enforce_safety_floor


def _candidate_catalog() -> list[dict[str, Any]]:
    from intent_router import INTENTS

    rows = []
    for intent in INTENTS:
        rows.append(
            {
                "capability_id": intent.get("hero") or intent["id"],
                "canonical_id": intent.get("hero") or intent["id"],
                "intent_id": intent["id"],
                "freshness_ok": True,
                "coverage_ok": True,
                "rights_ok": True,
                "available": True,
                "entitled": True,
                "source_cluster": intent.get("hero") or intent["id"],
                "contradicts": intent.get("contradicts", False),
                "marginal_value": 1.0,
            }
        )
    return rows


def _mandatory_controls(intent: IntentContract) -> list[str]:
    return list(intent.required_safety_lenses)


def _cluster_dependence(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in candidates:
        cluster = row.get("source_cluster") or row["capability_id"]
        if cluster in seen:
            row["dependence_clustered"] = True
            continue
        seen.add(cluster)
        row["dependence_clustered"] = False
        out.append(row)
    return out


def _conflict_coverage(intent: IntentContract, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    sensitive = intent.decision_type in {"opportunity", "risk", "due_diligence"}
    contradictions = [c for c in candidates if c.get("contradicts")]
    if sensitive and contradictions and len(candidates) == len(contradictions):
        return {"ok": False, "reason": "unresolved_material_conflict"}
    return {"ok": True, "contradictions": contradictions}


def _apply_marginal_value(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=lambda c: float(c.get("marginal_value") or 0.0), reverse=True)
    return ranked


def route_intelligence_request(
    *,
    query: str | None = None,
    intent_id: str | None = None,
    asset: str | None = None,
    horizon: str | None = None,
    decision_type: str | None = None,
    budget: PerformanceBudget | None = None,
    force_degraded: bool = False,
) -> dict[str, Any]:
    """10-stage router: intent → controls → eligibility → dependence → conflict → marginal → budget → stop → abstain → explain."""
    started = time.perf_counter()
    budget = budget or PerformanceBudget()
    stages: list[str] = []

    intent = resolve_intent_contract(
        query=query,
        intent_id=intent_id,
        asset=asset,
        horizon=horizon,
        decision_type=decision_type,
    )
    stages.append("intent")

    mandatory = _mandatory_controls(intent)
    stages.append("mandatory_controls")

    candidates = _candidate_catalog()
    if force_degraded:
        for c in candidates:
            c["freshness_ok"] = False
    eligible = [
        c
        for c in candidates
        if c.get("freshness_ok")
        and c.get("coverage_ok")
        and c.get("rights_ok")
        and c.get("available")
        and c.get("entitled")
    ]
    stages.append("candidate_eligibility")
    if not eligible:
        return {
            "stance": "ABSTAIN",
            "reason": "no_eligible_candidates",
            "intent": intent.to_dict(),
            "mandatory_controls": mandatory,
            "router_stages_completed": stages,
            "abstention": True,
        }

    clustered = _cluster_dependence(eligible)
    stages.append("dependence_clustering")

    conflict = _conflict_coverage(intent, clustered)
    stages.append("conflict_coverage")
    if not conflict["ok"]:
        return {
            "stance": "ABSTAIN",
            "reason": conflict["reason"],
            "intent": intent.to_dict(),
            "mandatory_controls": mandatory,
            "router_stages_completed": stages,
            "abstention": True,
        }

    ranked = _apply_marginal_value(clustered)
    stages.append("marginal_value")

    selected = ranked[: budget.max_selected]
    stages.append("budget")
    if not selected:
        return {
            "stance": "ABSTAIN",
            "reason": "dependence_cluster_empty",
            "intent": intent.to_dict(),
            "mandatory_controls": mandatory,
            "router_stages_completed": stages,
            "abstention": True,
        }

    coverage_met = len(selected) >= 1
    stages.append("stop")
    if not coverage_met:
        return {
            "stance": "ABSTAIN",
            "reason": "coverage_not_met",
            "intent": intent.to_dict(),
            "mandatory_controls": mandatory,
            "router_stages_completed": stages,
            "abstention": True,
        }

    budget_report = check_budget(
        budget,
        candidate_count=len(candidates),
        selected_count=len(selected),
        elapsed_ms=(time.perf_counter() - started) * 1000,
    )
    stages.append("abstain_pass")

    explanation = {
        "selected": [s["capability_id"] for s in selected],
        "excluded": [c["capability_id"] for c in candidates if c not in selected],
        "mandatory_controls": mandatory,
        "stopping_reason": "coverage_met_within_budget",
        "budget": budget_report,
        "conflict": conflict,
    }
    stages.append("explain")

    result = enforce_safety_floor(
        {
            "decision_critical": True,
            "stance": "NEUTRAL",
            "freshness": "near_live",
            "evidence_state": "forward_shadow",
            "uncertainty": "medium",
            "critical_limitation": "Router v1 deterministic; not calibrated probability.",
            "invalidation_or_next_check": "recheck_on_stale_data",
            "intent": intent.to_dict(),
            "selected_capabilities": selected,
            "router_explanation": explanation,
            "router_stages_completed": stages,
            "abstention": False,
        }
    )
    return result
