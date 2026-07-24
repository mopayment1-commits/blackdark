"""
BLACKDARK — Live Data Ingestion Layer (Phase 1: Points 1, 2, 7, & 33).

Polls spot USDT pairs, triangular cross-pairs, linear perpetual futures, and
funding rates across Binance, OKX, and Bybit every POLL_INTERVAL_SECONDS.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import time
from datetime import datetime, timezone
from typing import Any, Literal, Optional

import aiohttp
from pydantic import BaseModel, Field, field_validator

import config
from hot_storage import (
    enqueue_funding_snapshot,
    enqueue_market_snapshot,
    shutdown_hot_pipeline,
    start_hot_pipeline,
)
from liquidity_discovery import (
    build_whitelist_fallback_manifest,
    initialize_operational_manifest,
    load_operational_manifest,
    manifest_approved,
    operational_exchanges_from_manifest,
    polling_symbols_from_manifest,
    print_manifest_summary,
    save_operational_manifest,
    wait_for_manifest_review,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("BLACKDARK.Aggregator")

REQUEST_TIMEOUT_SECONDS = 15
DEFAULT_OPPORTUNITY_SCORE = 0.0

MarketType = Literal["spot", "cross", "perpetual"]

EXCHANGE_ENDPOINTS: dict[str, dict[str, Any]] = {
    "binance": {
        "spot": {
            "base_url": "https://api.binance.com",
            "ticker_path": "/api/v3/ticker/24hr",
            "depth_path": "/api/v3/depth",
        },
        "perpetual": {
            "base_url": "https://fapi.binance.com",
            "ticker_path": "/fapi/v1/ticker/24hr",
            "depth_path": "/fapi/v1/depth",
            "funding_path": "/fapi/v1/premiumIndex",
        },
    },
    "okx": {
        "spot": {
            "base_url": "https://www.okx.com",
            "ticker_path": "/api/v5/market/ticker",
            "depth_path": "/api/v5/market/books",
        },
        "perpetual": {
            "base_url": "https://www.okx.com",
            "ticker_path": "/api/v5/market/ticker",
            "depth_path": "/api/v5/market/books",
            "funding_path": "/api/v5/public/funding-rate",
        },
    },
    "bybit": {
        "spot": {
            "base_url": "https://api.bybit.com",
            "ticker_path": "/v5/market/tickers",
            "depth_path": "/v5/market/orderbook",
            "category": "spot",
        },
        "perpetual": {
            "base_url": "https://api.bybit.com",
            "ticker_path": "/v5/market/tickers",
            "depth_path": "/v5/market/orderbook",
            "category": "linear",
        },
    },
}


class TickerSnapshot(BaseModel):
    exchange: str
    symbol: str
    price: float = Field(gt=0)
    volume: Optional[float] = Field(default=None, ge=0)
    market_type: MarketType


class OrderBookSnapshot(BaseModel):
    exchange: str
    symbol: str
    bids: list[list[float]]
    asks: list[list[float]]
    market_type: MarketType

    @field_validator("bids", "asks")
    @classmethod
    def validate_levels(cls, levels: list[list[float]]) -> list[list[float]]:
        if not levels:
            raise ValueError("order book must contain at least one level")
        return levels


class FundingSnapshot(BaseModel):
    exchange: str
    symbol: str
    funding_rate: float
    next_funding_time: Optional[str] = None


class CycleStats(BaseModel):
    exchange: str
    ok: int = 0
    failed: int = 0


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_levels(raw_levels: list[Any]) -> list[list[float]]:
    parsed: list[list[float]] = []
    for level in raw_levels:
        if not level or len(level) < 2:
            continue
        parsed.append([float(level[0]), float(level[1])])
    return parsed


def _to_native_symbol(
    exchange_id: str,
    symbol: str,
    market_type: MarketType,
) -> str:
    base, quote = symbol.split("/")
    if market_type == "perpetual":
        if exchange_id == "okx":
            return f"{base}-{quote}-SWAP"
        return f"{base}{quote}"

    if exchange_id == "okx":
        return f"{base}-{quote}"
    return f"{base}{quote}"


def _market_type_for_symbol(
    symbol: str,
    *,
    spot_symbol_set: set[str] | None = None,
) -> MarketType:
    if spot_symbol_set is not None:
        if symbol in spot_symbol_set:
            return "spot"
        return "cross"
    if symbol in config.SYMBOLS:
        return "spot"
    return "cross"


async def _fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    params: Optional[dict[str, Any]] = None,
) -> Any:
    async with session.get(url, params=params) as response:
        response.raise_for_status()
        return await response.json()


async def _fetch_binance_market(
    session: aiohttp.ClientSession,
    symbol: str,
    market_type: MarketType,
) -> tuple[TickerSnapshot, OrderBookSnapshot]:
    native = _to_native_symbol("binance", symbol, market_type)
    endpoints = (
        EXCHANGE_ENDPOINTS["binance"]["perpetual"]
        if market_type == "perpetual"
        else EXCHANGE_ENDPOINTS["binance"]["spot"]
    )

    ticker_payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['ticker_path']}",
        {"symbol": native},
    )
    depth_payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['depth_path']}",
        {"symbol": native, "limit": config.ORDER_BOOK_DEPTH},
    )

    return (
        TickerSnapshot(
            exchange="binance",
            symbol=symbol,
            price=float(ticker_payload["lastPrice"]),
            volume=float(ticker_payload.get("volume") or 0),
            market_type=market_type,
        ),
        OrderBookSnapshot(
            exchange="binance",
            symbol=symbol,
            bids=_parse_levels(depth_payload.get("bids", [])),
            asks=_parse_levels(depth_payload.get("asks", [])),
            market_type=market_type,
        ),
    )


async def _fetch_okx_market(
    session: aiohttp.ClientSession,
    symbol: str,
    market_type: MarketType,
) -> tuple[TickerSnapshot, OrderBookSnapshot]:
    native = _to_native_symbol("okx", symbol, market_type)
    endpoints = (
        EXCHANGE_ENDPOINTS["okx"]["perpetual"]
        if market_type == "perpetual"
        else EXCHANGE_ENDPOINTS["okx"]["spot"]
    )

    ticker_payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['ticker_path']}",
        {"instId": native},
    )
    depth_payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['depth_path']}",
        {"instId": native, "sz": str(config.ORDER_BOOK_DEPTH)},
    )

    ticker_row = ticker_payload["data"][0]
    depth_row = depth_payload["data"][0]

    return (
        TickerSnapshot(
            exchange="okx",
            symbol=symbol,
            price=float(ticker_row["last"]),
            volume=float(ticker_row.get("vol24h") or 0),
            market_type=market_type,
        ),
        OrderBookSnapshot(
            exchange="okx",
            symbol=symbol,
            bids=_parse_levels(depth_row.get("bids", [])),
            asks=_parse_levels(depth_row.get("asks", [])),
            market_type=market_type,
        ),
    )


async def _fetch_bybit_market(
    session: aiohttp.ClientSession,
    symbol: str,
    market_type: MarketType,
) -> tuple[TickerSnapshot, OrderBookSnapshot]:
    native = _to_native_symbol("bybit", symbol, market_type)
    endpoints = (
        EXCHANGE_ENDPOINTS["bybit"]["perpetual"]
        if market_type == "perpetual"
        else EXCHANGE_ENDPOINTS["bybit"]["spot"]
    )
    category = endpoints["category"]

    ticker_payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['ticker_path']}",
        {"category": category, "symbol": native},
    )
    depth_payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['depth_path']}",
        {"category": category, "symbol": native, "limit": config.ORDER_BOOK_DEPTH},
    )

    ticker_row = ticker_payload["result"]["list"][0]
    depth_row = depth_payload["result"]

    return (
        TickerSnapshot(
            exchange="bybit",
            symbol=symbol,
            price=float(ticker_row["lastPrice"]),
            volume=float(ticker_row.get("volume24h") or 0),
            market_type=market_type,
        ),
        OrderBookSnapshot(
            exchange="bybit",
            symbol=symbol,
            bids=_parse_levels(depth_row.get("b", [])),
            asks=_parse_levels(depth_row.get("a", [])),
            market_type=market_type,
        ),
    )


MARKET_FETCHERS = {
    "binance": _fetch_binance_market,
    "okx": _fetch_okx_market,
    "bybit": _fetch_bybit_market,
}


async def _fetch_binance_funding(
    session: aiohttp.ClientSession,
    symbol: str,
) -> FundingSnapshot:
    native = _to_native_symbol("binance", symbol, "perpetual")
    endpoints = EXCHANGE_ENDPOINTS["binance"]["perpetual"]
    payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['funding_path']}",
        {"symbol": native},
    )
    next_funding = payload.get("nextFundingTime")
    return FundingSnapshot(
        exchange="binance",
        symbol=symbol,
        funding_rate=float(payload["lastFundingRate"]),
        next_funding_time=str(next_funding) if next_funding is not None else None,
    )


async def _fetch_okx_funding(
    session: aiohttp.ClientSession,
    symbol: str,
) -> FundingSnapshot:
    native = _to_native_symbol("okx", symbol, "perpetual")
    endpoints = EXCHANGE_ENDPOINTS["okx"]["perpetual"]
    payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['funding_path']}",
        {"instId": native},
    )
    row = payload["data"][0]
    return FundingSnapshot(
        exchange="okx",
        symbol=symbol,
        funding_rate=float(row["fundingRate"]),
        next_funding_time=row.get("fundingTime"),
    )


async def _fetch_bybit_funding(
    session: aiohttp.ClientSession,
    symbol: str,
) -> FundingSnapshot:
    native = _to_native_symbol("bybit", symbol, "perpetual")
    endpoints = EXCHANGE_ENDPOINTS["bybit"]["perpetual"]
    payload = await _fetch_json(
        session,
        f"{endpoints['base_url']}{endpoints['ticker_path']}",
        {"category": endpoints["category"], "symbol": native},
    )
    row = payload["result"]["list"][0]
    return FundingSnapshot(
        exchange="bybit",
        symbol=symbol,
        funding_rate=float(row["fundingRate"]),
        next_funding_time=row.get("nextFundingTime"),
    )


FUNDING_FETCHERS = {
    "binance": _fetch_binance_funding,
    "okx": _fetch_okx_funding,
    "bybit": _fetch_bybit_funding,
}


async def _persist_market_snapshot(
    ticker: TickerSnapshot,
    order_book: OrderBookSnapshot,
    timestamp: str,
) -> None:
    enqueue_market_snapshot(
        exchange=ticker.exchange,
        symbol=ticker.symbol,
        price=ticker.price,
        volume=ticker.volume,
        bids=order_book.bids,
        asks=order_book.asks,
        timestamp=timestamp,
        market_type=ticker.market_type,
        opportunity_score=DEFAULT_OPPORTUNITY_SCORE,
    )


async def _poll_market_symbol(
    session: aiohttp.ClientSession,
    exchange_id: str,
    symbol: str,
    market_type: MarketType,
) -> None:
    fetcher = MARKET_FETCHERS[exchange_id]
    timestamp = _utcnow_iso()
    ticker, order_book = await fetcher(session, symbol, market_type)
    await _persist_market_snapshot(ticker, order_book, timestamp)


async def _poll_funding_symbol(
    session: aiohttp.ClientSession,
    exchange_id: str,
    symbol: str,
) -> None:
    fetcher = FUNDING_FETCHERS[exchange_id]
    timestamp = _utcnow_iso()
    funding = await fetcher(session, symbol)
    enqueue_funding_snapshot(
        exchange=funding.exchange,
        symbol=funding.symbol,
        funding_rate=funding.funding_rate,
        next_funding_time=funding.next_funding_time,
        timestamp=timestamp,
    )


async def _poll_exchange(
    session: aiohttp.ClientSession,
    exchange_id: str,
    *,
    spot_symbols: list[str],
    cross_symbols: set[str],
    perp_symbols: list[str],
) -> CycleStats:
    stats = CycleStats(exchange=exchange_id)
    stable_spot_symbols = [symbol for symbol in spot_symbols if symbol not in cross_symbols]

    tasks: list[Any] = []
    labels: list[str] = []

    for symbol in spot_symbols:
        market_type = _market_type_for_symbol(
            symbol,
            spot_symbol_set=set(stable_spot_symbols),
        )
        tasks.append(_poll_market_symbol(session, exchange_id, symbol, market_type))
        labels.append(f"{symbol}:{market_type}")

    for symbol in perp_symbols:
        tasks.append(_poll_market_symbol(session, exchange_id, symbol, "perpetual"))
        labels.append(f"{symbol}:perpetual")
        tasks.append(_poll_funding_symbol(session, exchange_id, symbol))
        labels.append(f"{symbol}:funding")

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for label, result in zip(labels, results):
        if isinstance(result, Exception):
            stats.failed += 1
            logger.warning(
                "Fetch failed | exchange=%s target=%s error=%s",
                exchange_id,
                label,
                result,
            )
        else:
            stats.ok += 1

    logger.info(
        "Cycle complete | exchange=%s ok=%d failed=%d spot=%d perp=%d",
        exchange_id,
        stats.ok,
        stats.failed,
        len(spot_symbols),
        len(perp_symbols),
    )
    return stats


class Aggregator:
    """Coordinates concurrent exchange polling on a fixed interval."""

    def __init__(self) -> None:
        self._shutdown = asyncio.Event()
        self._session: Optional[aiohttp.ClientSession] = None
        self._operational_manifest: dict[str, Any] | None = None

    async def _initialize_operational_inventory(self) -> None:
        """
        Build manifest, persist review file, and pause until approved.

        No hot pipeline, websocket loops, or polling start before approval.
        """
        try:
            manifest = await initialize_operational_manifest()
        except Exception:
            logger.exception(
                "Operational manifest generation failed; falling back to whitelist baseline."
            )
            manifest = load_operational_manifest()
            if manifest is None:
                manifest = build_whitelist_fallback_manifest()
                save_operational_manifest(manifest)
                print_manifest_summary(manifest, manifest_path=str(config.OPERATIONAL_MANIFEST_PATH))

        if manifest is None:
            logger.error("Unable to build or load operational manifest; aborting startup.")
            raise RuntimeError("Operational manifest is required before ingestion can start.")

        if config.MANIFEST_REQUIRE_REVIEW and not manifest_approved(manifest):
            manifest = await wait_for_manifest_review(manifest)

        if config.MANIFEST_REQUIRE_REVIEW and not manifest_approved(manifest):
            logger.error(
                "Operational manifest remains unapproved. Ingestion will not start."
            )
            raise RuntimeError("Operational manifest review required.")

        self._operational_manifest = manifest
        operational_exchanges = operational_exchanges_from_manifest(manifest)
        logger.info(
            "Operational manifest ready | exchanges=%d ingestion_ready=%s",
            len(operational_exchanges),
            sorted(set(operational_exchanges) & set(config.INGESTION_READY_EXCHANGES)),
        )

    async def start(self) -> None:
        await self._initialize_operational_inventory()

        await start_hot_pipeline()

        timeout = aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS)
        self._session = aiohttp.ClientSession(timeout=timeout)
        self._register_signal_handlers()

        exchanges = [
            exchange_id
            for exchange_id in operational_exchanges_from_manifest(self._operational_manifest)
            if exchange_id in config.INGESTION_READY_EXCHANGES and exchange_id in MARKET_FETCHERS
        ]
        if not exchanges:
            exchanges = [
                exchange_id
                for exchange_id in config.INGESTION_READY_EXCHANGES
                if exchange_id in MARKET_FETCHERS
            ]

        spot_symbols, cross_symbols, perp_symbols = polling_symbols_from_manifest(
            self._operational_manifest
        )
        logger.info(
            "Aggregator started | manifest_status=%s exchanges=%s spot=%d cross=%d perp=%d interval=%ss hot_pipeline=enabled",
            (self._operational_manifest or {}).get("status", "unknown"),
            exchanges,
            len(spot_symbols),
            len(cross_symbols),
            len(perp_symbols),
            config.POLL_INTERVAL_SECONDS,
        )

        try:
            await self._run_loop(
                exchanges,
                spot_symbols=spot_symbols,
                cross_symbols=set(cross_symbols),
                perp_symbols=perp_symbols,
            )
        finally:
            await self._close_session()
            await shutdown_hot_pipeline()

    async def _run_loop(
        self,
        exchanges: list[str],
        *,
        spot_symbols: list[str],
        cross_symbols: set[str],
        perp_symbols: list[str],
    ) -> None:
        assert self._session is not None

        while not self._shutdown.is_set():
            cycle_started = time.monotonic()

            results = await asyncio.gather(
                *(
                    _poll_exchange(
                        self._session,
                        exchange_id,
                        spot_symbols=spot_symbols,
                        cross_symbols=cross_symbols,
                        perp_symbols=perp_symbols,
                    )
                    for exchange_id in exchanges
                ),
                return_exceptions=True,
            )

            for exchange_id, result in zip(exchanges, results):
                if isinstance(result, Exception):
                    logger.error(
                        "Exchange worker crashed | exchange=%s error=%s",
                        exchange_id,
                        result,
                    )

            elapsed = time.monotonic() - cycle_started
            sleep_for = max(0.0, config.POLL_INTERVAL_SECONDS - elapsed)
            if sleep_for > 0 and not self._shutdown.is_set():
                try:
                    await asyncio.wait_for(self._shutdown.wait(), timeout=sleep_for)
                except asyncio.TimeoutError:
                    pass

        logger.info("Aggregator shutdown complete.")

    def _register_signal_handlers(self) -> None:
        loop = asyncio.get_running_loop()

        def _request_shutdown() -> None:
            if not self._shutdown.is_set():
                logger.info("Shutdown signal received.")
                self._shutdown.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, _request_shutdown)
            except NotImplementedError:
                signal.signal(sig, lambda _signum, _frame: _request_shutdown())

    async def _close_session(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
            await asyncio.sleep(0)
            logger.info("aiohttp ClientSession closed.")


async def run_aggregator() -> None:
    aggregator = Aggregator()
    await aggregator.start()


def main() -> None:
    try:
        asyncio.run(run_aggregator())
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received; exiting.")


if __name__ == "__main__":
    main()
