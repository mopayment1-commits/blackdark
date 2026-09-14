"""DTS-046 — NO DECISION as first-class product state."""

from __future__ import annotations

from typing import Any


def build_no_decision_surface(payload: dict[str, Any], *, why_not_engine: dict[str, Any] | None = None) -> dict[str, Any]:
    """Surface NO DECISION / ABSTAINED as governed capability, not error."""
    state = str(payload.get("decision_truth_state") or "")
    action = str(payload.get("decision_action") or "")
    is_no_decision = action == "NO_DECISION" or state in {"REJECTED", "ABSTAINED", "UNAVAILABLE", "DEGRADED"}

    why = why_not_engine or ((payload.get("decision_truth") or {}).get("why_not") or {})
    machine = why.get("machine_readable") or {}
    codes = list(why.get("codes") or machine.get("reason_codes") or [])

    reconsider: list[str] = []
    if machine.get("freshness_state", {}).get("state") in {"STALE", "UNKNOWN"}:
        reconsider.append("fresh_inputs_required")
    if any("conflict" in c.lower() for c in codes):
        reconsider.append("source_conflict_resolution")
    if machine.get("evidence_state", {}).get("grade") in {"UNAVAILABLE", "F", None}:
        reconsider.append("sufficient_evidence_grade")
    if machine.get("uncertainty_calibration_state", {}).get("high_uncertainty"):
        reconsider.append("lower_uncertainty_or_wider_interval")

    return {
        "first_class_state": True,
        "hidden_as_error": False,
        "decision_action": action or ("NO_DECISION" if is_no_decision else "AVAILABLE"),
        "decision_truth_state": state,
        "is_no_decision": is_no_decision,
        "reason": why.get("human_explanation") or _default_reason(state, codes),
        "evidence_gap": _evidence_gap(machine),
        "conflict": any("conflict" in c.lower() for c in codes),
        "stale_state": machine.get("freshness_state", {}).get("state") in {"STALE", "UNKNOWN"},
        "uncertainty": machine.get("uncertainty_calibration_state"),
        "what_would_be_needed_to_reconsider": reconsider or ["mandatory_gates_must_pass"],
        "methodology_version": "dts-p5-no-decision-1.0",
    }


def _default_reason(state: str, codes: list[str]) -> str:
    if state == "ABSTAINED":
        return "NO DECISION — insufficient evidence to admit this opportunity."
    if state == "REJECTED":
        return f"NO DECISION — rejected ({', '.join(codes[:3]) or 'gate failure'})."
    if state == "DEGRADED":
        return "NO DECISION — degraded confidence; mandatory safety conditions not fully met."
    return "Decision available."


def _evidence_gap(machine: dict[str, Any]) -> dict[str, Any] | None:
    ev = machine.get("evidence_state") or {}
    if ev.get("grade") in {"UNAVAILABLE", "F"} or ev.get("lifecycle_state") == "UNAVAILABLE":
        return {"grade": ev.get("grade"), "evidence_class": ev.get("evidence_class")}
    return None
