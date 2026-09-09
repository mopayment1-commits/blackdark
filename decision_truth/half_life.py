"""Opportunity half-life wrapper (DTS-015)."""

from __future__ import annotations

from typing import Any

from decision_truth.methodology import METHODOLOGY_VERSIONS


def attach_half_life(opportunity: dict[str, Any]) -> dict[str, Any]:
    half = opportunity.get("opportunity_half_life")
    if isinstance(half, dict) and half.get("error"):
        return {
            "status": "unavailable",
            "reason": "insufficient_history",
            "methodology_version": METHODOLOGY_VERSIONS["half_life"],
        }
    if isinstance(half, dict):
        return {
            **half,
            "methodology_version": METHODOLOGY_VERSIONS["half_life"],
            "status": "estimated",
        }
    return {
        "status": "unavailable",
        "reason": "not_computed",
        "methodology_version": METHODOLOGY_VERSIONS["half_life"],
    }
