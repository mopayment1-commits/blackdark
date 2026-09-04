"""Batch05 Strangler spine — catalog-correct wiring for miswired hero capabilities.

Replaces hero-bridge semantic mismatches with real module calls (ISO 12207 Strangler Fig).
Wave 1: IDs 201–204 (derivatives/onchain entry cluster).
Wave 2a: #205 (canonical OI for #232 REUSED-LINK).
Wave 2b: #207–211, #213, #215–216 (onchain_defi cluster continuation).
"""

from __future__ import annotations

import asyncio
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


async def build_open_interest_205(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.free_market_data import binance_futures_snapshot

    snap = await binance_futures_snapshot(symbol)
    oi_usd = float(snap.get("open_interest_usd") or 0)
    payload = _base(
        205,
        symbol,
        "open_interest_intelligence",
        open_interest_usd=oi_usd,
        open_interest_contracts=snap.get("open_interest_contracts"),
        mark_price=snap.get("mark_price"),
        funding_rate_pct=snap.get("funding_rate_pct"),
        long_short_ratio=snap.get("long_short_ratio"),
        futures_snapshot=snap,
        free_tier_available=bool(snap.get("available")),
        source="free_market_data.binance_futures_snapshot",
        attribution="Free-tier: Binance Futures public OI — canonical for #232 REUSED-LINK",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_price_volume_market_metrics_207(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.free_market_data import binance_futures_snapshot
    from market_context import probe_price_sources

    probe, futures = await asyncio.gather(
        probe_price_sources(symbol),
        binance_futures_snapshot(symbol),
    )
    payload = _base(
        207,
        symbol,
        "price_volume_market_metrics",
        price_probe=probe,
        resolved_price=probe.get("resolved_price"),
        resolved_source=probe.get("resolved_source"),
        volume_24h_context=futures.get("change_24h_pct"),
        futures_metrics=futures,
        source="market_context.probe_price_sources+free_market_data.binance_futures_snapshot",
        attribution="Free-tier: multi-source price probe + Binance futures volume context",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_metric_correlation_workbench_208(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.free_market_data import binance_futures_snapshot

    futures = await binance_futures_snapshot(symbol)
    metrics = {
        "funding_rate_pct": futures.get("funding_rate_pct"),
        "long_short_ratio": futures.get("long_short_ratio"),
        "taker_buy_sell_ratio": futures.get("taker_buy_sell_ratio"),
        "change_24h_pct": futures.get("change_24h_pct"),
    }
    numeric = [float(v) for v in metrics.values() if isinstance(v, (int, float))]
    spread = round(max(numeric) - min(numeric), 4) if len(numeric) >= 2 else 0.0
    payload = _base(
        208,
        symbol,
        "metric_correlation_workbench",
        workbench_metrics=metrics,
        metric_spread=spread,
        correlation_inputs=len(numeric),
        source="free_market_data.binance_futures_snapshot",
        attribution="Free-tier: futures metric correlation workbench (rule-based spread)",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_custom_chart_builder_209(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    from cap646.fallbacks import resolve_ohlcv_closes

    interval = str(params.get("interval") or "1h")
    closes, ohlcv_source = await resolve_ohlcv_closes(symbol, interval=interval, limit=24)
    bars = [{"close": c} for c in closes] if closes else []
    payload = _base(
        209,
        symbol,
        "custom_chart_builder",
        chart_interval=interval,
        bar_count=len(bars),
        ohlcv_bars=bars[-30:],
        ohlcv_source=ohlcv_source,
        source="cap646.fallbacks.resolve_ohlcv_closes",
        attribution="Free-tier: OHLCV closes for custom chart builder surface",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_custom_dashboards_layouts_210(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.market_rankings import market_rankings

    rankings = await market_rankings(limit=int(params.get("limit") or 12))
    assets = rankings.get("assets") or rankings.get("rankings") or []
    widgets = [
        {"id": "market_overview", "type": "rankings", "count": len(assets)},
        {"id": "focus_symbol", "type": "symbol", "symbol": symbol.upper()},
    ]
    payload = _base(
        210,
        symbol,
        "custom_dashboards_layouts",
        dashboard_layout={"widgets": widgets, "layout_version": "batch05-strangler-v1"},
        rankings_preview=assets[:8],
        source="bd_platform.market_rankings.market_rankings",
        attribution="Free-tier: dashboard layout scaffold over market rankings",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_screener_211(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.market_rankings import market_rankings

    limit = int(params.get("limit") or 50)
    rankings = await market_rankings(limit=limit)
    assets = rankings.get("assets") or rankings.get("rankings") or []
    sym = symbol.upper()
    matches = [
        a for a in assets
        if isinstance(a, dict) and str(a.get("symbol", "")).upper() in {sym, sym.replace("USDT", "")}
    ]
    payload = _base(
        211,
        symbol,
        "screener",
        screener_results=matches or assets[:10],
        match_count=len(matches),
        universe_size=len(assets),
        source="bd_platform.market_rankings.market_rankings",
        attribution="Free-tier: CoinGecko/Binance market rankings screener",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_anomaly_detection_alerts_213(*, symbol: str, params: dict[str, Any]) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.footprint_analytics import footprint_snapshot

    snap = await footprint_snapshot(symbol)
    levels = snap.get("depth_levels") or []
    max_imbalance = max((abs(float(d.get("imbalance") or 0)) for d in levels), default=0.0)
    threshold = float(params.get("imbalance_threshold") or 0.25)
    alert_triggered = max_imbalance >= threshold
    payload = _base(
        213,
        symbol,
        "anomaly_detection_alerts",
        footprint=snap,
        max_orderbook_imbalance=round(max_imbalance, 4),
        alert_triggered=alert_triggered,
        alert_threshold=threshold,
        source="footprint_analytics.footprint_snapshot",
        attribution="Free-tier: order-book imbalance anomaly alerts (rule-based)",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_community_explorer_215(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.onchain_defi_sources_layer import ingest_reddit_sentiment_208

    community = ingest_reddit_sentiment_208(seed=seed or _default_seed())
    payload = _base(
        215,
        symbol,
        "community_explorer",
        community_feed=community.get("posts") or [],
        post_count=community.get("post_count", 0),
        sentiment_direction=community.get("sentiment_direction"),
        source="onchain_defi_sources_layer.ingest_reddit_sentiment_208",
        attribution="Free-tier: Reddit community feed for explorer surface",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_research_market_insights_216(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.market_rankings import market_rankings
    from bd_platform.onchain_defi_sources_layer import ingest_reddit_sentiment_208

    rankings = await market_rankings(limit=15)
    sentiment = ingest_reddit_sentiment_208(seed=seed or _default_seed())
    assets = rankings.get("assets") or rankings.get("rankings") or []
    payload = _base(
        216,
        symbol,
        "research_market_insights",
        market_rankings_preview=assets[:10],
        social_sentiment=sentiment,
        insight_count=len(assets),
        source="market_rankings+onchain_defi_sources_layer.ingest_reddit_sentiment_208",
        attribution="Free-tier: composite research insights (rankings + social)",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


STRANGLER_BUILDERS: dict[int, Any] = {
    201: build_network_growth_201,
    202: build_supply_distribution_202,
    203: build_dex_trading_203,
    204: build_defi_protocol_activity_204,
    205: build_open_interest_205,
    207: build_price_volume_market_metrics_207,
    208: build_metric_correlation_workbench_208,
    209: build_custom_chart_builder_209,
    210: build_custom_dashboards_layouts_210,
    211: build_screener_211,
    213: build_anomaly_detection_alerts_213,
    215: build_community_explorer_215,
    216: build_research_market_insights_216,
}

STRANGLER_IMPLEMENTED_IDS: frozenset[int] = frozenset(STRANGLER_BUILDERS)
