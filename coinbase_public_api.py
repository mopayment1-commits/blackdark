"""
Coinbase Exchange public REST (no API key) — spot ticker, 24h stats, order book.

https://api.exchange.coinbase.com
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.CoinbasePublic")

_BASE = "https://api.exchange.coinbase.com"
_TIMEOUT = aiohttp.ClientTimeout(total=12)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}


def pair_to_product_id(pair: str) -> str | None:
    cleaned = (pair or "").upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        base = cleaned[:-4]
    elif cleaned.endswith("USD"):
        base = cleaned[:-3]
    else:
        base = cleaned
    if not base or not base.isalnum():
        return None
    return f"{base}-USD"


async def _get_json(
    session: aiohttp.ClientSession,
    path: str,
) -> Any | None:
    url = f"{_BASE}{path}"
    try:
        async with session.get(url, headers=_HEADERS) as resp:
            if resp.status != 200:
                logger.debug("Coinbase HTTP %s %s", resp.status, path)
                return None
            return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


def _ticker_from_stats_and_ticker(
    ticker: dict[str, Any],
    stats: dict[str, Any],
    *,
    product_id: str,
) -> dict[str, Any] | None:
    try:
        price = float(ticker.get("price") or stats.get("last") or 0)
        if price <= 0:
            return None
        open_px = float(stats.get("open") or 0)
        change = ((price - open_px) / open_px * 100.0) if open_px > 0 else 0.0
        volume = float(ticker.get("volume") or stats.get("volume") or 0)
        quote_volume = volume * price
        row: dict[str, Any] = {
            "price": price,
            "change_24h": round(change, 4),
            "volume": volume,
            "quote_volume": quote_volume,
            "high_24h": float(stats.get("high") or 0),
            "low_24h": float(stats.get("low") or 0),
            "source": "coinbase_exchange",
            "product_id": product_id,
        }
        if ticker.get("time"):
            row["event_time"] = ticker.get("time")
        bid = ticker.get("bid")
        ask = ticker.get("ask")
        if bid and ask:
            try:
                best_bid = float(bid)
                best_ask = float(ask)
                mid = (best_bid + best_ask) / 2.0
                spread_bps = ((best_ask - best_bid) / mid * 10000.0) if mid else 0.0
                row["best_bid"] = best_bid
                row["best_ask"] = best_ask
                row["spread_bps"] = round(spread_bps, 2)
            except (TypeError, ValueError):
                pass
        return row
    except (KeyError, TypeError, ValueError):
        return None


async def fetch_order_book(
    product_id: str,
    *,
    session: aiohttp.ClientSession | None = None,
    level: int = 1,
) -> dict[str, Any] | None:
    owns = session is None
    if owns:
        session = aiohttp.ClientSession(timeout=_TIMEOUT)
    try:
        assert session is not None
        data = await _get_json(session, f"/products/{product_id}/book?level={level}")
        if not isinstance(data, dict):
            return None
        bids = data.get("bids") or []
        asks = data.get("asks") or []
        if not bids or not asks:
            return None
        best_bid = float(bids[0][0])
        best_ask = float(asks[0][0])
        if best_bid <= 0 or best_ask <= 0:
            return None
        mid = (best_bid + best_ask) / 2.0
        spread_bps = ((best_ask - best_bid) / mid * 10000.0) if mid else 0.0
        bid_qty = sum(float(b[1]) for b in bids[:10] if len(b) > 1)
        ask_qty = sum(float(a[1]) for a in asks[:10] if len(a) > 1)
        return {
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread_bps": round(spread_bps, 2),
            "bid_depth_base": round(bid_qty, 6),
            "ask_depth_base": round(ask_qty, 6),
            "source": "coinbase_book",
            "level": level,
        }
    finally:
        if owns and session is not None:
            await session.close()


async def fetch_public_spot_market(pair: str) -> dict[str, Any] | None:
    """Ticker + 24h stats + level-1 book for a USDT-style pair (maps to *-USD)."""
    product_id = pair_to_product_id(pair)
    if not product_id:
        return None
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        ticker = await _get_json(session, f"/products/{product_id}/ticker")
        stats = await _get_json(session, f"/products/{product_id}/stats")
        if not isinstance(ticker, dict) or not isinstance(stats, dict):
            return None
        row = _ticker_from_stats_and_ticker(ticker, stats, product_id=product_id)
        if row is None:
            return None
        book = await fetch_order_book(product_id, session=session, level=1)
        if book:
            row["order_book"] = book
            row["best_bid"] = book.get("best_bid")
            row["best_ask"] = book.get("best_ask")
            row["spread_bps"] = book.get("spread_bps")
        return row


async def fetch_spot_for_asset(asset: str) -> dict[str, Any] | None:
    sym = (asset or "").upper().strip()
    if not sym:
        return None
    return await fetch_public_spot_market(f"{sym}USDT")
