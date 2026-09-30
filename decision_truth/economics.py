"""Economic reality stage for Decision Truth (P2 economic/execution truth)."""

from __future__ import annotations

from typing import Any

from decision_truth.capacity import estimate_opportunity_capacity
from decision_truth.execution_feasibility import evaluate_execution_feasibility
from decision_truth.half_life import evaluate_opportunity_half_life
from decision_truth.net_edge import evaluate_formal_net_edge


def economic_reality(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Canonical economic reality pack: net edge, execution, capacity, half-life."""
    opp = dict(opportunity or {})
    if opp.get("truth_indicative_only"):
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

    net_edge = evaluate_formal_net_edge(opp)
    execution = evaluate_execution_feasibility(opp, economics=net_edge)
    capacity = estimate_opportunity_capacity(opp, economics=net_edge)
    enriched = evaluate_opportunity_half_life(opp)
    half_life = enriched.get("opportunity_half_life") or {}

    reject = bool(net_edge.get("reject"))
    if execution.get("state") == "EXECUTION_FEASIBILITY_UNAVAILABLE":
        reject = True
    if net_edge.get("state") == "UNAVAILABLE":
        reject = True

    return {
        **net_edge,
        "execution_feasibility": execution,
        "capacity": capacity,
        "opportunity_half_life": half_life,
        "reject": reject,
        "pass": not reject,
        "economics_integrated": True,
    }
