"""Material change detection for Decision Truth surfaces."""

from __future__ import annotations

from typing import Any


def detect_material_changes(
    current: dict[str, Any],
    previous: dict[str, Any] | None = None,
    *,
    threshold_score_delta: float = 5.0,
) -> list[dict[str, Any]]:
    """Return material deltas between decision snapshots."""
    if not previous:
        return []
    changes: list[dict[str, Any]] = []
    cur_score = float(current.get("opportunity_score") or 0)
    prev_score = float(previous.get("opportunity_score") or 0)
    if abs(cur_score - prev_score) >= threshold_score_delta:
        changes.append(
            {
                "field": "opportunity_score",
                "previous": prev_score,
                "current": cur_score,
                "material": True,
            }
        )
    cur_verdict = str(current.get("verdict") or "")
    prev_verdict = str(previous.get("verdict") or "")
    if cur_verdict and prev_verdict and cur_verdict != prev_verdict:
        changes.append(
            {
                "field": "verdict",
                "previous": prev_verdict,
                "current": cur_verdict,
                "material": True,
            }
        )
    cur_state = current.get("data_governance_state") or (current.get("data_governance") or {}).get("gates", {}).get("data_governance_state")
    prev_state = previous.get("data_governance_state")
    if cur_state and prev_state and cur_state != prev_state:
        changes.append(
            {
                "field": "data_governance_state",
                "previous": prev_state,
                "current": cur_state,
                "material": True,
            }
        )
    return changes
