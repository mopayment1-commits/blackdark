"""Independent reference oracles for Batch10 parameterized semantics (451–500).

Deliberately does NOT import bd_platform.batch10_semantic_engine RULES or compute_semantic_extra.
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
    "protocol_dominance": "protocol_dominance",
    "aave_multi_chain": "aave_multi_chain",
    "risk_curation": "risk_curation",
    "capital_protection": "capital_protection",
    "stress_testing": "stress_testing",
    "cross_protocol_contagion": "cross_protocol_contagion",
    "protocol_risk_passport": "protocol_risk_passport",
    "network_data_pro": "network_data_pro",
    "atlas_blockchain_search": "atlas_blockchain_search",
    "address_balance_search": "address_balance_search",
    "transaction_search": "transaction_search",
    "block_search": "block_search",
    "balance_updates": "balance_updates",
    "stablecoin_network": "stablecoin_network_metrics",
    "market_data_feed": "market_data_feed",
    "market_data_pro": "market_data_pro",
    "reference_rates": "reference_rates",
    "indexes": "indexes",
    "realized_metrics": "realized_metrics",
    "supply_metrics": "supply_metrics",
    "mining_validator": "mining_validator_metrics",
    "fee_metrics": "fee_metrics",
    "activity_metrics": "activity_metrics",
    "custom_metric_workbench": "custom_metric_workbench",
    "community_charts_api": "community_charts_api",
    "market_network_join": "market_network_join",
    "data_quality_methodologies": "data_quality_methodologies",
    "historical_research_dataset": "historical_research_dataset",
    "institutional_apis": "institutional_apis",
    "cross_network_decision": "cross_network_decision_intelligence",
    "institutional_trade_data": "institutional_trade_data",
    "order_book_data": "order_book_data",
    "ohlcv_data": "ohlcv_data",
    "derivatives_data": "derivatives_data",
    "open_interest_data": "open_interest_data",
    "funding_rate_data": "funding_rate_data",
    "index_data": "index_data",
    "reference_pricing": "reference_pricing",
    "exchange_metadata": "exchange_metadata",
    "asset_metadata": "asset_metadata",
    "historical_market_archive": "historical_market_archive",
    "real_time_streams": "real_time_streams",
    "market_aggregates": "market_aggregates",
    "liquidity_analytics": "liquidity_analytics",
    "volatility_analytics": "volatility_analytics",
    "market_cap_supply": "market_cap_supply",
    "etf_etp_data": "etf_etp_data",
    "api_coverage_registry": "api_coverage_registry",
    "data_quality_normalization": "data_quality_normalization",
}


def independent_primary(rule: str, inputs: dict[str, float], symbol: str = "ETH") -> float:
    i = inputs
    if rule == "protocol_dominance":
        return round(_ratio(i["protocol_tvl_usd"], i["sector_tvl_usd"]) + i["market_share_delta_pct"], 4)
    if rule == "aave_multi_chain":
        return round(i["active_chains"] * i["avg_supply_usd"] / 1e9, 4)
    if rule == "risk_curation":
        return _weighted((i["audit_score"], 0.4), (100 - i["exploit_score"], 0.35), (i["liquidity_score"], 0.25))
    if rule == "capital_protection":
        return round(i["protection_buffer_pct"] - i["drawdown_pct"], 4)
    if rule == "stress_testing":
        return round(i["shock_pct"] * i["exposure_usd"] / 1e6, 4)
    if rule == "cross_protocol_contagion":
        return round(i["shared_collateral_pct"] * i["correlation_coeff"] * 100, 4)
    if rule == "protocol_risk_passport":
        return _weighted((i["audit_score"], 0.5), (i["governance_score"], 0.3), (100 - i["exploit_history"], 0.2))
    if rule == "network_data_pro":
        return round(i["node_coverage_pct"] * i["metric_families"], 4)
    if rule == "atlas_blockchain_search":
        return round(i["indexed_entities"] / max(i["query_latency_ms"], 1.0), 4)
    if rule == "address_balance_search":
        return round(i["addresses_indexed"] / max(i["lookup_ms"], 1.0), 4)
    if rule == "transaction_search":
        return round(i["tx_indexed"] / max(i["search_ms"], 1.0), 4)
    if rule == "block_search":
        return round(i["blocks_indexed"] / max(i["height_span"], 1.0), 4)
    if rule == "balance_updates":
        return round(i["updates_per_min"] * i["wallets_tracked"], 4)
    if rule == "stablecoin_network":
        return round(_ratio(i["transfer_volume_usd"], i["supply_usd"]), 4)
    if rule == "market_data_feed":
        return round(i["symbols_covered"] / max(i["latency_ms"], 1.0), 4)
    if rule == "market_data_pro":
        return round(i["pro_fields"] * i["venue_count"], 4)
    if rule == "reference_rates":
        return _spread(i["reference_bps"], i["spot_bps"])
    if rule == "indexes":
        return round(i["constituents"] * i["rebalance_freq_per_year"], 4)
    if rule == "realized_metrics":
        return round(i["realized_cap_usd"] / max(i["volume_usd"], 1.0) * 100, 4)
    if rule == "supply_metrics":
        return round(_ratio(i["issuance_usd"], i["circulating_usd"]), 4)
    if rule == "mining_validator":
        return round(i["validator_uptime_pct"] * i["active_validators"] / 100, 4)
    if rule == "fee_metrics":
        return round(_ratio(i["fees_burned_usd"], i["fees_total_usd"]), 4)
    if rule == "activity_metrics":
        return round(i["daily_active_addresses"] * i["tx_per_address"], 4)
    if rule == "custom_metric_workbench":
        return round(i["saved_metrics"] * i["formula_complexity"], 4)
    if rule == "community_charts_api":
        return round(i["chart_calls_24h"] / max(i["unique_users"], 1.0), 4)
    if rule == "market_network_join":
        return _weighted((i["market_match_pct"], 0.6), (i["network_match_pct"], 0.4))
    if rule == "data_quality_methodologies":
        return round(i["methodology_score"] * i["documented_sources"], 4)
    if rule == "historical_research_dataset":
        return round(i["years_depth"] * i["series_count"], 4)
    if rule == "institutional_apis":
        return round(i["endpoint_count"] * i["sla_uptime_pct"] / 100, 4)
    if rule == "cross_network_decision":
        return _weighted((i["btc_signal"], 0.34), (i["eth_signal"], 0.33), (i["alt_signal"], 0.33))
    if rule == "institutional_trade_data":
        return round(i["block_trade_usd"] / 1e6, 4)
    if rule == "open_book_data":
        pass
    if rule == "order_book_data":
        return round(i["bid_depth_usd"] + i["ask_depth_usd"], 4)
    if rule == "ohlcv_data":
        return round(_ratio(i["candles_present"], i["candles_expected"]), 4)
    if rule == "derivatives_data":
        return round(i["open_interest_usd"] / max(i["spot_volume_usd"], 1.0) * 100, 4)
    if rule == "open_interest_data":
        return round(i["oi_change_24h_pct"] * i["oi_usd"] / 1e9, 4)
    if rule == "funding_rate_data":
        return _spread(i["perp_funding_bps"], i["spot_implied_bps"])
    if rule == "index_data":
        return round(i["index_levels"] * i["rebalance_events_ytd"], 4)
    if rule == "reference_pricing":
        return round(abs(_spread(i["reference_price"], i["consensus_price"])), 4)
    if rule == "exchange_metadata":
        return round(i["exchange_count"] * i["metadata_fields"], 4)
    if rule == "asset_metadata":
        return round(_ratio(i["fields_populated"], i["fields_required"]), 4)
    if rule == "historical_market_archive":
        return round(i["archive_tb"] * i["retention_years"], 4)
    if rule == "real_time_streams":
        return round(i["messages_per_sec"] * i["active_streams"], 4)
    if rule == "market_aggregates":
        return round(i["aggregate_volume_usd"] / 1e9, 4)
    if rule == "liquidity_analytics":
        return _weighted((i["depth_score"], 0.5), (i["turnover_score"], 0.5))
    if rule == "volatility_analytics":
        return round(i["realized_vol_pct"] * i["lookback_days"] ** 0.5, 4)
    if rule == "market_cap_supply":
        return round(_ratio(i["market_cap_usd"], i["circulating_supply_units"], scale=1.0), 4)
    if rule == "etf_etp_data":
        return round(i["net_flow_usd"] / 1e6, 4)
    if rule == "api_coverage_registry":
        return round(_ratio(i["endpoints_implemented"], i["endpoints_catalogued"]), 4)
    if rule == "data_quality_normalization":
        return _weighted((i["normalization_score"], 0.6), (i["outlier_rejection_pct"], 0.4))
    raise KeyError(rule)
