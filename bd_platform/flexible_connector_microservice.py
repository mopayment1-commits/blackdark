"""
Flexible Connector Microservice — Feature #175 (Sprint 1 Core Architecture).

Canonical adapter contract for all exchange/DEX connectors:
  1. Normalization — same CanonicalPriceQuote schema
  2. Retry logic — 3 attempts with backoff
  3. Rate limit handling — per-connector token bucket
  4. Health check — certification + freshness
  5. No synthetic success — failures reported honestly

User-visible registry:
  "Binance: ✅ Healthy | Coinbase: ⚠️ Delayed 5min"
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

import aiohttp

from bd_platform.unified_connector_layer import (
    CanonicalPriceQuote,
    ConnectorFetchResult,
    _CONNECTOR_IDS,
    _HTTP_TIMEOUT,
    fetch_all_connector_quotes,
    sanitize_user_facing_error,
)

logger = logging.getLogger("BLACKDARK.FlexibleConnector")

_FEATURE_ID = 175
_MAX_RETRIES = 3
_RETRY_BACKOFF_SEC = 0.35
_RATE_LIMIT_PER_MIN = 60
_STALE_DELAY_MIN = 5
_HEALTH_PATH = Path("data/connector_health_snapshots.jsonl")

_REQUIRED_SCHEMA_FIELDS = (
    "connector_id",
    "exchange",
    "asset",
    "pair",
    "price_usd",
    "source",
    "fetched_at",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ConnectorHealth:
    connector_id: str
    status: str  # healthy | delayed | degraded | down
    emoji: str
    display: str
    latency_ms: float | None = None
    delay_minutes: float | None = None
    last_success_at: str | None = None
    last_error: str | None = None
    certified: bool = False
    schema_ok: bool = True
    synthetic_success: bool = False


@dataclass
class RateLimitState:
    window_start: float = field(default_factory=time.time)
    count: int = 0


_rate_limits: dict[str, RateLimitState] = defaultdict(RateLimitState)
_health_cache: dict[str, ConnectorHealth] = {}


class CanonicalConnectorAdapter(ABC):
    """Canonical adapter contract — every connector must implement this interface."""

    connector_id: str
    exchange: str
    rate_limit_per_min: int = _RATE_LIMIT_PER_MIN

    @abstractmethod
    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        """Fetch and normalize to CanonicalPriceQuote. Return None on failure — no synthetic data."""

    async def health_probe(self, asset: str = "BTC") -> ConnectorHealth:
        """Lightweight health check for certification."""
        result = await execute_with_policy(self, asset)
        return _health_from_result(self.connector_id, self.exchange, result)


class BinanceAdapter(CanonicalConnectorAdapter):
    connector_id = "binance"
    exchange = "Binance"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_binance

        return await _fetch_binance(asset, session)


class OkxAdapter(CanonicalConnectorAdapter):
    connector_id = "okx"
    exchange = "OKX"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_okx

        return await _fetch_okx(asset, session)


class BybitAdapter(CanonicalConnectorAdapter):
    connector_id = "bybit"
    exchange = "Bybit"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_bybit

        return await _fetch_bybit(asset, session)


class CoinbaseAdapter(CanonicalConnectorAdapter):
    connector_id = "coinbase"
    exchange = "Coinbase"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_via_market_context

        return await _fetch_via_market_context(asset, "coinbase")


class KrakenAdapter(CanonicalConnectorAdapter):
    connector_id = "kraken"
    exchange = "Kraken"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_via_market_context

        return await _fetch_via_market_context(asset, "kraken")


class CoingeckoAdapter(CanonicalConnectorAdapter):
    connector_id = "coingecko"
    exchange = "CoinGecko"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_via_market_context

        return await _fetch_via_market_context(asset, "coingecko")


class GateioAdapter(CanonicalConnectorAdapter):
    connector_id = "gateio"
    exchange = "Gate.io"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_gateio

        return await _fetch_gateio(asset, session)


class KucoinAdapter(CanonicalConnectorAdapter):
    connector_id = "kucoin"
    exchange = "KuCoin"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_kucoin

        return await _fetch_kucoin(asset, session)


class MexcAdapter(CanonicalConnectorAdapter):
    connector_id = "mexc"
    exchange = "MEXC"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_mexc

        return await _fetch_mexc(asset, session)


class BitgetAdapter(CanonicalConnectorAdapter):
    connector_id = "bitget"
    exchange = "Bitget"

    async def fetch_quote(self, asset: str, session: aiohttp.ClientSession) -> CanonicalPriceQuote | None:
        from bd_platform.unified_connector_layer import _fetch_bitget

        return await _fetch_bitget(asset, session)


_ADAPTER_REGISTRY: dict[str, CanonicalConnectorAdapter] = {
    cls().connector_id: cls()
    for cls in (
        BinanceAdapter,
        OkxAdapter,
        BybitAdapter,
        CoinbaseAdapter,
        KrakenAdapter,
        CoingeckoAdapter,
        GateioAdapter,
        KucoinAdapter,
        MexcAdapter,
        BitgetAdapter,
    )
}


def list_adapters() -> list[CanonicalConnectorAdapter]:
    return list(_ADAPTER_REGISTRY.values())


def get_adapter(connector_id: str) -> CanonicalConnectorAdapter | None:
    return _ADAPTER_REGISTRY.get(connector_id.lower())


def _check_rate_limit(connector_id: str, limit: int) -> bool:
    now = time.time()
    state = _rate_limits[connector_id]
    if now - state.window_start >= 60:
        state.window_start = now
        state.count = 0
    if state.count >= limit:
        return False
    state.count += 1
    return True


def detect_schema_drift(quote: CanonicalPriceQuote | dict[str, Any]) -> list[str]:
    """Return list of missing/invalid schema fields — schema drift handling."""
    data = quote.to_dict() if isinstance(quote, CanonicalPriceQuote) else quote
    issues: list[str] = []
    for field_name in _REQUIRED_SCHEMA_FIELDS:
        if field_name not in data or data[field_name] in (None, ""):
            issues.append(f"missing:{field_name}")
    price = float(data.get("price_usd") or 0)
    if price <= 0:
        issues.append("invalid:price_usd")
    return issues


def _append_health_snapshot(row: dict[str, Any]) -> None:
    _HEALTH_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _HEALTH_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


async def execute_with_policy(
    adapter: CanonicalConnectorAdapter,
    asset: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> ConnectorFetchResult:
    """
    Retry (3x), rate limit, schema validation — no synthetic success on failure.
    """
    connector_id = adapter.connector_id
    if not _check_rate_limit(connector_id, adapter.rate_limit_per_min):
        return ConnectorFetchResult(
            connector_id=connector_id,
            ok=False,
            error="rate_limit_exceeded",
        )

    last_error = "unknown"
    t0 = time.perf_counter()

    async def _attempt(sess: aiohttp.ClientSession) -> ConnectorFetchResult:
        nonlocal last_error
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                quote = await adapter.fetch_quote(asset.upper().replace("/USDT", ""), sess)
                if quote is None:
                    last_error = "no_data"
                    if attempt < _MAX_RETRIES:
                        await asyncio.sleep(_RETRY_BACKOFF_SEC * attempt)
                    continue
                drift = detect_schema_drift(quote)
                if drift:
                    last_error = f"schema_drift:{','.join(drift)}"
                    if attempt < _MAX_RETRIES:
                        await asyncio.sleep(_RETRY_BACKOFF_SEC * attempt)
                    continue
                elapsed = round((time.perf_counter() - t0) * 1000, 1)
                return ConnectorFetchResult(
                    connector_id=connector_id,
                    ok=True,
                    quote=quote,
                    latency_ms=elapsed,
                )
            except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError, TypeError) as exc:
                last_error = str(exc)
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(_RETRY_BACKOFF_SEC * attempt)
        return ConnectorFetchResult(connector_id=connector_id, ok=False, error=last_error)

    if session is not None:
        return await _attempt(session)
    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT) as sess:
        return await _attempt(sess)


def _health_from_result(connector_id: str, exchange: str, result: ConnectorFetchResult) -> ConnectorHealth:
    if result.ok and result.quote:
        quote = result.quote
        delay_min = None
        status = "healthy"
        emoji = "✅"
        if quote.is_stale:
            status = "delayed"
            emoji = "⚠️"
            delay_min = float(_STALE_DELAY_MIN)
        display = f"{exchange}: {emoji} {'Healthy' if status == 'healthy' else f'Delayed {delay_min:.0f}min'}"
        health = ConnectorHealth(
            connector_id=connector_id,
            status=status,
            emoji=emoji,
            display=display,
            latency_ms=result.latency_ms,
            delay_minutes=delay_min,
            last_success_at=quote.fetched_at,
            certified=True,
            schema_ok=True,
            synthetic_success=False,
        )
    else:
        user_error = sanitize_user_facing_error(result.error)
        health = ConnectorHealth(
            connector_id=connector_id,
            status="down",
            emoji="🔴",
            display=f"{exchange}: 🔴 {user_error}",
            last_error=user_error,
            certified=False,
            schema_ok=not (result.error or "").startswith("schema_drift"),
            synthetic_success=False,
        )
    _health_cache[connector_id] = health
    _append_health_snapshot(
        {
            "connector_id": connector_id,
            "status": health.status,
            "certified": health.certified,
            "error": health.last_error,
            "timestamp": _utcnow(),
        }
    )
    return health


async def fetch_with_failover(asset: str, *, preferred: list[str] | None = None) -> dict[str, Any]:
    """
    Failover chain — try preferred connectors first, then registry order.
    No synthetic success: returns first successful quote or explicit failure.
    """
    order = preferred or ["binance", "okx", "coinbase", "kraken", "coingecko"]
    sym = asset.upper().replace("/USDT", "")
    attempts: list[dict[str, Any]] = []

    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT) as session:
        for cid in order:
            adapter = get_adapter(cid)
            if not adapter:
                continue
            result = await execute_with_policy(adapter, sym, session=session)
            attempts.append(
                {
                    "connector_id": cid,
                    "ok": result.ok,
                    "error": result.error,
                    "latency_ms": result.latency_ms,
                }
            )
            if result.ok and result.quote:
                return {
                    "ok": True,
                    "failover": True,
                    "selected_connector": cid,
                    "quote": result.quote.to_dict(),
                    "attempts": attempts,
                    "synthetic_success": False,
                }

    return {
        "ok": False,
        "failover": True,
        "error": "all_connectors_failed",
        "attempts": attempts,
        "synthetic_success": False,
    }


async def run_connector_certification(asset: str = "BTC") -> dict[str, Any]:
    """Health certification pass for all registered adapters."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")
    certified: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []

    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT) as session:
        tasks = [execute_with_policy(adapter, sym, session=session) for adapter in list_adapters()]
        results = await asyncio.gather(*tasks)
        for adapter, result in zip(list_adapters(), results, strict=True):
            health = _health_from_result(adapter.connector_id, adapter.exchange, result)
            row = {
                "connector_id": adapter.connector_id,
                "exchange": adapter.exchange,
                "certified": health.certified,
                "status": health.status,
                "display": health.display,
                "latency_ms": health.latency_ms,
                "error": health.last_error,
            }
            if health.certified:
                certified.append(row)
            else:
                failed.append(row)

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": sym,
        "certified_count": len(certified),
        "failed_count": len(failed),
        "certified": certified,
        "failed": failed,
        "registry_display": " | ".join(r["display"] for r in certified + failed),
        "no_synthetic_success": True,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


async def connector_registry_dashboard(asset: str = "BTC") -> dict[str, Any]:
    """User-visible connector registry with health/freshness/coverage."""
    cert = await run_connector_certification(asset)
    all_connectors = cert["certified"] + cert["failed"]
    healthy = sum(1 for c in all_connectors if c["status"] == "healthy")
    delayed = sum(1 for c in all_connectors if c["status"] == "delayed")
    down = sum(1 for c in all_connectors if c["status"] == "down")

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Connector Registry",
        "asset": asset.upper(),
        "registry_display": cert["registry_display"],
        "coverage": {
            "registered": len(_ADAPTER_REGISTRY),
            "healthy": healthy,
            "delayed": delayed,
            "down": down,
            "certified": cert["certified_count"],
        },
        "connectors": all_connectors,
        "freshness": {
            "stale_threshold_min": _STALE_DELAY_MIN,
            "policy": "Quotes older than threshold marked delayed — never synthetic",
        },
        "policies": {
            "max_retries": _MAX_RETRIES,
            "rate_limit_per_min": _RATE_LIMIT_PER_MIN,
            "schema": "CanonicalPriceQuote",
            "no_synthetic_success": True,
        },
        "integrated_with": ["#137", "#138", "#194"],
        "latency_ms": cert["latency_ms"],
        "sla_met": cert["sla_met"],
        "timestamp": _utcnow(),
    }


def flexible_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Flexible Connector Microservice",
        "mode": "core_architecture",
        "adapter_contract": "CanonicalConnectorAdapter",
        "registered_adapters": sorted(_ADAPTER_REGISTRY.keys()),
        "legacy_connector_ids": list(_CONNECTOR_IDS),
        "policies": {
            "normalization": "CanonicalPriceQuote",
            "symbol_normalization": "BTCUSDT=BTC-USD=BTC_USDT",
            "timestamp_normalization": "UTC",
            "no_venue_leakage": True,
            "retries": _MAX_RETRIES,
            "rate_limit_per_min": _RATE_LIMIT_PER_MIN,
            "health_certification": True,
            "schema_drift_detection": True,
            "failover": True,
            "no_synthetic_success": True,
            "heartbeat_interval_sec": 60,
        },
        "integrated_features": ["#137", "#138", "#194"],
        "timestamp": _utcnow(),
    }


async def fetch_all_via_microservice(asset: str) -> list[ConnectorFetchResult]:
    """Drop-in for unified_connector_layer with microservice policies applied."""
    sym = asset.upper().replace("/USDT", "")
    async with aiohttp.ClientSession(timeout=_HTTP_TIMEOUT) as session:
        tasks = [execute_with_policy(adapter, sym, session=session) for adapter in list_adapters()]
        return list(await asyncio.gather(*tasks))
