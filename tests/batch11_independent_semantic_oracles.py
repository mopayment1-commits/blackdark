"""Independent reference oracles for Batch11 parameterized semantics (501–550).

Deliberately does NOT import bd_platform.batch11_semantic_engine RULES or compute_semantic_extra.
"""

from __future__ import annotations

from typing import Any


def _ratio(a: float, b: float, *, scale: float = 100.0) -> float:
    return round(a / max(b, 1e-9) * scale, 4)


def _spread(a: float, b: float) -> float:
    return round(a - b, 4)


def _weighted(*pairs: tuple[float, float]) -> float:
    num = sum(v * w for v, w in pairs)
    den = sum(w for _, w in pairs)
    return round(num / max(den, 1e-9), 4)

PRIMARY_FIELD: dict[str, str] = {
    "ai_market_grounding": "ai_market_grounding",
    "api_indicator_platform": "api_indicator_platform",
    "asset_symbol_metadata": "asset_symbol_metadata",
    "benchmark_administration": "benchmark_administration",
    "bot_activity_detection": "bot_activity_detection",
    "bucketed_cvd": "bucketed_cvd",
    "cross_derivatives_decision": "cross_derivatives_decision",
    "cross_market_data": "cross_market_data",
    "data_health_sla": "data_health_sla",
    "derivatives_dashboard": "derivatives_dashboard",
    "ems_integration_boundary": "ems_integration_boundary",
    "exchange_rates_vwap": "exchange_rates_vwap",
    "funding_oi_liquidation": "funding_oi_liquidation",
    "funding_rate_intelligence": "funding_rate_intelligence",
    "funding_rates": "funding_rates",
    "global_liquidation_metrics": "global_liquidation_metrics",
    "global_order_book_metrics": "global_order_book_metrics",
    "high_resolution_multi_pane": "high_resolution_multi_pane",
    "historical_flat_files": "historical_flat_files",
    "indexes": "indexes",
    "institutional_delivery": "institutional_delivery",
    "l1_order_book": "l1_order_book",
    "l2_order_book": "l2_order_book",
    "l3_order_book": "l3_order_book",
    "liquidation_cascade_model": "liquidation_cascade_model",
    "liquidation_heatmap": "liquidation_heatmap",
    "liquidation_pressure_score": "liquidation_pressure_score",
    "liquidity_zones": "liquidity_zones",
    "market_positioning": "market_positioning",
    "mcp_for_ai": "mcp_for_ai",
    "ohlcv": "ohlcv",
    "open_interest": "open_interest",
    "open_interest_intelligence": "open_interest_intelligence",
    "options_market_data": "options_market_data",
    "order_book_imbalance": "order_book_imbalance",
    "order_flow_intelligence": "order_flow_intelligence",
    "orderflow_anomaly_detection": "orderflow_anomaly_detection",
    "quote_data": "quote_data",
    "rest_api": "rest_api",
    "slippage_intelligence": "slippage_intelligence",
    "symbol_mapping_engine": "symbol_mapping_engine",
    "tick_trade_data": "tick_trade_data",
    "trader_cohort_intelligence": "trader_cohort_intelligence",
    "unified_exchange_connector": "unified_exchange_connector",
    "volatility_index": "volatility_index",
    "websocket_streaming": "websocket_streaming",
    "whale_vs_retail_flow": "whale_vs_retail_flow",
}

def independent_primary(rule: str, inputs: dict[str, float], symbol: str = "ETH") -> float:
    i = inputs
    if rule == "ai_market_grounding":
        return round(i['grounding_confidence'] * i['validated_sources'] * 10, 4)
    if rule == "api_indicator_platform":
        return round(i['indicators_available'] * i['api_calls_24h'] / max(i['unique_users'], 1.0), 4)
    if rule == "asset_symbol_metadata":
        return round(_ratio(i['fields_mapped'], i['fields_required']), 4)
    if rule == "benchmark_administration":
        return round(_ratio(i['administered_benchmarks'], i['total_benchmarks']), 4)
    if rule == "bot_activity_detection":
        return round(i['bot_trade_pct'] * i['trade_velocity'] / 100, 4)
    if rule == "bucketed_cvd":
        return round(i['cvd_buckets'] * i['avg_bucket_delta'] / 1e6, 4)
    if rule == "cross_derivatives_decision":
        return _weighted((i['spot_signal'], 0.34), (i['perp_signal'], 0.33), (i['options_signal'], 0.33))
    if rule == "cross_market_data":
        return _weighted((100 - i['primary_latency_ms'], 0.5), (100 - i['secondary_latency_ms'], 0.3), (i['venue_match_pct'], 0.2))
    if rule == "data_health_sla":
        return round(_ratio(i['healthy_feeds'], i['total_feeds']), 4)
    if rule == "derivatives_dashboard":
        return round(i['widgets_active'] * i['refresh_rate_hz'], 4)
    if rule == "ems_integration_boundary":
        return _weighted((i['order_routing_score'], 0.4), (i['compliance_score'], 0.35), (i['latency_score'], 0.25))
    if rule == "exchange_rates_vwap":
        return _spread(i['vwap_bps'], i['spot_bps'])
    if rule == "funding_oi_liquidation":
        return _weighted((i['funding_bps'], 0.34), (i['oi_change_24h_pct'], 0.33), (i['liq_volume_usd'] / 1e6, 0.33))
    if rule == "funding_rate_intelligence":
        return round(abs(_spread(i['perp_funding_bps'], i['historical_avg_bps'])), 4)
    if rule == "funding_rates":
        return _spread(i['perp_funding_bps'], i['spot_implied_bps'])
    if rule == "global_liquidation_metrics":
        return round(i['global_liq_usd_24h'] / 1e6, 4)
    if rule == "global_order_book_metrics":
        return round(i['global_bid_depth_usd'] + i['global_ask_depth_usd'], 4)
    if rule == "high_resolution_multi_pane":
        return round(i['panes_count'] * i['resolution_factor'] * i['refresh_hz'], 4)
    if rule == "historical_flat_files":
        return round(i['archive_tb'] * i['file_formats'] * i['retention_years'], 4)
    if rule == "indexes":
        return round(i['constituents'] * i['rebalance_events_ytd'], 4)
    if rule == "institutional_delivery":
        return _weighted((i['sla_uptime_pct'], 0.5), (i['venues_connected'], 0.3), (100 - i['latency_ms'], 0.2))
    if rule == "l1_order_book":
        return round(i['bid_depth_usd'] + i['ask_depth_usd'], 4)
    if rule == "l2_order_book":
        return round(i['l2_levels'] * i['depth_per_level_usd'] / 1e6, 4)
    if rule == "l3_order_book":
        return round(i['l3_orders_tracked'] / max(i['update_latency_ms'], 1.0), 4)
    if rule == "liquidation_cascade_model":
        return round(i['cascade_probability'] * i['oi_at_risk_usd'] / 1e9 * i['leverage_factor'], 4)
    if rule == "liquidation_heatmap":
        return round(i['liquidation_zones'] * i['heat_intensity'] * i['price_levels_tracked'] / 100, 4)
    if rule == "liquidation_pressure_score":
        return _weighted((i['oi_leverage'], 0.35), (i['funding_stress'], 0.35), (i['liq_proximity_pct'], 0.3))
    if rule == "liquidity_zones":
        return round(i['zone_count'] * i['zone_strength_avg'] * i['price_range_pct'], 4)
    if rule == "market_positioning":
        return _spread(i['long_ratio_pct'], i['short_ratio_pct'])
    if rule == "mcp_for_ai":
        return round(i['tool_count'] * i['context_tokens_k'] / 10, 4)
    if rule == "ohlcv":
        return round(_ratio(i['candles_present'], i['candles_expected']), 4)
    if rule == "open_interest":
        return round(_ratio(i['oi_usd'], i['spot_volume_usd']), 4)
    if rule == "open_interest_intelligence":
        return round(i['oi_change_24h_pct'] * i['oi_usd'] / 1e9, 4)
    if rule == "options_market_data":
        return round(i['options_contracts'] * i['greeks_fields'], 4)
    if rule == "order_book_imbalance":
        return round(_ratio(i['bid_depth_usd'], i['ask_depth_usd']), 4)
    if rule == "order_flow_intelligence":
        return round(_spread(i['buy_volume_usd'], i['sell_volume_usd']) / 1e6, 4)
    if rule == "orderflow_anomaly_detection":
        return round(i['anomaly_score'] * i['z_score'] * 10, 4)
    if rule == "quote_data":
        return round(i['quotes_per_sec'] / max(i['latency_ms'], 1.0), 4)
    if rule == "rest_api":
        return round(i['endpoint_count'] * i['sla_uptime_pct'] / 100, 4)
    if rule == "slippage_intelligence":
        return _weighted((100 - i['expected_slippage_bps'], 0.4), (i['depth_score'], 0.35), (100 - i['volatility_pct'], 0.25))
    if rule == "symbol_mapping_engine":
        return round(_ratio(i['mapped_symbols'], i['total_symbols']), 4)
    if rule == "tick_trade_data":
        return round(i['ticks_per_sec'] * i['symbols_streaming'] / max(100 - i['drop_rate_pct'], 1), 4)
    if rule == "trader_cohort_intelligence":
        return _weighted((i['win_rate_pct'], 0.4), (i['avg_hold_hours'], 0.3), (i['cohort_size'] / 100, 0.3))
    if rule == "unified_exchange_connector":
        return round(_ratio(i['connected_exchanges'], i['target_exchanges']) * i['connector_uptime_pct'] / 100, 4)
    if rule == "volatility_index":
        return round(i['realized_vol_pct'] * i['lookback_days'] ** 0.5, 4)
    if rule == "websocket_streaming":
        return round(i['streams_active'] * i['messages_per_sec'] / max(100 - i['reconnect_rate_pct'], 1), 4)
    if rule == "whale_vs_retail_flow":
        return _spread(i['whale_flow_pct'], i['retail_flow_pct'])
    raise KeyError(rule)
