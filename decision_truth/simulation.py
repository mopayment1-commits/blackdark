"""Institutional simulation summary (DTS-037–040)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from decision_truth.methodology import METHODOLOGY_VERSIONS


def simulation_summary(opportunity: dict[str, Any]) -> dict[str, Any]:
    existing = opportunity.get("simulation_summary")
    if isinstance(existing, dict) and existing.get("methodology_version"):
        return existing
    return {
        "status": "available_on_request",
        "historical_simulated": True,
        "methodology_version": METHODOLOGY_VERSIONS["simulation"],
        "sample_period": opportunity.get("simulation_period") or "walk_forward_90d",
        "assumptions": ["realistic_fees", "slippage_model_v1", "capacity_limits"],
        "cost_model": "net_edge_v2",
        "evidence_class": opportunity.get("evidence_class") or "BACKTESTED",
        "limitations": ["no_future_guarantee", "regime_shift_risk"],
        "metrics": {
            "expected_pnl": opportunity.get("sim_expected_pnl"),
            "max_drawdown": opportunity.get("sim_max_drawdown"),
            "sharpe": opportunity.get("sim_sharpe"),
            "breakeven": opportunity.get("sim_breakeven"),
        },
        "evaluated_at": datetime.now(UTC).isoformat(),
    }
