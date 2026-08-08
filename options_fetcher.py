"""
BLACKDARK — Options data fetcher (Deribit) — Buyer Requirement #11.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.OptionsFetcher")

DERIBIT_PUBLIC = "https://www.deribit.com/api/v2/public"


async def fetch_deribit_options_summary(currency: str = "BTC") -> dict[str, Any]:
    """Fetch Deribit option instruments + mark prices."""
    url = f"{DERIBIT_PUBLIC}/get_book_summary_by_currency"
    params = {"currency": currency.upper(), "kind": "option"}
    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url, params=params) as resp:
            if resp.status != 200:
                return {"success": False, "error": f"HTTP {resp.status}"}
            data = await resp.json()
            items = data.get("result") or []
            summaries = []
            for item in items[:50]:
                summaries.append({
                    "instrument": item.get("instrument_name"),
                    "mark_price": item.get("mark_price"),
                    "bid": item.get("bid_price"),
                    "ask": item.get("ask_price"),
                    "open_interest": item.get("open_interest"),
                    "volume": item.get("volume"),
                })
            return {
                "success": True,
                "exchange": "deribit",
                "currency": currency.upper(),
                "count": len(items),
                "instruments": summaries,
            }
    except (aiohttp.ClientError, TypeError, ValueError) as exc:
        logger.warning("Deribit options fetch failed | %s", exc)
        return {"success": False, "error": str(exc)}


async def fetch_options_overview(assets: list[str] | None = None) -> dict[str, Any]:
    targets = assets or ["BTC", "ETH"]
    results = {}
    for asset in targets:
        results[asset] = await fetch_deribit_options_summary(asset)
    return {
        "provider": "deribit",
        "assets": results,
        "note": "Options intelligence for institutional due diligence — not auto-execution.",
    }
