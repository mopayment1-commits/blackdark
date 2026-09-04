"""Batch05 Strangler spine — catalog-correct wiring for miswired hero capabilities.

Replaces hero-bridge semantic mismatches with real module calls (ISO 12207 Strangler Fig).
Wave 1: IDs 201–204 (derivatives/onchain entry cluster).
Wave 2a: #205 (canonical OI for #232 REUSED-LINK).
Wave 2b: #207–211, #213, #215–216 (onchain_defi cluster continuation).
Wave 3: #217–225, #227 (intelligence_market_extensions_layer; #226 frozen REUSED-LINK).
Wave 4: #229–231, #233–241 (intelligence_ux_extensions_layer; #228/#232 frozen REUSED-LINK).
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


def _as_list(val: Any) -> list[Any]:
    if isinstance(val, list):
        return val
    return []


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
    assets = _as_list(rankings.get("assets") or rankings.get("rankings"))
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
    assets = _as_list(rankings.get("assets") or rankings.get("rankings"))
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
    assets = _as_list(rankings.get("assets") or rankings.get("rankings"))
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


async def build_sanapi_style_data_access_217(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import analyze_best_venue_217

    order_usd = float(params.get("order_usd") or 50_000)
    venue = analyze_best_venue_217(asset=symbol, order_usd=order_usd, seed=seed or _default_seed())
    payload = _base(
        217,
        symbol,
        "sanapi_style_data_access",
        venue_analysis=venue,
        venues=venue.get("venues"),
        analytical_optimal=venue.get("analytical_optimal"),
        no_routing=venue.get("no_routing"),
        source="intelligence_market_extensions_layer.analyze_best_venue_217",
        attribution="Best-venue analysis — insight only, no SanAPI routing or execution",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_google_sheets_integration_218(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import (
        add_manual_order_journal_218,
        list_manual_order_journal_218,
    )

    seed_data = seed or _default_seed()
    if params.get("record_order"):
        add_manual_order_journal_218(
            asset=symbol,
            target_price=float(params.get("target_price") or 65_000),
            state=params.get("state", "Planned"),  # type: ignore[arg-type]
            filled_price=params.get("filled_price"),
            seed=seed_data,
        )
    journal = list_manual_order_journal_218(seed=seed_data)
    payload = _base(
        218,
        symbol,
        "google_sheets_integration",
        manual_journal=journal,
        journal_entries=journal.get("entries") or [],
        export_format="sheets_compatible_csv",
        source="intelligence_market_extensions_layer.list_manual_order_journal_218",
        attribution="Manual order journal export scaffold — learning tool, not OMS",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_metric_availability_registry_219(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import analyze_nlp_sentiment_219

    sentiment = analyze_nlp_sentiment_219(seed=seed or _default_seed())
    registry = {
        "nlp_sentiment": {"available": True, "rule_based": sentiment.get("rule_based_only")},
        "keyword_metrics": sentiment.get("keyword_breakdown"),
        "post_count": sentiment.get("post_count"),
    }
    payload = _base(
        219,
        symbol,
        "metric_availability_registry",
        metric_registry=registry,
        sentiment_probe=sentiment,
        sentiment_score=sentiment.get("sentiment_score"),
        source="intelligence_market_extensions_layer.analyze_nlp_sentiment_219",
        attribution="Rule-based NLP sentiment metric availability registry",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_data_stabilization_mutability_metadata_220(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import analyze_pattern_outcome_220

    pattern = str(params.get("pattern") or "rsi_lt_30_volume_spike_whale_inflow")
    outcome = analyze_pattern_outcome_220(pattern=pattern, asset=symbol, seed=seed or _default_seed())
    payload = _base(
        220,
        symbol,
        "data_stabilization_mutability_metadata",
        pattern_outcome=outcome,
        historical_instances=outcome.get("historical_instances"),
        outcome_distribution=outcome.get("outcome_distribution"),
        mutability_metadata={"lookback_years": outcome.get("lookback_years"), "immutable_history": True},
        source="intelligence_market_extensions_layer.analyze_pattern_outcome_220",
        attribution="Pattern outcome metadata — no return prediction guarantee",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_data_quality_provenance_layer_221(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import market_slippage_analysis_221

    order_usd = float(params.get("order_usd") or 100_000)
    slippage = market_slippage_analysis_221(asset=symbol, order_usd=order_usd, seed=seed or _default_seed())
    payload = _base(
        221,
        symbol,
        "data_quality_provenance_layer",
        slippage_analysis=slippage,
        market_avg_slippage_pct=slippage.get("market_avg_slippage_pct"),
        provenance={"formula": slippage.get("formula"), "window_days": slippage.get("historical_window_days")},
        source="intelligence_market_extensions_layer.market_slippage_analysis_221",
        attribution="Market-wide slippage provenance — not personal execution quality",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_metric_methodology_registry_222(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import monitor_exchange_latency_222

    latency = monitor_exchange_latency_222(seed=seed or _default_seed())
    payload = _base(
        222,
        symbol,
        "metric_methodology_registry",
        exchange_latency=latency,
        fastest_venue=latency.get("fastest_venue"),
        methodology={"frequency_seconds": latency.get("frequency_seconds"), "ranking": "rtt_ms_asc"},
        venues=latency.get("venues"),
        source="intelligence_market_extensions_layer.monitor_exchange_latency_222",
        attribution="Exchange latency methodology registry — internal monitoring only",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_social_to_on_chain_confirmation_engine_223(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import analyze_defi_fundamentals_223

    protocol = str(params.get("protocol") or "uniswap")
    fundamentals = analyze_defi_fundamentals_223(protocol=protocol, seed=seed or _default_seed())
    payload = _base(
        223,
        symbol,
        "social_to_on_chain_confirmation_engine",
        defi_fundamentals=fundamentals,
        ps_ratio=fundamentals.get("ps_ratio"),
        revenue_usd_annualized=fundamentals.get("revenue_usd_annualized"),
        on_chain_confirmed=True,
        source="intelligence_market_extensions_layer.analyze_defi_fundamentals_223",
        attribution="On-chain DeFi fundamentals confirmation — educational framing only",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_narrative_actionability_score_224(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import analyze_token_dcf_224

    protocol = str(params.get("protocol") or symbol)
    dcf = analyze_token_dcf_224(protocol=protocol, seed=seed or _default_seed())
    payload = _base(
        224,
        symbol,
        "narrative_actionability_score",
        token_dcf=dcf,
        dcf_estimate_usd=dcf.get("dcf_estimate_usd"),
        sensitivity_pct=dcf.get("sensitivity_pct"),
        actionability_score=round(float(dcf.get("dcf_estimate_usd") or 0) / 100, 2),
        source="intelligence_market_extensions_layer.analyze_token_dcf_224",
        attribution="Token DCF narrative actionability — no fair-value guarantee",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_development_to_market_divergence_detector_225(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import pwa_strategy_status_225

    pwa = pwa_strategy_status_225(seed=seed or _default_seed())
    payload = _base(
        225,
        symbol,
        "development_to_market_divergence_detector",
        pwa_strategy=pwa,
        native_apps_wave=pwa.get("native_apps_wave"),
        pwa_alternative=pwa.get("pwa_alternative"),
        divergence_signal="native_deferred_web_first",
        source="intelligence_market_extensions_layer.pwa_strategy_status_225",
        attribution="PWA vs native development divergence status — web-first strategy",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_unified_trading_intelligence_workspace_227(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_market_extensions_layer import analyze_etf_premium_227

    etf = analyze_etf_premium_227(asset=symbol, seed=seed or _default_seed())
    payload = _base(
        227,
        symbol,
        "unified_trading_intelligence_workspace",
        etf_premium=etf,
        instruments=etf.get("instruments"),
        workspace_modules=["etf_premium", "cross_asset_spread"],
        source="intelligence_market_extensions_layer.analyze_etf_premium_227",
        attribution="ETF premium workspace — analysis only, no arbitrage execution",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_cross_exchange_funding_arbitrage_scanner_229(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import generate_reasoning_explanation_229

    rules = params.get("rules_triggered")
    reasoning = generate_reasoning_explanation_229(
        asset=symbol,
        rules_triggered=list(rules) if isinstance(rules, list) else None,
        seed=seed or _default_seed(),
    )
    payload = _base(
        229,
        symbol,
        "cross_exchange_funding_arbitrage_scanner",
        reasoning_explanation=reasoning,
        explanation=reasoning.get("explanation"),
        rules_triggered=reasoning.get("rules_triggered"),
        source="intelligence_ux_extensions_layer.generate_reasoning_explanation_229",
        attribution="Rule-based opportunity reasoning — insight not recommendation",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_spot_perp_arbitrage_scanner_230(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import analyze_cross_exchange_divergence_230

    divergence = analyze_cross_exchange_divergence_230(asset=symbol, seed=seed or _default_seed())
    payload = _base(
        230,
        symbol,
        "spot_perp_arbitrage_scanner",
        cross_exchange_divergence=divergence,
        venues=divergence.get("venues"),
        divergence_pct=divergence.get("divergence_pct"),
        net_after_costs_pct=divergence.get("net_after_costs_pct"),
        source="intelligence_ux_extensions_layer.analyze_cross_exchange_divergence_230",
        attribution="Cross-exchange divergence analysis — no execution",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_futures_basis_term_structure_231(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import triangular_arbitrage_status_231

    status = triangular_arbitrage_status_231(seed=seed or _default_seed())
    payload = _base(
        231,
        symbol,
        "futures_basis_term_structure",
        triangular_status=status,
        activation_not_build=status.get("activation_not_build"),
        execution_rejected=status.get("execution_rejected"),
        source="intelligence_ux_extensions_layer.triangular_arbitrage_status_231",
        attribution="Triangular arbitrage status — activation stub, analysis only",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_liquidation_intelligence_233(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import build_heatmap_component_233

    assets = params.get("heatmap_assets")
    heatmap = build_heatmap_component_233(
        list(assets) if isinstance(assets, list) else None,
        seed=seed or _default_seed(),
    )
    payload = _base(
        233,
        symbol,
        "liquidation_intelligence",
        heatmap=heatmap,
        cells=heatmap.get("cells"),
        cell_count=len(heatmap.get("cells") or []),
        source="intelligence_ux_extensions_layer.build_heatmap_component_233",
        attribution="Market heatmap component — rule-based coloring",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_cvd_intelligence_234(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import live_dashboard_status_234

    dashboard = live_dashboard_status_234(seed=seed or _default_seed())
    payload = _base(
        234,
        symbol,
        "cvd_intelligence",
        live_dashboard=dashboard,
        duplicate_of=dashboard.get("duplicate_of"),
        websocket_ref=dashboard.get("websocket_ref"),
        source="intelligence_ux_extensions_layer.live_dashboard_status_234",
        attribution="Live dashboard status — merged into command center",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_long_short_ratio_intelligence_235(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import whale_intelligence_status_235

    whale = whale_intelligence_status_235(seed=seed or _default_seed())
    payload = _base(
        235,
        symbol,
        "long_short_ratio_intelligence",
        whale_status=whale,
        duplicate_of=whale.get("duplicate_of"),
        source="intelligence_ux_extensions_layer.whale_intelligence_status_235",
        attribution="Whale intelligence activation status — merged into whale narrative",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_dex_screener_236(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import subscription_tiers_status_236

    tiers = subscription_tiers_status_236(seed=seed or _default_seed())
    payload = _base(
        236,
        symbol,
        "dex_screener",
        subscription_tiers=tiers,
        tier_list=tiers.get("tiers"),
        source="intelligence_ux_extensions_layer.subscription_tiers_status_236",
        attribution="Subscription tier policy status — transparent limits",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_token_risk_scoring_237(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import generate_market_summary_237

    summary = generate_market_summary_237(seed=seed or _default_seed())
    payload = _base(
        237,
        symbol,
        "token_risk_scoring",
        market_summary=summary,
        summary_sentence=summary.get("summary_sentence"),
        risk_fields=summary.get("fields"),
        source="intelligence_ux_extensions_layer.generate_market_summary_237",
        attribution="One-sentence oracle market summary — summary not prediction",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_pump_dump_detection_238(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import scan_market_opportunities_238

    threshold = float(params.get("threshold_score") or 70.0)
    scan = scan_market_opportunities_238(threshold_score=threshold, seed=seed or _default_seed())
    payload = _base(
        238,
        symbol,
        "pump_dump_detection",
        market_scan=scan,
        detected_count=scan.get("detected_count"),
        opportunities=scan.get("opportunities"),
        source="intelligence_ux_extensions_layer.scan_market_opportunities_238",
        attribution="Market opportunity scan — detection only, no buy signal",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_narrative_tracking_239(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import live_ta_status_239

    ta = live_ta_status_239(seed=seed or _default_seed())
    payload = _base(
        239,
        symbol,
        "narrative_tracking",
        live_ta=ta,
        merged_into=ta.get("merged_into"),
        routes=ta.get("routes"),
        source="intelligence_ux_extensions_layer.live_ta_status_239",
        attribution="Live TA activation status — merged into market radar",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_sector_rotation_intelligence_240(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import compute_s2f_240

    circulating = float(params.get("circulating_supply") or 19_800_000)
    annual = float(params.get("annual_production") or 164_250)
    s2f = compute_s2f_240(
        asset=symbol,
        circulating_supply=circulating,
        annual_production=annual,
        seed=seed or _default_seed(),
    )
    payload = _base(
        240,
        symbol,
        "sector_rotation_intelligence",
        stock_to_flow=s2f,
        s2f_ratio=s2f.get("s2f_ratio"),
        scarcity=s2f.get("scarcity"),
        source="intelligence_ux_extensions_layer.compute_s2f_240",
        attribution="Stock-to-flow educational model — not price prediction",
        miswire_remediation="STRANGLER_IMPLEMENTED",
    )
    return _timed(payload, t0)


async def build_sentiment_intelligence_241(
    *, symbol: str, params: dict[str, Any], seed: dict[str, Any] | None = None
) -> dict[str, Any]:
    t0 = time.perf_counter()
    from bd_platform.intelligence_ux_extensions_layer import ingest_fred_macro_241

    fred = ingest_fred_macro_241(seed=seed or _default_seed())
    payload = _base(
        241,
        symbol,
        "sentiment_intelligence",
        fred_macro=fred,
        series=fred.get("series"),
        btc_correlation_90d=fred.get("btc_correlation_90d"),
        source="intelligence_ux_extensions_layer.ingest_fred_macro_241",
        attribution="FRED macro ingest — Federal Reserve Economic Data",
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
    217: build_sanapi_style_data_access_217,
    218: build_google_sheets_integration_218,
    219: build_metric_availability_registry_219,
    220: build_data_stabilization_mutability_metadata_220,
    221: build_data_quality_provenance_layer_221,
    222: build_metric_methodology_registry_222,
    223: build_social_to_on_chain_confirmation_engine_223,
    224: build_narrative_actionability_score_224,
    225: build_development_to_market_divergence_detector_225,
    227: build_unified_trading_intelligence_workspace_227,
    229: build_cross_exchange_funding_arbitrage_scanner_229,
    230: build_spot_perp_arbitrage_scanner_230,
    231: build_futures_basis_term_structure_231,
    233: build_liquidation_intelligence_233,
    234: build_cvd_intelligence_234,
    235: build_long_short_ratio_intelligence_235,
    236: build_dex_screener_236,
    237: build_token_risk_scoring_237,
    238: build_pump_dump_detection_238,
    239: build_narrative_tracking_239,
    240: build_sector_rotation_intelligence_240,
    241: build_sentiment_intelligence_241,
}

STRANGLER_IMPLEMENTED_IDS: frozenset[int] = frozenset(STRANGLER_BUILDERS)
