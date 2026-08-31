"""
Live market context — free public APIs for user-facing enrichment.

CoinGecko + Binance public. Missing data → unavailable (never zero placeholder).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from bd_platform.institutional_standards import missing_value

logger = logging.getLogger("BLACKDARK.LiveMarketContext")

_CACHE: dict[str, Any] = {}
_CACHE_TS: float = 0.0
_CACHE_TTL = 60.0


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _fetch_coingecko_simple(ids: str = "bitcoin,ethereum") -> dict[str, Any]:
    from bd_platform.free_market_data import coingecko_simple_prices

    try:
        return await coingecko_simple_prices(ids=ids)
    except Exception as exc:
        logger.warning("coingecko fetch failed: %s", exc)
        return {"ok": False, "error": "coingecko_unavailable"}


async def _fetch_binance_btc() -> dict[str, Any]:
    from bd_platform.free_market_data import binance_futures_snapshot

    try:
        return await binance_futures_snapshot("BTC")
    except Exception as exc:
        logger.warning("binance fetch failed: %s", exc)
        return {"available": False}


async def build_live_market_strip() -> dict[str, Any]:
    """Top-of-hub live prices — real APIs with fail-closed unavailable labels."""
    global _CACHE, _CACHE_TS
    import time

    now = time.time()
    if _CACHE and (now - _CACHE_TS) < _CACHE_TTL:
        return _CACHE

    cg, bn = await asyncio.gather(_fetch_coingecko_simple(), _fetch_binance_btc())

    assets: list[dict[str, Any]] = []
    prices = (cg.get("prices") or {}) if cg.get("ok") else {}

    for coin_id, label in (("bitcoin", "BTC"), ("ethereum", "ETH")):
        row = prices.get(coin_id) or {}
        price = row.get("usd")
        change = row.get("usd_24h_change")
        assets.append({
            "asset": label,
            "coin_id": coin_id,
            "price_usd": price if price is not None else missing_value(numeric=True),
            "change_24h_pct": change if change is not None else missing_value(numeric=True),
            "source": "coingecko_public" if price is not None else missing_value(),
            "available": price is not None,
        })

    btc_futures = {
        "funding_rate_pct": bn.get("funding_rate_pct") if bn.get("available") else missing_value(numeric=True),
        "open_interest_usd": bn.get("open_interest_usd") if bn.get("available") else missing_value(numeric=True),
        "mark_price": bn.get("mark_price") if bn.get("available") else missing_value(numeric=True),
        "source": "binance_futures_public" if bn.get("available") else missing_value(),
        "available": bool(bn.get("available")),
    }

    result = {
        "ok": True,
        "live_data": True,
        "evidence_class": "SHADOW_LIVE_FORWARD",
        "assets": assets,
        "btc_futures": btc_futures,
        "cache_ttl_seconds": _CACHE_TTL,
        "unknown_is_not_zero": True,
        "disclaimer": "Live public market data — not investment advice. Stale/unavailable shown explicitly.",
        "as_of": _utcnow(),
    }
    _CACHE = result
    _CACHE_TS = now
    return result


def build_live_market_strip_sync() -> dict[str, Any]:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return _CACHE or {
                "ok": False,
                "error": "async_context",
                "message": missing_value(),
            }
        return loop.run_until_complete(build_live_market_strip())
    except RuntimeError:
        return asyncio.run(build_live_market_strip())
