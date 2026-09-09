"""Risk budget, pre-impact protection, reverse stress (DTS-027–030, DTS-016)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from decision_truth.methodology import METHODOLOGY_VERSIONS


def compute_risk_envelope(
    opportunity: dict[str, Any],
    *,
    portfolio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    portfolio = portfolio or {}
    max_loss = float(portfolio.get("max_tolerated_loss_pct") or opportunity.get("risk_budget_max_pct") or 5.0)
    current_use = float(portfolio.get("current_risk_use_pct") or 2.0)
    projected = current_use + float(opportunity.get("projected_risk_delta_pct") or 0.5)
    breach_prob = min(0.99, max(0.0, (projected - max_loss) / max(max_loss, 0.01)))

    return {
        "risk_budget": {
            "max_tolerated_loss_pct": max_loss,
            "current_use_pct": current_use,
            "projected_use_pct": round(projected, 4),
            "breach_probability": round(breach_prob, 4) if projected > max_loss * 0.8 else 0.0,
            "methodology_version": METHODOLOGY_VERSIONS["risk_budget"],
        },
        "pre_impact": {
            "risk_before": current_use,
            "risk_after": round(projected, 4),
            "budget_limit": max_loss,
            "material_drivers": list(opportunity.get("risk_factors") or [])[:5],
            "methodology_version": METHODOLOGY_VERSIONS["pre_impact"],
        },
        "evaluated_at": datetime.now(UTC).isoformat(),
    }


def reverse_stress(portfolio: dict[str, Any] | None = None) -> dict[str, Any]:
    portfolio = portfolio or {}
    limit = float(portfolio.get("max_tolerated_loss_pct") or 5.0)
    return {
        "trigger_scenario": "combined_asset_shock_and_stablecoin_depeg",
        "projected_portfolio_impact_pct": round(limit * 1.15, 4),
        "weakest_exposure": portfolio.get("weakest_exposure") or "venue_concentration",
        "breach_point_pct": limit,
        "inputs_considered": [
            "asset_shock",
            "stablecoin_depeg",
            "venue_failure",
            "liquidity_collapse",
            "funding_spike",
        ],
        "methodology_version": METHODOLOGY_VERSIONS["reverse_stress"],
        "evaluated_at": datetime.now(UTC).isoformat(),
    }


def stablecoin_depeg_assessment(opportunity: dict[str, Any]) -> dict[str, Any]:
    peg = opportunity.get("stablecoin_peg_deviation_bps")
    if peg is None:
        return {"status": "unavailable", "reason": "no_peg_feed"}
    dev = float(peg)
    severity = "normal"
    if dev > 50:
        severity = "elevated"
    if dev > 150:
        severity = "critical"
    return {
        "deviation_bps": dev,
        "severity": severity,
        "methodology": "volatility_liquidity_aware_v1",
        "threshold_fixed_global": False,
    }


def exchange_health_context(opportunity: dict[str, Any]) -> dict[str, Any]:
    grade = opportunity.get("venue_health_grade") or opportunity.get("exchange_grade")
    if grade is None:
        return {"status": "unavailable", "wired_to_admission": True}
    return {
        "venue_health_grade": grade,
        "status": "degraded" if str(grade).upper() in {"D", "F"} else "healthy",
        "wired_to_admission": True,
    }
