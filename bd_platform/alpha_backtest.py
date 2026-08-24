"""
Alpha Engine backtest metrics (#13) — realistic MVP thresholds.

Targets: Sharpe ≥0.8, Max DD ≤25%, Win Rate ≥50-55%
(not institutional Sharpe ≥1.5 / DD ≤15% — improve over time).
"""

from __future__ import annotations

import math
from typing import Any


MVP_THRESHOLDS = {
    "sharpe_min": 0.8,
    "max_drawdown_pct_max": 25.0,
    "win_rate_min": 0.50,
    "backtest_years_min": 2,
    "latency_minutes_max": 5,
}


def _max_drawdown(equity: list[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            dd = (peak - v) / peak
            max_dd = max(max_dd, dd)
    return round(max_dd * 100, 2)


def _sharpe(returns: list[float], *, periods_per_year: int = 365) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var) if var > 0 else 0.0
    if std == 0:
        return 0.0
    return round((mean / std) * math.sqrt(periods_per_year), 3)


def walk_forward_backtest(
  daily_returns: list[float],
  *,
  train_window: int = 180,
  test_window: int = 30,
) -> dict[str, Any]:
    """
    Simple walk-forward evaluation on daily return series.

    Signal rule (MVP): go long when rolling mean > 0, flat otherwise.
    """
    if len(daily_returns) < train_window + test_window:
        return {
            "ok": False,
            "error": "insufficient_history",
            "min_days": train_window + test_window,
            "available_days": len(daily_returns),
        }

    equity = [1.0]
    strategy_returns: list[float] = []
    wins = 0
    trades = 0
    i = train_window
    while i + test_window <= len(daily_returns):
        train = daily_returns[i - train_window : i]
        mu = sum(train) / len(train)
        for r in daily_returns[i : i + test_window]:
            position = 1.0 if mu > 0 else 0.0
            sr = r * position
            strategy_returns.append(sr)
            equity.append(equity[-1] * (1 + sr))
            if position > 0:
                trades += 1
                if sr > 0:
                    wins += 1
        i += test_window

    sharpe = _sharpe(strategy_returns)
    max_dd = _max_drawdown(equity)
    win_rate = round(wins / trades, 3) if trades else 0.0
    years = round(len(daily_returns) / 365, 2)

    return {
        "ok": True,
        "method": "walk_forward_mvp",
        "model": "rule_based_momentum_gate",
        "periods": len(strategy_returns),
        "years_approx": years,
        "sharpe": sharpe,
        "max_drawdown_pct": max_dd,
        "win_rate": win_rate,
        "mvp_thresholds": MVP_THRESHOLDS,
        "acceptance": {
            "sharpe_met": sharpe >= MVP_THRESHOLDS["sharpe_min"],
            "max_drawdown_met": max_dd <= MVP_THRESHOLDS["max_drawdown_pct_max"],
            "win_rate_met": win_rate >= MVP_THRESHOLDS["win_rate_min"],
            "backtest_years_met": years >= MVP_THRESHOLDS["backtest_years_min"],
        },
        "note": "MVP thresholds (Sharpe≥0.8, DD≤25%) — institutional targets deferred",
    }


async def alpha_backtest_summary(symbol: str = "BTC") -> dict[str, Any]:
    """Run MVP backtest using CoinGecko historical proxy (market_chart)."""
    import os

    import aiohttp

    from blackdark.ingestion.coingecko_connector import coingecko_id_for

    sym = symbol.upper()
    cg_id = coingecko_id_for(sym) or "bitcoin"
    url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
    params = {"vs_currency": "usd", "days": "730", "interval": "daily"}
    headers = {"User-Agent": "BLACKDARK/1.0"}
    key = (os.getenv("COINGECKO_API_KEY") or "").strip()
    if key:
        headers["x-cg-demo-api-key"] = key

    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return {"ok": False, "error": f"coingecko_http_{resp.status}"}
                data = await resp.json()
    except (aiohttp.ClientError, TimeoutError) as exc:
        return {"ok": False, "error": str(exc)}

    prices = [float(p[1]) for p in (data.get("prices") or []) if len(p) >= 2]
    daily_returns: list[float] = []
    for i in range(1, len(prices)):
        prev, curr = prices[i - 1], prices[i]
        if prev > 0:
            daily_returns.append((curr - prev) / prev)

    result = walk_forward_backtest(daily_returns)
    result["asset"] = sym
    result["data_source"] = "coingecko_market_chart_730d"

    try:
        from blackdark.ingestion.historical_flat_archive import backtest_coverage_years

        archive = backtest_coverage_years(symbol=sym, interval="1d")
        if archive.get("years_available"):
            result["archive_years"] = archive.get("years_available")
            result["user_facing_note"] = archive.get("user_facing_note")
            if archive.get("meets_2y_backtest"):
                result["acceptance"]["backtest_years_met"] = True
    except Exception:
        pass

    return result
