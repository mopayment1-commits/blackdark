"""Native public REST L2 fetchers for regional CEX (real multi-level books).

Replaces CoinGecko 1-level synthetic TOB for venues that expose public depth.
Never fabricates ladder sizes. Never claims LIVE without a successful HTTP book.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp

logger = logging.getLogger("BLACKDARK.NativeRegionalCEX")

MarketType = Literal["spot", "cross", "perpetual"]

# Venue → default spot symbol used by mesh overrides / prove surfaces.
NATIVE_REGIONAL_DEFAULT_SYMBOL: dict[str, str] = {
    "valr": "BTC/ZAR",
    "korbit": "BTC/KRW",
    "buda": "BTC/CLP",
    "coinone": "BTC/KRW",
    "bitfinex": "BTC/USDT",
    "woox": "BTC/USDT",
    "hotcoin": "BTC/USDT",
    "paribu": "BTC/USDT",
    # Brand/regional aliases sharing a public parent book (honest venue_l2 from parent API).
    "gemini_uk": "BTC/USD",
    "cryptocom_us": "BTC/USDT",
    # Former CoinGecko 1-level proxies upgraded to real public L2 books.
    "pionex": "BTC/USDT",
    "coinw": "BTC/USDT",
    "orangex": "BTC/USDT",
    "biconomy": "BTC/USDT",
    "coinstore": "BTC/USDT",
    "azbit": "BTC/USDT",
}

NATIVE_REGIONAL_VENUES: frozenset[str] = frozenset(NATIVE_REGIONAL_DEFAULT_SYMBOL.keys())


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _book_ok(bids: list[list[float]], asks: list[list[float]], *, min_levels: int = 5) -> bool:
    return len(bids) >= min_levels and len(asks) >= min_levels


async def _fetch_valr(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    # VALR public orderbook — BTCZAR etc.
    pair = symbol.replace("/", "")
    url = f"https://api.valr.com/v1/public/{pair}/orderbook"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    bids = [[float(x["price"]), float(x["quantity"])] for x in (body.get("Bids") or [])]
    asks = [[float(x["price"]), float(x["quantity"])] for x in (body.get("Asks") or [])]
    return bids, asks


def _levels_pq(rows: list[Any]) -> list[list[float]]:
    out: list[list[float]] = []
    for row in rows or []:
        if not row or len(row) < 2:
            continue
        out.append([float(row[0]), float(row[1])])
    return out


async def _fetch_korbit(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    pair = symbol.replace("/", "_").lower()
    url = f"https://api.korbit.co.kr/v1/orderbook?currency_pair={pair}"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    # Korbit levels are [price, qty, order_count]
    return _levels_pq(body.get("bids") or []), _levels_pq(body.get("asks") or [])


async def _fetch_buda(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    market = symbol.replace("/", "-").lower()
    url = f"https://www.buda.com/api/v2/markets/{market}/order_book"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    ob = body.get("order_book") or {}
    return _levels_pq(ob.get("bids") or []), _levels_pq(ob.get("asks") or [])


async def _fetch_coinone(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    base = symbol.split("/")[0].lower()
    url = f"https://api.coinone.co.kr/orderbook/?currency={base}"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    if body.get("result") != "success":
        raise ValueError(f"coinone_error:{body.get('errorCode')}")
    bids = [[float(x["price"]), float(x["qty"])] for x in (body.get("bid") or [])]
    asks = [[float(x["price"]), float(x["qty"])] for x in (body.get("ask") or [])]
    return bids, asks


async def _fetch_bitfinex(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    # Prefer UST (Tether) book which is the liquid Bitfinex BTC pair.
    base, quote = symbol.split("/")
    pair = f"t{base}UST" if quote in {"USDT", "UST"} else f"t{base}{quote}"
    url = f"https://api-pub.bitfinex.com/v2/book/{pair}/P0?len=25"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    if not isinstance(body, list):
        raise ValueError("bitfinex_bad_book")
    bids: list[list[float]] = []
    asks: list[list[float]] = []
    for row in body:
        # [price, count, amount] — amount>0 bid, amount<0 ask
        if not row or len(row) < 3:
            continue
        price = float(row[0])
        amount = float(row[2])
        if amount > 0:
            bids.append([price, amount])
        elif amount < 0:
            asks.append([price, abs(amount)])
    return bids, asks


async def _fetch_woox(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    # Woo X public orderbook — registry id "woox", API symbol SPOT_BTC_USDT.
    base, quote = symbol.split("/")
    woo_sym = f"SPOT_{base}_{quote}"
    url = f"https://api.woo.org/v1/public/orderbook/{woo_sym}"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    if not body.get("success"):
        raise ValueError(f"woox_error:{body.get('code') or body.get('message')}")
    bids = [[float(x["price"]), float(x["quantity"])] for x in (body.get("bids") or [])]
    asks = [[float(x["price"]), float(x["quantity"])] for x in (body.get("asks") or [])]
    return bids, asks


async def _fetch_hotcoin(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    base, quote = symbol.split("/")
    pair = f"{base.lower()}_{quote.lower()}"
    url = f"https://api.hotcoinfin.com/v1/depth?symbol={pair}"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    if int(body.get("code") or 0) != 200:
        raise ValueError(f"hotcoin_error:{body.get('msg') or body.get('code')}")
    depth = (body.get("data") or {}).get("depth") or {}
    return _levels_pq(depth.get("bids") or []), _levels_pq(depth.get("asks") or [])


async def _fetch_paribu(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    base, quote = symbol.split("/")
    # Paribu public L2 — BTC_USDT / BTC_TL.
    market = f"{base.upper()}_{quote.upper()}"
    if quote.upper() == "USD":
        market = f"{base.upper()}_USDT"
    url = f"https://api.paribu.com/orderbook?market={market}"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    return _levels_pq(body.get("bids") or []), _levels_pq(body.get("asks") or [])


async def _fetch_gemini_uk(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    # Gemini UK catalog alias — same public Gemini REST book (BTCUSD).
    base, quote = symbol.split("/")
    pair = f"{base.upper()}{quote.upper()}"
    if quote.upper() == "USDT":
        pair = f"{base.upper()}USD"
    url = f"https://api.gemini.com/v1/book/{pair}?limit_bids=20&limit_asks=20"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    bids = [[float(x["price"]), float(x["amount"])] for x in (body.get("bids") or [])]
    asks = [[float(x["price"]), float(x["amount"])] for x in (body.get("asks") or [])]
    return bids, asks


async def _fetch_cryptocom_us(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    # Crypto.com US catalog alias — public Crypto.com Exchange book.
    base, quote = symbol.split("/")
    instrument = f"{base.upper()}_{quote.upper()}"
    url = (
        "https://api.crypto.com/exchange/v1/public/get-book"
        f"?instrument_name={instrument}&depth=20"
    )
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    if int(body.get("code") or 0) != 0:
        raise ValueError(f"cryptocom_us_error:{body.get('message') or body.get('code')}")
    data = ((body.get("result") or {}).get("data") or [{}])[0]
    return _levels_pq(data.get("bids") or []), _levels_pq(data.get("asks") or [])


async def _fetch_pionex(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    base, quote = symbol.split("/")
    pair = f"{base.upper()}_{quote.upper()}"
    url = f"https://api.pionex.com/api/v1/market/depth?symbol={pair}&limit=20"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    if not body.get("result"):
        raise ValueError(f"pionex_error:{body.get('error_msg') or body}")
    data = body.get("data") or {}
    return _levels_pq(data.get("bids") or []), _levels_pq(data.get("asks") or [])


async def _fetch_coinw(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    base, quote = symbol.split("/")
    pair = f"{base.upper()}_{quote.upper()}"
    url = (
        "https://api.coinw.com/api/v1/public"
        f"?command=returnOrderBook&symbol={pair}&size=20"
    )
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    if str(body.get("code") or "") not in {"200", "0"}:
        raise ValueError(f"coinw_error:{body.get('msg') or body.get('message') or body.get('code')}")
    data = body.get("data") or {}
    return _levels_pq(data.get("bids") or []), _levels_pq(data.get("asks") or [])


async def _fetch_orangex(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    base, quote = symbol.split("/")
    instrument = f"{base.upper()}-{quote.upper()}"
    url = "https://api.orangex.com/api/v1/public/get_order_book"
    async with session.get(url, params={"instrument_name": instrument, "depth": 20}) as r:
        r.raise_for_status()
        body = await r.json()
    data = body.get("result") or {}
    return _levels_pq(data.get("bids") or []), _levels_pq(data.get("asks") or [])


async def _fetch_biconomy(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    base, quote = symbol.split("/")
    pair = f"{base.upper()}_{quote.upper()}"
    url = f"https://www.biconomy.com/api/v1/depth?symbol={pair}&size=20"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    return _levels_pq(body.get("bids") or []), _levels_pq(body.get("asks") or [])


async def _fetch_coinstore(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    base, quote = symbol.split("/")
    pair = f"{base.upper()}{quote.upper()}"
    url = f"https://api.coinstore.com/api/v1/market/depth/{pair}?depth=20"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    data = body.get("data") or {}
    # a=asks, b=bids; levels [price, qty, ...]
    return _levels_pq(data.get("b") or []), _levels_pq(data.get("a") or [])


async def _fetch_azbit(session: aiohttp.ClientSession, symbol: str) -> tuple[list[list[float]], list[list[float]]]:
    base, quote = symbol.split("/")
    pair = f"{base.upper()}_{quote.upper()}"
    url = f"https://data.azbit.com/api/orderbook?currencyPairCode={pair}"
    async with session.get(url) as r:
        r.raise_for_status()
        body = await r.json()
    if not isinstance(body, list):
        raise ValueError("azbit_bad_book")
    bids: list[list[float]] = []
    asks: list[list[float]] = []
    for row in body:
        price = float(row.get("price") or 0)
        amount = float(row.get("amount") or 0)
        if price <= 0 or amount <= 0:
            continue
        if row.get("isBid"):
            bids.append([price, amount])
        else:
            asks.append([price, amount])
    bids.sort(key=lambda x: x[0], reverse=True)
    asks.sort(key=lambda x: x[0])
    return bids, asks


_FETCHERS: dict[str, Callable[..., Any]] = {
    "valr": _fetch_valr,
    "korbit": _fetch_korbit,
    "buda": _fetch_buda,
    "coinone": _fetch_coinone,
    "bitfinex": _fetch_bitfinex,
    "woox": _fetch_woox,
    "hotcoin": _fetch_hotcoin,
    "paribu": _fetch_paribu,
    "gemini_uk": _fetch_gemini_uk,
    "cryptocom_us": _fetch_cryptocom_us,
    "pionex": _fetch_pionex,
    "coinw": _fetch_coinw,
    "orangex": _fetch_orangex,
    "biconomy": _fetch_biconomy,
    "coinstore": _fetch_coinstore,
    "azbit": _fetch_azbit,
}


async def fetch_native_regional_market(
    session: aiohttp.ClientSession,
    symbol: str,
    market_type: MarketType,
    *,
    exchange_id: str,
) -> tuple[Any, Any]:
    from aggregator import OrderBookSnapshot, TickerSnapshot

    if market_type not in {"spot", "cross"}:
        raise ValueError(f"native_regional_spot_only:{exchange_id}")
    fn = _FETCHERS.get(exchange_id)
    if not fn:
        raise ValueError(f"native_regional_unknown:{exchange_id}")
    bids, asks = await fn(session, symbol)
    if not _book_ok(bids, asks):
        raise ValueError(
            f"insufficient_l2:{exchange_id}:bids={len(bids)}:asks={len(asks)}"
        )
    mid = (bids[0][0] + asks[0][0]) / 2.0
    return (
        TickerSnapshot(
            exchange=exchange_id,
            symbol=symbol,
            price=mid,
            volume=0.0,
            market_type="spot",
        ),
        OrderBookSnapshot(
            exchange=exchange_id,
            symbol=symbol,
            bids=bids,
            asks=asks,
            market_type="spot",
        ),
    )


def make_market_fetcher(exchange_id: str) -> Callable[..., Any]:
    async def _fetch(session: Any, symbol: str, market_type: MarketType) -> tuple[Any, Any]:
        return await fetch_native_regional_market(
            session, symbol, market_type, exchange_id=exchange_id
        )

    return _fetch


def build_native_regional_market_fetchers() -> dict[str, Callable[..., Any]]:
    return {vid: make_market_fetcher(vid) for vid in sorted(NATIVE_REGIONAL_VENUES)}
