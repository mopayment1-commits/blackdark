"""Signal Admission Gate — mandatory pipeline gate (DTS-017)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from decision_truth.methodology import METHODOLOGY_VERSIONS
from failure.decision import DecisionSafetyState, evaluate_decision_safety
from failure.freshness import FreshnessEvidence, FreshnessState, classify_freshness
from failure.quality import DataQualityState, classify_quality


class AdmissionState(StrEnum):
    ADMITTED = "ADMITTED"
    DEGRADED = "DEGRADED"
    REJECTED = "REJECTED"
    ABSTAINED = "ABSTAINED"


GATE_NAMES = (
    "freshness",
    "data_quality",
    "evidence",
    "liquidity",
    "execution_feasibility",
    "net_edge",
    "risk",
    "uncertainty",
)


def evaluate_admission_gate(
    opportunity: dict[str, Any],
    *,
    net_edge: dict[str, Any],
    execution: dict[str, Any],
    capacity: dict[str, Any],
    risk: dict[str, Any],
    evidence_grade: dict[str, Any],
) -> dict[str, Any]:
    dg = opportunity.get("data_governance") or {}
    dg_fresh = dg.get("freshness") or {}
    dg_quality = dg.get("quality") or {}
    age_ms = ((net_edge.get("truth") or {}).get("economics") or {}).get("quote_age_ms")
    age_sec = dg_fresh.get("age_seconds")
    if age_sec is None and age_ms:
        age_sec = float(age_ms) / 1000.0
    freshness = classify_freshness(age_seconds=float(age_sec) if age_sec is not None else None)
    if dg_fresh.get("freshness_state"):
        try:
            freshness = FreshnessEvidence(
                state=FreshnessState(dg_fresh["freshness_state"]),
                age_seconds=freshness.age_seconds,
                last_successful_update=freshness.last_successful_update,
            )
        except Exception:
            pass
    conflicting = bool((opportunity.get("dimension_conflict") or {}).get("veto"))
    quality = classify_quality(
        partial=bool(opportunity.get("partial_data")),
        conflicting=conflicting or bool((dg.get("reconciliation") or {}).get("conflict")),
        source_count=int(opportunity.get("source_count") or 1),
    )
    if dg_quality.get("quality_state"):
        try:
            from failure.quality import DataQuality

            quality = DataQuality(state=DataQualityState(dg_quality["quality_state"]))
        except Exception:
            pass
    safety = evaluate_decision_safety(
        freshness=freshness.state,
        quality=quality.state,
        source_count=int(opportunity.get("source_count") or 1),
        conflicting=conflicting,
    )

    gates: dict[str, dict[str, Any]] = {}
    gates["freshness"] = {"pass": freshness.state not in {FreshnessState.STALE, FreshnessState.UNKNOWN}, "state": freshness.state.value}
    gates["data_quality"] = {"pass": quality.state not in {DataQualityState.CONFLICTING, DataQualityState.INSUFFICIENT}, "state": quality.state.value}
    gates["evidence"] = {"pass": evidence_grade.get("overall_grade") not in {"F", "E"}, "grade": evidence_grade.get("overall_grade")}
    gates["liquidity"] = {"pass": capacity.get("status") != "unavailable" or capacity.get("capacity_usd"), "capacity_usd": capacity.get("capacity_usd")}
    gates["execution_feasibility"] = {"pass": float(execution.get("execution_feasibility_score") or 0) >= 40.0, "score": execution.get("execution_feasibility_score")}
    truth = net_edge.get("truth") or {}
    gates["net_edge"] = {"pass": not truth.get("reject"), "expected_usd": net_edge.get("expected_net_edge_usd")}
    pre = risk.get("pre_impact") or {}
    gates["risk"] = {"pass": float(pre.get("risk_after") or 0) <= float(pre.get("budget_limit") or 100), "risk_after": pre.get("risk_after")}
    interval = net_edge.get("net_edge_interval") or {}
    gates["uncertainty"] = {"pass": interval.get("method") != "unavailable", "method": interval.get("method")}

    dg_gates = (dg.get("gates") or {})
    if dg_gates.get("data_governance_state") == "ABSTAINED" or opportunity.get("data_governance_state") == "ABSTAINED":
        gates["data_governance"] = {"pass": False, "state": "ABSTAINED"}
    elif dg_gates.get("failed_gates") or opportunity.get("data_governance_failed_gates"):
        failed_dg = dg_gates.get("failed_gates") or opportunity.get("data_governance_failed_gates") or []
        gates["data_governance"] = {"pass": False, "failed": failed_dg}
    else:
        prov_score = ((dg.get("provenance") or {}).get("provenance_score"))
        gates["data_governance"] = {
            "pass": prov_score is None or float(prov_score) >= 40,
            "provenance_score": prov_score,
        }

    failed = [name for name, g in gates.items() if not g.get("pass")]
    if safety.decision_state == DecisionSafetyState.ABSTAINED:
        state = AdmissionState.ABSTAINED
    elif safety.decision_state == DecisionSafetyState.UNAVAILABLE:
        state = AdmissionState.ABSTAINED
    elif truth.get("reject") or "net_edge" in failed:
        state = AdmissionState.REJECTED
    elif failed:
        state = AdmissionState.DEGRADED
    else:
        state = AdmissionState.ADMITTED

    return {
        "admission_state": state.value,
        "gates": gates,
        "failed_gates": failed,
        "evidence_context": safety.to_dict(),
        "methodology_version": METHODOLOGY_VERSIONS["admission_gate"],
    }
