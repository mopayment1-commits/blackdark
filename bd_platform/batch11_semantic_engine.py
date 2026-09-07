"""Batch11 (501–550) capability-specific semantic transforms for institutional delivery shared core."""

from __future__ import annotations

from typing import Any, Callable

TransformFn = Callable[[dict[str, float], str], dict[str, Any]]


from bd_platform.batch_semantic_primitives import ratio as _ratio, semantic_inputs as _inputs, spread as _spread, weighted as _weighted

def _institutional_delivery(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['sla_uptime_pct'], 0.5), (i['venues_connected'], 0.3), (100 - i['latency_ms'], 0.2))
    return {
        "institutional_delivery": primary,
        "sla_uptime_pct": i["sla_uptime_pct"],
        "venues_connected": i["venues_connected"],
        "latency_ms": i["latency_ms"],
        "symbol_focus": symbol.upper(),
    }

def _benchmark_administration(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['administered_benchmarks'], i['total_benchmarks']), 4)
    return {
        "benchmark_administration": primary,
        "administered_benchmarks": i["administered_benchmarks"],
        "total_benchmarks": i["total_benchmarks"],
        "rebalance_events_ytd": i["rebalance_events_ytd"],
        "symbol_focus": symbol.upper(),
    }

def _cross_market_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((100 - i['primary_latency_ms'], 0.5), (100 - i['secondary_latency_ms'], 0.3), (i['venue_match_pct'], 0.2))
    return {
        "cross_market_data": primary,
        "primary_latency_ms": i["primary_latency_ms"],
        "secondary_latency_ms": i["secondary_latency_ms"],
        "venue_match_pct": i["venue_match_pct"],
        "symbol_focus": symbol.upper(),
    }

def _unified_exchange_connector(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['connected_exchanges'], i['target_exchanges']) * i['connector_uptime_pct'] / 100, 4)
    return {
        "unified_exchange_connector": primary,
        "connected_exchanges": i["connected_exchanges"],
        "target_exchanges": i["target_exchanges"],
        "connector_uptime_pct": i["connector_uptime_pct"],
        "symbol_focus": symbol.upper(),
    }

def _tick_trade_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['ticks_per_sec'] * i['symbols_streaming'] / max(100 - i['drop_rate_pct'], 1), 4)
    return {
        "tick_trade_data": primary,
        "ticks_per_sec": i["ticks_per_sec"],
        "symbols_streaming": i["symbols_streaming"],
        "drop_rate_pct": i["drop_rate_pct"],
        "symbol_focus": symbol.upper(),
    }

def _quote_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['quotes_per_sec'] / max(i['latency_ms'], 1.0), 4)
    return {
        "quote_data": primary,
        "quotes_per_sec": i["quotes_per_sec"],
        "latency_ms": i["latency_ms"],
        "symbols_covered": i["symbols_covered"],
        "symbol_focus": symbol.upper(),
    }

def _ohlcv(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['candles_present'], i['candles_expected']), 4)
    return {
        "ohlcv": primary,
        "candles_present": i["candles_present"],
        "candles_expected": i["candles_expected"],
        "interval_minutes": i["interval_minutes"],
        "symbol_focus": symbol.upper(),
    }

def _l1_order_book(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['bid_depth_usd'] + i['ask_depth_usd'], 4)
    return {
        "l1_order_book": primary,
        "bid_depth_usd": i["bid_depth_usd"],
        "ask_depth_usd": i["ask_depth_usd"],
        "spread_bps": i["spread_bps"],
        "symbol_focus": symbol.upper(),
    }

def _l2_order_book(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['l2_levels'] * i['depth_per_level_usd'] / 1e6, 4)
    return {
        "l2_order_book": primary,
        "l2_levels": i["l2_levels"],
        "depth_per_level_usd": i["depth_per_level_usd"],
        "update_hz": i["update_hz"],
        "symbol_focus": symbol.upper(),
    }

def _l3_order_book(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['l3_orders_tracked'] / max(i['update_latency_ms'], 1.0), 4)
    return {
        "l3_order_book": primary,
        "l3_orders_tracked": i["l3_orders_tracked"],
        "update_latency_ms": i["update_latency_ms"],
        "cancel_ratio_pct": i["cancel_ratio_pct"],
        "symbol_focus": symbol.upper(),
    }

def _options_market_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['options_contracts'] * i['greeks_fields'], 4)
    return {
        "options_market_data": primary,
        "options_contracts": i["options_contracts"],
        "greeks_fields": i["greeks_fields"],
        "expiry_buckets": i["expiry_buckets"],
        "symbol_focus": symbol.upper(),
    }

def _funding_oi_liquidation(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['funding_bps'], 0.34), (i['oi_change_24h_pct'], 0.33), (i['liq_volume_usd'] / 1e6, 0.33))
    return {
        "funding_oi_liquidation": primary,
        "funding_bps": i["funding_bps"],
        "oi_change_24h_pct": i["oi_change_24h_pct"],
        "liq_volume_usd": i["liq_volume_usd"],
        "symbol_focus": symbol.upper(),
    }

def _asset_symbol_metadata(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['fields_mapped'], i['fields_required']), 4)
    return {
        "asset_symbol_metadata": primary,
        "fields_mapped": i["fields_mapped"],
        "fields_required": i["fields_required"],
        "symbols_catalogued": i["symbols_catalogued"],
        "symbol_focus": symbol.upper(),
    }

def _historical_flat_files(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['archive_tb'] * i['file_formats'] * i['retention_years'], 4)
    return {
        "historical_flat_files": primary,
        "archive_tb": i["archive_tb"],
        "file_formats": i["file_formats"],
        "retention_years": i["retention_years"],
        "symbol_focus": symbol.upper(),
    }

def _rest_api(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['endpoint_count'] * i['sla_uptime_pct'] / 100, 4)
    return {
        "rest_api": primary,
        "endpoint_count": i["endpoint_count"],
        "sla_uptime_pct": i["sla_uptime_pct"],
        "p95_latency_ms": i["p95_latency_ms"],
        "symbol_focus": symbol.upper(),
    }

def _websocket_streaming(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['streams_active'] * i['messages_per_sec'] / max(100 - i['reconnect_rate_pct'], 1), 4)
    return {
        "websocket_streaming": primary,
        "streams_active": i["streams_active"],
        "messages_per_sec": i["messages_per_sec"],
        "reconnect_rate_pct": i["reconnect_rate_pct"],
        "symbol_focus": symbol.upper(),
    }

def _mcp_for_ai(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['tool_count'] * i['context_tokens_k'] / 10, 4)
    return {
        "mcp_for_ai": primary,
        "tool_count": i["tool_count"],
        "context_tokens_k": i["context_tokens_k"],
        "grounding_hits_24h": i["grounding_hits_24h"],
        "symbol_focus": symbol.upper(),
    }

def _exchange_rates_vwap(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['vwap_bps'], i['spot_bps'])
    return {
        "exchange_rates_vwap": primary,
        "vwap_bps": i["vwap_bps"],
        "spot_bps": i["spot_bps"],
        "venue_count": i["venue_count"],
        "symbol_focus": symbol.upper(),
    }

def _indexes(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['constituents'] * i['rebalance_events_ytd'], 4)
    return {
        "indexes": primary,
        "constituents": i["constituents"],
        "rebalance_events_ytd": i["rebalance_events_ytd"],
        "tracking_error_bps": i["tracking_error_bps"],
        "symbol_focus": symbol.upper(),
    }

def _volatility_index(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['realized_vol_pct'] * i['lookback_days'] ** 0.5, 4)
    return {
        "volatility_index": primary,
        "realized_vol_pct": i["realized_vol_pct"],
        "lookback_days": i["lookback_days"],
        "implied_vol_pct": i["implied_vol_pct"],
        "symbol_focus": symbol.upper(),
    }

def _ems_integration_boundary(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['order_routing_score'], 0.4), (i['compliance_score'], 0.35), (i['latency_score'], 0.25))
    return {
        "ems_integration_boundary": primary,
        "order_routing_score": i["order_routing_score"],
        "compliance_score": i["compliance_score"],
        "latency_score": i["latency_score"],
        "symbol_focus": symbol.upper(),
    }

def _data_health_sla(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['healthy_feeds'], i['total_feeds']), 4)
    return {
        "data_health_sla": primary,
        "healthy_feeds": i["healthy_feeds"],
        "total_feeds": i["total_feeds"],
        "breach_count_24h": i["breach_count_24h"],
        "symbol_focus": symbol.upper(),
    }

def _symbol_mapping_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['mapped_symbols'], i['total_symbols']), 4)
    return {
        "symbol_mapping_engine": primary,
        "mapped_symbols": i["mapped_symbols"],
        "total_symbols": i["total_symbols"],
        "alias_conflicts": i["alias_conflicts"],
        "symbol_focus": symbol.upper(),
    }

def _ai_market_grounding(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['grounding_confidence'] * i['validated_sources'] * 10, 4)
    return {
        "ai_market_grounding": primary,
        "grounding_confidence": i["grounding_confidence"],
        "validated_sources": i["validated_sources"],
        "hallucination_flags_24h": i["hallucination_flags_24h"],
        "symbol_focus": symbol.upper(),
    }

def _liquidation_heatmap(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['liquidation_zones'] * i['heat_intensity'] * i['price_levels_tracked'] / 100, 4)
    return {
        "liquidation_heatmap": primary,
        "liquidation_zones": i["liquidation_zones"],
        "heat_intensity": i["heat_intensity"],
        "price_levels_tracked": i["price_levels_tracked"],
        "symbol_focus": symbol.upper(),
    }

def _liquidation_cascade_model(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['cascade_probability'] * i['oi_at_risk_usd'] / 1e9 * i['leverage_factor'], 4)
    return {
        "liquidation_cascade_model": primary,
        "cascade_probability": i["cascade_probability"],
        "oi_at_risk_usd": i["oi_at_risk_usd"],
        "leverage_factor": i["leverage_factor"],
        "symbol_focus": symbol.upper(),
    }

def _global_liquidation_metrics(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['global_liq_usd_24h'] / 1e6, 4)
    return {
        "global_liquidation_metrics": primary,
        "global_liq_usd_24h": i["global_liq_usd_24h"],
        "long_liq_pct": i["long_liq_pct"],
        "short_liq_pct": i["short_liq_pct"],
        "symbol_focus": symbol.upper(),
    }

def _open_interest(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['oi_usd'], i['spot_volume_usd']), 4)
    return {
        "open_interest": primary,
        "oi_usd": i["oi_usd"],
        "spot_volume_usd": i["spot_volume_usd"],
        "oi_change_24h_pct": i["oi_change_24h_pct"],
        "symbol_focus": symbol.upper(),
    }

def _funding_rates(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['perp_funding_bps'], i['spot_implied_bps'])
    return {
        "funding_rates": primary,
        "perp_funding_bps": i["perp_funding_bps"],
        "spot_implied_bps": i["spot_implied_bps"],
        "venues_tracked": i["venues_tracked"],
        "symbol_focus": symbol.upper(),
    }

def _order_flow_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_spread(i['buy_volume_usd'], i['sell_volume_usd']) / 1e6, 4)
    return {
        "order_flow_intelligence": primary,
        "buy_volume_usd": i["buy_volume_usd"],
        "sell_volume_usd": i["sell_volume_usd"],
        "aggressor_ratio": i["aggressor_ratio"],
        "symbol_focus": symbol.upper(),
    }

def _bucketed_cvd(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['cvd_buckets'] * i['avg_bucket_delta'] / 1e6, 4)
    return {
        "bucketed_cvd": primary,
        "cvd_buckets": i["cvd_buckets"],
        "avg_bucket_delta": i["avg_bucket_delta"],
        "lookback_hours": i["lookback_hours"],
        "symbol_focus": symbol.upper(),
    }

def _whale_vs_retail_flow(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['whale_flow_pct'], i['retail_flow_pct'])
    return {
        "whale_vs_retail_flow": primary,
        "whale_flow_pct": i["whale_flow_pct"],
        "retail_flow_pct": i["retail_flow_pct"],
        "whale_trade_count": i["whale_trade_count"],
        "symbol_focus": symbol.upper(),
    }

def _slippage_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((100 - i['expected_slippage_bps'], 0.4), (i['depth_score'], 0.35), (100 - i['volatility_pct'], 0.25))
    return {
        "slippage_intelligence": primary,
        "expected_slippage_bps": i["expected_slippage_bps"],
        "depth_score": i["depth_score"],
        "volatility_pct": i["volatility_pct"],
        "symbol_focus": symbol.upper(),
    }

def _global_order_book_metrics(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['global_bid_depth_usd'] + i['global_ask_depth_usd'], 4)
    return {
        "global_order_book_metrics": primary,
        "global_bid_depth_usd": i["global_bid_depth_usd"],
        "global_ask_depth_usd": i["global_ask_depth_usd"],
        "venue_count": i["venue_count"],
        "symbol_focus": symbol.upper(),
    }

def _order_book_imbalance(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['bid_depth_usd'], i['ask_depth_usd']), 4)
    return {
        "order_book_imbalance": primary,
        "bid_depth_usd": i["bid_depth_usd"],
        "ask_depth_usd": i["ask_depth_usd"],
        "imbalance_threshold_pct": i["imbalance_threshold_pct"],
        "symbol_focus": symbol.upper(),
    }

def _liquidity_zones(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['zone_count'] * i['zone_strength_avg'] * i['price_range_pct'], 4)
    return {
        "liquidity_zones": primary,
        "zone_count": i["zone_count"],
        "zone_strength_avg": i["zone_strength_avg"],
        "price_range_pct": i["price_range_pct"],
        "symbol_focus": symbol.upper(),
    }

def _bot_activity_detection(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['bot_trade_pct'] * i['trade_velocity'] / 100, 4)
    return {
        "bot_activity_detection": primary,
        "bot_trade_pct": i["bot_trade_pct"],
        "trade_velocity": i["trade_velocity"],
        "cancel_replace_ratio": i["cancel_replace_ratio"],
        "symbol_focus": symbol.upper(),
    }

def _market_positioning(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['long_ratio_pct'], i['short_ratio_pct'])
    return {
        "market_positioning": primary,
        "long_ratio_pct": i["long_ratio_pct"],
        "short_ratio_pct": i["short_ratio_pct"],
        "crowding_score": i["crowding_score"],
        "symbol_focus": symbol.upper(),
    }

def _liquidation_pressure_score(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['oi_leverage'], 0.35), (i['funding_stress'], 0.35), (i['liq_proximity_pct'], 0.3))
    return {
        "liquidation_pressure_score": primary,
        "oi_leverage": i["oi_leverage"],
        "funding_stress": i["funding_stress"],
        "liq_proximity_pct": i["liq_proximity_pct"],
        "symbol_focus": symbol.upper(),
    }

def _orderflow_anomaly_detection(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['anomaly_score'] * i['z_score'] * 10, 4)
    return {
        "orderflow_anomaly_detection": primary,
        "anomaly_score": i["anomaly_score"],
        "z_score": i["z_score"],
        "baseline_trades_24h": i["baseline_trades_24h"],
        "symbol_focus": symbol.upper(),
    }

def _api_indicator_platform(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['indicators_available'] * i['api_calls_24h'] / max(i['unique_users'], 1.0), 4)
    return {
        "api_indicator_platform": primary,
        "indicators_available": i["indicators_available"],
        "api_calls_24h": i["api_calls_24h"],
        "unique_users": i["unique_users"],
        "symbol_focus": symbol.upper(),
    }

def _trader_cohort_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['win_rate_pct'], 0.4), (i['avg_hold_hours'], 0.3), (i['cohort_size'] / 100, 0.3))
    return {
        "trader_cohort_intelligence": primary,
        "win_rate_pct": i["win_rate_pct"],
        "avg_hold_hours": i["avg_hold_hours"],
        "cohort_size": i["cohort_size"],
        "symbol_focus": symbol.upper(),
    }

def _cross_derivatives_decision(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['spot_signal'], 0.34), (i['perp_signal'], 0.33), (i['options_signal'], 0.33))
    return {
        "cross_derivatives_decision": primary,
        "spot_signal": i["spot_signal"],
        "perp_signal": i["perp_signal"],
        "options_signal": i["options_signal"],
        "symbol_focus": symbol.upper(),
    }

def _high_resolution_multi_pane(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['panes_count'] * i['resolution_factor'] * i['refresh_hz'], 4)
    return {
        "high_resolution_multi_pane": primary,
        "panes_count": i["panes_count"],
        "resolution_factor": i["resolution_factor"],
        "refresh_hz": i["refresh_hz"],
        "symbol_focus": symbol.upper(),
    }

def _derivatives_dashboard(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['widgets_active'] * i['refresh_rate_hz'], 4)
    return {
        "derivatives_dashboard": primary,
        "widgets_active": i["widgets_active"],
        "refresh_rate_hz": i["refresh_rate_hz"],
        "alerts_configured": i["alerts_configured"],
        "symbol_focus": symbol.upper(),
    }

def _funding_rate_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(abs(_spread(i['perp_funding_bps'], i['historical_avg_bps'])), 4)
    return {
        "funding_rate_intelligence": primary,
        "perp_funding_bps": i["perp_funding_bps"],
        "historical_avg_bps": i["historical_avg_bps"],
        "venue_count": i["venue_count"],
        "symbol_focus": symbol.upper(),
    }

def _open_interest_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['oi_change_24h_pct'] * i['oi_usd'] / 1e9, 4)
    return {
        "open_interest_intelligence": primary,
        "oi_change_24h_pct": i["oi_change_24h_pct"],
        "oi_usd": i["oi_usd"],
        "concentration_pct": i["concentration_pct"],
        "symbol_focus": symbol.upper(),
    }

RULES: dict[str, TransformFn] = {
    "institutional_delivery": _institutional_delivery,
    "benchmark_administration": _benchmark_administration,
    "cross_market_data": _cross_market_data,
    "unified_exchange_connector": _unified_exchange_connector,
    "tick_trade_data": _tick_trade_data,
    "quote_data": _quote_data,
    "ohlcv": _ohlcv,
    "l1_order_book": _l1_order_book,
    "l2_order_book": _l2_order_book,
    "l3_order_book": _l3_order_book,
    "options_market_data": _options_market_data,
    "funding_oi_liquidation": _funding_oi_liquidation,
    "asset_symbol_metadata": _asset_symbol_metadata,
    "historical_flat_files": _historical_flat_files,
    "rest_api": _rest_api,
    "websocket_streaming": _websocket_streaming,
    "mcp_for_ai": _mcp_for_ai,
    "exchange_rates_vwap": _exchange_rates_vwap,
    "indexes": _indexes,
    "volatility_index": _volatility_index,
    "ems_integration_boundary": _ems_integration_boundary,
    "data_health_sla": _data_health_sla,
    "symbol_mapping_engine": _symbol_mapping_engine,
    "ai_market_grounding": _ai_market_grounding,
    "liquidation_heatmap": _liquidation_heatmap,
    "liquidation_cascade_model": _liquidation_cascade_model,
    "global_liquidation_metrics": _global_liquidation_metrics,
    "open_interest": _open_interest,
    "funding_rates": _funding_rates,
    "order_flow_intelligence": _order_flow_intelligence,
    "bucketed_cvd": _bucketed_cvd,
    "whale_vs_retail_flow": _whale_vs_retail_flow,
    "slippage_intelligence": _slippage_intelligence,
    "global_order_book_metrics": _global_order_book_metrics,
    "order_book_imbalance": _order_book_imbalance,
    "liquidity_zones": _liquidity_zones,
    "bot_activity_detection": _bot_activity_detection,
    "market_positioning": _market_positioning,
    "liquidation_pressure_score": _liquidation_pressure_score,
    "orderflow_anomaly_detection": _orderflow_anomaly_detection,
    "api_indicator_platform": _api_indicator_platform,
    "trader_cohort_intelligence": _trader_cohort_intelligence,
    "cross_derivatives_decision": _cross_derivatives_decision,
    "high_resolution_multi_pane": _high_resolution_multi_pane,
    "derivatives_dashboard": _derivatives_dashboard,
    "funding_rate_intelligence": _funding_rate_intelligence,
    "open_interest_intelligence": _open_interest_intelligence,
}

CAPABILITY_SEMANTIC_SPECS: dict[int, dict[str, Any]] = {
    501: {"rule": "institutional_delivery", "defaults": {"sla_uptime_pct": 99.7, "venues_connected": 28, "latency_ms": 42}, "feature": "Institutional Delivery"},
    502: {"rule": "benchmark_administration", "defaults": {"administered_benchmarks": 18, "total_benchmarks": 24, "rebalance_events_ytd": 6}, "feature": "Benchmark Administration Metadata"},
    503: {"rule": "cross_market_data", "defaults": {"primary_latency_ms": 38, "secondary_latency_ms": 52, "venue_match_pct": 91}, "feature": "Cross-Market Data Intelligence"},
    504: {"rule": "unified_exchange_connector", "defaults": {"connected_exchanges": 22, "target_exchanges": 26, "connector_uptime_pct": 98.5}, "feature": "Unified Exchange Connector Layer"},
    505: {"rule": "tick_trade_data", "defaults": {"ticks_per_sec": 1250, "symbols_streaming": 48, "drop_rate_pct": 0.2}, "feature": "Tick Trade Data"},
    506: {"rule": "quote_data", "defaults": {"quotes_per_sec": 840, "latency_ms": 12, "symbols_covered": 320}, "feature": "Quote Data"},
    507: {"rule": "ohlcv", "defaults": {"candles_present": 4320, "candles_expected": 4500, "interval_minutes": 1}, "feature": "OHLCV"},
    508: {"rule": "l1_order_book", "defaults": {"bid_depth_usd": 4200000.0, "ask_depth_usd": 3800000.0, "spread_bps": 3.5}, "feature": "L1 Order Book"},
    509: {"rule": "l2_order_book", "defaults": {"l2_levels": 25, "depth_per_level_usd": 185000, "update_hz": 12}, "feature": "L2 Order Book"},
    510: {"rule": "l3_order_book", "defaults": {"l3_orders_tracked": 18500, "update_latency_ms": 8, "cancel_ratio_pct": 42}, "feature": "L3 Order Book"},
    511: {"rule": "options_market_data", "defaults": {"options_contracts": 420, "greeks_fields": 6, "expiry_buckets": 8}, "feature": "Options Market Data"},
    512: {"rule": "funding_oi_liquidation", "defaults": {"funding_bps": 7.2, "oi_change_24h_pct": 4.5, "liq_volume_usd": 28000000.0}, "feature": "Funding / OI / Liquidation Metrics"},
    513: {"rule": "asset_symbol_metadata", "defaults": {"fields_mapped": 22, "fields_required": 24, "symbols_catalogued": 680}, "feature": "Asset & Symbol Metadata"},
    514: {"rule": "historical_flat_files", "defaults": {"archive_tb": 62, "file_formats": 4, "retention_years": 8}, "feature": "Historical Flat Files"},
    515: {"rule": "rest_api", "defaults": {"endpoint_count": 72, "sla_uptime_pct": 99.6, "p95_latency_ms": 85}, "feature": "REST API"},
    516: {"rule": "websocket_streaming", "defaults": {"streams_active": 36, "messages_per_sec": 9800, "reconnect_rate_pct": 0.4}, "feature": "WebSocket Streaming"},
    518: {"rule": "mcp_for_ai", "defaults": {"tool_count": 24, "context_tokens_k": 128, "grounding_hits_24h": 4200}, "feature": "MCP for AI"},
    519: {"rule": "exchange_rates_vwap", "defaults": {"vwap_bps": 11.4, "spot_bps": 8.6, "venue_count": 14}, "feature": "Exchange Rates / VWAP"},
    520: {"rule": "indexes", "defaults": {"constituents": 20, "rebalance_events_ytd": 14, "tracking_error_bps": 6.5}, "feature": "Indexes"},
    521: {"rule": "volatility_index", "defaults": {"realized_vol_pct": 62, "lookback_days": 21, "implied_vol_pct": 58}, "feature": "Volatility Index"},
    522: {"rule": "ems_integration_boundary", "defaults": {"order_routing_score": 88, "compliance_score": 92, "latency_score": 85}, "feature": "EMS Integration Boundary"},
    523: {"rule": "data_health_sla", "defaults": {"healthy_feeds": 46, "total_feeds": 50, "breach_count_24h": 2}, "feature": "Data Health / SLA Monitoring"},
    524: {"rule": "symbol_mapping_engine", "defaults": {"mapped_symbols": 920, "total_symbols": 980, "alias_conflicts": 3}, "feature": "Symbol Mapping Engine"},
    526: {"rule": "ai_market_grounding", "defaults": {"grounding_confidence": 0.91, "validated_sources": 18, "hallucination_flags_24h": 1}, "feature": "AI Market Data Grounding Layer"},
    527: {"rule": "liquidation_heatmap", "defaults": {"liquidation_zones": 12, "heat_intensity": 0.78, "price_levels_tracked": 240}, "feature": "Liquidation Heatmap"},
    529: {"rule": "liquidation_cascade_model", "defaults": {"cascade_probability": 0.34, "oi_at_risk_usd": 1800000000.0, "leverage_factor": 12}, "feature": "Liquidation Cascade Model"},
    530: {"rule": "global_liquidation_metrics", "defaults": {"global_liq_usd_24h": 420000000.0, "long_liq_pct": 58, "short_liq_pct": 42}, "feature": "Global Liquidation Metrics"},
    531: {"rule": "open_interest", "defaults": {"oi_usd": 11500000000.0, "spot_volume_usd": 32000000000.0, "oi_change_24h_pct": 2.8}, "feature": "Open Interest"},
    532: {"rule": "funding_rates", "defaults": {"perp_funding_bps": 8.1, "spot_implied_bps": 5.4, "venues_tracked": 16}, "feature": "Funding Rates"},
    533: {"rule": "order_flow_intelligence", "defaults": {"buy_volume_usd": 125000000.0, "sell_volume_usd": 118000000.0, "aggressor_ratio": 1.06}, "feature": "Order Flow Intelligence"},
    534: {"rule": "bucketed_cvd", "defaults": {"cvd_buckets": 24, "avg_bucket_delta": 420000, "lookback_hours": 12}, "feature": "Bucketed CVD"},
    535: {"rule": "whale_vs_retail_flow", "defaults": {"whale_flow_pct": 62, "retail_flow_pct": 38, "whale_trade_count": 145}, "feature": "Whale vs Retail Flow"},
    536: {"rule": "slippage_intelligence", "defaults": {"expected_slippage_bps": 9.5, "depth_score": 78, "volatility_pct": 48}, "feature": "Slippage Intelligence"},
    537: {"rule": "global_order_book_metrics", "defaults": {"global_bid_depth_usd": 18000000.0, "global_ask_depth_usd": 16500000.0, "venue_count": 14}, "feature": "Global Order Book Metrics"},
    538: {"rule": "order_book_imbalance", "defaults": {"bid_depth_usd": 9200000.0, "ask_depth_usd": 7100000.0, "imbalance_threshold_pct": 15}, "feature": "Order Book Imbalance"},
    539: {"rule": "liquidity_zones", "defaults": {"zone_count": 8, "zone_strength_avg": 0.72, "price_range_pct": 4.5}, "feature": "Liquidity Zones"},
    540: {"rule": "bot_activity_detection", "defaults": {"bot_trade_pct": 34, "trade_velocity": 820, "cancel_replace_ratio": 2.4}, "feature": "Bot Activity Detection"},
    541: {"rule": "market_positioning", "defaults": {"long_ratio_pct": 54, "short_ratio_pct": 46, "crowding_score": 62}, "feature": "Market Positioning"},
    542: {"rule": "liquidation_pressure_score", "defaults": {"oi_leverage": 18, "funding_stress": 72, "liq_proximity_pct": 8.5}, "feature": "Liquidation Pressure Score"},
    543: {"rule": "orderflow_anomaly_detection", "defaults": {"anomaly_score": 0.82, "z_score": 2.6, "baseline_trades_24h": 125000}, "feature": "Orderflow Anomaly Detection"},
    544: {"rule": "api_indicator_platform", "defaults": {"indicators_available": 64, "api_calls_24h": 18500, "unique_users": 420}, "feature": "API Indicator Platform"},
    545: {"rule": "trader_cohort_intelligence", "defaults": {"win_rate_pct": 58, "avg_hold_hours": 18, "cohort_size": 2400}, "feature": "Trader Cohort Intelligence"},
    546: {"rule": "cross_derivatives_decision", "defaults": {"spot_signal": 0.61, "perp_signal": 0.57, "options_signal": 0.52}, "feature": "Cross-Derivatives Decision Intelligence"},
    547: {"rule": "high_resolution_multi_pane", "defaults": {"panes_count": 6, "resolution_factor": 2.5, "refresh_hz": 4}, "feature": "High-Resolution Multi-Pane Charts"},
    548: {"rule": "derivatives_dashboard", "defaults": {"widgets_active": 18, "refresh_rate_hz": 2, "alerts_configured": 12}, "feature": "Derivatives Dashboard"},
    549: {"rule": "funding_rate_intelligence", "defaults": {"perp_funding_bps": 9.2, "historical_avg_bps": 5.8, "venue_count": 12}, "feature": "Funding Rate Intelligence"},
}

def compute_semantic_extra(cap_id: int, *, symbol: str, seed: dict[str, Any]) -> dict[str, Any]:
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    inputs = _inputs(seed, cap_id, spec["defaults"])
    transform = RULES[spec["rule"]]
    payload = transform(inputs, symbol.upper())
    payload["feature"] = spec["feature"]
    payload["semantic_rule"] = spec["rule"]
    payload["attribution"] = "BLACKDARK institutional delivery intelligence layer"
    payload["formula_visible"] = True
    payload["analysis_only"] = True
    return payload


def semantic_profile(cap_id: int) -> dict[str, Any]:
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    return {
        "capability_id": cap_id,
        "semantic_rule": spec["rule"],
        "input_defaults": spec["defaults"],
        "feature": spec["feature"],
    }


def shared_core_ids() -> list[int]:
    return sorted(CAPABILITY_SEMANTIC_SPECS.keys())
