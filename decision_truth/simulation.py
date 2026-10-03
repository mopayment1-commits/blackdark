"""Institutional simulation beside decision (DTS-037, DTS-038, DTS-039, DTS-040)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p4-simulation-1.0"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def evaluate_simulation_context(
    payload: dict[str, Any],
    *,
    economics: dict[str, Any] | None = None,
    portfolio_context: dict[str, Any] | None = None,
    evidence_class: str | None = None,
) -> dict[str, Any]:
    """Link admitted decisions to canonical simulation context."""
    if payload.get("truth_indicative_only"):
        return {"state": "NOT_APPLICABLE", "reason": "advisory_only", "methodology_version": METHODOLOGY_VERSION}

    explicit = payload.get("simulation_context") or payload.get("institutional_simulation")
    if isinstance(explicit, dict) and explicit.get("results"):
        return _wrap_explicit(explicit, evidence_class=evidence_class, portfolio_context=portfolio_context)

    net = economics or {}
    notional = _optional_float(payload.get("quote_amount")) or 1000.0
    expected_edge = _optional_float(net.get("expected_net_edge_usd"))
    costs = _optional_float(net.get("total_costs_usd")) or 0.0
    slip_bps = _optional_float(payload.get("total_slippage_bps")) or 0.0
    capacity = (net.get("capacity") or {}).get("capacity_usd")

    methodology = {
        "in_sample_separation": {"state": "NOT_APPLICABLE", "reason": "single_opportunity_evaluation"},
        "out_of_sample": {"state": "UNAVAILABLE", "reason": "requires_historical_backtest_dataset"},
        "walk_forward": {"state": "UNAVAILABLE", "reason": "requires_historical_backtest_dataset"},
        "transaction_costs": {"state": "AVAILABLE", "value_usd": costs},
        "slippage": {"state": "AVAILABLE", "bps": slip_bps},
        "liquidity_capacity": {"state": "AVAILABLE" if capacity else "UNAVAILABLE", "capacity_usd": capacity},
        "latency": {"state": "AVAILABLE" if payload.get("quote_age_ms") else "UNAVAILABLE"},
        "regime_segmentation": {"state": "UNAVAILABLE", "reason": "insufficient_regime_labels"},
        "parameter_stability": {"state": "UNAVAILABLE", "reason": "no_parameter_search_run"},
        "sensitivity": {"state": "AVAILABLE", "note": "edge_uncertainty_from_net_edge"},
        "sample_adequacy": {"state": "UNAVAILABLE", "reason": "opportunity_level_not_portfolio_backtest"},
        "uncertainty": net.get("uncertainty") or {"state": "UNCERTAINTY_UNAVAILABLE"},
        "multiple_testing_awareness": {"state": "AVAILABLE", "control": "single_hypothesis_per_decision"},
        "overfitting_controls": {"state": "AVAILABLE", "control": "oos_required_for_institutional_claims"},
    }

    portfolio_sim = _portfolio_simulation(portfolio_context, expected_edge=expected_edge, notional=notional)

    if expected_edge is None:
        return {
            "state": "UNAVAILABLE",
            "reason": "missing_economics_for_simulation",
            "institutional_methodology": methodology,
            "portfolio_simulation": portfolio_sim,
            "methodology_version": METHODOLOGY_VERSION,
            "disclosures": _disclosures(evidence_class, sample_period=None),
            "timestamp_utc": _utc_now(),
        }

    return {
        "state": "AVAILABLE",
        "linkage_id": f"sim_{payload.get('symbol') or 'BTC'}_{int(datetime.now(UTC).timestamp())}",
        "expected_pnl_usd": expected_edge,
        "expected_pnl_range_usd": {
            "low": (net.get("uncertainty") or {}).get("low_usd"),
            "high": (net.get("uncertainty") or {}).get("high_usd"),
        },
        "notional_usd": notional,
        "institutional_methodology": methodology,
        "portfolio_simulation": portfolio_sim,
        "disclosures": _disclosures(evidence_class, sample_period="opportunity_level_proxy"),
        "methodology_version": METHODOLOGY_VERSION,
        "execution_mode": payload.get("simulation_execution_mode") or "inline_proxy",
        "timestamp_utc": _utc_now(),
        "live_validation": "LIVE_VALIDATION_PENDING",
    }


def _wrap_explicit(explicit: dict[str, Any], *, evidence_class: str | None, portfolio_context: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "state": "AVAILABLE",
        "linkage_id": explicit.get("linkage_id"),
        "results": explicit.get("results"),
        "institutional_methodology": explicit.get("institutional_methodology") or {},
        "portfolio_simulation": explicit.get("portfolio_simulation") or _portfolio_simulation(portfolio_context),
        "disclosures": explicit.get("disclosures") or _disclosures(evidence_class, sample_period=explicit.get("sample_period")),
        "methodology_version": METHODOLOGY_VERSION,
        "timestamp_utc": _utc_now(),
    }


def _portfolio_simulation(
    portfolio_context: dict[str, Any] | None,
    *,
    expected_edge: float | None = None,
    notional: float | None = None,
) -> dict[str, Any]:
    ctx = portfolio_context or {}
    if ctx.get("state") not in {"AVAILABLE", "PARTIAL"}:
        return {"state": "PORTFOLIO_SIMULATION_UNAVAILABLE", "reason": "portfolio_context_unavailable"}
    total = _optional_float(ctx.get("total_value_usd"))
    if total is None or expected_edge is None:
        return {"state": "PORTFOLIO_SIMULATION_UNAVAILABLE", "reason": "insufficient_portfolio_or_edge_data"}
    impact_pct = (expected_edge / max(total, 1.0)) * 100.0
    return {
        "state": "AVAILABLE",
        "expected_pnl_usd": expected_edge,
        "expected_pnl_range_usd": None,
        "portfolio_impact_pct": round(impact_pct, 6),
        "drawdown_proxy_pct": round(max(0.0, -impact_pct), 6),
        "sharpe_equivalent": {"state": "UNAVAILABLE", "reason": "insufficient_return_series"},
        "breakeven_notional_usd": notional,
        "risk_budget_impact": {"state": "AVAILABLE", "note": "see_portfolio_pre_impact"},
        "capacity_limit_usd": None,
        "uncertainty": {"state": "UNAVAILABLE", "reason": "portfolio_return_series_required"},
        "methodology_version": METHODOLOGY_VERSION,
    }


def _disclosures(evidence_class: str | None, *, sample_period: str | None) -> dict[str, Any]:
    return {
        "nature": "historical_or_simulated_proxy",
        "no_future_guarantee": True,
        "methodology_version": METHODOLOGY_VERSION,
        "sample_period": sample_period or "not_applicable",
        "assumptions": ["costs_from_net_edge_truth", "not_live_outcome"],
        "cost_model": "decision_truth_net_edge_v1",
        "evidence_class": evidence_class or "UNAVAILABLE",
        "limitations": ["opportunity_level_proxy", "not_full_institutional_backtest_unless_explicit_context"],
        "wording_policy": "must_not_imply_live_outcome",
    }
