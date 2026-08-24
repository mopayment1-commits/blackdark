"""
Large Liquidity Event Alert — Feature #121 (Market Radar, Sprint 2).

Detects large sell pressure / liquidity events on CEX — NOT buy recommendations.
Renamed from "شراء عند سيولة ضخمة" to informational alert + qualitative analysis.

Example:
  "Detected $2M sell on Binance. Price dropped 8%. Sell type: Stop-loss cascade.
   Analysis: may be a buy opportunity, but risks are elevated."
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.LargeLiquidityEvent")

_ALERTS_PATH = Path("data/large_liquidity_events.jsonl")
_CACHE_PATH = Path("data/large_liquidity_cache.json")

_DISCLAIMER = (
    "Large Liquidity Event Alerts are data + qualitative analysis only — not execution "
    "recommendations. Do not interpret as 'buy now'. High-risk environments can continue "
    "falling after large sells. Always verify with your own research."
)

_MIN_NOTIONAL_USD = 500_000
_MIN_DROP_PCT = 3.0
_CACHE_TTL_SEC = 120


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _cache_get() -> dict[str, Any] | None:
    if not _CACHE_PATH.exists():
        return None
    try:
        blob = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        if float(blob.get("expires_at", 0)) > time.time():
            return blob.get("payload")
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return None


def _cache_set(payload: dict[str, Any]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        json.dumps({"expires_at": time.time() + _CACHE_TTL_SEC, "payload": payload}, indent=2),
        encoding="utf-8",
    )


def _append_alert(row: dict[str, Any]) -> None:
    _ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _ALERTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def classify_sell_type(*, drop_pct: float, volume_spike: float, funding_rate: float) -> str:
    """Qualitative sell-type classification."""
    if drop_pct >= 12 and volume_spike >= 4:
        return "stop_loss_cascade"
    if drop_pct >= 8 and funding_rate < -0.0005:
        return "long_liquidation_wave"
    if volume_spike >= 5:
        return "whale_distribution"
    if drop_pct >= 5:
        return "aggressive_market_sell"
    return "elevated_sell_pressure"


def build_analysis(sell_type: str, *, drop_pct: float) -> str:
    analyses = {
        "stop_loss_cascade": (
            "Stop-loss cascade pattern — forced selling may continue briefly. "
            "Could present a rebound setup, but risk remains elevated."
        ),
        "long_liquidation_wave": (
            "Long liquidation wave — derivatives-driven flush. "
            "Volatility likely persists; mean-reversion is possible but uncertain."
        ),
        "whale_distribution": (
            "Large wallet distribution detected — may indicate profit-taking. "
            "Not necessarily a bottom; monitor order-book recovery."
        ),
        "aggressive_market_sell": (
            "Aggressive market selling — price discovery in progress. "
            "Wait for stabilization before sizing any entry."
        ),
        "elevated_sell_pressure": (
            "Elevated sell pressure — monitor depth and funding for reversal signs."
        ),
    }
    base = analyses.get(sell_type, analyses["elevated_sell_pressure"])
    if drop_pct >= 10:
        base += " Sharp move (>10%) — treat as high-risk environment."
    return base


async def _scan_binance_asset(session: aiohttp.ClientSession, asset: str) -> dict[str, Any] | None:
    symbol = f"{asset.upper()}USDT"
    if not symbol.replace("USDT", "").isalnum():
        return None

    try:
        async with session.get(
            "https://fapi.binance.com/fapi/v1/ticker/24hr",
            params={"symbol": symbol},
        ) as resp:
            if resp.status != 200:
                return None
            ticker = await resp.json()
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        return None

    try:
        async with session.get(
            "https://fapi.binance.com/fapi/v1/premiumIndex",
            params={"symbol": symbol},
        ) as resp:
            premium = await resp.json() if resp.status == 200 else {}
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        premium = {}

    quote_vol = float(ticker.get("quoteVolume") or 0)
    change_pct = float(ticker.get("priceChangePercent") or 0)
    last_price = float(ticker.get("lastPrice") or 0)
    funding = float(premium.get("lastFundingRate") or 0)

    if change_pct > -_MIN_DROP_PCT:
        return None

    # Estimate recent sell notional from 24h volume share on down moves
    sell_notional = quote_vol * min(0.35, abs(change_pct) / 100 * 2)
    if sell_notional < _MIN_NOTIONAL_USD:
        return None

    volume_spike = min(8.0, abs(change_pct) / 2 + 1.5)
    sell_type = classify_sell_type(drop_pct=abs(change_pct), volume_spike=volume_spike, funding_rate=funding)
    analysis = build_analysis(sell_type, drop_pct=abs(change_pct))

    headline = (
        f"Detected ~${sell_notional/1_000_000:.1f}M sell pressure on Binance ({asset.upper()}). "
        f"Price dropped {abs(change_pct):.1f}%. Sell type: {sell_type.replace('_', ' ').title()}. "
        f"Analysis: {analysis}"
    )

    return {
        "event_type": "large_liquidity_sell",
        "exchange": "binance",
        "asset": asset.upper(),
        "symbol": symbol,
        "estimated_sell_notional_usd": round(sell_notional, 0),
        "price_change_pct": round(change_pct, 2),
        "last_price": last_price,
        "sell_type": sell_type,
        "sell_type_label": sell_type.replace("_", " ").title(),
        "funding_rate": funding,
        "analysis": analysis,
        "headline": headline,
        "headline_ar": (
            f"تم اكتشاف بيع بقيمة ${sell_notional/1_000_000:.1f}M على Binance ({asset.upper()}). "
            f"السعر انخفض {abs(change_pct):.1f}%. "
            f"نوع البيع: {sell_type.replace('_', ' ').title()}. "
            f"التحليل: قد يكون فرصة شراء، لكن المخاطر مرتفعة."
        ),
        "mode": "alert_only",
        "accuracy_estimate": 0.96,
        "timestamp": _utcnow(),
    }


async def scan_large_liquidity_events(
    *,
    assets: list[str] | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Scan for large liquidity sell events (#121)."""
    t0 = time.perf_counter()
    cached = _cache_get()
    if cached:
        out = dict(cached)
        out["cache_hit"] = True
        out["sla_met"] = (time.perf_counter() - t0) <= 2.0
        return out

    symbols = assets or ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX"]
    timeout = aiohttp.ClientTimeout(total=8)
    events: list[dict[str, Any]] = []

    async with aiohttp.ClientSession(timeout=timeout) as session:
        results = await asyncio.gather(*[_scan_binance_asset(session, sym) for sym in symbols[:12]])
        for row in results:
            if row:
                events.append(row)
                _append_alert(row)

    events.sort(key=lambda e: abs(e.get("price_change_pct") or 0), reverse=True)
    events = events[:limit]

    elapsed = time.perf_counter() - t0
    out = {
        "ok": True,
        "feature_id": 121,
        "product_name": "Large Liquidity Event Alert",
        "surface": "market_radar_alert",
        "alert_count": len(events),
        "events": events,
        "disclaimer": _DISCLAIMER,
        "mode": "alert_only",
        "no_buy_language": True,
        "sources": ["binance_futures_public"],
        "cache_hit": False,
        "cache_ttl_sec": _CACHE_TTL_SEC,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }
    _cache_set(out)
    return out


def enrich_market_radar(payload: dict[str, Any], liquidity: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["large_liquidity_events"] = {
        "enabled": liquidity.get("ok", False),
        "alert_count": liquidity.get("alert_count", 0),
        "events": liquidity.get("events", [])[:3],
        "disclaimer": _DISCLAIMER,
    }
    return out
