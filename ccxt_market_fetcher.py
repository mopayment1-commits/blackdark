"""
BLACKDARK — CCXT Market Fetcher (Phase B).

Generic spot + swap polling for Tier-2 CEX venues via ccxt.async_support.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

import config

logger = logging.getLogger("BLACKDARK.CCXTFetcher")

MarketType = Literal["spot", "cross", "perpetual"]

# Internal BLACKDARK id → ccxt.pro exchange id
CCXT_ID_MAP: dict[str, str] = {
    # Phase B (already live)
    "htx": "htx",
    "cryptocom": "cryptocom",
    "bingx": "bingx",
    "bitfinex": "bitfinex",
    "bitstamp": "bitstamp",
    "poloniex": "poloniex",
    "phemex": "phemex",
    "whitebit": "whitebit",
    "bitmart": "bitmart",
    "coinex": "coinex",
    "lbank": "lbank",
    "ascendex": "ascendex",
    "digifinex": "digifinex",
    "probit": "probit",
    "xt": "xt",
    "gemini": "gemini",
    "bitvavo": "bitvavo",
    # Phase B2 — additional CEX / regional
    "toobit": "toobit",
    "deepcoin": "deepcoin",
    "weex": "weex",
    "bigone": "bigone",
    "woox": "woo",
    "upbit": "upbit",
    "bithumb": "bithumb",
    "tokocrypto": "tokocrypto",
    "bitflyer": "bitflyer",
    "coincheck": "coincheck",
    "mercadobitcoin": "mercado",
    "independentreserve": "independentreserve",
    "luno": "luno",
    "bitso": "bitso",
    "btcturk": "btcturk",
    "coinone": "coinone",
    "bitbank": "bitbank",
}


def _discover_ccxt_phase_b2() -> frozenset[str]:
    try:
        import ccxt

        supported: set[str] = set(CCXT_ID_MAP.keys())
        for exchange_id, ccxt_id in tuple(CCXT_ID_MAP.items()):
            if ccxt_id not in ccxt.exchanges:
                supported.discard(exchange_id)
        return frozenset(supported)
    except ImportError:
        return frozenset(CCXT_ID_MAP.keys())


PHASE_B_EXCHANGES: frozenset[str] = _discover_ccxt_phase_b2()

# Spot-only CCXT venues (no perp/funding in aggregator loop)
CCXT_SPOT_ONLY: frozenset[str] = frozenset(
    {
        "bitfinex",
        "bitstamp",
        "poloniex",
        "coinex",
        "lbank",
        "ascendex",
        "digifinex",
        "probit",
        "xt",
        "bitvavo",
        "gemini",
        "upbit",
        "bithumb",
        "bitflyer",
        "coincheck",
        "coinone",
        "bitbank",
        "btcturk",
        "bitso",
        "luno",
        "independentreserve",
        "tokocrypto",
        "mercadobitcoin",
        "toobit",
        "deepcoin",
        "weex",
        "bigone",
        "woox",
    }
)

# CCXT venues with swap + funding support
CCXT_PERP_READY: frozenset[str] = frozenset(
    {"htx", "cryptocom", "bingx", "phemex", "whitebit", "bitmart"}
)

_exchange_pool: dict[str, Any] = {}
_exchange_locks: dict[str, asyncio.Lock] = {}
_markets_loaded: set[str] = set()


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def ccxt_exchange_id(exchange_id: str) -> str:
    return CCXT_ID_MAP.get(exchange_id.strip().lower(), exchange_id.strip().lower())


async def _get_exchange(exchange_id: str) -> Any:
    import ccxt.async_support as ccxt_async

    ccxt_id = ccxt_exchange_id(exchange_id)
    if ccxt_id not in ccxt_async.exchanges:
        raise ValueError(f"CCXT does not support exchange: {ccxt_id}")

    if exchange_id in _exchange_pool:
        return _exchange_pool[exchange_id]

    lock = _exchange_locks.setdefault(exchange_id, asyncio.Lock())
    async with lock:
        if exchange_id in _exchange_pool:
            return _exchange_pool[exchange_id]
        exchange_class = getattr(ccxt_async, ccxt_id)
        exchange = exchange_class(
            {
                "enableRateLimit": True,
                "timeout": 20000,
                "options": {"defaultType": "spot"},
            }
        )
        _exchange_pool[exchange_id] = exchange
        return exchange


async def _ensure_markets(exchange_id: str) -> Any:
    exchange = await _get_exchange(exchange_id)
    if exchange_id not in _markets_loaded:
        await exchange.load_markets()
        _markets_loaded.add(exchange_id)
    return exchange


def _resolve_symbol(exchange: Any, symbol: str, market_type: MarketType) -> str | None:
    if market_type in {"spot", "cross"}:
        if symbol in exchange.markets:
            return symbol
        return None

    swap = f"{symbol}:USDT"
    if swap in exchange.markets:
        return swap
    alt = symbol.replace("/", "") + ":USDT"
    if alt in exchange.markets:
        return alt
    return None


def _parse_book_side(levels: list[Any]) -> list[list[float]]:
    parsed: list[list[float]] = []
    for level in levels or []:
        if not level or len(level) < 2:
            continue
        parsed.append([float(level[0]), float(level[1])])
    return parsed


async def fetch_ccxt_market(
    _session: Any,
    symbol: str,
    market_type: MarketType,
    *,
    exchange_id: str,
) -> tuple[Any, Any]:
    """Returns (TickerSnapshot, OrderBookSnapshot) compatible with aggregator models."""
    from aggregator import OrderBookSnapshot, TickerSnapshot

    exchange = await _ensure_markets(exchange_id)
    ccxt_symbol = _resolve_symbol(exchange, symbol, market_type)
    if ccxt_symbol is None:
        raise ValueError(f"Symbol unavailable on {exchange_id}: {symbol} ({market_type})")

    ticker = await exchange.fetch_ticker(ccxt_symbol)
    book = await exchange.fetch_order_book(ccxt_symbol, limit=config.ORDER_BOOK_DEPTH)

    price = float(ticker.get("last") or ticker.get("close") or 0)
    if price <= 0:
        raise ValueError(f"Invalid ticker price | exchange={exchange_id} symbol={ccxt_symbol}")

    return (
        TickerSnapshot(
            exchange=exchange_id,
            symbol=symbol,
            price=price,
            volume=float(ticker.get("baseVolume") or ticker.get("volume") or 0),
            market_type=market_type,
        ),
        OrderBookSnapshot(
            exchange=exchange_id,
            symbol=symbol,
            bids=_parse_book_side(book.get("bids")),
            asks=_parse_book_side(book.get("asks")),
            market_type=market_type,
            book_origin="venue_l2",
            decision_grade=True,
        ),
    )


async def fetch_ccxt_funding(
    _session: Any,
    symbol: str,
    *,
    exchange_id: str,
) -> Any:
    from aggregator import FundingSnapshot

    exchange = await _ensure_markets(exchange_id)
    ccxt_symbol = _resolve_symbol(exchange, symbol, "perpetual")
    if ccxt_symbol is None:
        raise ValueError(f"No swap market for funding | exchange={exchange_id} symbol={symbol}")

    rate_payload = await exchange.fetch_funding_rate(ccxt_symbol)
    return FundingSnapshot(
        exchange=exchange_id,
        symbol=symbol,
        funding_rate=float(rate_payload.get("fundingRate") or 0),
        next_funding_time=str(rate_payload.get("fundingTimestamp") or "") or None,
    )


def make_market_fetcher(exchange_id: str) -> Callable[..., Any]:
    async def _fetch(session: Any, symbol: str, market_type: MarketType) -> tuple[Any, Any]:
        return await fetch_ccxt_market(
            session,
            symbol,
            market_type,
            exchange_id=exchange_id,
        )

    return _fetch


def make_funding_fetcher(exchange_id: str) -> Callable[..., Any]:
    async def _fetch(session: Any, symbol: str) -> Any:
        return await fetch_ccxt_funding(session, symbol, exchange_id=exchange_id)

    return _fetch


def build_ccxt_market_fetchers() -> dict[str, Callable[..., Any]]:
    return {exchange_id: make_market_fetcher(exchange_id) for exchange_id in PHASE_B_EXCHANGES}


def all_ccxt_exchange_ids() -> frozenset[str]:
    return PHASE_B_EXCHANGES


def build_ccxt_funding_fetchers() -> dict[str, Callable[..., Any]]:
    return {
        exchange_id: make_funding_fetcher(exchange_id)
        for exchange_id in CCXT_PERP_READY
    }


def symbols_for_exchange(exchange_id: str, spot_symbols: list[str]) -> list[str]:
    """Limit CCXT venue symbol fan-out to protect rate limits."""
    if exchange_id not in PHASE_B_EXCHANGES:
        return spot_symbols

    limit = max(5, int(getattr(config, "CCXT_SYMBOL_LIMIT", 25)))
    core_assets = set(config.WHITELIST_ASSETS)
    core = [sym for sym in spot_symbols if sym.split("/")[0] in core_assets]
    rest = [sym for sym in spot_symbols if sym.split("/")[0] not in core_assets]
    return core + rest[: max(0, limit - len(core))]


async def close_ccxt_pool() -> None:
    for exchange_id, exchange in tuple(_exchange_pool.items()):
        try:
            await exchange.close()
        except Exception:
            logger.warning("Failed closing CCXT exchange | id=%s", exchange_id)
    _exchange_pool.clear()
    _markets_loaded.clear()


async def probe_phase_b_exchanges(sample_symbol: str = "BTC/USDT") -> dict[str, Any]:
    """Quick health probe for dashboard / diagnostics."""
    results: list[dict[str, Any]] = []
    for exchange_id in sorted(PHASE_B_EXCHANGES):
        row = {"exchange": exchange_id, "ccxt_id": ccxt_exchange_id(exchange_id), "ok": False}
        try:
            ticker, _book = await fetch_ccxt_market(None, sample_symbol, "spot", exchange_id=exchange_id)
            row["ok"] = True
            row["price"] = ticker.price
        except Exception as exc:
            row["error"] = str(exc)[:180]
        results.append(row)
    ok_count = sum(1 for row in results if row["ok"])
    await close_ccxt_pool()
    return {
        "phase": "B",
        "total": len(PHASE_B_EXCHANGES),
        "ok": ok_count,
        "failed": len(PHASE_B_EXCHANGES) - ok_count,
        "results": results,
        "timestamp": _utcnow_iso(),
    }
