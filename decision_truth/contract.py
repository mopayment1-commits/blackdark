"""Decision contract and scorecard (DTS-018, DTS-033, DTS-047)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from decision_truth.methodology import methodology_versions


def build_decision_contract(
    opportunity: dict[str, Any],
    *,
    net_edge: dict[str, Any],
    execution: dict[str, Any],
    capacity: dict[str, Any],
    half_life: dict[str, Any],
    risk: dict[str, Any],
    evidence_grade: dict[str, Any],
    evidence_class: str,
    admission: dict[str, Any],
    why: list[str] | None = None,
    why_not: list[str] | None = None,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    truth = net_edge.get("truth") or {}
    freshness = ((admission.get("evidence_context") or {}).get("freshness_state")) or "UNKNOWN"
    quality = ((admission.get("evidence_context") or {}).get("quality_state")) or "UNKNOWN"
    admission_state = admission.get("admission_state") or "ABSTAINED"

    if admission_state == "REJECTED":
        decision_state = "REJECTED"
    elif admission_state == "ABSTAINED":
        decision_state = "ABSTAINED"
    elif admission_state == "DEGRADED":
        decision_state = "DEGRADED"
    else:
        decision_state = "AVAILABLE"

    pre = risk.get("pre_impact") or {}
    interval = net_edge.get("net_edge_interval") or {}

    return {
        "decision_id": opportunity.get("decision_id") or f"dts-{uuid4().hex[:16]}",
        "decision_state": decision_state,
        "detected_at": now.isoformat(),
        "source_timestamp": opportunity.get("source_timestamp") or now.isoformat(),
        "freshness_state": freshness,
        "data_quality_state": quality,
        "gross_edge": net_edge.get("theoretical_edge_usd"),
        "expected_net_edge": net_edge.get("expected_net_edge_usd"),
        "realizable_net_edge": net_edge.get("realizable_net_edge_usd"),
        "net_edge_interval": interval,
        "execution_feasibility_score": execution.get("execution_feasibility_score"),
        "fill_probability": net_edge.get("fill_probability"),
        "capacity": capacity.get("capacity_usd"),
        "opportunity_half_life": half_life.get("remaining_seconds") or half_life.get("expected_half_life_seconds"),
        "risk_score": pre.get("risk_after"),
        "portfolio_impact": pre.get("material_drivers"),
        "risk_budget_before": pre.get("risk_before"),
        "risk_budget_after": pre.get("risk_after"),
        "evidence_grade": evidence_grade.get("overall_grade"),
        "evidence_class": evidence_class,
        "source_count": int(opportunity.get("source_count") or 1),
        "conflict_state": (admission.get("evidence_context") or {}).get("conflict_state"),
        "simulation_summary": opportunity.get("simulation_summary"),
        "calibration_summary": opportunity.get("calibration_summary"),
        "time_horizon": opportunity.get("time_horizon") or "1h",
        "entry_assumptions": opportunity.get("entry_assumptions") or [],
        "invalidation_condition": opportunity.get("invalidation_condition") or "freshness_stale_or_edge_below_threshold",
        "review_time": (now + timedelta(hours=1)).isoformat(),
        "admission_state": admission_state,
        "rejection_reasons": admission.get("failed_gates") if admission_state == "REJECTED" else [],
        "abstention_reasons": admission.get("failed_gates") if admission_state == "ABSTAINED" else [],
        "why": why or _default_why(decision_state, net_edge, execution),
        "why_not": why_not or _default_why_not(admission),
        "methodology_versions": methodology_versions(),
        "scorecard": {
            "decision_state": decision_state,
            "expected_net_edge": net_edge.get("expected_net_edge_usd"),
            "realizable_net_edge": net_edge.get("realizable_net_edge_usd"),
            "execution_feasibility": execution.get("execution_feasibility_score"),
            "capacity": capacity.get("capacity_usd"),
            "opportunity_half_life": half_life.get("remaining_seconds") or half_life.get("expected_half_life_seconds"),
            "risk": pre.get("risk_after"),
            "portfolio_impact": pre.get("material_drivers"),
            "evidence_grade": evidence_grade.get("overall_grade"),
            "evidence_class": evidence_class,
            "freshness": freshness,
            "data_quality": quality,
            "uncertainty": interval,
            "simulation_result": opportunity.get("simulation_summary"),
            "calibration_status": (opportunity.get("calibration_summary") or {}).get("status"),
            "invalidation_condition": opportunity.get("invalidation_condition"),
            "review_time": (now + timedelta(hours=1)).isoformat(),
            "why": why or _default_why(decision_state, net_edge, execution),
            "why_not": why_not or _default_why_not(admission),
        },
    }


def _default_why(state: str, net_edge: dict[str, Any], execution: dict[str, Any]) -> list[str]:
    if state in {"REJECTED", "ABSTAINED"}:
        return []
    return [
        f"expected_net_edge_usd:{net_edge.get('expected_net_edge_usd')}",
        f"execution_feasibility:{execution.get('execution_feasibility_score')}",
    ]


def _default_why_not(admission: dict[str, Any]) -> list[str]:
    failed = admission.get("failed_gates") or []
    if not failed:
        return []
    return [f"failed_gate:{g}" for g in failed]
