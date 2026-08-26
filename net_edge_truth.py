"""
BLACKDARK — Net-Edge Truth Score (Feature #417 / Differentiator D3).

Intelligence Ledger core scoring engine — compresses opportunity quality into a
score based on executable net edge, not raw gross spread.

Formula version 2.0.0 — see docs/features/NET_EDGE_TRUTH_SCORE.md
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.NetEdgeTruth")

FEATURE_REF = 417
FORMULA_VERSION = "2.0.0"
_HISTORY_PATH = Path("data/net_edge_truth_history.jsonl")

# Weighted components (documented in ToS + NET_EDGE_TRUTH_SCORE.md)
_WEIGHT_EDGE = 0.45
_WEIGHT_LATENCY = 0.25
_WEIGHT_SLIPPAGE = 0.15
_WEIGHT_FEES = 0.15

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


def _direct_quote_age_ms(opportunity: dict[str, Any]) -> float | None:
    for key in ("quote_age_ms", "rewalk_age_ms", "book_age_ms", "age_ms"):
        try:
            value = float(opportunity.get(key) or 0)
        except (TypeError, ValueError):
            value = 0.0
        if value > 0:
            return value
    return None


def _quote_symbol(opportunity: dict[str, Any]) -> str:
    asset = str(opportunity.get("asset") or opportunity.get("symbol") or "BTC")
    return asset if "/" in asset else f"{asset.split('/')[0]}/USDT"


def _live_quote_ages(opportunity: dict[str, Any], symbol: str) -> list[float]:
    buy_ex = str(opportunity.get("buy_exchange") or opportunity.get("buy_venue") or "")
    sell_ex = str(opportunity.get("sell_exchange") or opportunity.get("sell_venue") or "")
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
    return ages


def _quote_age_ms(opportunity: dict[str, Any]) -> float | None:
    direct_age = _direct_quote_age_ms(opportunity)
    if direct_age is not None:
        return direct_age
    ages = _live_quote_ages(opportunity, _quote_symbol(opportunity))
    return max(ages) if ages else None


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


def _worst_case_costs(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Worst-case cost bounds — unknown costs must never be treated as zero."""
    raw = opportunity.get("worst_case_costs") or {}
    return raw if isinstance(raw, dict) else {}


def _parse_withdrawal_fee_usdt(
    opportunity: dict[str, Any],
) -> tuple[float | None, dict[str, Any]]:
    """Return (fee, cost_policy). Missing → None unless worst-case estimate applies."""
    policy: dict[str, Any] = {"field": "withdrawal_fee_usdt", "source": "unknown"}
    if "withdrawal_fee_usdt" in opportunity:
        raw = opportunity.get("withdrawal_fee_usdt")
        if raw is None:
            return None, {**policy, "source": "explicit_null"}
        try:
            return float(raw), {**policy, "source": "reported", "value": float(raw)}
        except (TypeError, ValueError):
            return None, {**policy, "source": "unparseable"}

    worst = _worst_case_costs(opportunity)
    wc = worst.get("withdrawal_fee_usdt")
    if wc is not None:
        try:
            value = float(wc)
            return value, {
                **policy,
                "source": "worst_case_estimate",
                "value": value,
                "never_zero": True,
            }
        except (TypeError, ValueError):
            pass
    return None, policy


def _parse_trading_fees_usdt(
    opportunity: dict[str, Any],
) -> tuple[float | None, dict[str, Any]]:
    policy: dict[str, Any] = {"field": "trading_fees_usdt", "source": "unknown"}
    if "trading_fees_usdt" in opportunity:
        raw = opportunity.get("trading_fees_usdt")
        if raw is not None:
            try:
                return float(raw), {**policy, "source": "reported", "value": float(raw)}
            except (TypeError, ValueError):
                pass
    if "fees_usdt" in opportunity:
        raw = opportunity.get("fees_usdt")
        if raw is not None:
            try:
                return float(raw), {**policy, "source": "reported_fees_usdt", "value": float(raw)}
            except (TypeError, ValueError):
                pass

    worst = _worst_case_costs(opportunity)
    wc = worst.get("trading_fees_usdt")
    if wc is not None:
        try:
            value = float(wc)
            return value, {**policy, "source": "worst_case_estimate", "value": value, "never_zero": True}
        except (TypeError, ValueError):
            pass
    return None, policy


def _parse_network_cost_usdt(opportunity: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    """Transfer/network cost — explicit, worst-case, or zero only when reported."""
    policy: dict[str, Any] = {"field": "transfer_cost_usdt", "source": "unknown"}
    for key in ("transfer_cost_usdt", "network_cost_usdt"):
        if key in opportunity and opportunity.get(key) is not None:
            try:
                value = float(opportunity[key])
                return value, {**policy, "source": "reported", "value": value, "field": key}
            except (TypeError, ValueError):
                pass
    worst = _worst_case_costs(opportunity)
    wc = worst.get("transfer_cost_usdt") or worst.get("network_cost_usdt")
    if wc is not None:
        try:
            value = float(wc)
            return value, {**policy, "source": "worst_case_estimate", "value": value, "never_zero": True}
        except (TypeError, ValueError):
            pass
    return 0.0, {**policy, "source": "absent_assumed_zero_reported", "value": 0.0}


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _truth_inputs(
    opportunity: dict[str, Any],
    net_profit_usdt: float | None,
    quote_amount: float | None,
    total_slippage_bps: float | None,
) -> tuple[float | None, float, float | None, float | None, float | None, float, dict[str, Any]]:
    """Parse Truth inputs without inventing optimistic zeros for missing economics."""
    cost_policies: dict[str, Any] = {}
    if net_profit_usdt is not None:
        net = _optional_float(net_profit_usdt)
    elif "net_profit_usdt" in opportunity:
        net = _optional_float(opportunity.get("net_profit_usdt"))
    elif "net_edge_usdt" in opportunity:
        net = _optional_float(opportunity.get("net_edge_usdt"))
    else:
        net = None
    notional = float(
        quote_amount
        if quote_amount is not None
        else opportunity.get("quote_amount")
        or opportunity.get("quote_usd")
        or getattr(config, "DEFAULT_QUOTE_AMOUNT", 100)
        or 100
    )
    if total_slippage_bps is not None:
        slippage_bps = _optional_float(total_slippage_bps)
    elif "total_slippage_bps" in opportunity:
        slippage_bps = _optional_float(opportunity.get("total_slippage_bps"))
    elif "slippage_bps" in opportunity:
        slippage_bps = _optional_float(opportunity.get("slippage_bps"))
    else:
        slippage_bps = None

    withdrawal, w_policy = _parse_withdrawal_fee_usdt(opportunity)
    cost_policies["withdrawal"] = w_policy
    trading_fees, t_policy = _parse_trading_fees_usdt(opportunity)
    cost_policies["trading_fees"] = t_policy
    network_cost, n_policy = _parse_network_cost_usdt(opportunity)
    cost_policies["network"] = n_policy
    if net is not None:
        net = net - network_cost
    return net, notional, slippage_bps, withdrawal, trading_fees, network_cost, cost_policies


def _latency_buffer_usd(age_ms: float | None, notional: float) -> float:
    if age_ms is None or notional <= 0:
        return 0.0
    return notional * ((_latency_cost_bps_per_second() * (age_ms / 1000.0)) / 10_000)


def _edge_score(truth_edge: float) -> float:
    if truth_edge >= _min_residual_usd() * 3:
        return 100.0
    if truth_edge >= _min_residual_usd():
        return 55.0 + 45.0 * min(
            1.0,
            (truth_edge - _min_residual_usd()) / max(_min_residual_usd() * 2, 1e-9),
        )
    if truth_edge > 0:
        return 35.0 * (truth_edge / max(_min_residual_usd(), 1e-9))
    return 0.0


def _latency_score(age_ms: float | None) -> float:
    if age_ms is None:
        return 60.0  # unknown → cautious mid
    if age_ms <= 400:
        return 100.0
    if age_ms <= _max_quote_age_ms():
        return 100.0 - 55.0 * ((age_ms - 400) / max(_max_quote_age_ms() - 400, 1.0))
    return max(0.0, 30.0 - (age_ms - _max_quote_age_ms()) / 100.0)


def _slippage_score(slippage_bps: float) -> float:
    if slippage_bps <= 5:
        return 100.0
    if slippage_bps <= 25:
        return 100.0 - (slippage_bps - 5) * 3.0
    return max(0.0, 40.0 - (slippage_bps - 25) * 1.5)


def _fee_score(withdrawal: float, trading_fees: float, net: float) -> float:
    fee_drag = withdrawal + trading_fees
    fee_ratio = fee_drag / max(abs(net) + fee_drag, 1e-9)
    return max(0.0, 100.0 - fee_ratio * 120.0)


def _truth_score(
    edge_score: float,
    latency_score: float,
    slip_score: float,
    fee_score: float,
    *,
    capacity_penalty: float = 0.0,
) -> float:
    raw = (
        _WEIGHT_EDGE * edge_score
        + _WEIGHT_LATENCY * latency_score
        + _WEIGHT_SLIPPAGE * slip_score
        + _WEIGHT_FEES * fee_score
    )
    return round(max(0.0, raw - capacity_penalty), 2)


def _feasibility_context(opportunity: dict[str, Any]) -> dict[str, Any]:
    """#415 integration — depth/capacity + stale/unfillable fail-closed."""
    feasibility = opportunity.get("volume_feasibility") or opportunity.get("feasibility") or {}
    if feasibility.get("status") == "not_applicable_for_triangular":
        return {
            "applicable": False,
            "executable_size": None,
            "capacity_penalty": 0.0,
            "reject_reasons": [],
            "evidence": {"status": "not_applicable_for_triangular"},
        }

    buy_leg = feasibility.get("buy_leg") or {}
    sell_leg = feasibility.get("sell_leg") or {}
    verdict = feasibility.get("verdict") or buy_leg.get("verdict") or sell_leg.get("verdict")
    max_exec = feasibility.get("max_executable_size")
    if max_exec is None:
        buy_fill = float(buy_leg.get("fillable_size") or 0)
        sell_fill = float(sell_leg.get("fillable_size") or 0)
        max_exec = min(buy_fill, sell_fill) if buy_fill and sell_fill else 0.0

    reject_reasons: list[str] = []
    stale = bool(buy_leg.get("stale") or sell_leg.get("stale"))
    if stale:
        reject_reasons.append("stale_depth_not_fillable")
    if verdict == "not_fillable" or feasibility.get("signal_suppressed"):
        reject_reasons.append("insufficient_liquidity")
    if buy_leg.get("reason") == "missing_depth_never_executable" or sell_leg.get("reason") == "missing_depth_never_executable":
        reject_reasons.append("missing_depth_never_executable")

    liq_score = feasibility.get("liquidity_score")
    capacity_penalty = 0.0
    if liq_score is not None:
        capacity_penalty = max(0.0, (100.0 - float(liq_score)) * 0.15)

    return {
        "applicable": True,
        "executable_size": round(float(max_exec), 8) if max_exec else 0.0,
        "capacity_penalty": capacity_penalty,
        "reject_reasons": reject_reasons,
        "liquidity_score": liq_score,
        "verdict": verdict,
        "evidence": {
            "buy_verdict": buy_leg.get("verdict"),
            "sell_verdict": sell_leg.get("verdict"),
            "signal_suppressed": feasibility.get("signal_suppressed"),
        },
    }


def _net_return_pct(truth_edge: float, notional: float) -> float | None:
    if notional <= 0:
        return None
    return round((truth_edge / notional) * 100.0, 4)


def _append_history_record(
    opportunity: dict[str, Any],
    result: dict[str, Any],
) -> None:
    """Truth Score History — predicted score for trust calibration."""
    try:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "formula_version": FORMULA_VERSION,
            "feature_ref": FEATURE_REF,
            "opportunity_id": opportunity.get("opportunity_id"),
            "asset": opportunity.get("asset") or opportunity.get("symbol"),
            "predicted_truth_score": result.get("truth_score"),
            "predicted_net_return_pct": result.get("net_return_pct"),
            "reject": result.get("reject"),
            "rejection_reasons": result.get("reasons") or [],
            "outcome": None,
            "outcome_recorded": False,
        }
        _HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _HISTORY_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        logger.debug("truth history append failed", exc_info=True)


def load_truth_score_history(*, limit: int = 50) -> list[dict[str, Any]]:
    if not _HISTORY_PATH.is_file():
        return []
    lines = _HISTORY_PATH.read_text(encoding="utf-8").strip().splitlines()
    records = []
    for line in lines[-limit:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def truth_score_history_summary() -> dict[str, Any]:
    records = load_truth_score_history(limit=500)
    scored = [r for r in records if r.get("outcome_recorded")]
    correct = sum(1 for r in scored if r.get("outcome") == "correct")
    predicted_pass = sum(1 for r in records if not r.get("reject"))
    return {
        "total_predictions": len(records),
        "outcomes_recorded": len(scored),
        "correct_predictions": correct,
        "accuracy_rate": round(correct / len(scored), 4) if scored else None,
        "predicted_pass_rate": round(predicted_pass / len(records), 4) if records else None,
        "formula_version": FORMULA_VERSION,
        "feature_ref": FEATURE_REF,
    }


def _disabled_truth_result(truth_score: float) -> dict[str, Any]:
    return {
        "enabled": False,
        "truth_score": truth_score,
        "reject": False,
        "pass": True,
        "reason": "guard_disabled",
    }


def _reject_reasons(
    opportunity: dict[str, Any],
    truth_edge: float,
    age_ms: float | None,
    truth_score: float,
    *,
    feasibility: dict[str, Any] | None = None,
) -> list[str]:
    reasons: list[str] = []
    if truth_edge < _min_residual_usd():
        reasons.append("residual_edge_below_threshold")
    if age_ms is not None and age_ms > _max_quote_age_ms():
        reasons.append("stale_quote_latency")
    if truth_score < _min_truth_score():
        reasons.append("truth_score_below_minimum")
    if opportunity.get("executable") is False and opportunity.get("flywheel_saturation"):
        reasons.append("crowd_liquidity_depleted")
    if truth_edge < 0:
        reasons.append("negative_net_edge")
    if feasibility and feasibility.get("applicable"):
        for reason in feasibility.get("reject_reasons") or []:
            if reason not in reasons:
                reasons.append(reason)
    return reasons


def _record_truth_stats(reject: bool, reasons: list[str], truth_score: float, opportunity: dict[str, Any]) -> None:
    _STATS["evaluated"] += 1
    if not reject:
        _STATS["passed"] += 1
        return
    _STATS["rejected"] += 1
    for reason in reasons:
        _bump_reason(reason)
    try:
        from kill_rate_board import record_kill

        record_kill(
            "net_edge_truth",
            reasons[0] if reasons else "rejected",
            meta={"truth_score": truth_score, "asset": opportunity.get("asset") or opportunity.get("symbol")},
        )
    except Exception:
        logger.debug("kill_rate record failed", exc_info=True)


def _missing_field_reject(
    opportunity: dict[str, Any],
    *,
    reason: str,
    net: float | None,
    notional: float,
) -> dict[str, Any]:
    """Fail closed: missing economics must not invent optimistic Truth inputs."""
    reasons = [reason]
    _record_truth_stats(True, reasons, 0.0, opportunity)
    return {
        "enabled": True,
        "truth_score": 0.0,
        "reject": True,
        "pass": False,
        "reasons": reasons,
        "components": {
            "edge_score": 0.0,
            "latency_score": 0.0,
            "slippage_score": 0.0,
            "fee_score": 0.0,
        },
        "economics": {
            "net_profit_usdt": None if net is None else round(net, 6),
            "residual_after_crowd_usd": None,
            "latency_buffer_usd": None,
            "truth_edge_usd": None,
            "min_residual_usd": _min_residual_usd(),
            "quote_age_ms": None,
            "total_slippage_bps": None,
            "withdrawal_fee_usdt": None,
            "trading_fees_usdt": None,
            "notional_usd": round(notional, 4),
        },
        "crowd": {},
        "thresholds": {
            "min_truth_score": _min_truth_score(),
            "min_residual_usd": _min_residual_usd(),
            "max_quote_age_ms": _max_quote_age_ms(),
        },
    }


def _missing_withdrawal_reject(opportunity: dict[str, Any], *, net: float | None, notional: float) -> dict[str, Any]:
    """Fail closed: unknown withdrawal must not inflate net-edge / Truth Score."""
    return _missing_field_reject(
        opportunity, reason="missing_withdrawal_fee", net=net, notional=notional
    )


def _truth_result(pack: dict[str, Any]) -> dict[str, Any]:
    age_ms = pack["age_ms"]
    feasibility = pack.get("feasibility") or {}
    return {
        "enabled": True,
        "feature_ref": FEATURE_REF,
        "formula_version": FORMULA_VERSION,
        "truth_score": pack["truth_score"],
        "net_edge_score": pack["truth_score"],
        "reject": pack["reject"],
        "pass": not pack["reject"],
        "reasons": pack["reasons"],
        "net_return_pct": pack.get("net_return_pct"),
        "executable_size": feasibility.get("executable_size"),
        "components": {
            "edge_score": round(pack["edge_score"], 2),
            "latency_score": round(pack["latency_score"], 2),
            "slippage_score": round(pack["slip_score"], 2),
            "fee_score": round(pack["fee_score"], 2),
            "capacity_penalty": round(pack.get("capacity_penalty", 0.0), 2),
        },
        "economics": {
            "net_profit_usdt": round(pack["net"], 6),
            "residual_after_crowd_usd": round(pack["residual"], 6),
            "latency_buffer_usd": round(pack["latency_buffer_usd"], 6),
            "truth_edge_usd": round(pack["truth_edge"], 6),
            "network_cost_usdt": round(pack.get("network_cost", 0.0), 6),
            "min_residual_usd": _min_residual_usd(),
            "quote_age_ms": None if age_ms is None else round(age_ms, 1),
            "total_slippage_bps": round(pack["slippage_bps"], 2),
            "withdrawal_fee_usdt": round(pack["withdrawal"], 6),
            "trading_fees_usdt": round(pack["trading_fees"], 6),
            "notional_usd": round(pack["notional"], 4),
        },
        "crowd": pack["crowd_meta"],
        "feasibility": feasibility.get("evidence") if feasibility.get("applicable") else feasibility,
        "cost_policies": pack.get("cost_policies") or {},
        "evidence": {
            "formula": (
                f"truth_score = {_WEIGHT_EDGE}×edge + {_WEIGHT_LATENCY}×latency + "
                f"{_WEIGHT_SLIPPAGE}×slippage + {_WEIGHT_FEES}×fees − capacity_penalty"
            ),
            "formula_version": FORMULA_VERSION,
            "unknown_costs_never_zero": True,
            "fail_closed_on_stale_unfillable": True,
            "cost_policies": pack.get("cost_policies") or {},
        },
        "thresholds": {
            "min_truth_score": _min_truth_score(),
            "min_residual_usd": _min_residual_usd(),
            "max_quote_age_ms": _max_quote_age_ms(),
        },
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
    net, notional, slippage_bps, withdrawal, trading_fees, network_cost, cost_policies = _truth_inputs(
        opp,
        net_profit_usdt,
        quote_amount,
        total_slippage_bps,
    )
    if net is None:
        return _missing_field_reject(opp, reason="missing_net_profit", net=None, notional=notional)
    if slippage_bps is None:
        return _missing_field_reject(opp, reason="missing_slippage_bps", net=net, notional=notional)
    if trading_fees is None:
        return _missing_field_reject(opp, reason="missing_trading_fees", net=net, notional=notional)
    if withdrawal is None:
        # Executable / net-edge claims must not invent a zero withdrawal fee.
        return _missing_withdrawal_reject(opp, net=net, notional=notional)
    residual, crowd_meta = _crowd_residual_profit(opp, net)
    age_ms = _quote_age_ms(opp)
    latency_buffer_usd = _latency_buffer_usd(age_ms, notional)
    truth_edge = residual - latency_buffer_usd
    feasibility = _feasibility_context(opp)

    # Component scores
    edge_score = _edge_score(truth_edge)
    latency_score = _latency_score(age_ms)
    slip_score = _slippage_score(slippage_bps)
    fee_score = _fee_score(withdrawal, trading_fees, net)
    capacity_penalty = float(feasibility.get("capacity_penalty") or 0.0)
    truth_score = _truth_score(
        edge_score, latency_score, slip_score, fee_score, capacity_penalty=capacity_penalty
    )

    if not _enabled():
        return _disabled_truth_result(truth_score)

    reasons = _reject_reasons(opp, truth_edge, age_ms, truth_score, feasibility=feasibility)
    reject = bool(reasons)
    _record_truth_stats(reject, reasons, truth_score, opp)
    result = _truth_result(
        {
            "truth_score": truth_score,
            "reject": reject,
            "reasons": reasons,
            "edge_score": edge_score,
            "latency_score": latency_score,
            "slip_score": slip_score,
            "fee_score": fee_score,
            "capacity_penalty": capacity_penalty,
            "net": net,
            "residual": residual,
            "latency_buffer_usd": latency_buffer_usd,
            "truth_edge": truth_edge,
            "net_return_pct": _net_return_pct(truth_edge, notional),
            "age_ms": age_ms,
            "slippage_bps": slippage_bps,
            "withdrawal": withdrawal,
            "trading_fees": trading_fees,
            "network_cost": network_cost,
            "notional": notional,
            "crowd_meta": crowd_meta,
            "feasibility": feasibility,
            "cost_policies": cost_policies,
        }
    )
    _append_history_record(opp, result)
    return result


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


def rank_opportunity_with_diligence_risk(
    opportunity: dict[str, Any],
    *,
    truth_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#460+#417 — final opportunity rank with diligence risk adjustment."""
    from bd_platform.diligence_risk_scoring import apply_risk_to_net_edge_ranking

    return apply_risk_to_net_edge_ranking(opportunity, truth_result=truth_result)


def net_edge_truth_status() -> dict[str, Any]:
    evaluated = int(_STATS["evaluated"])
    rejected = int(_STATS["rejected"])
    return {
        "enabled": _enabled(),
        "feature_ref": FEATURE_REF,
        "formula_version": FORMULA_VERSION,
        "evaluated": evaluated,
        "passed": int(_STATS["passed"]),
        "rejected": rejected,
        "reject_rate": round(rejected / evaluated, 4) if evaluated else 0.0,
        "reject_reasons": dict(_STATS["reject_reasons"]),
        "formula": {
            "edge_weight": _WEIGHT_EDGE,
            "latency_weight": _WEIGHT_LATENCY,
            "slippage_weight": _WEIGHT_SLIPPAGE,
            "fee_weight": _WEIGHT_FEES,
            "unknown_costs_never_zero": True,
            "fail_closed_stale_unfillable": True,
        },
        "history": truth_score_history_summary(),
        "thresholds": {
            "min_truth_score": _min_truth_score(),
            "min_residual_usd": _min_residual_usd(),
            "max_quote_age_ms": _max_quote_age_ms(),
        },
    }
