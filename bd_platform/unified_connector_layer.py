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
_CONNECTOR_VERSION = "1.1.0"
_HEARTBEAT_INTERVAL_SEC = 60
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

# Primary exchange APIs vs aggregator backup/cross-reference (#138)
_PRIMARY_CONNECTOR_IDS: tuple[str, ...] = (
    "binance", "okx", "bybit", "kraken", "coinbase", "gateio", "kucoin", "mexc", "bitget",
)
_AGGREGATOR_CONNECTOR_IDS: tuple[str, ...] = ("coingecko",)

_connector_heartbeats: dict[str, dict[str, Any]] = {}


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


def normalize_symbol(raw: str) -> dict[str, str]:
    """
    Symbol normalization — BTCUSDT (Binance) = BTC-USD (Coinbase) = BTC_USDT (internal).

    Returns canonical asset + venue-specific pair formats.
    """
    s = raw.upper().strip().replace(" ", "")
    compact = s.replace("-", "").replace("_", "").replace("/", "")
    asset = compact
    quote = "USDT"
    for q in ("USDT", "USDC", "BUSD", "USD"):
        if compact.endswith(q) and len(compact) > len(q):
            asset = compact[: -len(q)]
            quote = "USDT" if q == "USD" else q  # USD → USDT canonical for internal pair
            break
    return {
        "canonical_asset": asset,
        "internal_pair": f"{asset}_{quote}",
        "venue_pair_binance": f"{asset}{quote}",
        "venue_pair_coinbase": f"{asset}-{quote}",
        "venue_pair_okx": f"{asset}-{quote}",
        "venue_pair_kraken": f"{asset}{quote}",
        "timestamp_tz": "UTC",
    }


def sanitize_user_facing_error(error: str | None) -> str:
    """No venue-specific leakage — user sees generic source status only."""
    if not error:
        return "Source temporarily unavailable"
    if error == "rate_limit_exceeded" or "rate_limit" in error.lower():
        return "Source rate limited — retry shortly"
    err = error.lower()
    venue_tokens = (
        "binance", "okx", "coinbase", "kraken", "bybit", "gateio", "kucoin",
        "mexc", "bitget", "coingecko", "api.", "http", "timeout",
    )
    if any(tok in err for tok in venue_tokens):
        return "Source temporarily unavailable"
    if error in {"no_data", "unknown"}:
        return "Source temporarily unavailable"
    return "Source temporarily unavailable"


def record_connector_heartbeat(
    connector_id: str,
    *,
    ok: bool,
    latency_ms: float = 0.0,
    error: str | None = None,
) -> dict[str, Any]:
    """Record connector heartbeat — target interval 60 seconds."""
    now = _utcnow()
    prev = _connector_heartbeats.get(connector_id) or {}
    row = {
        "connector_id": connector_id,
        "ok": ok,
        "latency_ms": latency_ms,
        "error": sanitize_user_facing_error(error) if error else None,
        "last_heartbeat_at": now,
        "heartbeat_interval_sec": _HEARTBEAT_INTERVAL_SEC,
        "version": _CONNECTOR_VERSION,
        "consecutive_failures": 0 if ok else int(prev.get("consecutive_failures") or 0) + 1,
    }
    _connector_heartbeats[connector_id] = row
    return row


def connector_heartbeat_snapshot() -> dict[str, Any]:
    return {
        "interval_sec": _HEARTBEAT_INTERVAL_SEC,
        "version": _CONNECTOR_VERSION,
        "connectors": dict(_connector_heartbeats),
    }


def cross_reference_quotes(
    results: list[ConnectorFetchResult],
    *,
    tolerance_pct: float = 2.0,
) -> dict[str, Any]:
    """
  #138 — Cross-validate primary exchange quotes against aggregator backup.

    Primary sources: exchange APIs. Aggregators: backup + cross-reference only.
    """
    primary_prices: list[float] = []
    aggregator_prices: list[float] = []
    by_id: dict[str, float] = {}

    for r in results:
        if not r.ok or not r.quote or r.quote.price_usd <= 0:
            continue
        by_id[r.connector_id] = r.quote.price_usd
        if r.connector_id in _AGGREGATOR_CONNECTOR_IDS:
            aggregator_prices.append(r.quote.price_usd)
        else:
            primary_prices.append(r.quote.price_usd)

    if not primary_prices:
        return {
            "ok": False,
            "reason": "no_primary_sources",
            "user_message": "Source temporarily unavailable",
        }

    primary_median = sorted(primary_prices)[len(primary_prices) // 2]
    agg_median = (
        sorted(aggregator_prices)[len(aggregator_prices) // 2] if aggregator_prices else None
    )

    divergence_pct = None
    verified = True
    if agg_median is not None and primary_median > 0:
        divergence_pct = abs(agg_median - primary_median) / primary_median * 100
        verified = divergence_pct <= tolerance_pct

    return {
        "ok": True,
        "primary_median_usd": round(primary_median, 4),
        "aggregator_median_usd": round(agg_median, 4) if agg_median else None,
        "divergence_pct": round(divergence_pct, 4) if divergence_pct is not None else None,
        "cross_reference_verified": verified,
        "primary_source_count": len(primary_prices),
        "aggregator_source_count": len(aggregator_prices),
        "policy": "Primary exchange APIs + aggregator backup/cross-reference (#138)",
        "prices_by_connector": {k: round(v, 4) for k, v in by_id.items()},
    }


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
                record_connector_heartbeat(label, ok=False, error=str(item))
                results.append(
                    ConnectorFetchResult(
                        connector_id=label,
                        ok=False,
                        error=sanitize_user_facing_error(str(item)),
                    )
                )
            elif item is None:
                record_connector_heartbeat(label, ok=False, error="no_data")
                results.append(
                    ConnectorFetchResult(
                        connector_id=label,
                        ok=False,
                        error=sanitize_user_facing_error("no_data"),
                    )
                )
            else:
                record_connector_heartbeat(label, ok=True, latency_ms=item.latency_ms)
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
        "version": _CONNECTOR_VERSION,
        "registered_connectors": list(_CONNECTOR_IDS),
        "primary_connectors": list(_PRIMARY_CONNECTOR_IDS),
        "aggregator_connectors": list(_AGGREGATOR_CONNECTOR_IDS),
        "connector_count": len(_CONNECTOR_IDS),
        "schema": "CanonicalPriceQuote",
        "symbol_normalization": "BTCUSDT=BTC-USD=BTC_USDT",
        "timestamp_normalization": "UTC only",
        "no_venue_leakage": True,
        "heartbeat_interval_sec": _HEARTBEAT_INTERVAL_SEC,
        "feeds_features": ["#133", "#127", "#128", "#137", "#138", "#175"],
        "merged_with": "#175 Flexible Connector Microservice",
        "expansion_target_exchanges": 400,
        "timestamp": _utcnow(),
    }
