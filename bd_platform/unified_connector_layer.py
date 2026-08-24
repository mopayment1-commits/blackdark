"""
Unified Connector Layer — Feature #194 (Sprint 0 infrastructure).

Canonical schema + multi-exchange price connectors for #133 (aggregation)
and #127 (live refresh). NOT user-facing — feeds price_aggregation_engine.

Design:
  1. Canonical quote schema across all venues
  2. Parallel connector fetch with source metadata
  3. Extensible registry (400+ exchanges target via connector expansion)
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

import aiohttp

logger = logging.getLogger("BLACKDARK.UnifiedConnector")

_FEATURE_ID = 194
_HTTP_TIMEOUT = aiohttp.ClientTimeout(total=6)

# Registered connectors — expand toward 400+ exchange coverage
_CONNECTOR_IDS: tuple[str, ...] = (
    "binance",
    "okx",
    "bybit",
    "kraken",
    "coinbase",
    "coingecko",
    "gateio",
    "kucoin",
    "mexc",
    "bitget",
)


@dataclass(frozen=True)
class CanonicalPriceQuote:
    """Unified price quote schema for all connectors."""

    connector_id: str
    exchange: str
    asset: str
    pair: str
    price_usd: float
    bid: float | None = None
    ask: float | None = None
    volume_24h_usd: float = 0.0
    change_24h_pct: float = 0.0
    canonical_id: str | None = None
    source: str = ""
    market_type: str = "spot"
    fetched_at: str = ""
    latency_ms: float = 0.0
    is_stale: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConnectorFetchResult:
    connector_id: str
    ok: bool
    quote: CanonicalPriceQuote | None = None
    error: str | None = None
    latency_ms: float = 0.0


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _resolve_canonical(asset: str) -> tuple[str, str | None]:
    try:
        from blackdark.canonical.resolver import resolve_asset

        result = resolve_asset(asset)
        if result.found and result.symbol:
            return result.symbol.upper(), result.canonical_id
    except Exception:
        pass
    return asset.upper().replace("/USDT", ""), None


async def _fetch_binance(asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
    pair = f"{asset}USDT"
    t0 = time.perf_counter()
    try:
        async with session.get(
            "https://api.binance.com/api/v3/ticker/24hr",
            params={"symbol": pair},
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
        price = float(data.get("lastPrice") or 0)
        if price <= 0:
            return None
        sym, cid = _resolve_canonical(asset)
        return CanonicalPriceQuote(
            connector_id="binance",
            exchange="binance",
            asset=sym,
            pair=pair,
            price_usd=price,
            bid=float(data.get("bidPrice") or 0) or None,
            ask=float(data.get("askPrice") or 0) or None,
            volume_24h_usd=float(data.get("quoteVolume") or 0),
            change_24h_pct=float(data.get("priceChangePercent") or 0),
            canonical_id=cid,
            source="binance:api.binance.com",
            fetched_at=_utcnow(),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError):
        return None


async def _fetch_okx(asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
    inst = f"{asset}-USDT"
    t0 = time.perf_counter()
    try:
        async with session.get(
            "https://www.okx.com/api/v5/market/ticker",
            params={"instId": inst},
        ) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
        rows = (payload.get("data") or [])
        if not rows:
            return None
        row = rows[0]
        price = float(row.get("last") or 0)
        if price <= 0:
            return None
        sym, cid = _resolve_canonical(asset)
        return CanonicalPriceQuote(
            connector_id="okx",
            exchange="okx",
            asset=sym,
            pair=inst,
            price_usd=price,
            bid=float(row.get("bidPx") or 0) or None,
            ask=float(row.get("askPx") or 0) or None,
            volume_24h_usd=float(row.get("volCcy24h") or 0),
            canonical_id=cid,
            source="okx:public",
            fetched_at=_utcnow(),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError):
        return None


async def _fetch_bybit(asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
    sym = f"{asset}USDT"
    t0 = time.perf_counter()
    try:
        async with session.get(
            "https://api.bybit.com/v5/market/tickers",
            params={"category": "spot", "symbol": sym},
        ) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
        rows = ((payload.get("result") or {}).get("list") or [])
        if not rows:
            return None
        row = rows[0]
        price = float(row.get("lastPrice") or 0)
        if price <= 0:
            return None
        sym_u, cid = _resolve_canonical(asset)
        return CanonicalPriceQuote(
            connector_id="bybit",
            exchange="bybit",
            asset=sym_u,
            pair=sym,
            price_usd=price,
            bid=float(row.get("bid1Price") or 0) or None,
            ask=float(row.get("ask1Price") or 0) or None,
            volume_24h_usd=float(row.get("turnover24h") or 0),
            change_24h_pct=float(row.get("price24hPcnt") or 0) * 100,
            canonical_id=cid,
            source="bybit:public",
            fetched_at=_utcnow(),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError):
        return None


async def _fetch_via_market_context(asset: str, fetcher_name: str) -> CanonicalPriceQuote | None:
    """Delegate to market_context REST fetchers."""
    from market_context import (
        _fetch_coinbase_ticker,
        _fetch_coingecko_ticker,
        _fetch_kraken_ticker,
    )

    fetchers: dict[str, Callable[..., Awaitable[dict[str, Any] | None]]] = {
        "kraken": _fetch_kraken_ticker,
        "coinbase": _fetch_coinbase_ticker,
        "coingecko": _fetch_coingecko_ticker,
    }
    fn = fetchers.get(fetcher_name)
    if not fn:
        return None
    t0 = time.perf_counter()
    row = await fn(asset)
    if not row or float(row.get("price") or 0) <= 0:
        return None
    sym, cid = _resolve_canonical(asset)
    return CanonicalPriceQuote(
        connector_id=fetcher_name,
        exchange=fetcher_name,
        asset=sym,
        pair=f"{sym}USDT",
        price_usd=float(row["price"]),
        volume_24h_usd=float(row.get("quote_volume") or row.get("volume") or 0),
        change_24h_pct=float(row.get("change_24h") or 0),
        canonical_id=cid or row.get("canonical_id"),
        source=str(row.get("source") or fetcher_name),
        fetched_at=_utcnow(),
        latency_ms=round((time.perf_counter() - t0) * 1000, 1),
    )


async def _fetch_gateio(asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
    pair = f"{asset}_USDT"
    t0 = time.perf_counter()
    try:
        async with session.get(
            "https://api.gateio.ws/api/v4/spot/tickers",
            params={"currency_pair": pair},
        ) as resp:
            if resp.status != 200:
                return None
            rows = await resp.json()
        if not rows:
            return None
        row = rows[0]
        price = float(row.get("last") or 0)
        if price <= 0:
            return None
        sym, cid = _resolve_canonical(asset)
        return CanonicalPriceQuote(
            connector_id="gateio",
            exchange="gateio",
            asset=sym,
            pair=pair,
            price_usd=price,
            volume_24h_usd=float(row.get("quote_volume") or 0),
            change_24h_pct=float(row.get("change_percentage") or 0),
            canonical_id=cid,
            source="gateio:public",
            fetched_at=_utcnow(),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError):
        return None


async def _fetch_kucoin(asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
    sym = f"{asset}-USDT"
    t0 = time.perf_counter()
    try:
        async with session.get(
            "https://api.kucoin.com/api/v1/market/stats",
            params={"symbol": sym},
        ) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
        data = (payload.get("data") or {})
        price = float(data.get("last") or 0)
        if price <= 0:
            return None
        sym_u, cid = _resolve_canonical(asset)
        return CanonicalPriceQuote(
            connector_id="kucoin",
            exchange="kucoin",
            asset=sym_u,
            pair=sym,
            price_usd=price,
            volume_24h_usd=float(data.get("volValue") or 0),
            change_24h_pct=float(data.get("changeRate") or 0) * 100,
            canonical_id=cid,
            source="kucoin:public",
            fetched_at=_utcnow(),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError):
        return None


async def _fetch_mexc(asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
    sym = f"{asset}USDT"
    t0 = time.perf_counter()
    try:
        async with session.get(
            "https://api.mexc.com/api/v3/ticker/24hr",
            params={"symbol": sym},
        ) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
        price = float(data.get("lastPrice") or 0)
        if price <= 0:
            return None
        sym_u, cid = _resolve_canonical(asset)
        return CanonicalPriceQuote(
            connector_id="mexc",
            exchange="mexc",
            asset=sym_u,
            pair=sym,
            price_usd=price,
            volume_24h_usd=float(data.get("quoteVolume") or 0),
            change_24h_pct=float(data.get("priceChangePercent") or 0),
            canonical_id=cid,
            source="mexc:public",
            fetched_at=_utcnow(),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError):
        return None


async def _fetch_bitget(asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
    sym = f"{asset}USDT"
    t0 = time.perf_counter()
    try:
        async with session.get(
            "https://api.bitget.com/api/v2/spot/market/tickers",
            params={"symbol": sym},
        ) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
        rows = (payload.get("data") or [])
        if not rows:
            return None
        row = rows[0]
        price = float(row.get("lastPr") or 0)
        if price <= 0:
            return None
        sym_u, cid = _resolve_canonical(asset)
        return CanonicalPriceQuote(
            connector_id="bitget",
            exchange="bitget",
            asset=sym_u,
            pair=sym,
            price_usd=price,
            volume_24h_usd=float(row.get("quoteVolume") or 0),
            change_24h_pct=float(row.get("change24h") or 0) * 100,
            canonical_id=cid,
            source="bitget:public",
            fetched_at=_utcnow(),
            latency_ms=round((time.perf_counter() - t0) * 1000, 1),
        )
    except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError):
        return None


async def _fetch_ws_redis_quote(asset: str) -> CanonicalPriceQuote | None:
    """Live path — Redis / WS top-of-book (#127 invisible infra)."""
    try:
        from redis_price_cache import get_best_price

        for venue in ("binance", "okx", "bybit"):
            row = await get_best_price(venue, f"{asset}/USDT")
            if row and float(row.get("mid") or 0) > 0:
                sym, cid = _resolve_canonical(asset)
                return CanonicalPriceQuote(
                    connector_id=f"ws_{venue}",
                    exchange=venue,
                    asset=sym,
                    pair=f"{asset}USDT",
                    price_usd=float(row["mid"]),
                    bid=float(row.get("bid") or 0) or None,
                    ask=float(row.get("ask") or 0) or None,
                    canonical_id=cid,
                    source=f"ws:{venue}:redis",
                    market_type="spot",
                    fetched_at=_utcnow(),
                    latency_ms=0.5,
                    is_stale=bool(row.get("stale")),
                )
    except Exception:
        pass
    return None


async def fetch_all_connector_quotes(asset: str) -> list[ConnectorFetchResult]:
    """Parallel fetch from all registered connectors (#194)."""
    sym = asset.upper().replace("/USDT", "")
    results: list[ConnectorFetchResult] = []

    ws_quote = await _fetch_ws_redis_quote(sym)
    if ws_quote:
        results.append(
            ConnectorFetchResult(connector_id=ws_quote.connector_id, ok=True, quote=ws_quote, latency_ms=0.5)
        )

    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT) as session:
        tasks = [
            _fetch_binance(sym, session),
            _fetch_okx(sym, session),
            _fetch_bybit(sym, session),
            _fetch_gateio(sym, session),
            _fetch_kucoin(sym, session),
            _fetch_mexc(sym, session),
            _fetch_bitget(sym, session),
            _fetch_via_market_context(sym, "kraken"),
            _fetch_via_market_context(sym, "coinbase"),
            _fetch_via_market_context(sym, "coingecko"),
        ]
        labels = [
            "binance", "okx", "bybit", "gateio", "kucoin", "mexc", "bitget",
            "kraken", "coinbase", "coingecko",
        ]
        fetched = await asyncio.gather(*tasks, return_exceptions=True)
        for label, item in zip(labels, fetched):
            if isinstance(item, Exception):
                results.append(ConnectorFetchResult(connector_id=label, ok=False, error=str(item)))
            elif item is None:
                results.append(ConnectorFetchResult(connector_id=label, ok=False, error="no_data"))
            else:
                results.append(
                    ConnectorFetchResult(
                        connector_id=label,
                        ok=True,
                        quote=item,
                        latency_ms=item.latency_ms,
                    )
                )
    return results


def connector_layer_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "role": "unified_connector_layer",
        "user_facing": False,
        "registered_connectors": list(_CONNECTOR_IDS),
        "connector_count": len(_CONNECTOR_IDS),
        "schema": "CanonicalPriceQuote",
        "feeds_features": ["#133", "#127", "#128"],
        "expansion_target_exchanges": 400,
        "timestamp": _utcnow(),
    }
