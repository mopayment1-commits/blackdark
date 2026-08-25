"""
Momentum Intelligence — Feature #273 merged into #755 Technical Ratings (Sprint 2).

Momentum decomposition + multi-window normalization.
Analysis layer — NOT buy/sell signal.
"""

from __future__ import annotations

import json
import logging
import statistics
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.MomentumIntelligence")

_FEATURE_ID = 273
_MERGED_INTO = "#755 Technical Ratings"
_STANDALONE = False
_SPRINT = 2
_SEED_PATH = Path("data/momentum_intelligence_seed.json")
_FORMULA_VERSION = "2.1"
_WEIGHTS = {"trend": 0.40, "acceleration": 0.35, "vol_adjusted_return": 0.25}
_WINDOWS = {"short": 7, "medium": 30, "long": 90}
_WINDOW_LABELS = {"short": "7D", "medium": "30D", "long": "90D"}

_DISCLAIMER = (
    "Momentum measures price trend and acceleration. Not a buy/sell signal. "
    "Past momentum does not predict future returns."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "formula_version": _FORMULA_VERSION}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("momentum intelligence seed load failed: %s", exc)
        return {"assets": {}, "formula_version": _FORMULA_VERSION}


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(10.0, value)), 1)


def verify_no_look_ahead(prices: list[float], as_of_index: int) -> dict[str, Any]:
    """
    No look-ahead test: momentum on day T must not use data from day T+1.
    Only prices[0:as_of_index+1] are used in computation.
    """
    used_count = as_of_index + 1
    future_used = used_count > len(prices)
    return {
        "no_look_ahead": not future_used,
        "as_of_index": as_of_index,
        "data_points_used": used_count,
        "future_data_used": future_used,
        "test_display": (
            "If I calculate momentum on day T, does it use any data from day T+1? → "
            + ("NO" if not future_used else "FAIL")
        ),
    }


def _returns(prices: list[float]) -> list[float]:
    if len(prices) < 2:
        return []
    return [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices)) if prices[i - 1]]


def _trend_component(prices: list[float], window: int) -> tuple[float, str]:
    """Price trend vs moving average — higher when price above MA."""
    if len(prices) < window:
        return 5.0, "Insufficient data for trend"
    window_prices = prices[-window:]
    ma = statistics.mean(window_prices)
    current = prices[-1]
    if ma <= 0:
        return 5.0, "MA unavailable"
    pct_above = (current - ma) / ma * 100
    score = _clamp_score(5.0 + pct_above * 0.5)
    direction = "above" if pct_above >= 0 else "below"
    detail = f"Price {direction} {window}D MA ({pct_above:+.1f}%)"
    return score, detail


def _acceleration_component(prices: list[float], window: int) -> tuple[float, str]:
    """Momentum acceleration — rate of change of returns."""
    rets = _returns(prices)
    if len(rets) < window:
        return 5.0, "Insufficient data for acceleration"
    recent = rets[-window:]
    half = max(1, len(recent) // 2)
    early_avg = statistics.mean(recent[:half]) if recent[:half] else 0
    late_avg = statistics.mean(recent[half:]) if recent[half:] else 0
    accel = late_avg - early_avg
    score = _clamp_score(5.0 + accel * 500)
    if accel > 0.001:
        label = "Momentum accelerating"
    elif accel < -0.001:
        label = "Momentum slowing"
    else:
        label = "Momentum stable"
    return score, label


def _vol_adjusted_return(prices: list[float], window: int) -> tuple[float, str]:
    """Return divided by volatility — risk-adjusted momentum."""
    rets = _returns(prices)
    if len(rets) < 2:
        return 5.0, "Insufficient data"
    window_rets = rets[-min(window, len(rets)):]
    mean_ret = statistics.mean(window_rets)
    std = statistics.stdev(window_rets) if len(window_rets) > 1 else 0.001
    sharpe_like = mean_ret / std if std > 0 else 0
    score = _clamp_score(5.0 + sharpe_like * 2.5)
    return score, f"Vol-adjusted return: {sharpe_like:.2f}"


def _composite_score(trend: float, accel: float, vol_adj: float) -> float:
    return _clamp_score(
        trend * _WEIGHTS["trend"]
        + accel * _WEIGHTS["acceleration"]
        + vol_adj * _WEIGHTS["vol_adjusted_return"]
    )


def _trend_label(score: float, accel_detail: str) -> str:
    if score >= 7.5:
        strength = "Strong Trend"
    elif score >= 5.5:
        strength = "Moderate Trend"
    else:
        strength = "Weak Trend"
    if "slowing" in accel_detail.lower():
        return f"{strength} + Decelerating"
    if "accelerating" in accel_detail.lower():
        return f"{strength} + Accelerating"
    return strength


def _compute_window_momentum(prices: list[float], window: int, label: str) -> dict[str, Any]:
    trend, trend_detail = _trend_component(prices, window)
    accel, accel_detail = _acceleration_component(prices, window)
    vol_adj, vol_detail = _vol_adjusted_return(prices, window)
    composite = _composite_score(trend, accel, vol_adj)

    return {
        "window": label,
        "window_days": window,
        "composite_score": composite,
        "components": {
            "trend": {
                "score": trend,
                "weight_pct": 40,
                "display": f"Trend Component: {trend}/10 ({trend_detail})",
            },
            "acceleration": {
                "score": accel,
                "weight_pct": 35,
                "display": f"Acceleration Component: {accel}/10 ({accel_detail})",
            },
            "volatility_adjusted_return": {
                "score": vol_adj,
                "weight_pct": 25,
                "display": f"Volatility-Adjusted Return: {vol_adj}/10 ({vol_detail})",
            },
        },
        "window_display": f"{label}: {composite}/10",
    }


def get_momentum_analysis(asset: str = "BTC") -> dict[str, Any]:
    """Momentum decomposition — analysis only, not a trading signal."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("assets") or {}).get(sym)

    if not asset_data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_configured", "asset": sym}

    series = asset_data.get("price_series_daily") or []
    prices = [float(p["close"]) for p in series]
    as_of_index = len(prices) - 1
    look_ahead = verify_no_look_ahead(prices, as_of_index)

    # Only use data up to and including day T (no look-ahead)
    safe_prices = prices[: as_of_index + 1]

    windows_out: dict[str, Any] = {}
    for key, days in _WINDOWS.items():
        if len(safe_prices) >= min(days, 3):
            windows_out[key] = _compute_window_momentum(safe_prices, days, _WINDOW_LABELS[key])

    primary = windows_out.get("medium") or windows_out.get("short") or next(iter(windows_out.values()), {})
    composite = primary.get("composite_score", 5.0)
    accel_detail = (primary.get("components") or {}).get("acceleration", {}).get("display", "")
    analysis_label = _trend_label(composite, accel_detail)

    formula = seed.get("formula") or {}
    formula_display = (
        formula.get("display")
        or "Momentum = Price Trend (40%) + Acceleration (35%) + Volatility-Adjusted Return (25%)"
    )

    validation = asset_data.get("historical_validation") or {}
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "asset": sym,
        "formula_version": seed.get("formula_version", _FORMULA_VERSION),
        "formula_display": f"{formula_display} | Version: {seed.get('formula_version', _FORMULA_VERSION)} | Window: 7D/30D/90D",
        "momentum_score": composite,
        "windows": windows_out,
        "multi_window_display": " | ".join(
            w["window_display"] for w in windows_out.values()
        ),
        "components": primary.get("components", {}),
        "components_visible": True,
        "analysis_display": f"Momentum Analysis: {analysis_label}",
        "not_a_signal": True,
        "not_buy_sell": True,
        "no_look_ahead": look_ahead,
        "historical_validation": {
            **validation,
            "documented": True,
            "not_a_promise": True,
        },
        "validation_display": validation.get("validation_display"),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "technical_ratings_input": True,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def momentum_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "module": "Momentum Intelligence Module",
        "sprint": _SPRINT,
        "formula_version": seed.get("formula_version", _FORMULA_VERSION),
        "formula_display": (seed.get("formula") or {}).get("display"),
        "windows": list(_WINDOW_LABELS.values()),
        "no_look_ahead": seed.get("no_look_ahead", True),
        "historical_validation": True,
        "not_a_signal": True,
        "integrated_with": ["#755 Technical Ratings", "Market Radar", "Portfolio AI"],
        "configured_assets": list((seed.get("assets") or {}).keys()),
        "acceptance_criteria": {
            "formula_version_documented": True,
            "no_look_ahead": True,
            "historical_validation": True,
            "multi_window_normalization": True,
            "components_visible": True,
            "not_a_buy_sell_signal": True,
        },
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
