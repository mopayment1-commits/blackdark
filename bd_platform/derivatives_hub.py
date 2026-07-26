"""CoinGlass + derivatives hub — free Binance fallback when no paid key."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.DerivativesHub")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _coinglass_get(path: str, params: dict | None = None) -> dict[str, Any]:
    key = os.getenv("COINGLASS_API_KEY", "").strip()
    if not key:
        return {"available": False, "reason": "COINGLASS_API_KEY not set (optional paid tier)"}
    url = f"https://open-api-v4.coinglass.com{path}"
    headers = {"CG-API-KEY": key, "accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                return {"available": False, "status": resp.status}
            data = await resp.json()
    return {"available": True, "data": data}


async def derivatives_overview(asset: str = "BTC") -> dict[str, Any]:
    from bd_platform.free_market_data import binance_futures_snapshot
    from options_fetcher import fetch_options_overview

    symbol = asset.upper().replace("USDT", "")
    free = await binance_futures_snapshot(symbol)
    cg_funding = await _coinglass_get("/api/futures/funding-rate/exchange-list", {"symbol": symbol})
    cg_liq = await _coinglass_get("/api/futures/liquidation/aggregated-history", {"symbol": symbol, "time_type": "h1"})
    cg_oi = await _coinglass_get("/api/futures/open-interest/aggregated-history", {"symbol": symbol, "interval": "h1"})
    options = await fetch_options_overview([symbol])

    return {
        "asset": symbol,
        "timestamp": _utcnow(),
        "free_tier": free,
        "coinglass": {
            "funding": cg_funding,
            "liquidations": cg_liq,
            "open_interest": cg_oi,
            "note": "CoinGlass enhances data when COINGLASS_API_KEY is set",
        },
        "deribit_options": options,
        "sources": ["Binance Futures (free)", "Deribit", "CoinGlass (optional)"],
        "primary_source": "binance_futures_public" if free.get("available") else "coinglass",
    }


async def cex_dex_derivatives_compare(asset: str = "BTC") -> dict[str, Any]:
    import asyncio

    from bd_platform.free_market_data import binance_futures_snapshot
    from database import fetch_latest_funding_rates
    from perp_dex_fetcher import PERP_DEX_VENUES, fetch_perp_dex_market

    symbol = asset.upper()
    pair = f"{symbol}/USDT"

    async def _dex_quote(venue_id: str) -> dict[str, Any] | None:
        try:
            ticker, _book = await fetch_perp_dex_market(
                None, pair, "perpetual", exchange_id=venue_id
            )
            return {
                "exchange": venue_id,
                "venue": venue_id,
                "mark_price": ticker.price,
                "price": ticker.price,
            }
        except Exception as exc:
            logger.debug("DEX quote failed %s %s: %s", venue_id, symbol, exc)
            return None

    dex_rows = await asyncio.gather(*[_dex_quote(v) for v in sorted(PERP_DEX_VENUES)])
    perp_dex = [row for row in dex_rows if row]
    cex_funding = await fetch_latest_funding_rates()
    cex_rows = []
    for ex, syms in (cex_funding or {}).items():
        row = syms.get(f"{symbol}/USDT") or syms.get(f"{symbol}USDT")
        if row:
            cex_rows.append({"exchange": ex, **row})

    binance_snap = await binance_futures_snapshot(symbol)
    if binance_snap.get("available"):
        cex_rows.insert(0, {
            "exchange": "binance_futures",
            "funding_rate": binance_snap.get("funding_rate"),
            "open_interest_usd": binance_snap.get("open_interest_usd"),
            "mark_price": binance_snap.get("mark_price"),
        })

    return {
        "asset": symbol,
        "timestamp": _utcnow(),
        "cex_funding": cex_rows[:10],
        "dex_perp_quotes": perp_dex,
        "binance_futures": binance_snap,
        "comparison_note": "Funding + mark basis CEX vs on-chain perp DEX venues (Binance free tier included)",
    }
