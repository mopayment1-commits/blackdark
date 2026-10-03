"""Material change detection for Decision Truth surfaces."""

from __future__ import annotations

from typing import Any

from decision_truth.change_detector import detect_decision_changes


def detect_material_changes(
    current: dict[str, Any],
    previous: dict[str, Any] | None = None,
    *,
    threshold_score_delta: float = 5.0,
) -> list[dict[str, Any]]:
    """Backward-compatible facade to canonical change detector."""
    return detect_decision_changes(current, previous)
