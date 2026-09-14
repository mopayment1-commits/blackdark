"""Decision Change Detector (DTS-023, DTS-060)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from decision_truth.methodology_versions import DTS_METHODOLOGY_VERSIONS


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_MATERIAL_FIELDS = (
    "decision_state",
    "decision_truth_state",
    "evidence_class",
    "grade",
    "verdict",
    "admission_state",
    "data_governance_state",
    "failure_state",
)


def detect_decision_changes(
    current: dict[str, Any],
    previous: dict[str, Any] | None = None,
    *,
    previous_decision_state: str | None = None,
) -> list[dict[str, Any]]:
    """Detect material lifecycle changes beyond score delta."""
    if not previous and not previous_decision_state:
        return []

    changes: list[dict[str, Any]] = []
    prev_state = previous_decision_state or (previous or {}).get("decision_truth_state") or (previous or {}).get("decision_state")
    cur_state = current.get("decision_truth_state") or current.get("decision_state")
    if prev_state and cur_state and str(prev_state) != str(cur_state):
        changes.append(_change("decision_state", prev_state, cur_state, material=True, reason="state_transition"))

    if previous:
        for field in _MATERIAL_FIELDS:
            prev_val = previous.get(field)
            cur_val = current.get(field)
            if field == "decision_state":
                continue
            if prev_val is not None and cur_val is not None and str(prev_val) != str(cur_val):
                changes.append(_change(field, prev_val, cur_val, material=True, reason="semantic_field_change"))

        prev_ec = (previous.get("decision_truth") or {}).get("contract", {}).get("evidence_class")
        cur_ec = (current.get("decision_truth") or {}).get("contract", {}).get("evidence_class")
        if prev_ec and cur_ec and prev_ec != cur_ec:
            changes.append(_change("evidence_class", prev_ec, cur_ec, material=True, reason="evidence_class_change"))

        prev_grade = (previous.get("decision_truth") or {}).get("contract", {}).get("grade")
        cur_grade = (current.get("decision_truth") or {}).get("contract", {}).get("grade")
        if prev_grade and cur_grade and prev_grade != cur_grade:
            changes.append(_change("grade", prev_grade, cur_grade, material=True, reason="grade_change"))

        cur_score = float(current.get("opportunity_score") or 0)
        prev_score = float(previous.get("opportunity_score") or 0)
        if abs(cur_score - prev_score) >= 5.0:
            changes.append(_change("opportunity_score", prev_score, cur_score, material=False, reason="score_delta"))

    return [c for c in changes if c.get("material")]


def _change(field: str, previous: Any, current: Any, *, material: bool, reason: str) -> dict[str, Any]:
    return {
        "field": field,
        "previous": previous,
        "current": current,
        "material": material,
        "materiality": "high" if material else "low",
        "reason": reason,
        "timestamp_utc": _utc_now(),
        "methodology_version": DTS_METHODOLOGY_VERSIONS["change_detector"],
        "evidence_delta": {"previous": previous, "current": current},
    }
