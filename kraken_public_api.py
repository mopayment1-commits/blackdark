"""
Kraken public REST (no API key) — spot ticker and order book depth.

https://api.kraken.com/0/public/
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.KrakenPublic")

_BASE = "https://api.kraken.com/0/public"
_TIMEOUT = aiohttp.ClientTimeout(total=12)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}

# Kraken pair names (USD spot).
_KRAKEN_PAIRS: dict[str, str] = {
    "BTC": "XBTUSD",
    "XBT": "XBTUSD",
    "DOGE": "XDGUSD",
    "ETH": "ETHUSD",
    "SOL": "SOLUSD",
    "XRP": "XRPUSD",
    "ADA": "ADAUSD",
    "DOT": "DOTUSD",
    "LINK": "LINKUSD",
    "LTC": "LTCUSD",
    "AVAX": "AVAXUSD",
    "ATOM": "ATOMUSD",
    "UNI": "UNIUSD",
    "NEAR": "NEARUSD",
    "APT": "APTUSD",
    "ARB": "ARBUSD",
    "OP": "OPUSD",
    "SUI": "SUIUSD",
    "PEPE": "PEPEUSD",
    "SHIB": "SHIBUSD",
    "BNB": "BNBUSD",
    "MATIC": "MATICUSD",
    "POL": "MATICUSD",
}


def asset_to_kraken_pair(asset: str) -> str:
    sym = (asset or "").upper().strip()
    if sym.endswith("USDT"):
        sym = sym[:-4]
    if sym.endswith("USD"):
        sym = sym[:-3]
    return _KRAKEN_PAIRS.get(sym, f"{sym}USD")


def pair_to_kraken_pair(pair: str) -> str | None:
    cleaned = (pair or "").upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return asset_to_kraken_pair(cleaned[:-4])
    if cleaned.endswith("USD"):
        return asset_to_kraken_pair(cleaned[:-3])
    if not cleaned:
        return None
    return asset_to_kraken_pair(cleaned)


async def _get_json(
    session: aiohttp.ClientSession,
    path: str,
    *,
    params: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    url = f"{_BASE}/{path.lstrip('/')}"
    try:
        async with session.get(url, params=params, headers=_HEADERS) as resp:
            if resp.status != 200:
                logger.debug("Kraken HTTP %s %s", resp.status, path)
                return None
            data = await resp.json()
            if not isinstance(data, dict):
                return None
            if data.get("error"):
                logger.debug("Kraken API error: %s", data.get("error"))
                return None
            return data
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


def _ticker_from_kraken_row(row: dict[str, Any], *, kraken_pair: str) -> dict[str, Any] | None:
    try:
        price = float(row["c"][0])
        if price <= 0:
            return None
        open_today = float(row.get("o") or price)
        change = ((price - open_today) / open_today * 100.0) if open_today else 0.0
        vol_row = row.get("v") or [0, 0]
        volume = float(vol_row[1] if len(vol_row) > 1 else vol_row[0])
        quote_volume = volume * price
        out: dict[str, Any] = {
            "price": price,
            "change_24h": round(change, 4),
            "volume": volume,
            "quote_volume": round(quote_volume, 2),
            "source": "kraken_public",
            "kraken_pair": kraken_pair,
        }
        low_row = row.get("l") or []
        high_row = row.get("h") or []
        if len(low_row) > 1:
            out["low_24h"] = float(low_row[1])
        if len(high_row) > 1:
            out["high_24h"] = float(high_row[1])
        ask = row.get("a")
        bid = row.get("b")
        if ask and bid:
            best_ask = float(ask[0])
            best_bid = float(bid[0])
            mid = (best_bid + best_ask) / 2.0
            spread_bps = ((best_ask - best_bid) / mid * 10000.0) if mid else 0.0
            out["best_bid"] = best_bid
            out["best_ask"] = best_ask
            out["spread_bps"] = round(spread_bps, 2)
        return out
    except (KeyError, TypeError, ValueError, IndexError):
        return None


async def fetch_order_book(
    kraken_pair: str,
    *,
    session: aiohttp.ClientSession | None = None,
    count: int = 10,
) -> dict[str, Any] | None:
    owns = session is None
    if owns:
        session = aiohttp.ClientSession(timeout=_TIMEOUT)
    try:
        assert session is not None
        data = await _get_json(
            session,
            "Depth",
            params={"pair": kraken_pair, "count": str(max(1, min(count, 25)))},
        )
        if not data:
            return None
        result = data.get("result") or {}
        if not result:
            return None
        book = next(iter(result.values()))
        if not isinstance(book, dict):
            return None
        bids = book.get("bids") or []
        asks = book.get("asks") or []
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
            "source": "kraken_depth",
            "count": count,
        }
    finally:
        if owns and session is not None:
            await session.close()


async def fetch_public_spot_market(pair: str) -> dict[str, Any] | None:
    """24h ticker + depth for a Binance-style pair (e.g. BTCUSDT → XBTUSD)."""
    kraken_pair = pair_to_kraken_pair(pair)
    if not kraken_pair:
        return None
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        data = await _get_json(session, "Ticker", params={"pair": kraken_pair})
        if not data:
            return None
        result = data.get("result") or {}
        if not result:
            return None
        row = next(iter(result.values()))
        if not isinstance(row, dict):
            return None
        snap = _ticker_from_kraken_row(row, kraken_pair=kraken_pair)
        if snap is None:
            return None
        book = await fetch_order_book(kraken_pair, session=session, count=10)
        if book:
            snap["order_book"] = book
            snap["best_bid"] = book.get("best_bid")
            snap["best_ask"] = book.get("best_ask")
            snap["spread_bps"] = book.get("spread_bps")
        return snap


async def fetch_spot_for_asset(asset: str) -> dict[str, Any] | None:
    sym = (asset or "").upper().strip()
    if not sym:
        return None
    return await fetch_public_spot_market(f"{sym}USDT")
