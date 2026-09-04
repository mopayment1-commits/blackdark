"""Batch05 Strangler spine — catalog-correct wiring for miswired hero capabilities.

Replaces hero-bridge semantic mismatches with real module calls (ISO 12207 Strangler Fig).
Wave 1: IDs 201–204 (derivatives/onchain entry cluster).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from cap646.dedicated_common import holder_analytics_bundle, seed as _default_seed


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _base(capability_id: int, symbol: str, catalog_goal: str, **extra: Any) -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ref": capability_id,
        "symbol": symbol.upper(),
        "catalog_goal": catalog_goal,
        "rule_based": True,
        "ai_classification": "rule-based",
        "ai_drift_monitoring": "N/A",
        "data_freshness": _utcnow(),
        **extra,
    }


def _timed(extra: dict[str, Any], t0: float) -> dict[str, Any]:
    extra["latency_ms"] = round((time.perf_counter() - t0) * 1000, 1)
    extra.setdefault("performance_tier", "fast" if extra["latency_ms"] < 500 else "moderate")
    return extra


async def build_network_growth_201(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.footprint_analytics import footprint_snapshot

    snap = await footprint_snapshot(symbol)
    payload = _base(
        201,
        symbol,
        "network_growth_intelligence",
        footprint=snap,
        network_growth=snap,
        aggregate_bid_depth_5=snap.get("aggregate_bid_depth_5"),
        aggregate_ask_depth_5=snap.get("aggregate_ask_depth_5"),
        order_flow_delta=snap.get("order_flow_delta"),
        venue_count=len(snap.get("top_of_book") or []),
        source="footprint_analytics.footprint_snapshot",
        attribution="Free-tier: multi-venue CEX footprint as network-activity proxy",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_supply_distribution_202(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    dist, metrics = await holder_analytics_bundle(symbol)
    circ = float(metrics.get("circulating_supply") or 0)
    total = float(metrics.get("total_supply") or 0)
    payload = _base(
        202,
        symbol,
        "supply_distribution_intelligence",
        supply_distribution=dist,
        holder_metrics=metrics,
        circulating_supply=circ,
        total_supply=total,
        locked_supply_pct=metrics.get("locked_supply_pct"),
        source=dist.get("source", "holder_analytics"),
        attribution="Free-tier: CoinGecko supply distribution + Binance futures context",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_dex_trading_203(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.onchain_hub import dexscreener_pairs

    dex = await dexscreener_pairs(symbol)
    pairs = dex.get("pairs") or []
    payload = _base(
        203,
        symbol,
        "dex_trading_intelligence",
        dex_pairs=pairs[:10],
        pair_count=int(dex.get("count") or len(pairs)),
        query=dex.get("query"),
        source="onchain_hub.dexscreener_pairs",
        attribution="Free-tier: DexScreener DEX pair search",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_defi_protocol_activity_204(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.onchain_defi_sources_layer import ingest_bscscan_204

    address = str(params.get("address") or "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
    raw = ingest_bscscan_204(address=address, seed=seed or _default_seed())
    payload = _base(
        204,
        symbol,
        "defi_protocol_activity_intelligence",
        protocol_activity=raw,
        chain=raw.get("chain"),
        block_height=raw.get("block_height"),
        recent_transfers=raw.get("recent_transfers"),
        source="onchain_defi_sources_layer.ingest_bscscan_204",
        attribution="BSC on-chain protocol activity sample — insight only, no execution",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


STRANGLER_BUILDERS: dict[int, Any] = {
    201: build_network_growth_201,
    202: build_supply_distribution_202,
    203: build_dex_trading_203,
    204: build_defi_protocol_activity_204,
}

STRANGLER_IMPLEMENTED_IDS: frozenset[int] = frozenset(STRANGLER_BUILDERS)
