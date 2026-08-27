"""Multi-Factor Alpha Ranking — cross-asset composite score."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from bd_platform.market_rankings import market_rankings

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 90.0
_DEFAULT_FACTORS = ("momentum", "liquidity", "trend", "volatility_penalty")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _momentum_score(change_24h: float | None) -> float:
    ch = float(change_24h or 0)
    return _clamp(50 + ch * 4)  # -12.5% -> 0, +12.5% -> 100


def _liquidity_score(volume: float | None, mcap: float | None) -> float:
    vol = float(volume or 0)
    cap = float(mcap or 1)
    if cap <= 0:
        return 50.0
    ratio = vol / cap
    return _clamp(ratio * 500)  # 20% vol/mcap -> 100


def _trend_score(sparkline: list[float] | None) -> float:
    if not sparkline or len(sparkline) < 4:
        return 50.0
    start = float(sparkline[0] or 0)
    end = float(sparkline[-1] or 0)
    if start <= 0:
        return 50.0
    pct = (end - start) / start * 100
    return _clamp(50 + pct * 3)


def _volatility_penalty(change_24h: float | None) -> float:
    ch = abs(float(change_24h or 0))
    return _clamp(100 - ch * 5)  # high vol reduces alpha


def _composite(factors: dict[str, float]) -> float:
    weights = {"momentum": 0.35, "liquidity": 0.25, "trend": 0.25, "volatility_penalty": 0.15}
    return round(sum(factors[k] * weights[k] for k in _DEFAULT_FACTORS), 2)


def _rank_coin(row: dict[str, Any], *, btc_change: float) -> dict[str, Any]:
    sym = str(row.get("symbol") or "").upper()
    ch = float(row.get("change_24h_pct") or 0)
    factors = {
        "momentum": _momentum_score(ch),
        "liquidity": _liquidity_score(row.get("volume_24h_usd"), row.get("market_cap_usd")),
        "trend": _trend_score(row.get("sparkline_7d")),
        "volatility_penalty": _volatility_penalty(ch),
    }
    if sym != "BTC":
        rel = ch - btc_change
        factors["relative_strength"] = _clamp(50 + rel * 5)
    alpha = _composite(factors)
    if sym != "BTC" and "relative_strength" in factors:
        alpha = round(alpha * 0.85 + factors["relative_strength"] * 0.15, 2)
    return {
        "symbol": sym,
        "name": row.get("name"),
        "rank_by_mcap": row.get("rank"),
        "price_usd": row.get("price_usd"),
        "change_24h_pct": ch,
        "alpha_score": alpha,
        "factors": factors,
        "alerts": _alpha_alerts(alpha, ch),
    }


def _alpha_alerts(score: float, change: float) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    if score >= 75:
        alerts.append({"level": "high", "code": "ALPHA_LEADER", "message": f"Alpha score {score:.0f} — top quartile"})
    elif score <= 30:
        alerts.append({"level": "warn", "code": "ALPHA_LAGGARD", "message": f"Alpha score {score:.0f} — weak factor profile"})
    if change >= 8:
        alerts.append({"level": "medium", "code": "MOMENTUM_SPIKE", "message": f"+{change:.1f}% 24h momentum"})
    return alerts


async def rank_assets_by_alpha_factors(*, limit: int = 25) -> dict[str, Any]:
    """CAP978 ID 127 — ranked multi-factor alpha table."""
    t0 = time.perf_counter()
    cache_key = f"alpha:{limit}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        return cached[1]

    market = await market_rankings(limit=min(limit, 50))
    coins = market.get("coins") or []
    stable = {"USDT", "USDC", "DAI", "BUSD", "TUSD", "USDE", "FDUSD"}
    coins = [c for c in coins if str(c.get("symbol", "")).upper() not in stable]
    if not coins:
        return {
            "success": False,
            "ok": False,
            "data_state": "MISSING",
            "error": "market_data_unavailable",
            "timestamp": _utcnow(),
        }

    btc_change = 0.0
    for c in coins:
        if str(c.get("symbol")).upper() == "BTC":
            btc_change = float(c.get("change_24h_pct") or 0)
            break

    ranked = [_rank_coin(c, btc_change=btc_change) for c in coins]
    ranked.sort(key=lambda x: x["alpha_score"], reverse=True)
    for i, row in enumerate(ranked, start=1):
        row["alpha_rank"] = i

    top = ranked[:limit]
    result = {
        "success": True,
        "ok": True,
        "capability_id": 127,
        "surface": "multi_factor_alpha_ranking",
        "count": len(top),
        "rankings": top,
        "factor_model": list(_DEFAULT_FACTORS) + ["relative_strength"],
        "btc_benchmark_change_24h_pct": btc_change,
        "data_state": "LIVE",
        "sources": [market.get("style", "coingecko")],
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
        "disclaimer": "Free-tier factor model; institutional factor library = expandable",
    }
    _CACHE[cache_key] = (time.time(), result)
    return result
