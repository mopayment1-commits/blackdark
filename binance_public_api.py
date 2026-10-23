"""
Binance spot public REST (no API key).

Used as the primary price/volume/depth source for Oracle quick + Trust Pulse.
"""

from __future__ import annotations

import logging
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.BinancePublic")

_PUBLIC_HOSTS: tuple[str, ...] = (
    "api.binance.com",
    "data-api.binance.vision",
    "api.binance.us",
)

_HTTP_TIMEOUT = aiohttp.ClientTimeout(total=12)
_HTTP_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/json",
}


def public_hosts() -> tuple[str, ...]:
    return _PUBLIC_HOSTS


def _pair_ok(pair: str) -> bool:
    cleaned = (pair or "").upper().strip()
    return bool(cleaned) and cleaned.isalnum()


async def _get_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    params: dict[str, str | int] | None = None,
) -> Any | None:
    try:
        async with session.get(url, params=params, headers=_HTTP_HEADERS) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


def _ticker_from_24hr(data: dict[str, Any], *, host: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "price": float(data["lastPrice"]),
        "change_24h": float(data["priceChangePercent"]),
        "volume": float(data["volume"]),
        "quote_volume": float(data.get("quoteVolume") or 0),
        "high_24h": float(data.get("highPrice") or 0),
        "low_24h": float(data.get("lowPrice") or 0),
        "source": f"binance_rest:{host}",
    }
    close_time = data.get("closeTime")
    if close_time is not None:
        row["event_time"] = close_time
    return row


async def fetch_ticker_24hr(
    pair: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    """GET /api/v3/ticker/24hr — last price, 24h change %, volumes."""
    if not _pair_ok(pair):
        return None
    owns = session is None
    if owns:
        session = aiohttp.ClientSession(timeout=_HTTP_TIMEOUT)
    try:
        assert session is not None
        for host in _PUBLIC_HOSTS:
            data = await _get_json(
                session,
                f"https://{host}/api/v3/ticker/24hr",
                params={"symbol": pair.upper()},
            )
            if not isinstance(data, dict):
                continue
            try:
                return _ticker_from_24hr(data, host=host)
            except (KeyError, TypeError, ValueError):
                continue
    finally:
        if owns:
            await session.close()
    return None


async def fetch_order_book(
    pair: str,
    *,
    limit: int = 20,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any] | None:
    """GET /api/v3/depth — shallow book for spread / liquidity hints."""
    if not _pair_ok(pair):
        return None
    lim = max(5, min(int(limit), 100))
    owns = session is None
    if owns:
        session = aiohttp.ClientSession(timeout=_HTTP_TIMEOUT)
    try:
        assert session is not None
        for host in _PUBLIC_HOSTS:
            data = await _get_json(
                session,
                f"https://{host}/api/v3/depth",
                params={"symbol": pair.upper(), "limit": lim},
            )
            if not isinstance(data, dict):
                continue
            bids = data.get("bids") or []
            asks = data.get("asks") or []
            if not bids or not asks:
                continue
            try:
                best_bid = float(bids[0][0])
                best_ask = float(asks[0][0])
                if best_bid <= 0 or best_ask <= 0:
                    continue
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
                    "source": f"binance_depth:{host}",
                    "limit": lim,
                }
            except (TypeError, ValueError, IndexError):
                continue
    finally:
        if owns:
            await session.close()
    return None


async def fetch_klines_closes(
    pair: str,
    *,
    interval: str = "1h",
    limit: int = 200,
    session: aiohttp.ClientSession | None = None,
) -> tuple[list[float], str | None]:
    """GET /api/v3/klines — close prices only."""
    if not _pair_ok(pair):
        return [], None
    lim = max(1, min(int(limit), 1000))
    owns = session is None
    if owns:
        session = aiohttp.ClientSession(timeout=_HTTP_TIMEOUT)
    try:
        assert session is not None
        for host in _PUBLIC_HOSTS:
            data = await _get_json(
                session,
                f"https://{host}/api/v3/klines",
                params={"symbol": pair.upper(), "interval": interval, "limit": lim},
            )
            if not isinstance(data, list):
                continue
            closes: list[float] = []
            for row in data:
                if isinstance(row, list) and len(row) > 4:
                    try:
                        closes.append(float(row[4]))
                    except (TypeError, ValueError):
                        continue
            if closes:
                return closes, host
    finally:
        if owns:
            await session.close()
    return [], None


async def fetch_public_spot_market(pair: str) -> dict[str, Any] | None:
    """
    Primary spot snapshot: 24hr ticker + shallow order book (single session).
    """
    if not _pair_ok(pair):
        return None
    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT) as session:
        ticker = await fetch_ticker_24hr(pair, session=session)
        if ticker is None:
            return None
        depth = await fetch_order_book(pair, limit=20, session=session)
        out = dict(ticker)
        if depth:
            out["order_book"] = depth
            out["best_bid"] = depth.get("best_bid")
            out["best_ask"] = depth.get("best_ask")
            out["spread_bps"] = depth.get("spread_bps")
        return out
