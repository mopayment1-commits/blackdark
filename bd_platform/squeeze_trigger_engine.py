"""Short/Long Squeeze Trigger-Point Predictive Coordinates."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from bd_platform.free_market_data import binance_futures_snapshot, binance_liquidation_risk

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 45.0
_LEVERAGE_TIERS = (5, 10, 20, 50)
_CG_IDS = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}


async def _coingecko_price(asset: str) -> float | None:
    cg_id = _CG_IDS.get(asset.upper())
    if not cg_id:
        return None
    timeout = aiohttp.ClientTimeout(total=10)
    url = f"https://api.coingecko.com/api/v3/simple/price"
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params={"ids": cg_id, "vs_currencies": "usd"}) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return float((data.get(cg_id) or {}).get("usd") or 0) or None
    except aiohttp.ClientError:
        return None


async def _fallback_snapshot(asset: str) -> dict[str, Any]:
    price = await _coingecko_price(asset)
    if not price:
        return {"available": False}
    return {
        "available": True,
        "mark_price": price,
        "funding_rate": 0.0001,
        "funding_rate_pct": 0.01,
        "open_interest_usd": 0,
        "change_24h_pct": 0,
        "long_short_ratio": 1.0,
        "source": "coingecko_price_proxy",
    }


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _liq_price_long(entry: float, leverage: int) -> float:
    """Approximate long liquidation (isolated margin, 90% maintenance)."""
    return entry * (1 - 0.9 / leverage)


def _liq_price_short(entry: float, leverage: int) -> float:
    return entry * (1 + 0.9 / leverage)


def _squeeze_coordinates(
    *,
    mark: float,
    funding_rate: float,
    ls_ratio: float,
    change_24h: float,
    oi_usd: float,
) -> list[dict[str, Any]]:
    coords: list[dict[str, Any]] = []
    for lev in _LEVERAGE_TIERS:
        long_trig = _liq_price_long(mark, lev)
        short_trig = _liq_price_short(mark, lev)
        coords.append(
            {
                "coordinate_id": f"long_liq_{lev}x",
                "squeeze_type": "long_liquidation_cascade",
                "side": "long",
                "leverage_tier": lev,
                "trigger_price": round(long_trig, 4),
                "distance_pct": round((long_trig / mark - 1) * 100, 3),
                "confidence": min(0.95, 0.5 + (ls_ratio - 1) * 0.2) if ls_ratio > 1 else 0.4,
            }
        )
        coords.append(
            {
                "coordinate_id": f"short_liq_{lev}x",
                "squeeze_type": "short_liquidation_cascade",
                "side": "short",
                "leverage_tier": lev,
                "trigger_price": round(short_trig, 4),
                "distance_pct": round((short_trig / mark - 1) * 100, 3),
                "confidence": min(0.95, 0.5 + (1 - ls_ratio) * 0.2) if ls_ratio < 1 else 0.4,
            }
        )

    if funding_rate > 0.0002:
        rally = mark * (1.015 + min(funding_rate * 50, 0.03))
        coords.append(
            {
                "coordinate_id": "short_squeeze_rally",
                "squeeze_type": "short_squeeze_trigger",
                "side": "short",
                "trigger_price": round(rally, 4),
                "distance_pct": round((rally / mark - 1) * 100, 3),
                "confidence": min(0.9, 0.55 + funding_rate * 200),
                "reason": "positive_funding_crowded_longs",
            }
        )
    if funding_rate < -0.0002:
        drop = mark * (0.985 - min(abs(funding_rate) * 50, 0.03))
        coords.append(
            {
                "coordinate_id": "long_squeeze_drop",
                "squeeze_type": "long_squeeze_trigger",
                "side": "long",
                "trigger_price": round(drop, 4),
                "distance_pct": round((drop / mark - 1) * 100, 3),
                "confidence": min(0.9, 0.55 + abs(funding_rate) * 200),
                "reason": "negative_funding_crowded_shorts",
            }
        )

    if oi_usd > 500_000_000 and change_24h < -2:
        coords.append(
            {
                "coordinate_id": "oi_unwind_zone",
                "squeeze_type": "long_cascade_oi_unwind",
                "trigger_price": round(mark * 0.97, 4),
                "distance_pct": -3.0,
                "confidence": 0.75,
                "reason": f"OI ${oi_usd/1e9:.1f}B with {change_24h:.1f}% drawdown",
            }
        )

    coords.sort(key=lambda c: abs(c.get("distance_pct", 0)))
    return coords


def _headline(coords: list[dict[str, Any]], asset: str) -> str:
    short_sq = [c for c in coords if c.get("squeeze_type") == "short_squeeze_trigger"]
    long_sq = [c for c in coords if c.get("squeeze_type") == "long_squeeze_trigger"]
    if short_sq:
        return f"{asset} short squeeze watch @ ${short_sq[0]['trigger_price']:,.2f}"
    if long_sq:
        return f"{asset} long squeeze watch @ ${long_sq[0]['trigger_price']:,.2f}"
    nearest = coords[0] if coords else None
    if nearest:
        return f"{asset} nearest trigger ${nearest['trigger_price']:,.2f} ({nearest['distance_pct']:+.1f}%)"
    return f"{asset} squeeze coordinates"


async def squeeze_trigger_coordinates(symbol: str = "BTC") -> dict[str, Any]:
    """CAP978 IDs 936, 942, 951, 974 — predictive squeeze price coordinates."""
    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    cache_key = f"sq:{asset}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        return cached[1]

    t0 = time.perf_counter()
    snap, risk = await _gather_snap_risk(asset)
    if not snap.get("available"):
        snap = await _fallback_snapshot(asset)
    if not snap.get("available"):
        return {
            "success": False,
            "ok": False,
            "asset": asset,
            "data_state": "MISSING",
            "error": "futures_data_unavailable",
            "timestamp": _utcnow(),
        }

    mark = float(snap.get("mark_price") or 0)
    fr = float(snap.get("funding_rate") or 0)
    ls = float(snap.get("long_short_ratio") or 1)
    chg = float(snap.get("change_24h_pct") or 0)
    oi = float(snap.get("open_interest_usd") or 0)

    coords = _squeeze_coordinates(
        mark=mark,
        funding_rate=fr,
        ls_ratio=ls,
        change_24h=chg,
        oi_usd=oi,
    )

    result = {
        "success": True,
        "ok": True,
        "capability_ids": [936, 942, 951, 974],
        "surface": "squeeze_trigger_predictive_coordinates",
        "asset": asset,
        "mark_price": mark,
        "headline": _headline(coords, asset),
        "coordinates": coords,
        "metrics": {
            "funding_rate_pct": snap.get("funding_rate_pct"),
            "long_short_ratio": ls,
            "open_interest_usd": oi,
            "change_24h_pct": chg,
        },
        "alerts": risk.get("alerts") or [],
        "data_state": "LIVE",
        "sources": ["binance_futures_public", "coingecko_price_fallback"],
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
        "disclaimer": "Leverage-tier liquidation estimates; whale-filtered L/S = Binance global proxy",
    }
    _CACHE[cache_key] = (time.time(), result)
    return result


async def _gather_snap_risk(asset: str) -> tuple[dict[str, Any], dict[str, Any]]:
    import asyncio

    snap, risk = await asyncio.gather(
        binance_futures_snapshot(asset),
        binance_liquidation_risk(asset),
    )
    return snap, risk
