"""Canonical quantitative metrics for scoped CAP-01..CAP-28."""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass
from typing import Any, Literal

METHODOLOGY_VERSION = "capability_spine_quant_v1"


def _returns(prices: list[float]) -> list[float]:
    if len(prices) < 2:
        return []
    return [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices)) if prices[i - 1] != 0]


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _std(values: list[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _cov(a: list[float], b: list[float]) -> float:
    n = min(len(a), len(b))
    if n < 2:
        return 0.0
    a_slice, b_slice = a[-n:], b[-n:]
    ma, mb = _mean(a_slice), _mean(b_slice)
    return sum((a_slice[i] - ma) * (b_slice[i] - mb) for i in range(n)) / n


def _var(values: list[float]) -> float:
    return _cov(values, values)


# ── CAP-01 Amihud Illiquidity Ratio ────────────────────────────────────────────


def amihud_illiquidity(
    prices: list[float],
    volumes: list[float],
    *,
    interval: str = "1d",
    window: int | None = None,
) -> dict[str, Any]:
    """|return| / dollar_volume aggregated over rolling window."""
    if len(prices) < 2 or len(volumes) < 2:
        return {"ok": False, "reason": "insufficient_data", "methodology_version": METHODOLOGY_VERSION}
    rets = _returns(prices)
    n = min(len(rets), len(volumes[1:]))
    if window:
        rets = rets[-window:]
        vols = volumes[-window:]
    else:
        vols = volumes[1:][-n:]
        rets = rets[-n:]
    ratios: list[float] = []
    for r, v in zip(rets, vols, strict=False):
        if v is None or v <= 0:
            continue
        ratios.append(abs(r) / float(v))
    if not ratios:
        return {
            "ok": False,
            "reason": "zero_or_missing_dollar_volume",
            "interval": interval,
            "methodology_version": METHODOLOGY_VERSION,
        }
    value = _mean(ratios)
    return {
        "ok": True,
        "amihud_ratio": round(value, 12),
        "sample_count": len(ratios),
        "interval": interval,
        "aggregation": "mean_abs_return_over_dollar_volume",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-02 Kyle's Lambda ───────────────────────────────────────────────────────


def kyles_lambda(
    price_changes: list[float],
    signed_flow: list[float],
    *,
    method: str = "ols_slope",
) -> dict[str, Any]:
    """Price impact via regression of price change on signed order flow."""
    n = min(len(price_changes), len(signed_flow))
    if n < 3:
        return {"ok": False, "reason": "insufficient_sample", "methodology_version": METHODOLOGY_VERSION}
    x = signed_flow[-n:]
    y = price_changes[-n:]
    x_mean, y_mean = _mean(x), _mean(y)
    num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    den = sum((x[i] - x_mean) ** 2 for i in range(n))
    if den == 0:
        return {"ok": False, "reason": "zero_flow_variance", "methodology_version": METHODOLOGY_VERSION}
    slope = num / den
    return {
        "ok": True,
        "lambda": round(slope, 10),
        "method": method,
        "units": "price_change_per_signed_flow_unit",
        "sample_count": n,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-04 VWAP Deviation Index ────────────────────────────────────────────────


def vwap_deviation_index(
    prices: list[float],
    volumes: list[float],
    *,
    reference_price: float | None = None,
    basis: Literal["market", "execution"] = "market",
) -> dict[str, Any]:
    if not prices or not volumes or len(prices) != len(volumes):
        return {"ok": False, "reason": "misaligned_or_empty_series", "methodology_version": METHODOLOGY_VERSION}
    total_vol = sum(volumes)
    if total_vol <= 0:
        return {"ok": False, "reason": "zero_volume", "methodology_version": METHODOLOGY_VERSION}
    vwap = sum(p * v for p, v in zip(prices, volumes, strict=False)) / total_vol
    ref = reference_price if reference_price is not None else prices[-1]
    deviation = ref - vwap
    deviation_bps = (deviation / vwap) * 10_000 if vwap else 0.0
    return {
        "ok": True,
        "vwap": round(vwap, 8),
        "reference_price": round(ref, 8),
        "deviation": round(deviation, 8),
        "deviation_bps": round(deviation_bps, 4),
        "basis": basis,
        "formula": "vwap=sum(price*volume)/sum(volume)",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-05 Volume-Velocity Tracker ─────────────────────────────────────────────


def volume_velocity(
    volumes: list[float],
    *,
    horizon: int = 5,
    interval: str = "1h",
) -> dict[str, Any]:
    if len(volumes) < horizon + 1:
        return {"ok": False, "reason": "insufficient_intervals", "methodology_version": METHODOLOGY_VERSION}
    recent = volumes[-horizon:]
    prior = volumes[-(horizon * 2) : -horizon]
    if not prior:
        return {"ok": False, "reason": "missing_prior_window", "methodology_version": METHODOLOGY_VERSION}
    recent_avg = _mean(recent)
    prior_avg = _mean(prior)
    if prior_avg == 0:
        velocity = None if recent_avg == 0 else float("inf")
    else:
        velocity = (recent_avg - prior_avg) / prior_avg
    return {
        "ok": True,
        "velocity": None if velocity is None else round(velocity, 6),
        "recent_avg_volume": round(recent_avg, 4),
        "prior_avg_volume": round(prior_avg, 4),
        "horizon_intervals": horizon,
        "interval": interval,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-06 Order Cancellation Velocity ─────────────────────────────────────────


def order_cancellation_velocity(
    events: list[dict[str, Any]],
    *,
    window_seconds: float = 60.0,
) -> dict[str, Any]:
    """Count explicit cancellation/removal events — not inferred book shrink."""
    cancels = [e for e in events if str(e.get("event_type", "")).lower() in {"cancel", "cancellation", "remove"}]
    if not cancels:
        return {"ok": False, "reason": "no_cancellation_events", "methodology_version": METHODOLOGY_VERSION}
    ts_values = [float(e["timestamp"]) for e in cancels if e.get("timestamp") is not None]
    if len(ts_values) < 2:
        rate = len(cancels) / window_seconds
    else:
        span = max(ts_values) - min(ts_values)
        rate = len(cancels) / span if span > 0 else len(cancels) / window_seconds
    return {
        "ok": True,
        "cancellation_count": len(cancels),
        "velocity_per_second": round(rate, 6),
        "window_seconds": window_seconds,
        "semantics": "explicit_cancel_events_only",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-07 VaR 99% ─────────────────────────────────────────────────────────────


def var_99(prices: list[float], *, notional: float = 10_000.0, horizon: str = "1d") -> dict[str, Any]:
    rets = _returns(prices)
    if len(rets) < 10:
        return {"ok": False, "reason": "insufficient_return_series", "methodology_version": METHODOLOGY_VERSION}
    sorted_rets = sorted(rets)
    idx = max(0, int((1 - 0.99) * len(sorted_rets)) - 1)
    var_return = sorted_rets[idx]
    var_usd = abs(var_return * notional)
    exceedances = sum(1 for r in rets if r <= var_return)
    return {
        "ok": True,
        "confidence": 0.99,
        "var_return": round(var_return, 8),
        "var_usd": round(var_usd, 4),
        "var_percent": round(abs(var_return) * 100, 4),
        "method": "historical_simulation",
        "horizon": horizon,
        "backtest_exceedances": exceedances,
        "sample_count": len(rets),
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-08 CVaR / Expected Shortfall ───────────────────────────────────────────


def cvar_expected_shortfall(
    prices: list[float],
    *,
    confidence: float = 0.95,
    notional: float = 10_000.0,
) -> dict[str, Any]:
    rets = _returns(prices)
    if len(rets) < 10:
        return {"ok": False, "reason": "insufficient_return_series", "methodology_version": METHODOLOGY_VERSION}
    sorted_rets = sorted(rets)
    idx = max(0, int((1 - confidence) * len(sorted_rets)) - 1)
    var_return = sorted_rets[idx]
    tail = [r for r in rets if r <= var_return]
    if not tail:
        return {"ok": False, "reason": "empty_tail", "methodology_version": METHODOLOGY_VERSION}
    es_return = _mean(tail)
    return {
        "ok": True,
        "confidence": confidence,
        "var_return": round(var_return, 8),
        "cvar_return": round(es_return, 8),
        "cvar_usd": round(abs(es_return * notional), 4),
        "tail_count": len(tail),
        "method": "historical_expected_shortfall",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-09 Monte Carlo ─────────────────────────────────────────────────────────


def monte_carlo_scenarios(
    prices: list[float],
    *,
    simulations: int = 1000,
    horizon_steps: int = 5,
    seed: int = 42,
    notional: float = 10_000.0,
) -> dict[str, Any]:
    rets = _returns(prices)
    if len(rets) < 10:
        return {"ok": False, "reason": "insufficient_return_series", "methodology_version": METHODOLOGY_VERSION}
    mu = _mean(rets)
    sigma = _std(rets) or 1e-9
    rng = random.Random(seed)
    terminal_returns: list[float] = []
    for _ in range(simulations):
        cumulative = 0.0
        for _step in range(horizon_steps):
            cumulative += rng.gauss(mu, sigma)
        terminal_returns.append(cumulative)
    terminal_returns.sort()
    p05 = terminal_returns[int(0.05 * len(terminal_returns))]
    p50 = terminal_returns[int(0.50 * len(terminal_returns))]
    p95 = terminal_returns[int(0.95 * len(terminal_returns))]
    return {
        "ok": True,
        "simulations": simulations,
        "horizon_steps": horizon_steps,
        "seed": seed,
        "model": "gaussian_iid_returns",
        "calibrated_mu": round(mu, 8),
        "calibrated_sigma": round(sigma, 8),
        "p05_return": round(p05, 8),
        "p50_return": round(p50, 8),
        "p95_return": round(p95, 8),
        "p05_usd": round(p05 * notional, 4),
        "p50_usd": round(p50 * notional, 4),
        "p95_usd": round(p95 * notional, 4),
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-10 Sharpe ──────────────────────────────────────────────────────────────


def sharpe_ratio(
    prices: list[float],
    *,
    risk_free_rate: float = 0.0,
    periods_per_year: int = 365,
) -> dict[str, Any]:
    rets = _returns(prices)
    if len(rets) < 2:
        return {"ok": False, "reason": "insufficient_return_series", "methodology_version": METHODOLOGY_VERSION}
    excess = [r - risk_free_rate / periods_per_year for r in rets]
    vol = _std(excess)
    if vol == 0:
        return {"ok": True, "sharpe": None, "reason": "zero_volatility", "methodology_version": METHODOLOGY_VERSION}
    sharpe = (_mean(excess) / vol) * math.sqrt(periods_per_year)
    return {
        "ok": True,
        "sharpe": round(sharpe, 6),
        "risk_free_rate": risk_free_rate,
        "periods_per_year": periods_per_year,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-11 Sortino ─────────────────────────────────────────────────────────────


def sortino_ratio(
    prices: list[float],
    *,
    mar: float = 0.0,
    periods_per_year: int = 365,
) -> dict[str, Any]:
    rets = _returns(prices)
    if len(rets) < 2:
        return {"ok": False, "reason": "insufficient_return_series", "methodology_version": METHODOLOGY_VERSION}
    downside = [min(0.0, r - mar) for r in rets]
    downside_dev = math.sqrt(_mean([d * d for d in downside]))
    if downside_dev == 0:
        return {"ok": True, "sortino": None, "reason": "no_downside_deviation", "methodology_version": METHODOLOGY_VERSION}
    sortino = (_mean(rets) - mar) / downside_dev * math.sqrt(periods_per_year)
    return {
        "ok": True,
        "sortino": round(sortino, 6),
        "mar": mar,
        "periods_per_year": periods_per_year,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-12 Maximum Drawdown Duration ───────────────────────────────────────────


def max_drawdown_duration(prices: list[float]) -> dict[str, Any]:
    if len(prices) < 2:
        return {"ok": False, "reason": "insufficient_price_series", "methodology_version": METHODOLOGY_VERSION}
    peak = prices[0]
    peak_idx = 0
    max_duration = 0
    current_duration = 0
    underwater_start: int | None = None
    for i, p in enumerate(prices):
        if p >= peak:
            peak = p
            peak_idx = i
            if underwater_start is not None:
                duration = i - underwater_start
                max_duration = max(max_duration, duration)
            underwater_start = None
            current_duration = 0
        else:
            if underwater_start is None:
                underwater_start = peak_idx
            current_duration = i - underwater_start
            max_duration = max(max_duration, current_duration)
    unrecovered = underwater_start is not None and prices[-1] < peak
    return {
        "ok": True,
        "max_drawdown_duration_periods": max_duration,
        "unrecovered_at_end": unrecovered,
        "convention": "peak_to_recovery_periods",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-13 / CAP-14 Beta ───────────────────────────────────────────────────────


def beta_to_benchmark(asset_prices: list[float], benchmark_prices: list[float]) -> dict[str, Any]:
    a_rets = _returns(asset_prices)
    b_rets = _returns(benchmark_prices)
    n = min(len(a_rets), len(b_rets))
    if n < 3:
        return {"ok": False, "reason": "insufficient_aligned_returns", "methodology_version": METHODOLOGY_VERSION}
    a_slice, b_slice = a_rets[-n:], b_rets[-n:]
    b_var = _var(b_slice)
    if b_var == 0:
        return {"ok": False, "reason": "zero_benchmark_variance", "methodology_version": METHODOLOGY_VERSION}
    beta = _cov(a_slice, b_slice) / b_var
    return {
        "ok": True,
        "beta": round(beta, 6),
        "method": "covariance_over_variance",
        "sample_count": n,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-15 Correlation Decay Matrix ────────────────────────────────────────────


def correlation_decay_matrix(
    series_a: list[float],
    series_b: list[float],
    *,
    lags: tuple[int, ...] = (0, 1, 3, 5, 10),
) -> dict[str, Any]:
    a_rets = _returns(series_a)
    b_rets = _returns(series_b)
    matrix: dict[str, float | None] = {}
    for lag in lags:
        n = min(len(a_rets), len(b_rets)) - lag
        if n < 3:
            matrix[f"lag_{lag}"] = None
            continue
        a_slice = a_rets[-n - lag : -lag or None]
        b_slice = b_rets[-n:]
        sa, sb = _std(a_slice), _std(b_slice)
        if sa == 0 or sb == 0:
            matrix[f"lag_{lag}"] = None
        else:
            matrix[f"lag_{lag}"] = round(_cov(a_slice, b_slice) / (sa * sb), 6)
    return {
        "ok": True,
        "lags": list(lags),
        "matrix": matrix,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-16 De-Peg Risk Score ───────────────────────────────────────────────────


def depeg_risk_score(
    price: float,
    *,
    peg: float = 1.0,
    horizon_hours: float = 24.0,
    volatility: float | None = None,
) -> dict[str, Any]:
    if peg <= 0:
        return {"ok": False, "reason": "invalid_peg", "methodology_version": METHODOLOGY_VERSION}
    deviation_bps = abs(price - peg) / peg * 10_000
    vol = volatility if volatility is not None else 0.01
    score = min(100.0, deviation_bps / 10.0 + vol * 1000)
    return {
        "ok": True,
        "score": round(score, 2),
        "score_type": "heuristic_risk_score_not_calibrated_probability",
        "deviation_bps": round(deviation_bps, 4),
        "peg_reference": peg,
        "horizon_hours": horizon_hours,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-17 Large-vs-Small Trade Participation ──────────────────────────────────


def large_vs_small_trade_participation(
    trades: list[dict[str, Any]],
    *,
    large_threshold_usd: float = 50_000.0,
) -> dict[str, Any]:
    if not trades:
        return {"ok": False, "reason": "no_trades", "methodology_version": METHODOLOGY_VERSION}
    large = 0.0
    small = 0.0
    for t in trades:
        notional = float(t.get("notional_usd") or t.get("size_usd") or 0)
        if notional >= large_threshold_usd:
            large += notional
        else:
            small += notional
    total = large + small
    if total <= 0:
        return {"ok": False, "reason": "zero_notional", "methodology_version": METHODOLOGY_VERSION}
    return {
        "ok": True,
        "ratio_large_to_small": round(large / small, 6) if small > 0 else None,
        "large_participation_pct": round(large / total * 100, 4),
        "threshold_usd": large_threshold_usd,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-18 Maker/Taker Net Delta ───────────────────────────────────────────────


def maker_taker_net_delta(trades: list[dict[str, Any]]) -> dict[str, Any]:
    maker = 0.0
    taker = 0.0
    unknown = 0.0
    for t in trades:
        side = str(t.get("aggressor") or t.get("taker_side") or "UNKNOWN").upper()
        notional = float(t.get("notional_usd") or 0)
        if side in {"MAKER", "PASSIVE"}:
            maker += notional
        elif side in {"TAKER", "AGGRESSOR", "BUY", "SELL"}:
            taker += notional
        else:
            unknown += notional
    return {
        "ok": True,
        "maker_notional": round(maker, 4),
        "taker_notional": round(taker, 4),
        "net_delta": round(taker - maker, 4),
        "unknown_notional": round(unknown, 4),
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-19 OI Momentum Delta ───────────────────────────────────────────────────


def oi_momentum_delta(oi_series: list[float], *, horizon: int = 5) -> dict[str, Any]:
    if len(oi_series) < horizon + 1:
        return {"ok": False, "reason": "insufficient_oi_history", "methodology_version": METHODOLOGY_VERSION}
    current = oi_series[-1]
    prior = oi_series[-1 - horizon]
    if prior == 0:
        return {"ok": False, "reason": "zero_prior_oi", "methodology_version": METHODOLOGY_VERSION}
    delta = current - prior
    rate = delta / prior
    return {
        "ok": True,
        "oi_delta": round(delta, 4),
        "oi_momentum_rate": round(rate, 6),
        "horizon": horizon,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-20 Funding Momentum Shift ──────────────────────────────────────────────


def funding_momentum_shift(funding_rates: list[float], *, horizon: int = 3) -> dict[str, Any]:
    if len(funding_rates) < horizon + 1:
        return {"ok": False, "reason": "insufficient_funding_history", "methodology_version": METHODOLOGY_VERSION}
    recent = funding_rates[-horizon:]
    prior = funding_rates[-(horizon * 2) : -horizon]
    if not prior:
        return {"ok": False, "reason": "missing_prior_window", "methodology_version": METHODOLOGY_VERSION}
    shift = _mean(recent) - _mean(prior)
    sign_change = (_mean(prior) >= 0) != (_mean(recent) >= 0)
    return {
        "ok": True,
        "level": round(_mean(recent), 8),
        "shift": round(shift, 8),
        "sign_change": sign_change,
        "horizon": horizon,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-21 Derivative-to-Spot Volume Multiple ──────────────────────────────────


def derivative_to_spot_volume_multiple(
    derivative_volume: float,
    spot_volume: float,
    *,
    derivative_universe: str = "perpetual_futures",
) -> dict[str, Any]:
    if spot_volume <= 0:
        return {"ok": False, "reason": "zero_or_missing_spot_volume", "methodology_version": METHODOLOGY_VERSION}
    return {
        "ok": True,
        "multiple": round(derivative_volume / spot_volume, 6),
        "derivative_volume": derivative_volume,
        "spot_volume": spot_volume,
        "derivative_universe": derivative_universe,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-22 Effective Basis Yield ───────────────────────────────────────────────


def effective_basis_yield(
    spot_price: float,
    derivative_price: float,
    *,
    holding_days: float = 30.0,
    fees_bps: float = 10.0,
    funding_carry_bps: float = 0.0,
    slippage_bps: float = 5.0,
) -> dict[str, Any]:
    if spot_price <= 0:
        return {"ok": False, "reason": "invalid_spot_price", "methodology_version": METHODOLOGY_VERSION}
    gross_basis = (derivative_price - spot_price) / spot_price
    gross_annual = gross_basis * (365.0 / holding_days)
    net_bps = fees_bps + slippage_bps - funding_carry_bps
    net_annual = gross_annual - net_bps / 10_000
    return {
        "ok": True,
        "gross_basis": round(gross_basis, 8),
        "gross_annualized_yield": round(gross_annual, 8),
        "net_annualized_yield": round(net_annual, 8),
        "holding_days": holding_days,
        "costs_bps": {"fees": fees_bps, "slippage": slippage_bps, "funding_carry": funding_carry_bps},
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-23 Delta-Neutral Validator ─────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class PositionLeg:
    symbol: str
    quantity: float
    delta: float
    contract_multiplier: float = 1.0


def delta_neutral_validator(legs: list[PositionLeg], *, tolerance: float = 0.05) -> dict[str, Any]:
    if not legs:
        return {"ok": False, "reason": "no_legs", "methodology_version": METHODOLOGY_VERSION}
    net_delta = sum(leg.quantity * leg.delta * leg.contract_multiplier for leg in legs)
    neutral = abs(net_delta) <= tolerance
    return {
        "ok": True,
        "net_delta": round(net_delta, 8),
        "residual_delta": round(net_delta, 8),
        "neutral": neutral,
        "tolerance": tolerance,
        "leg_count": len(legs),
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-24 Funding Spread Matrix ───────────────────────────────────────────────


def funding_spread_matrix(venue_rates: dict[str, float | None], *, period_hours: float = 8.0) -> dict[str, Any]:
    available = {k: v for k, v in venue_rates.items() if v is not None}
    if len(available) < 2:
        return {"ok": False, "reason": "insufficient_venues", "methodology_version": METHODOLOGY_VERSION}
    venues = sorted(available.keys())
    matrix: dict[str, dict[str, float | None]] = {}
    for a in venues:
        matrix[a] = {}
        for b in venues:
            if a == b:
                matrix[a][b] = 0.0
            else:
                matrix[a][b] = round(available[a] - available[b], 8)  # type: ignore[operator]
    return {
        "ok": True,
        "matrix": matrix,
        "period_hours": period_hours,
        "venues_unavailable": [k for k, v in venue_rates.items() if v is None],
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-25 Liquidation Cascade Risk ────────────────────────────────────────────


def estimated_liquidation_cascade_risk(
    *,
    oi_usd: float,
    leverage_proxy: float,
    funding_rate: float,
    depth_usd: float,
    volatility: float,
) -> dict[str, Any]:
    if depth_usd <= 0:
        return {"ok": False, "reason": "missing_depth", "methodology_version": METHODOLOGY_VERSION}
    pressure = (oi_usd * leverage_proxy * abs(funding_rate) * volatility) / depth_usd
    score = min(100.0, pressure * 100)
    return {
        "ok": True,
        "estimated_risk_score": round(score, 2),
        "output_type": "model_derived_estimate_not_exact_liquidation_map",
        "drivers": {
            "oi_usd": oi_usd,
            "leverage_proxy": leverage_proxy,
            "funding_rate": funding_rate,
            "depth_usd": depth_usd,
            "volatility": volatility,
        },
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-26 IV Skew ───────────────────────────────────────────────────────────────


def iv_skew(
    call_iv: float | None,
    put_iv: float | None,
    *,
    tenor_days: float = 30.0,
    convention: str = "put_minus_call",
) -> dict[str, Any]:
    if call_iv is None or put_iv is None:
        return {"ok": False, "reason": "missing_options_iv", "methodology_version": METHODOLOGY_VERSION}
    skew = put_iv - call_iv if convention == "put_minus_call" else call_iv - put_iv
    return {
        "ok": True,
        "iv_skew": round(skew, 6),
        "call_iv": call_iv,
        "put_iv": put_iv,
        "tenor_days": tenor_days,
        "convention": convention,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-27 Put/Call Ratio ────────────────────────────────────────────────────────


def put_call_ratio(
    put_volume: float | None,
    call_volume: float | None,
    *,
    basis: Literal["volume", "oi"] = "volume",
) -> dict[str, Any]:
    if put_volume is None or call_volume is None or call_volume <= 0:
        return {"ok": False, "reason": "missing_or_zero_denominator", "methodology_version": METHODOLOGY_VERSION}
    return {
        "ok": True,
        "ratio": round(put_volume / call_volume, 6),
        "basis": basis,
        "put": put_volume,
        "call": call_volume,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-28 NVT ─────────────────────────────────────────────────────────────────


def nvt_ratio(
    market_cap: float,
    onchain_tx_value: float | None,
    *,
    cex_volume_proxy: float | None = None,
) -> dict[str, Any]:
    if onchain_tx_value is not None and onchain_tx_value > 0:
        return {
            "ok": True,
            "nvt": round(market_cap / onchain_tx_value, 4),
            "source": "on_chain_tx_value",
            "proxy": False,
            "methodology_version": METHODOLOGY_VERSION,
        }
    if cex_volume_proxy is not None and cex_volume_proxy > 0:
        return {
            "ok": True,
            "nvt": round(market_cap / cex_volume_proxy, 4),
            "source": "cex_volume",
            "proxy": True,
            "proxy_label": "PROXY",
            "methodology_version": METHODOLOGY_VERSION,
        }
    return {"ok": False, "reason": "missing_tx_value", "methodology_version": METHODOLOGY_VERSION}
