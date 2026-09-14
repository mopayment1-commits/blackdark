"""
Walk-forward backtesting harness for Decision Intelligence Engine (#48).

Gradual pipeline: prototype → backtest → paper → live.
Computes risk-adjusted metrics: Sharpe, max drawdown, win rate.
"""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.WalkForward")

ACCEPTANCE = {
    "sharpe_min": 1.5,
    "max_drawdown_pct": 15.0,
    "win_rate_min": 0.55,
    "backtest_years_min": 2.0,
}


async def _fetch_hourly_closes(symbol: str, *, limit: int = 2000) -> list[float]:
    pair = f"{symbol.upper()}USDT"
    if not pair.isalnum():
        return []
    url = "https://api.binance.com/api/v3/klines"
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params={"symbol": pair, "interval": "1h", "limit": limit}) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [float(row[4]) for row in data]
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        return []


def _signal_from_features(closes: list[float], idx: int) -> int:
    """
    Point-in-time signal: +1 long, -1 short, 0 flat.
    Uses momentum + mean-reversion blend (no future data).
    """
    if idx < 30:
        return 0
    window = closes[idx - 24 : idx + 1]
    ret = (window[-1] / window[0] - 1) * 100
    vol = sum(abs(window[i] / window[i - 1] - 1) for i in range(1, len(window))) / max(len(window) - 1, 1)
    if vol > 0.03 and abs(ret) > 3:
        return -1 if ret > 0 else 1  # mean-revert in high vol
    if ret > 1.5:
        return 1
    if ret < -1.5:
        return -1
    return 0


def _compute_metrics(returns: list[float]) -> dict[str, float]:
    if not returns:
        return {
            "sharpe": 0.0,
            "max_drawdown_pct": 100.0,
            "win_rate": 0.0,
            "total_return_pct": 0.0,
            "trade_count": 0,
        }

    wins = sum(1 for r in returns if r > 0)
    win_rate = wins / len(returns)
    mean_r = sum(returns) / len(returns)
    std_r = (sum((r - mean_r) ** 2 for r in returns) / len(returns)) ** 0.5
    sharpe = (mean_r / std_r) * math.sqrt(252 * 24) if std_r > 1e-9 else 0.0  # hourly → annualized

    equity = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        equity *= 1 + r / 100
        peak = max(peak, equity)
        dd = (peak - equity) / peak * 100 if peak > 0 else 0
        max_dd = max(max_dd, dd)

    total_return = (equity - 1) * 100
    return {
        "sharpe": round(sharpe, 3),
        "max_drawdown_pct": round(max_dd, 2),
        "win_rate": round(win_rate, 4),
        "total_return_pct": round(total_return, 2),
        "trade_count": len(returns),
    }


def walk_forward_backtest(
    closes: list[float],
    *,
    train_window: int = 168,
    test_window: int = 24,
    step: int = 24,
) -> dict[str, Any]:
    """
    Rolling walk-forward: train on past window, test on next window.
    Returns aggregated OOS metrics.
    """
    if len(closes) < train_window + test_window + 10:
        return {"ok": False, "error": "insufficient_data", "bars": len(closes)}

    all_oos_returns: list[float] = []
    folds = 0
    i = train_window
    while i + test_window < len(closes):
        test_slice = closes[i : i + test_window]
        position = 0
        fold_returns: list[float] = []
        for j in range(1, len(test_slice)):
            sig = _signal_from_features(closes, i + j - 1)
            if sig == 0:
                continue
            bar_ret = (test_slice[j] / test_slice[j - 1] - 1) * 100
            fold_returns.append(bar_ret * sig)
        all_oos_returns.extend(fold_returns)
        folds += 1
        i += step

    metrics = _compute_metrics(all_oos_returns)
    hours = len(closes)
    years = hours / (365.25 * 24)

    acceptance = {
        "sharpe_met": metrics["sharpe"] >= ACCEPTANCE["sharpe_min"],
        "drawdown_met": metrics["max_drawdown_pct"] <= ACCEPTANCE["max_drawdown_pct"],
        "win_rate_met": metrics["win_rate"] >= ACCEPTANCE["win_rate_min"],
        "backtest_years_met": years >= ACCEPTANCE["backtest_years_min"],
    }
    all_met = all(acceptance.values())

    stage = "prototype"
    if metrics["trade_count"] >= 50:
        stage = "backtest"
    if all_met:
        stage = "paper_trading"
    if all_met and metrics["sharpe"] >= 2.0:
        stage = "live_candidate"

    return {
        "ok": True,
        "method": "walk_forward",
        "folds": folds,
        "bars": len(closes),
        "backtest_years": round(years, 2),
        "metrics": metrics,
        "acceptance_criteria": ACCEPTANCE,
        "acceptance": acceptance,
        "acceptance_met": all_met,
        "pipeline_stage": stage,
        "note": (
            "Gradual pipeline — full acceptance (Sharpe≥1.5, DD≤15%, WR≥55%, ≥2yr) "
            "requires sufficient OOS history; prototype signals used until criteria met."
        ),
    }


async def run_walk_forward_backtest(
    asset: str = "BTC",
    *,
    limit: int = 2000,
) -> dict[str, Any]:
    """Fetch klines and run walk-forward backtest."""
    closes = await _fetch_hourly_closes(asset, limit=limit)
    if not closes:
        return {"ok": False, "error": "klines_unavailable", "asset": asset}
    result = walk_forward_backtest(closes)
    result["asset"] = asset.upper()
    return result
