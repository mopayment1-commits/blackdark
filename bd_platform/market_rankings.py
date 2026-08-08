"""CoinMarketCap-style market rankings."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import aiohttp


async def market_rankings(*, limit: int = 100) -> dict[str, Any]:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": min(limit, 250), "page": 1, "sparkline": "true"}
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url, params=params) as resp:
        if resp.status != 200:
            return {"available": False, "coins": []}
        rows = await resp.json()

    coins = []
    for i, row in enumerate(rows, start=1):
        coins.append(
            {
                "rank": i,
                "id": row.get("id"),
                "symbol": str(row.get("symbol", "")).upper(),
                "name": row.get("name"),
                "price_usd": row.get("current_price"),
                "market_cap_usd": row.get("market_cap"),
                "volume_24h_usd": row.get("total_volume"),
                "change_24h_pct": row.get("price_change_percentage_24h"),
                "sparkline_7d": (row.get("sparkline_in_7d") or {}).get("price"),
            }
        )
    return {
        "style": "coinmarketcap",
        "timestamp": datetime.now(UTC).isoformat(),
        "count": len(coins),
        "coins": coins,
    }


async def coin_detail(coin_id: str) -> dict[str, Any]:
    """Single coin detail page data from CoinGecko (free)."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id.lower()}"
    params = {
        "localization": "false",
        "tickers": "false",
        "community_data": "true",
        "developer_data": "false",
        "sparkline": "true",
    }
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url, params=params) as resp:
        if resp.status != 200:
            return {"available": False, "coin_id": coin_id}
        row = await resp.json()

    md = row.get("market_data") or {}
    return {
        "available": True,
        "id": row.get("id"),
        "symbol": str(row.get("symbol", "")).upper(),
        "name": row.get("name"),
        "description": (row.get("description") or {}).get("en", "")[:500],
        "price_usd": md.get("current_price"),
        "market_cap_usd": md.get("market_cap"),
        "volume_24h_usd": md.get("total_volume"),
        "change_24h_pct": md.get("price_change_percentage_24h"),
        "change_7d_pct": md.get("price_change_percentage_7d"),
        "change_30d_pct": md.get("price_change_percentage_30d"),
        "ath_usd": md.get("ath"),
        "atl_usd": md.get("atl"),
        "circulating_supply": md.get("circulating_supply"),
        "total_supply": md.get("total_supply"),
        "max_supply": md.get("max_supply"),
        "sparkline_7d": (md.get("sparkline_7d") or {}).get("price"),
        "links": row.get("links") or {},
        "timestamp": datetime.now(UTC).isoformat(),
    }
