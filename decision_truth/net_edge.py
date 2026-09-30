"""Formal Net Edge contract (DTS-009, DTS-010, DTS-011, DTS-012, DTS-006)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Literal

from decision_truth.precision import guard_precision

logger = logging.getLogger("BLACKDARK.DecisionTruth.NetEdge")

METHODOLOGY_VERSION = "dts-p2-net-edge-1.0"

ComponentState = Literal["AVAILABLE", "UNAVAILABLE", "NOT_APPLICABLE", "UNKNOWN"]

_COMPONENT_IDS = (
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


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _component(
    component_id: str,
    *,
    value: float | None = None,
    low: float | None = None,
    high: float | None = None,
    state: ComponentState,
    applicable: bool,
    source: str,
    reason: str | None = None,
    methodology: str = METHODOLOGY_VERSION,
    uncertainty: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return guard_precision(
        {
            "component": component_id,
            "state": state,
            "applicable": applicable,
            "value_usd": value,
            "range_usd": {"low": low, "high": high} if low is not None or high is not None else None,
            "source": source,
            "timestamp_utc": _utc_now(),
            "methodology_version": methodology,
            "uncertainty": uncertainty,
            "reason": reason,
        }
    )


def _kind(opportunity: dict[str, Any]) -> str:
    return str(opportunity.get("kind") or opportunity.get("opportunity_kind") or "cross_exchange").lower()


def _notional(opportunity: dict[str, Any]) -> float | None:
    for key in ("quote_amount", "notional_usd", "quote_usd"):
        val = _optional_float(opportunity.get(key))
        if val is not None and val > 0:
            return val
    return None


def _applicability(kind: str, opportunity: dict[str, Any]) -> dict[str, bool]:
    cex = kind in {"cross_exchange", "triangular", "spot_futures", "basis", "funding", "oracle_direction"}
    dex = kind in {"cex_dex", "dex_swap", "bridge_arb"}
    funding = kind in {"funding", "spot_futures", "basis"}
    borrow = kind in {"spot_futures", "basis", "margin"}
    bridge = kind in {"cex_dex", "bridge_arb", "cross_chain"}
    return {
        "gross_edge": True,
        "trading_fees": cex or dex,
        "expected_slippage": cex or dex,
        "price_impact": cex or dex,
        "gas_network_fees": dex,
        "funding": funding,
        "borrow_cost": borrow,
        "withdrawal_deposit_fees": kind in {"cross_exchange", "triangular", "cex_dex"},
        "bridge_costs": bridge,
        "fx_conversion_costs": kind in {"fx_arb"} or bool(opportunity.get("requires_fx_conversion")),
        "expected_opportunity_decay": cex or dex,
        "execution_latency_cost": cex or dex,
        "failed_partial_fill_cost": cex or dex,
        "hedging_cost": kind in {"basis", "spot_futures", "hedged_arb"},
    }


def _gross_edge(opportunity: dict[str, Any], notional: float | None) -> dict[str, Any]:
    gross_bps = _optional_float(opportunity.get("gross_edge_bps") or opportunity.get("spread_bps"))
    if gross_bps is not None and notional is not None:
        return _component(
            "gross_edge",
            value=notional * gross_bps / 10_000.0,
            state="AVAILABLE",
            applicable=True,
            source="opportunity.gross_edge_bps",
        )
    net = _optional_float(opportunity.get("net_profit_usdt") or opportunity.get("net_profit"))
    fees = _optional_float(opportunity.get("trading_fees_usdt") or opportunity.get("fees_usdt")) or 0.0
    slip_bps = _optional_float(opportunity.get("total_slippage_bps") or opportunity.get("slippage_bps"))
    withdrawal = _optional_float(opportunity.get("withdrawal_fee_usdt"))
    if net is not None:
        reconstruct = net
        if fees:
            reconstruct += fees
        if withdrawal is not None:
            reconstruct += withdrawal
        if slip_bps is not None and notional is not None:
            reconstruct += notional * slip_bps / 10_000.0
        return _component("gross_edge", value=reconstruct, state="AVAILABLE", applicable=True, source="reconstructed_from_net")
    return _component("gross_edge", state="UNAVAILABLE", applicable=True, source="none", reason="missing_gross_edge_inputs")


def _trading_fees(opportunity: dict[str, Any], applicable: bool) -> dict[str, Any]:
    if not applicable:
        return _component("trading_fees", state="NOT_APPLICABLE", applicable=False, source="kind_policy", reason="not_applicable_for_kind")
    raw = opportunity.get("trading_fees_usdt", opportunity.get("fees_usdt"))
    val = _optional_float(raw)
    if val is None and "trading_fees_usdt" not in opportunity and "fees_usdt" not in opportunity:
        return _component("trading_fees", state="UNAVAILABLE", applicable=True, source="none", reason="missing_trading_fees_evidence")
    if val is None:
        return _component("trading_fees", state="UNKNOWN", applicable=True, source="opportunity", reason="invalid_trading_fees")
    return _component("trading_fees", value=val, state="AVAILABLE", applicable=True, source="opportunity.trading_fees_usdt")


def _slippage(opportunity: dict[str, Any], notional: float | None, applicable: bool) -> dict[str, Any]:
    if not applicable:
        return _component("expected_slippage", state="NOT_APPLICABLE", applicable=False, source="kind_policy", reason="not_applicable_for_kind")
    bps = _optional_float(opportunity.get("total_slippage_bps") or opportunity.get("slippage_bps"))
    if bps is None:
        return _component("expected_slippage", state="UNAVAILABLE", applicable=True, source="none", reason="missing_slippage_bps")
    if notional is None:
        return _component("expected_slippage", state="UNAVAILABLE", applicable=True, source="none", reason="missing_notional_for_slippage")
    mid = notional * bps / 10_000.0
    return _component(
        "expected_slippage",
        value=mid,
        low=mid * 0.85,
        high=mid * 1.35,
        state="AVAILABLE",
        applicable=True,
        source="opportunity.total_slippage_bps",
        uncertainty={"method": "bps_range_heuristic", "confidence": "medium"},
    )


def _price_impact(opportunity: dict[str, Any], notional: float | None, applicable: bool) -> dict[str, Any]:
    if not applicable:
        return _component("price_impact", state="NOT_APPLICABLE", applicable=False, source="kind_policy", reason="not_applicable_for_kind")
    impact_bps = _optional_float(opportunity.get("price_impact_bps") or opportunity.get("impact_bps"))
    if impact_bps is None:
        depth = _optional_float(opportunity.get("depth_usd") or opportunity.get("liquidity_usd"))
        if depth is None or notional is None:
            return _component("price_impact", state="UNAVAILABLE", applicable=True, source="none", reason="missing_depth_for_impact")
        impact_bps = min(50.0, max(0.0, (notional / max(depth, 1.0)) * 100.0))
        return _component(
            "price_impact",
            value=notional * impact_bps / 10_000.0,
            low=0.0,
            high=notional * min(50.0, impact_bps * 2.0) / 10_000.0,
            state="AVAILABLE",
            applicable=True,
            source="depth_heuristic",
            uncertainty={"method": "depth_ratio_heuristic", "confidence": "low"},
        )
    if notional is None:
        return _component("price_impact", state="UNAVAILABLE", applicable=True, source="none", reason="missing_notional")
    val = notional * impact_bps / 10_000.0
    return _component("price_impact", value=val, state="AVAILABLE", applicable=True, source="opportunity.price_impact_bps")


def _simple_usd_component(
    component_id: str,
    opportunity: dict[str, Any],
    keys: tuple[str, ...],
    applicable: bool,
    *,
    reason_na: str = "not_applicable_for_kind",
) -> dict[str, Any]:
    if not applicable:
        return _component(component_id, state="NOT_APPLICABLE", applicable=False, source="kind_policy", reason=reason_na)
    for key in keys:
        if key in opportunity:
            val = _optional_float(opportunity.get(key))
            if val is None:
                return _component(component_id, state="UNKNOWN", applicable=True, source=f"opportunity.{key}", reason="invalid_value")
            return _component(component_id, value=val, state="AVAILABLE", applicable=True, source=f"opportunity.{key}")
    return _component(component_id, state="UNAVAILABLE", applicable=True, source="none", reason=f"missing_{component_id}_evidence")


def _latency_cost(opportunity: dict[str, Any], notional: float | None, applicable: bool) -> dict[str, Any]:
    if not applicable:
        return _component("execution_latency_cost", state="NOT_APPLICABLE", applicable=False, source="kind_policy", reason="not_applicable_for_kind")
    age_ms = _optional_float(opportunity.get("quote_age_ms") or opportunity.get("age_ms") or opportunity.get("rewalk_age_ms"))
    if age_ms is None or notional is None:
        return _component("execution_latency_cost", state="UNAVAILABLE", applicable=True, source="none", reason="missing_quote_age_or_notional")
    bps_per_sec = float(opportunity.get("latency_cost_bps_per_sec") or 1.5)
    val = notional * (bps_per_sec * (age_ms / 1000.0)) / 10_000.0
    return _component("execution_latency_cost", value=val, state="AVAILABLE", applicable=True, source="quote_age_latency_model")


def _decay_cost(opportunity: dict[str, Any], gross: float | None, applicable: bool) -> dict[str, Any]:
    if not applicable:
        return _component("expected_opportunity_decay", state="NOT_APPLICABLE", applicable=False, source="kind_policy", reason="not_applicable_for_kind")
    after = _optional_float(opportunity.get("flywheel_net_after_crowd_usd"))
    if after is not None and gross is not None:
        decay = max(0.0, gross - after)
        return _component("expected_opportunity_decay", value=decay, state="AVAILABLE", applicable=True, source="flywheel_rewalk")
    recipients = _optional_float(opportunity.get("estimated_recipients"))
    if gross is None:
        return _component("expected_opportunity_decay", state="UNAVAILABLE", applicable=True, source="none", reason="missing_gross_for_decay")
    if recipients is None:
        return _component("expected_opportunity_decay", state="UNAVAILABLE", applicable=True, source="none", reason="missing_crowd_evidence")
    decay_frac = min(0.85, 0.35 * max(1.0, recipients) / 10.0)
    val = gross * decay_frac
    return _component(
        "expected_opportunity_decay",
        value=val,
        low=val * 0.7,
        high=val * 1.3,
        state="AVAILABLE",
        applicable=True,
        source="crowd_heuristic",
        uncertainty={"method": "recipient_decay_heuristic", "confidence": "low"},
    )


def _partial_fill_cost(opportunity: dict[str, Any], notional: float | None, applicable: bool) -> dict[str, Any]:
    if not applicable:
        return _component("failed_partial_fill_cost", state="NOT_APPLICABLE", applicable=False, source="kind_policy", reason="not_applicable_for_kind")
    fill_prob = _optional_float(opportunity.get("fill_probability") or opportunity.get("expected_fill_probability"))
    if fill_prob is None:
        label = str(opportunity.get("execution_feasibility") or "").lower()
        if label in {"partial", "low", "below_threshold"}:
            fill_prob = 0.55
        elif label in {"full", "high"}:
            fill_prob = 0.95
        else:
            return _component("failed_partial_fill_cost", state="UNAVAILABLE", applicable=True, source="none", reason="missing_fill_probability")
    if notional is None:
        return _component("failed_partial_fill_cost", state="UNAVAILABLE", applicable=True, source="none", reason="missing_notional")
    slip_bps = _optional_float(opportunity.get("total_slippage_bps") or opportunity.get("slippage_bps")) or 0.0
    failed_frac = max(0.0, 1.0 - min(1.0, fill_prob))
    val = notional * (slip_bps / 10_000.0) * failed_frac * 0.5
    return _component(
        "failed_partial_fill_cost",
        value=val,
        state="AVAILABLE",
        applicable=True,
        source="fill_probability_model",
        uncertainty={"fill_probability": fill_prob},
    )


def _build_cost_autopsy(opportunity: dict[str, Any]) -> list[dict[str, Any]]:
    kind = _kind(opportunity)
    app = _applicability(kind, opportunity)
    notional = _notional(opportunity)
    gross_c = _gross_edge(opportunity, notional)
    gross_val = _optional_float(gross_c.get("value_usd"))
    return [
        gross_c,
        _trading_fees(opportunity, app["trading_fees"]),
        _slippage(opportunity, notional, app["expected_slippage"]),
        _price_impact(opportunity, notional, app["price_impact"]),
        _simple_usd_component("gas_network_fees", opportunity, ("gas_fee_usdt", "gas_cost_usdt", "network_fee_usdt"), app["gas_network_fees"]),
        _simple_usd_component("funding", opportunity, ("funding_cost_usdt", "funding_usd"), app["funding"]),
        _simple_usd_component("borrow_cost", opportunity, ("borrow_cost_usdt",), app["borrow_cost"]),
        _simple_usd_component(
            "withdrawal_deposit_fees",
            opportunity,
            ("withdrawal_fee_usdt", "deposit_fee_usdt"),
            app["withdrawal_deposit_fees"],
        ),
        _simple_usd_component("bridge_costs", opportunity, ("bridge_cost_usdt",), app["bridge_costs"]),
        _simple_usd_component("fx_conversion_costs", opportunity, ("fx_cost_usdt", "conversion_cost_usdt"), app["fx_conversion_costs"]),
        _decay_cost(opportunity, gross_val, app["expected_opportunity_decay"]),
        _latency_cost(opportunity, notional, app["execution_latency_cost"]),
        _partial_fill_cost(opportunity, notional, app["failed_partial_fill_cost"]),
        _simple_usd_component("hedging_cost", opportunity, ("hedging_cost_usdt",), app["hedging_cost"]),
    ]


def _sum_costs(autopsy: list[dict[str, Any]]) -> tuple[float | None, list[str]]:
    total = 0.0
    unknowns: list[str] = []
    for row in autopsy:
        cid = str(row.get("component") or "")
        if cid == "gross_edge":
            continue
        if not row.get("applicable"):
            continue
        state = str(row.get("state") or "")
        if state == "NOT_APPLICABLE":
            continue
        if state in {"UNAVAILABLE", "UNKNOWN"}:
            unknowns.append(cid)
            continue
        val = _optional_float(row.get("value_usd"))
        if val is None:
            unknowns.append(cid)
            continue
        total += val
    if unknowns:
        return None, unknowns
    return total, []


def _uncertainty_interval(expected: float | None, autopsy: list[dict[str, Any]]) -> dict[str, Any]:
    if expected is None:
        return {"state": "UNCERTAINTY_UNAVAILABLE", "reason": "expected_net_edge_unavailable"}
    lows: list[float] = []
    highs: list[float] = []
    for row in autopsy:
        if not row.get("applicable") or row.get("component") == "gross_edge":
            continue
        rng = row.get("range_usd") or {}
        low = _optional_float(rng.get("low"))
        high = _optional_float(rng.get("high"))
        val = _optional_float(row.get("value_usd"))
        if low is not None and high is not None and val is not None:
            lows.append(expected - (val - low))
            highs.append(expected + (high - val))
    if not lows:
        spread = abs(expected) * 0.15 + 0.05
        return guard_precision(
            {
                "state": "AVAILABLE",
                "methodology_version": METHODOLOGY_VERSION,
                "expected_usd": expected,
                "low_usd": expected - spread,
                "high_usd": expected + spread,
                "confidence": "low",
                "method": "conservative_default_spread",
            }
        )
    return guard_precision(
        {
            "state": "AVAILABLE",
            "methodology_version": METHODOLOGY_VERSION,
            "expected_usd": expected,
            "low_usd": min(lows),
            "high_usd": max(highs),
            "confidence": "medium",
            "method": "component_range_aggregation",
        }
    )


def _edge_separation(
    opportunity: dict[str, Any],
    *,
    gross: float | None,
    expected: float | None,
    autopsy: list[dict[str, Any]],
) -> dict[str, Any]:
    theoretical = gross
    if theoretical is None:
        theoretical_state = "UNAVAILABLE"
    else:
        theoretical_state = "AVAILABLE"
    expected_state = "AVAILABLE" if expected is not None else "UNAVAILABLE"
    fill_prob = _optional_float(opportunity.get("fill_probability") or opportunity.get("expected_fill_probability"))
    capacity_factor = _optional_float(opportunity.get("capacity_fill_factor"))
    timing_decay = _optional_float((opportunity.get("opportunity_half_life") or {}).get("disappearance_probability"))
    constraints: list[str] = []
    realizable: float | None = expected
    if expected is not None:
        multiplier = 1.0
        if fill_prob is not None:
            multiplier *= fill_prob
            constraints.append("fill_probability")
        else:
            constraints.append("fill_probability_unavailable")
        if capacity_factor is not None:
            multiplier *= capacity_factor
            constraints.append("capacity")
        elif opportunity.get("capacity_usd") is not None:
            notional = _notional(opportunity)
            cap = _optional_float(opportunity.get("capacity_usd"))
            if notional and cap is not None and notional > 0:
                multiplier *= min(1.0, cap / notional)
                constraints.append("capacity")
        if timing_decay is not None:
            multiplier *= max(0.0, 1.0 - timing_decay)
            constraints.append("timing_decay")
        if fill_prob is None and capacity_factor is None and opportunity.get("capacity_usd") is None:
            realizable_state = "UNAVAILABLE"
            realizable = None
        else:
            realizable = expected * multiplier
            realizable_state = "AVAILABLE"
    else:
        realizable_state = "UNAVAILABLE"
        realizable = None
    return guard_precision(
        {
            "THEORETICAL_EDGE": {"state": theoretical_state, "value_usd": theoretical},
            "EXPECTED_NET_EDGE": {"state": expected_state, "value_usd": expected},
            "REALIZABLE_NET_EDGE": {
                "state": realizable_state,
                "value_usd": realizable,
                "constraints_applied": constraints,
            },
            "methodology_version": METHODOLOGY_VERSION,
        }
    )


def evaluate_formal_net_edge(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Canonical formal net-edge evaluation."""
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
            "cost_autopsy": [],
            "edge_separation": {},
            "uncertainty": {"state": "UNCERTAINTY_UNAVAILABLE", "reason": "advisory_only"},
            "methodology_version": METHODOLOGY_VERSION,
        }

    autopsy = _build_cost_autopsy(opp)
    gross = _optional_float(next((r.get("value_usd") for r in autopsy if r.get("component") == "gross_edge"), None))
    total_costs, unknown_costs = _sum_costs(autopsy)
    if gross is None:
        return {
            "enabled": True,
            "reject": True,
            "pass": False,
            "state": "UNAVAILABLE",
            "reason": "missing_gross_edge",
            "unknown_cost_components": unknown_costs,
            "cost_autopsy": autopsy,
            "uncertainty": {"state": "UNCERTAINTY_UNAVAILABLE", "reason": "missing_gross_edge"},
            "edge_separation": _edge_separation(opp, gross=None, expected=None, autopsy=autopsy),
            "methodology_version": METHODOLOGY_VERSION,
        }
    if total_costs is None:
        return {
            "enabled": True,
            "reject": True,
            "pass": False,
            "state": "UNAVAILABLE",
            "reason": "incomplete_cost_evidence",
            "unknown_cost_components": unknown_costs,
            "cost_autopsy": autopsy,
            "gross_edge_usd": gross,
            "uncertainty": {"state": "UNCERTAINTY_UNAVAILABLE", "reason": "incomplete_cost_evidence"},
            "edge_separation": _edge_separation(opp, gross=gross, expected=None, autopsy=autopsy),
            "methodology_version": METHODOLOGY_VERSION,
        }

    expected = gross - total_costs
    uncertainty = _uncertainty_interval(expected, autopsy)
    edges = _edge_separation(opp, gross=gross, expected=expected, autopsy=autopsy)

    try:
        from net_edge_truth import compute_net_edge_truth

        legacy = compute_net_edge_truth(opp)
    except Exception as exc:
        logger.warning("legacy net_edge_truth unavailable", exc_info=True)
        legacy = {"truth_score": None, "reject": expected <= 0, "reasons": [str(exc)]}

    reject = bool(legacy.get("reject")) or expected <= 0
    return guard_precision(
        {
            "enabled": True,
            "reject": reject,
            "pass": not reject,
            "state": "AVAILABLE",
            "truth_score": legacy.get("truth_score"),
            "reasons": list(legacy.get("reasons") or []),
            "gross_edge_usd": gross,
            "total_costs_usd": total_costs,
            "expected_net_edge_usd": expected,
            "cost_autopsy": autopsy,
            "edge_separation": edges,
            "uncertainty": uncertainty,
            "unknown_cost_components": unknown_costs,
            "legacy_truth": legacy,
            "methodology_version": METHODOLOGY_VERSION,
        }
    )
