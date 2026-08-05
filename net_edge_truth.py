"""
BLACKDARK — Net-Edge Truth Score (Differentiator D3).

Rejects "feature-theater" opportunities that look profitable on gross spread
but fail after fees + withdrawal + slippage + latency buffer + crowd decay.

Institutional claim: fewer signals, higher executable hit-rate.
"""

from __future__ import annotations

import logging
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.NetEdgeTruth")

_STATS = {
    "evaluated": 0,
    "passed": 0,
    "rejected": 0,
    "reject_reasons": {},
}


def _enabled() -> bool:
    return getattr(config, "NET_EDGE_TRUTH_ENABLED", True)


def _min_truth_score() -> float:
    return float(getattr(config, "NET_EDGE_TRUTH_MIN_SCORE", 55.0))


def _min_residual_usd() -> float:
    return float(getattr(config, "NET_EDGE_TRUTH_MIN_RESIDUAL_USD", 0.08))


def _max_quote_age_ms() -> float:
    return float(getattr(config, "NET_EDGE_TRUTH_MAX_QUOTE_AGE_MS", 2500.0))


def _latency_cost_bps_per_second() -> float:
    return float(getattr(config, "NET_EDGE_TRUTH_LATENCY_COST_BPS_PER_SEC", 1.5))


def _crowd_decay_fraction() -> float:
    return float(getattr(config, "NET_EDGE_TRUTH_CROWD_DECAY_FRACTION", 0.35))


def _bump_reason(reason: str) -> None:
    bucket = _STATS["reject_reasons"]
    bucket[reason] = int(bucket.get(reason, 0)) + 1


def _quote_age_ms(opportunity: dict[str, Any]) -> float | None:
    for key in ("quote_age_ms", "rewalk_age_ms", "book_age_ms", "age_ms"):
        try:
            value = float(opportunity.get(key) or 0)
        except (TypeError, ValueError):
            value = 0.0
        if value > 0:
            return value

    buy_ex = str(opportunity.get("buy_exchange") or opportunity.get("buy_venue") or "")
    sell_ex = str(opportunity.get("sell_exchange") or opportunity.get("sell_venue") or "")
    asset = str(opportunity.get("asset") or opportunity.get("symbol") or "BTC")
    symbol = asset if "/" in asset else f"{asset.split('/')[0]}/USDT"
    ages: list[float] = []
    try:
        from live_book_hub import get_quote_age_ms

        for exchange in (buy_ex, sell_ex):
            if not exchange:
                continue
            age = get_quote_age_ms(exchange, symbol)
            if age is not None:
                ages.append(float(age))
    except Exception:
        logger.debug("quote age lookup failed", exc_info=True)
    if not ages:
        return None
    return max(ages)


def _crowd_residual_profit(opportunity: dict[str, Any], net_profit: float) -> tuple[float, dict[str, Any]]:
    """Conservative residual after estimated crowd competition (sync path)."""
    after_crowd = opportunity.get("flywheel_net_after_crowd_usd")
    if after_crowd is not None:
        try:
            residual = float(after_crowd)
            return residual, {
                "mode": "rewalk",
                "crowd_notional_usd": float(opportunity.get("flywheel_crowd_notional_usd") or 0),
                "residual_usd": residual,
            }
        except (TypeError, ValueError):
            pass

    recipients = int(
        opportunity.get("estimated_recipients")
        or (opportunity.get("flywheel_alert_meta") or {}).get("estimated_recipients")
        or getattr(config, "FLYWHEEL_ESTIMATED_ACTORS_PER_ALERT", 10)
    )
    decay = min(0.85, _crowd_decay_fraction() * max(1, recipients) / 10.0)
    residual = net_profit * (1.0 - decay)
    return residual, {
        "mode": "heuristic",
        "estimated_recipients": recipients,
        "decay_fraction": round(decay, 4),
        "residual_usd": round(residual, 6),
    }


def compute_net_edge_truth(
    opportunity: dict[str, Any] | None = None,
    *,
    net_profit_usdt: float | None = None,
    quote_amount: float | None = None,
    total_slippage_bps: float | None = None,
) -> dict[str, Any]:
    """
    Return Truth Score 0–100 plus hard reject flag.

    Components (weighted):
      residual edge 45% | latency freshness 25% | slippage quality 15% | fee drag clarity 15%
    """
    opp = dict(opportunity or {})
    net = float(
        net_profit_usdt
        if net_profit_usdt is not None
        else opp.get("net_profit_usdt")
        or 0.0
    )
    notional = float(
        quote_amount
        if quote_amount is not None
        else opp.get("quote_amount")
        or getattr(config, "DEFAULT_QUOTE_AMOUNT", 100)
        or 100
    )
    slippage_bps = float(
        total_slippage_bps
        if total_slippage_bps is not None
        else opp.get("total_slippage_bps")
        or 0.0
    )
    withdrawal = float(opp.get("withdrawal_fee_usdt") or 0.0)
    trading_fees = float(opp.get("trading_fees_usdt") or opp.get("fees_usdt") or 0.0)

    residual, crowd_meta = _crowd_residual_profit(opp, net)
    age_ms = _quote_age_ms(opp)
    latency_buffer_usd = 0.0
    if age_ms is not None and notional > 0:
        latency_buffer_usd = notional * ((_latency_cost_bps_per_second() * (age_ms / 1000.0)) / 10_000)
    truth_edge = residual - latency_buffer_usd

    # Component scores
    edge_score = 0.0
    if truth_edge >= _min_residual_usd() * 3:
        edge_score = 100.0
    elif truth_edge >= _min_residual_usd():
        edge_score = 55.0 + 45.0 * min(1.0, (truth_edge - _min_residual_usd()) / max(_min_residual_usd() * 2, 1e-9))
    elif truth_edge > 0:
        edge_score = 35.0 * (truth_edge / max(_min_residual_usd(), 1e-9))
    else:
        edge_score = 0.0

    if age_ms is None:
        latency_score = 60.0  # unknown → cautious mid
    elif age_ms <= 400:
        latency_score = 100.0
    elif age_ms <= _max_quote_age_ms():
        latency_score = 100.0 - 55.0 * ((age_ms - 400) / max(_max_quote_age_ms() - 400, 1.0))
    else:
        latency_score = max(0.0, 30.0 - (age_ms - _max_quote_age_ms()) / 100.0)

    if slippage_bps <= 5:
        slip_score = 100.0
    elif slippage_bps <= 25:
        slip_score = 100.0 - (slippage_bps - 5) * 3.0
    else:
        slip_score = max(0.0, 40.0 - (slippage_bps - 25) * 1.5)

    fee_drag = withdrawal + trading_fees
    fee_ratio = fee_drag / max(abs(net) + fee_drag, 1e-9)
    fee_score = max(0.0, 100.0 - fee_ratio * 120.0)

    truth_score = round(
        0.45 * edge_score + 0.25 * latency_score + 0.15 * slip_score + 0.15 * fee_score,
        2,
    )

    reasons: list[str] = []
    reject = False
    if not _enabled():
        return {
            "enabled": False,
            "truth_score": truth_score,
            "reject": False,
            "pass": True,
            "reason": "guard_disabled",
        }

    if truth_edge < _min_residual_usd():
        reject = True
        reasons.append("residual_edge_below_threshold")
    if age_ms is not None and age_ms > _max_quote_age_ms():
        reject = True
        reasons.append("stale_quote_latency")
    if truth_score < _min_truth_score():
        reject = True
        reasons.append("truth_score_below_minimum")
    if opp.get("executable") is False and opp.get("flywheel_saturation"):
        reject = True
        reasons.append("crowd_liquidity_depleted")

    _STATS["evaluated"] += 1
    if reject:
        _STATS["rejected"] += 1
        for reason in reasons:
            _bump_reason(reason)
    else:
        _STATS["passed"] += 1

    return {
        "enabled": True,
        "truth_score": truth_score,
        "reject": reject,
        "pass": not reject,
        "reasons": reasons,
        "components": {
            "edge_score": round(edge_score, 2),
            "latency_score": round(latency_score, 2),
            "slippage_score": round(slip_score, 2),
            "fee_score": round(fee_score, 2),
        },
        "economics": {
            "net_profit_usdt": round(net, 6),
            "residual_after_crowd_usd": round(residual, 6),
            "latency_buffer_usd": round(latency_buffer_usd, 6),
            "truth_edge_usd": round(truth_edge, 6),
            "min_residual_usd": _min_residual_usd(),
            "quote_age_ms": None if age_ms is None else round(age_ms, 1),
            "total_slippage_bps": round(slippage_bps, 2),
            "withdrawal_fee_usdt": round(withdrawal, 6),
            "trading_fees_usdt": round(trading_fees, 6),
            "notional_usd": round(notional, 4),
        },
        "crowd": crowd_meta,
        "thresholds": {
            "min_truth_score": _min_truth_score(),
            "min_residual_usd": _min_residual_usd(),
            "max_quote_age_ms": _max_quote_age_ms(),
        },
    }


def apply_truth_gate_to_score(score: float, truth: dict[str, Any]) -> float:
    """Soft-cap opportunity score when Truth rejects; mild haircut when weak."""
    if not truth.get("enabled", True):
        return score
    if truth.get("reject"):
        return min(score, 39.0)
    ts = float(truth.get("truth_score") or 0)
    if ts < 70:
        return round(score * (0.85 + 0.15 * (ts / 70.0)), 2)
    return score


def net_edge_truth_status() -> dict[str, Any]:
    evaluated = int(_STATS["evaluated"])
    rejected = int(_STATS["rejected"])
    return {
        "enabled": _enabled(),
        "evaluated": evaluated,
        "passed": int(_STATS["passed"]),
        "rejected": rejected,
        "reject_rate": round(rejected / evaluated, 4) if evaluated else 0.0,
        "reject_reasons": dict(_STATS["reject_reasons"]),
        "thresholds": {
            "min_truth_score": _min_truth_score(),
            "min_residual_usd": _min_residual_usd(),
            "max_quote_age_ms": _max_quote_age_ms(),
        },
    }
