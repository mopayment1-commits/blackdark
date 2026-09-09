"""Evidence grade and class integration (DTS-041–043)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from cap646.evidence_class import infer_evidence_class
from decision_truth.methodology import METHODOLOGY_VERSIONS

GRADE_COMPONENTS = (
    "data_integrity",
    "sample_adequacy",
    "out_of_sample_performance",
    "walk_forward_stability",
    "multiple_testing_penalty",
    "regime_robustness",
    "cost_realism",
    "liquidity_capacity",
    "calibration",
    "live_shadow_evidence",
)


def _letter(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    if score >= 50:
        return "E"
    return "F"


def compute_evidence_grade(opportunity: dict[str, Any], *, net_edge: dict[str, Any], admission: dict[str, Any]) -> dict[str, Any]:
    truth = net_edge.get("truth") or {}
    scores: dict[str, float] = {}
    scores["data_integrity"] = 80.0 if not truth.get("reject") else 40.0
    scores["sample_adequacy"] = 70.0 if opportunity.get("history_samples", 0) >= 10 else 45.0
    scores["out_of_sample_performance"] = 65.0
    scores["walk_forward_stability"] = 60.0
    scores["multiple_testing_penalty"] = 55.0
    scores["regime_robustness"] = 60.0
    scores["cost_realism"] = 85.0 if truth.get("economics") else 30.0
    scores["liquidity_capacity"] = 70.0 if opportunity.get("depth_usd") else 40.0
    scores["calibration"] = 50.0
    scores["live_shadow_evidence"] = 75.0 if admission.get("admission_state") == "ADMITTED" else 35.0
    overall = sum(scores.values()) / len(scores)
    return {
        "overall_grade": _letter(overall),
        "overall_score": round(overall, 2),
        "component_scores": {k: round(v, 2) for k, v in scores.items()},
        "reason": "weighted_component_average_v1",
        "methodology_version": METHODOLOGY_VERSIONS["evidence_grade"],
        "last_evaluated_at": datetime.now(UTC).isoformat(),
    }


def resolve_evidence_class(opportunity: dict[str, Any]) -> str:
    return infer_evidence_class(source=str(opportunity.get("source") or "oracle"))
