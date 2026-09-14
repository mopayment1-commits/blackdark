"""Economic reality stage for Decision Truth."""

from __future__ import annotations

from typing import Any


def economic_reality(opportunity: dict[str, Any]) -> dict[str, Any]:
    if opportunity.get("truth_indicative_only"):
        return {
            "enabled": True,
            "mode": "directional_advisory",
            "reject": False,
            "pass": True,
            "executable": False,
            "truth_score": None,
            "label": "ADVISORY_NOT_EXECUTABLE",
            "state": "NOT_APPLICABLE",
        }
    try:
        from net_edge_truth import compute_net_edge_truth

        return compute_net_edge_truth(opportunity)
    except Exception as exc:
        return {
            "reject": True,
            "truth_score": 0.0,
            "error": str(exc),
            "reason": "net_edge_unavailable",
            "state": "UNAVAILABLE",
        }
