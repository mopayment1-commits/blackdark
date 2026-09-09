"""Formal Net-Edge specification with cost autopsy and uncertainty (DTS-009–012)."""

from __future__ import annotations

from typing import Any

from decision_truth.methodology import METHODOLOGY_VERSIONS

COST_FIELDS = (
    "gross_edge",
    "trading_fees",
    "expected_slippage",
    "price_impact",
    "gas_network_fees",
    "funding",
    "borrow_cost",
    "withdrawal_deposit_fees",
    "bridge_costs",
    "fx_conversion_costs",
    "expected_opportunity_decay",
    "execution_latency_cost",
    "failed_partial_fill_cost",
    "hedging_cost",
)


def _na(reason: str) -> dict[str, Any]:
    return {"value": None, "status": "N/A", "reason": reason}


def _val(amount: float | None, *, source: str = "computed") -> dict[str, Any]:
    if amount is None:
        return _na("unavailable")
    return {"value": round(float(amount), 6), "status": "computed", "source": source}


def build_cost_autopsy(opportunity: dict[str, Any], economics: dict[str, Any]) -> dict[str, Any]:
    """Expose every material cost component — no silent zero defaults."""
    gross = economics.get("net_profit_usdt")
    if gross is None:
        gross = opportunity.get("gross_edge_usd") or opportunity.get("spread_usd")
    try:
        gross_f = float(gross) if gross is not None else None
    except (TypeError, ValueError):
        gross_f = None

    slippage_bps = economics.get("total_slippage_bps")
    notional = economics.get("notional_usd") or opportunity.get("quote_amount") or 1000.0
    try:
        notional_f = float(notional)
    except (TypeError, ValueError):
        notional_f = 1000.0
    slippage_usd = None
    if slippage_bps is not None:
        slippage_usd = notional_f * float(slippage_bps) / 10_000.0

    trading_fees = economics.get("trading_fees_usdt")
    withdrawal = economics.get("withdrawal_fee_usdt")
    latency = economics.get("latency_buffer_usd")
    crowd_decay = economics.get("residual_after_crowd_usd")
    decay_cost = None
    if gross_f is not None and crowd_decay is not None:
        decay_cost = max(0.0, gross_f - float(crowd_decay))

    components = {
        "gross_edge": _val(gross_f, source="opportunity"),
        "trading_fees": _val(float(trading_fees) if trading_fees is not None else None),
        "expected_slippage": _val(slippage_usd),
        "price_impact": _na("not_applicable_spot_arb") if not opportunity.get("price_impact_usd") else _val(float(opportunity["price_impact_usd"])),
        "gas_network_fees": _val(float(opportunity["gas_usd"])) if opportunity.get("gas_usd") is not None else _na("not_applicable_cex_route"),
        "funding": _val(float(opportunity["funding_cost_usd"])) if opportunity.get("funding_cost_usd") is not None else _na("not_applicable"),
        "borrow_cost": _na("not_applicable"),
        "withdrawal_deposit_fees": _val(float(withdrawal) if withdrawal is not None else None),
        "bridge_costs": _val(float(opportunity["bridge_cost_usd"])) if opportunity.get("bridge_cost_usd") is not None else _na("not_applicable"),
        "fx_conversion_costs": _na("usd_only_launch"),
        "expected_opportunity_decay": _val(decay_cost, source="crowd_decay"),
        "execution_latency_cost": _val(float(latency) if latency is not None else None),
        "failed_partial_fill_cost": _na("insufficient_fill_history"),
        "hedging_cost": _na("not_applicable"),
    }
    return {
        "components": components,
        "methodology_version": METHODOLOGY_VERSIONS["cost_autopsy"],
    }


def compute_formal_net_edge(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Canonical net-edge contract wrapping net_edge_truth with uncertainty + realizable edge."""
    from net_edge_truth import compute_net_edge_truth

    truth = compute_net_edge_truth(opportunity)
    economics = truth.get("economics") or {}
    cost_autopsy = build_cost_autopsy(opportunity, economics)

    expected = economics.get("truth_edge_usd")
    theoretical = economics.get("net_profit_usdt")
    realizable = economics.get("residual_after_crowd_usd")
    fill_prob = opportunity.get("fill_probability")
    if fill_prob is None and truth.get("executable") is False:
        fill_prob = 0.0
    elif fill_prob is None and expected is not None:
        fill_prob = min(1.0, max(0.0, float(truth.get("truth_score") or 0) / 100.0))

    realizable_edge = None
    if realizable is not None and fill_prob is not None:
        realizable_edge = float(realizable) * float(fill_prob)

    lower = upper = None
    if expected is not None:
        spread = abs(float(expected)) * 0.25 + 0.05
        lower = round(float(expected) - spread, 6)
        upper = round(float(expected) + spread, 6)

    return {
        "methodology_version": METHODOLOGY_VERSIONS["net_edge"],
        "theoretical_edge_usd": theoretical,
        "expected_net_edge_usd": expected,
        "realizable_net_edge_usd": realizable_edge,
        "net_edge_interval": {
            "lower_bound": lower,
            "upper_bound": upper,
            "method": "heuristic_spread_v1" if lower is not None else "unavailable",
            "confidence_context": "estimated" if lower is not None else "insufficient_data",
        },
        "fill_probability": fill_prob,
        "cost_autopsy": cost_autopsy,
        "truth": truth,
    }
