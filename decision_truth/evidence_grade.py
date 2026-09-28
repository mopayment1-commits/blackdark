"""Evidence Grade A–F methodology (DTS-041, DTS-042)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p4-evidence-grade-1.0"

COMPONENTS = (
    "data_integrity",
    "sample_adequacy",
    "oos_performance",
    "walk_forward_stability",
    "multiple_testing_penalty",
    "regime_robustness",
    "cost_realism",
    "liquidity_capacity",
    "calibration",
    "live_shadow_evidence",
)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _score_component(state: str | None, value: float | None = None) -> dict[str, Any]:
    if state in {"UNAVAILABLE", "CALIBRATION_INSUFFICIENT_DATA", "CALIBRATION_WEAK"}:
        return {"state": "UNAVAILABLE", "score": None, "reason": state}
    if state == "NOT_APPLICABLE":
        return {"state": "NOT_APPLICABLE", "score": None, "reason": "not_applicable"}
    if value is not None:
        return {"state": "AVAILABLE", "score": round(max(0.0, min(100.0, value)), 2)}
    if state == "AVAILABLE":
        return {"state": "AVAILABLE", "score": 70.0}
    return {"state": "UNAVAILABLE", "score": None, "reason": "missing_evidence"}


def evaluate_evidence_grade(
    payload: dict[str, Any],
    *,
    economics: dict[str, Any] | None = None,
    calibration: dict[str, Any] | None = None,
    simulation: dict[str, Any] | None = None,
    evidence_class: str | None = None,
) -> dict[str, Any]:
    """Compute explainable evidence grade without hardcoded defaults."""
    econ = economics or {}
    cal = calibration or {}
    sim = simulation or {}

    dq = _optional_float(payload.get("data_quality_score"))
    components = {
        "data_integrity": _score_component("AVAILABLE" if dq and dq >= 60 else "UNAVAILABLE", dq),
        "sample_adequacy": _score_component(sim.get("institutional_methodology", {}).get("sample_adequacy", {}).get("state")),
        "oos_performance": _score_component(sim.get("institutional_methodology", {}).get("out_of_sample", {}).get("state")),
        "walk_forward_stability": _score_component(sim.get("institutional_methodology", {}).get("walk_forward", {}).get("state")),
        "multiple_testing_penalty": _score_component("AVAILABLE", 75.0 if sim.get("state") == "AVAILABLE" else None),
        "regime_robustness": _score_component(sim.get("institutional_methodology", {}).get("regime_segmentation", {}).get("state")),
        "cost_realism": _score_component("AVAILABLE" if econ.get("cost_autopsy") else "UNAVAILABLE", 80.0 if econ.get("total_costs_usd") is not None else None),
        "liquidity_capacity": _score_component((econ.get("capacity") or {}).get("state"), 75.0 if (econ.get("capacity") or {}).get("capacity_usd") else None),
        "calibration": _score_component(cal.get("state"), 85.0 if cal.get("state") == "AVAILABLE" else (55.0 if cal.get("state") == "CALIBRATION_WEAK" else None)),
        "live_shadow_evidence": _score_component(
            "AVAILABLE" if evidence_class in {"SHADOW_LIVE_FORWARD", "PRODUCTION_VERIFIED"} else "UNAVAILABLE",
            90.0 if evidence_class == "PRODUCTION_VERIFIED" else (75.0 if evidence_class == "SHADOW_LIVE_FORWARD" else None),
        ),
    }

    scored = [c["score"] for c in components.values() if c.get("score") is not None]
    if len(scored) < 4:
        return {
            "state": "UNAVAILABLE",
            "overall_grade": "UNAVAILABLE",
            "components": components,
            "reason_codes": ["insufficient_component_evidence"],
            "methodology_version": METHODOLOGY_VERSION,
            "evaluated_at_utc": _utc_now(),
        }

    avg = sum(scored) / len(scored)
    grade = _to_letter(avg)
    return {
        "state": "AVAILABLE",
        "overall_grade": grade,
        "average_score": round(avg, 2),
        "components": components,
        "reason_codes": _grade_reasons(components, grade),
        "methodology_version": METHODOLOGY_VERSION,
        "evaluated_at_utc": _utc_now(),
    }


def _to_letter(avg: float) -> str:
    if avg >= 90:
        return "A"
    if avg >= 80:
        return "B"
    if avg >= 70:
        return "C"
    if avg >= 60:
        return "D"
    if avg >= 50:
        return "E"
    return "F"


def _grade_reasons(components: dict[str, dict[str, Any]], grade: str) -> list[str]:
    reasons = [f"overall_grade_{grade}"]
    for name, comp in components.items():
        if comp.get("state") == "UNAVAILABLE":
            reasons.append(f"{name}_unavailable")
    return reasons


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None
