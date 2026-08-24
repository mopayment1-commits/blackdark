"""MVRV Z-Score Dynamic Realignment — regime detection and band crossings."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

from bd_platform.onchain_advanced import _advanced_proxies, _klines, _mvrv_history, _std

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 60.0
_CG_IDS = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binancecoin"}


async def _fetch_closes(asset: str) -> list[float]:
    closes = await _klines(asset, limit=365)
    if len(closes) >= 210:
        return closes
    cg_id = _CG_IDS.get(asset.upper())
    if not cg_id:
        return closes
    timeout = aiohttp.ClientTimeout(total=12)
    url = f"https://api.coingecko.com/api/v3/coins/{cg_id}/market_chart"
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params={"vs_currency": "usd", "days": 365}) as resp:
                if resp.status != 200:
                    return closes
                data = await resp.json()
                prices = data.get("prices") or []
                return [float(p[1]) for p in prices if len(p) > 1]
    except aiohttp.ClientError:
        return closes

_BANDS = (
    ("extreme_undervalued", -2.0),
    ("undervalued", -1.0),
    ("neutral", 1.0),
    ("overheated", 2.0),
    ("extreme_overheated", 99.0),
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _regime_from_z(z: float) -> str:
    if z < -2:
        return "extreme_undervalued"
    if z < -1:
        return "undervalued"
    if z < 1:
        return "neutral"
    if z < 2:
        return "overheated"
    return "extreme_overheated"


def _realignment_signal(prev_z: float, curr_z: float) -> str:
    prev_regime = _regime_from_z(prev_z)
    curr_regime = _regime_from_z(curr_z)
    if prev_z < -1 <= curr_z:
        return "bullish_realignment"
    if prev_z > 1 >= curr_z:
        return "bearish_realignment"
    if prev_regime != curr_regime:
        return f"regime_shift_{curr_regime}"
    return "none"


def _z_history(closes: list[float]) -> list[float]:
    hist: list[float] = []
    for i in range(200, len(closes)):
        window = closes[: i + 1]
        price = closes[i]
        proxies = _advanced_proxies(window, price)
        mvrv_hist = _mvrv_history(window)
        if not mvrv_hist:
            hist.append(0.0)
            continue
        mvrv = proxies["mvrv"]
        z = (mvrv - (sum(mvrv_hist) / len(mvrv_hist))) / (_std(mvrv_hist) or 1)
        hist.append(z)
    return hist


def _alerts(z: float, signal: str) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if z >= 2:
        alerts.append(
            {
                "level": "high",
                "code": "MVRV_EXTREME_OVERHEATED",
                "message": f"MVRV Z-Score {z:.2f} — historically overheated zone",
            }
        )
    elif z <= -2:
        alerts.append(
            {
                "level": "high",
                "code": "MVRV_EXTREME_UNDERVALUED",
                "message": f"MVRV Z-Score {z:.2f} — deep value zone",
            }
        )
    if signal == "bullish_realignment":
        alerts.append(
            {
                "level": "medium",
                "code": "BULLISH_REALIGNMENT",
                "message": "Z-Score crossed up through -1 — bullish realignment",
            }
        )
    elif signal == "bearish_realignment":
        alerts.append(
            {
                "level": "medium",
                "code": "BEARISH_REALIGNMENT",
                "message": "Z-Score crossed down through +1 — bearish realignment",
            }
        )
    return alerts


async def compute_mvrv_realignment(symbol: str = "BTC") -> dict[str, Any]:
    """CAP978 IDs 40, 195 — live MVRV Z-Score with dynamic realignment."""
    asset = str(symbol or "BTC").upper().replace("/USDT", "")
    cache_key = f"mvrv:{asset}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        return cached[1]

    t0 = time.perf_counter()
    closes = await _fetch_closes(asset)
    if len(closes) < 210:
        return {
            "success": False,
            "ok": False,
            "asset": asset,
            "data_state": "MISSING",
            "error": "insufficient_price_history",
            "timestamp": _utcnow(),
        }

    price = closes[-1]
    proxies = _advanced_proxies(closes, price)
    z_series = _z_history(closes)
    prev_z = z_series[-2] if len(z_series) >= 2 else z_series[-1]
    curr_z = z_series[-1]
    signal = _realignment_signal(prev_z, curr_z)
    regime = _regime_from_z(curr_z)

    result = {
        "success": True,
        "ok": True,
        "capability_ids": [40, 195],
        "surface": "mvrv_z_score_dynamic_realignment",
        "asset": asset,
        "price": round(price, 2),
        "mvrv_ratio": round(proxies["mvrv"], 4),
        "z_score": round(curr_z, 4),
        "previous_z_score": round(prev_z, 4),
        "regime": regime,
        "realignment_signal": signal,
        "bands": [{"name": n, "threshold": t} for n, t in _BANDS],
        "z_history_30d": [round(z, 3) for z in z_series[-30:]],
        "alerts": _alerts(curr_z, signal),
        "data_state": "LIVE",
        "sources": ["binance_klines", "coingecko_fallback"],
        "method": "SMA200 realized proxy + rolling Z",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
        "disclaimer": "MVRV proxy from price history; Glassnode-grade on-chain MVRV = EXTERNAL EVIDENCE",
    }
    _CACHE[cache_key] = (time.time(), result)
    return result
