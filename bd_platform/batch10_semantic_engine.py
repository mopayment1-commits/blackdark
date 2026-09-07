"""Batch10 (451–500) capability-specific semantic transforms for market/network/risk shared core."""

from __future__ import annotations

from typing import Any, Callable

TransformFn = Callable[[dict[str, float], str], dict[str, Any]]


from bd_platform.batch_semantic_primitives import ratio as _ratio, semantic_inputs as _inputs, spread as _spread, weighted as _weighted


def _protocol_dominance(i: dict[str, float], symbol: str) -> dict[str, Any]:
    share = _ratio(i["protocol_tvl_usd"], i["sector_tvl_usd"])
    return {
        "protocol_dominance": round(share + i["market_share_delta_pct"], 4),
        "dominance_share_pct": share,
        "market_share_delta_pct": i["market_share_delta_pct"],
        "symbol_focus": symbol.upper(),
    }


def _aave_multi_chain(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "aave_multi_chain": round(i["active_chains"] * i["avg_supply_usd"] / 1e9, 4),
        "active_chains": i["active_chains"],
        "avg_supply_busd": round(i["avg_supply_usd"] / 1e9, 2),
    }


def _risk_curation(i: dict[str, float], symbol: str) -> dict[str, Any]:
    score = _weighted((i["audit_score"], 0.4), (100 - i["exploit_score"], 0.35), (i["liquidity_score"], 0.25))
    return {
        "risk_curation": score,
        "curated_risk_score": score,
        "watchlist_protocols": i["watchlist_protocols"],
    }


def _capital_protection(i: dict[str, float], symbol: str) -> dict[str, Any]:
    buffer = i["protection_buffer_pct"] - i["drawdown_pct"]
    return {
        "capital_protection": round(buffer, 4),
        "protection_buffer_pct": i["protection_buffer_pct"],
        "drawdown_pct": i["drawdown_pct"],
    }


def _stress_testing(i: dict[str, float], symbol: str) -> dict[str, Any]:
    loss = i["shock_pct"] * i["exposure_usd"] / 1e6
    return {
        "stress_testing": round(loss, 4),
        "scenario_loss_musd": round(loss, 2),
        "shock_pct": i["shock_pct"],
    }


def _cross_protocol_contagion(i: dict[str, float], symbol: str) -> dict[str, Any]:
    index = i["shared_collateral_pct"] * i["correlation_coeff"] * 100
    return {
        "cross_protocol_contagion": round(index, 4),
        "contagion_index": round(index, 2),
        "shared_collateral_pct": i["shared_collateral_pct"],
    }


def _protocol_risk_passport(i: dict[str, float], symbol: str) -> dict[str, Any]:
    passport = _weighted((i["audit_score"], 0.5), (i["governance_score"], 0.3), (100 - i["exploit_history"], 0.2))
    return {
        "protocol_risk_passport": passport,
        "passport_score": passport,
        "governance_score": i["governance_score"],
    }


def _network_data_pro(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "network_data_pro": round(i["node_coverage_pct"] * i["metric_families"], 4),
        "node_coverage_pct": i["node_coverage_pct"],
        "metric_families": i["metric_families"],
    }


def _atlas_blockchain_search(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "atlas_blockchain_search": round(i["indexed_entities"] / max(i["query_latency_ms"], 1.0), 4),
        "indexed_entities": i["indexed_entities"],
        "query_latency_ms": i["query_latency_ms"],
    }


def _address_balance_search(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "address_balance_search": round(i["addresses_indexed"] / max(i["lookup_ms"], 1.0), 4),
        "addresses_indexed": i["addresses_indexed"],
        "lookup_ms": i["lookup_ms"],
    }


def _transaction_search(i: dict[str, float], symbol: str) -> dict[str, Any]:
    throughput = i["tx_indexed"] / max(i["search_ms"], 1.0)
    return {
        "transaction_search": round(throughput, 4),
        "tx_throughput_per_ms": round(throughput, 2),
        "tx_indexed": i["tx_indexed"],
    }


def _block_search(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "block_search": round(i["blocks_indexed"] / max(i["height_span"], 1.0), 4),
        "blocks_indexed": i["blocks_indexed"],
        "height_span": i["height_span"],
    }


def _balance_updates(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "balance_updates": round(i["updates_per_min"] * i["wallets_tracked"], 4),
        "updates_per_min": i["updates_per_min"],
        "wallets_tracked": i["wallets_tracked"],
    }


def _stablecoin_network(i: dict[str, float], symbol: str) -> dict[str, Any]:
    velocity = _ratio(i["transfer_volume_usd"], i["supply_usd"])
    return {
        "stablecoin_network_metrics": round(velocity, 4),
        "velocity_pct": velocity,
        "supply_usd_b": round(i["supply_usd"] / 1e9, 2),
    }


def _market_data_feed(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "market_data_feed": round(i["symbols_covered"] / max(i["latency_ms"], 1.0), 4),
        "symbols_covered": i["symbols_covered"],
        "latency_ms": i["latency_ms"],
    }


def _market_data_pro(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "market_data_pro": round(i["pro_fields"] * i["venue_count"], 4),
        "pro_fields": i["pro_fields"],
        "venue_count": i["venue_count"],
    }


def _reference_rates(i: dict[str, float], symbol: str) -> dict[str, Any]:
    spread = _spread(i["reference_bps"], i["spot_bps"])
    return {
        "reference_rates": spread,
        "reference_spread_bps": spread,
        "spot_bps": i["spot_bps"],
    }


def _indexes(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "indexes": round(i["constituents"] * i["rebalance_freq_per_year"], 4),
        "constituents": i["constituents"],
        "rebalance_freq_per_year": i["rebalance_freq_per_year"],
    }


def _realized_metrics(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "realized_metrics": round(i["realized_cap_usd"] / max(i["volume_usd"], 1.0) * 100, 4),
        "realized_cap_musd": round(i["realized_cap_usd"] / 1e6, 2),
        "volume_musd": round(i["volume_usd"] / 1e6, 2),
    }


def _supply_metrics(i: dict[str, float], symbol: str) -> dict[str, Any]:
    inflation = _ratio(i["issuance_usd"], i["circulating_usd"])
    return {
        "supply_metrics": round(inflation, 4),
        "inflation_pct": inflation,
        "circulating_musd": round(i["circulating_usd"] / 1e6, 2),
    }


def _mining_validator(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "mining_validator_metrics": round(i["validator_uptime_pct"] * i["active_validators"] / 100, 4),
        "validator_uptime_pct": i["validator_uptime_pct"],
        "active_validators": i["active_validators"],
    }


def _fee_metrics(i: dict[str, float], symbol: str) -> dict[str, Any]:
    burn_ratio = _ratio(i["fees_burned_usd"], i["fees_total_usd"])
    return {
        "fee_metrics": round(burn_ratio, 4),
        "fee_burn_pct": burn_ratio,
        "fees_total_musd": round(i["fees_total_usd"] / 1e6, 2),
    }


def _activity_metrics(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "activity_metrics": round(i["daily_active_addresses"] * i["tx_per_address"], 4),
        "daily_active_addresses": i["daily_active_addresses"],
        "tx_per_address": i["tx_per_address"],
    }


def _custom_metric_workbench(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "custom_metric_workbench": round(i["saved_metrics"] * i["formula_complexity"], 4),
        "saved_metrics": i["saved_metrics"],
        "formula_complexity": i["formula_complexity"],
    }


def _community_charts_api(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "community_charts_api": round(i["chart_calls_24h"] / max(i["unique_users"], 1.0), 4),
        "chart_calls_24h": i["chart_calls_24h"],
        "unique_users": i["unique_users"],
    }


def _market_network_join(i: dict[str, float], symbol: str) -> dict[str, Any]:
    join_quality = _weighted((i["market_match_pct"], 0.6), (i["network_match_pct"], 0.4))
    return {
        "market_network_join": join_quality,
        "join_quality_score": join_quality,
        "market_match_pct": i["market_match_pct"],
    }


def _data_quality_methodologies(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "data_quality_methodologies": round(i["methodology_score"] * i["documented_sources"], 4),
        "methodology_score": i["methodology_score"],
        "documented_sources": i["documented_sources"],
    }


def _historical_research_dataset(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "historical_research_dataset": round(i["years_depth"] * i["series_count"], 4),
        "years_depth": i["years_depth"],
        "series_count": i["series_count"],
    }


def _institutional_apis(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "institutional_apis": round(i["endpoint_count"] * i["sla_uptime_pct"] / 100, 4),
        "endpoint_count": i["endpoint_count"],
        "sla_uptime_pct": i["sla_uptime_pct"],
    }


def _cross_network_decision(i: dict[str, float], symbol: str) -> dict[str, Any]:
    score = _weighted((i["btc_signal"], 0.34), (i["eth_signal"], 0.33), (i["alt_signal"], 0.33))
    return {
        "cross_network_decision_intelligence": score,
        "network_fusion_score": score,
        "btc_signal": i["btc_signal"],
    }


def _institutional_trade_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "institutional_trade_data": round(i["block_trade_usd"] / 1e6, 4),
        "block_trade_musd": round(i["block_trade_usd"] / 1e6, 2),
        "trade_count_24h": i["trade_count_24h"],
    }


def _order_book_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "order_book_data": round(i["bid_depth_usd"] + i["ask_depth_usd"], 4),
        "total_depth_musd": round((i["bid_depth_usd"] + i["ask_depth_usd"]) / 1e6, 2),
        "spread_bps": i["spread_bps"],
    }


def _ohlcv_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    completeness = _ratio(i["candles_present"], i["candles_expected"])
    return {
        "ohlcv_data": round(completeness, 4),
        "candle_completeness_pct": completeness,
        "interval_minutes": i["interval_minutes"],
    }


def _derivatives_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "derivatives_data": round(i["open_interest_usd"] / max(i["spot_volume_usd"], 1.0) * 100, 4),
        "oi_to_spot_pct": _ratio(i["open_interest_usd"], i["spot_volume_usd"]),
        "contracts_tracked": i["contracts_tracked"],
    }


def _open_interest_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "open_interest_data": round(i["oi_change_24h_pct"] * i["oi_usd"] / 1e9, 4),
        "oi_change_24h_pct": i["oi_change_24h_pct"],
        "oi_usd_b": round(i["oi_usd"] / 1e9, 2),
    }


def _funding_rate_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    basis = _spread(i["perp_funding_bps"], i["spot_implied_bps"])
    return {
        "funding_rate_data": basis,
        "funding_basis_bps": basis,
        "perp_funding_bps": i["perp_funding_bps"],
    }


def _index_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "index_data": round(i["index_levels"] * i["rebalance_events_ytd"], 4),
        "index_levels": i["index_levels"],
        "rebalance_events_ytd": i["rebalance_events_ytd"],
    }


def _reference_pricing(i: dict[str, float], symbol: str) -> dict[str, Any]:
    deviation = abs(_spread(i["reference_price"], i["consensus_price"]))
    return {
        "reference_pricing": round(deviation, 4),
        "price_deviation": deviation,
        "consensus_price": i["consensus_price"],
    }


def _exchange_metadata(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "exchange_metadata": round(i["exchange_count"] * i["metadata_fields"], 4),
        "exchange_count": i["exchange_count"],
        "metadata_fields": i["metadata_fields"],
    }


def _asset_metadata(i: dict[str, float], symbol: str) -> dict[str, Any]:
    completeness = _ratio(i["fields_populated"], i["fields_required"])
    return {
        "asset_metadata": round(completeness, 4),
        "metadata_completeness_pct": completeness,
        "assets_catalogued": i["assets_catalogued"],
    }


def _historical_market_archive(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "historical_market_archive": round(i["archive_tb"] * i["retention_years"], 4),
        "archive_tb": i["archive_tb"],
        "retention_years": i["retention_years"],
    }


def _real_time_streams(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "real_time_streams": round(i["messages_per_sec"] * i["active_streams"], 4),
        "messages_per_sec": i["messages_per_sec"],
        "active_streams": i["active_streams"],
    }


def _market_aggregates(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "market_aggregates": round(i["aggregate_volume_usd"] / 1e9, 4),
        "aggregate_volume_busd": round(i["aggregate_volume_usd"] / 1e9, 2),
        "venue_count": i["venue_count"],
    }


def _liquidity_analytics(i: dict[str, float], symbol: str) -> dict[str, Any]:
    score = _weighted((i["depth_score"], 0.5), (i["turnover_score"], 0.5))
    return {
        "liquidity_analytics": score,
        "liquidity_score": score,
        "depth_score": i["depth_score"],
    }


def _volatility_analytics(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "volatility_analytics": round(i["realized_vol_pct"] * i["lookback_days"] ** 0.5, 4),
        "realized_vol_pct": i["realized_vol_pct"],
        "lookback_days": i["lookback_days"],
    }


def _market_cap_supply(i: dict[str, float], symbol: str) -> dict[str, Any]:
    ratio = _ratio(i["market_cap_usd"], i["circulating_supply_units"], scale=1.0)
    return {
        "market_cap_supply": round(ratio, 4),
        "mcap_per_unit": ratio,
        "circulating_supply_m": round(i["circulating_supply_units"] / 1e6, 2),
    }


def _etf_etp_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "etf_etp_data": round(i["net_flow_usd"] / 1e6, 4),
        "net_flow_musd": round(i["net_flow_usd"] / 1e6, 2),
        "products_tracked": i["products_tracked"],
    }


def _api_coverage_registry(i: dict[str, float], symbol: str) -> dict[str, Any]:
    coverage = _ratio(i["endpoints_implemented"], i["endpoints_catalogued"])
    return {
        "api_coverage_registry": round(coverage, 4),
        "coverage_pct": coverage,
        "endpoints_catalogued": i["endpoints_catalogued"],
    }


def _data_quality_normalization(i: dict[str, float], symbol: str) -> dict[str, Any]:
    score = _weighted((i["normalization_score"], 0.6), (i["outlier_rejection_pct"], 0.4))
    return {
        "data_quality_normalization": score,
        "normalization_score": score,
        "outlier_rejection_pct": i["outlier_rejection_pct"],
    }


RULES: dict[str, TransformFn] = {
    "protocol_dominance": _protocol_dominance,
    "aave_multi_chain": _aave_multi_chain,
    "risk_curation": _risk_curation,
    "capital_protection": _capital_protection,
    "stress_testing": _stress_testing,
    "cross_protocol_contagion": _cross_protocol_contagion,
    "protocol_risk_passport": _protocol_risk_passport,
    "network_data_pro": _network_data_pro,
    "atlas_blockchain_search": _atlas_blockchain_search,
    "address_balance_search": _address_balance_search,
    "transaction_search": _transaction_search,
    "block_search": _block_search,
    "balance_updates": _balance_updates,
    "stablecoin_network": _stablecoin_network,
    "market_data_feed": _market_data_feed,
    "market_data_pro": _market_data_pro,
    "reference_rates": _reference_rates,
    "indexes": _indexes,
    "realized_metrics": _realized_metrics,
    "supply_metrics": _supply_metrics,
    "mining_validator": _mining_validator,
    "fee_metrics": _fee_metrics,
    "activity_metrics": _activity_metrics,
    "custom_metric_workbench": _custom_metric_workbench,
    "community_charts_api": _community_charts_api,
    "market_network_join": _market_network_join,
    "data_quality_methodologies": _data_quality_methodologies,
    "historical_research_dataset": _historical_research_dataset,
    "institutional_apis": _institutional_apis,
    "cross_network_decision": _cross_network_decision,
    "institutional_trade_data": _institutional_trade_data,
    "order_book_data": _order_book_data,
    "ohlcv_data": _ohlcv_data,
    "derivatives_data": _derivatives_data,
    "open_interest_data": _open_interest_data,
    "funding_rate_data": _funding_rate_data,
    "index_data": _index_data,
    "reference_pricing": _reference_pricing,
    "exchange_metadata": _exchange_metadata,
    "asset_metadata": _asset_metadata,
    "historical_market_archive": _historical_market_archive,
    "real_time_streams": _real_time_streams,
    "market_aggregates": _market_aggregates,
    "liquidity_analytics": _liquidity_analytics,
    "volatility_analytics": _volatility_analytics,
    "market_cap_supply": _market_cap_supply,
    "etf_etp_data": _etf_etp_data,
    "api_coverage_registry": _api_coverage_registry,
    "data_quality_normalization": _data_quality_normalization,
}


CAPABILITY_SEMANTIC_SPECS: dict[int, dict[str, Any]] = {
    451: {"rule": "protocol_dominance", "defaults": {"protocol_tvl_usd": 2.8e9, "sector_tvl_usd": 12e9, "market_share_delta_pct": 0.4}, "feature": "Protocol Dominance"},
    452: {"rule": "aave_multi_chain", "defaults": {"active_chains": 8, "avg_supply_usd": 420e6}, "feature": "Aave Multi-Chain Analytics"},
    453: {"rule": "risk_curation", "defaults": {"audit_score": 84, "exploit_score": 18, "liquidity_score": 76, "watchlist_protocols": 12}, "feature": "Risk Curation"},
    454: {"rule": "capital_protection", "defaults": {"protection_buffer_pct": 15, "drawdown_pct": 6.5}, "feature": "Capital Protection Controls"},
    455: {"rule": "stress_testing", "defaults": {"shock_pct": 35, "exposure_usd": 125e6}, "feature": "Stress Testing"},
    456: {"rule": "cross_protocol_contagion", "defaults": {"shared_collateral_pct": 22, "correlation_coeff": 0.71}, "feature": "Cross-Protocol Contagion"},
    457: {"rule": "protocol_risk_passport", "defaults": {"audit_score": 88, "governance_score": 79, "exploit_history": 12}, "feature": "Protocol Risk Passport"},
    459: {"rule": "network_data_pro", "defaults": {"node_coverage_pct": 94, "metric_families": 18}, "feature": "Network Data Pro Metrics"},
    460: {"rule": "atlas_blockchain_search", "defaults": {"indexed_entities": 1250000, "query_latency_ms": 42}, "feature": "Atlas Blockchain Search"},
    461: {"rule": "address_balance_search", "defaults": {"addresses_indexed": 890000, "lookup_ms": 18}, "feature": "Address/Balance Search"},
    462: {"rule": "transaction_search", "defaults": {"tx_indexed": 45000000, "search_ms": 25}, "feature": "Transaction Search"},
    463: {"rule": "block_search", "defaults": {"blocks_indexed": 920000, "height_span": 850000}, "feature": "Block Search"},
    464: {"rule": "balance_updates", "defaults": {"updates_per_min": 340, "wallets_tracked": 12500}, "feature": "Balance Updates"},
    465: {"rule": "stablecoin_network", "defaults": {"transfer_volume_usd": 8.2e9, "supply_usd": 38e9}, "feature": "Stablecoin Network Metrics"},
    466: {"rule": "market_data_feed", "defaults": {"symbols_covered": 420, "latency_ms": 85}, "feature": "Market Data Feed"},
    467: {"rule": "market_data_pro", "defaults": {"pro_fields": 28, "venue_count": 16}, "feature": "Market Data Pro"},
    468: {"rule": "reference_rates", "defaults": {"reference_bps": 12.5, "spot_bps": 8.2}, "feature": "Reference Rates"},
    469: {"rule": "indexes", "defaults": {"constituents": 24, "rebalance_freq_per_year": 4}, "feature": "Indexes"},
    470: {"rule": "realized_metrics", "defaults": {"realized_cap_usd": 620e6, "volume_usd": 1.8e9}, "feature": "Realized Metrics"},
    471: {"rule": "supply_metrics", "defaults": {"issuance_usd": 42e6, "circulating_usd": 18e9}, "feature": "Supply Metrics"},
    472: {"rule": "mining_validator", "defaults": {"validator_uptime_pct": 99.2, "active_validators": 850000}, "feature": "Mining/Validator Metrics"},
    473: {"rule": "fee_metrics", "defaults": {"fees_burned_usd": 1.2e6, "fees_total_usd": 3.8e6}, "feature": "Fee Metrics"},
    474: {"rule": "activity_metrics", "defaults": {"daily_active_addresses": 980000, "tx_per_address": 2.1}, "feature": "Activity Metrics"},
    475: {"rule": "custom_metric_workbench", "defaults": {"saved_metrics": 36, "formula_complexity": 1.8}, "feature": "Custom Metric Workbench"},
    476: {"rule": "community_charts_api", "defaults": {"chart_calls_24h": 18500, "unique_users": 920}, "feature": "Community Charts/API"},
    477: {"rule": "market_network_join", "defaults": {"market_match_pct": 92, "network_match_pct": 88}, "feature": "Market + Network Join"},
    478: {"rule": "data_quality_methodologies", "defaults": {"methodology_score": 0.91, "documented_sources": 42}, "feature": "Data Quality Methodologies"},
    479: {"rule": "historical_research_dataset", "defaults": {"years_depth": 8, "series_count": 240}, "feature": "Historical Research Dataset"},
    480: {"rule": "institutional_apis", "defaults": {"endpoint_count": 64, "sla_uptime_pct": 99.5}, "feature": "Institutional APIs"},
    481: {"rule": "cross_network_decision", "defaults": {"btc_signal": 0.62, "eth_signal": 0.58, "alt_signal": 0.51}, "feature": "Cross-Network Decision Intelligence"},
    482: {"rule": "institutional_trade_data", "defaults": {"block_trade_usd": 125e6, "trade_count_24h": 420}, "feature": "Institutional Trade Data"},
    483: {"rule": "order_book_data", "defaults": {"bid_depth_usd": 8.5e6, "ask_depth_usd": 7.2e6, "spread_bps": 4.5}, "feature": "Order Book Data"},
    484: {"rule": "ohlcv_data", "defaults": {"candles_present": 2880, "candles_expected": 3000, "interval_minutes": 5}, "feature": "OHLCV Data"},
    485: {"rule": "derivatives_data", "defaults": {"open_interest_usd": 12e9, "spot_volume_usd": 28e9, "contracts_tracked": 180}, "feature": "Derivatives Data"},
    486: {"rule": "open_interest_data", "defaults": {"oi_change_24h_pct": 3.2, "oi_usd": 9.5e9}, "feature": "Open Interest Data"},
    487: {"rule": "funding_rate_data", "defaults": {"perp_funding_bps": 6.8, "spot_implied_bps": 4.1}, "feature": "Funding Rate Data"},
    488: {"rule": "index_data", "defaults": {"index_levels": 12, "rebalance_events_ytd": 18}, "feature": "Index Data"},
    489: {"rule": "reference_pricing", "defaults": {"reference_price": 64250.5, "consensus_price": 64248.0}, "feature": "Reference Pricing"},
    490: {"rule": "exchange_metadata", "defaults": {"exchange_count": 28, "metadata_fields": 14}, "feature": "Exchange Metadata"},
    491: {"rule": "asset_metadata", "defaults": {"fields_populated": 18, "fields_required": 20, "assets_catalogued": 850}, "feature": "Asset Metadata"},
    492: {"rule": "historical_market_archive", "defaults": {"archive_tb": 48, "retention_years": 10}, "feature": "Historical Market Archive"},
    493: {"rule": "real_time_streams", "defaults": {"messages_per_sec": 12500, "active_streams": 42}, "feature": "Real-Time Streams"},
    494: {"rule": "market_aggregates", "defaults": {"aggregate_volume_usd": 85e9, "venue_count": 22}, "feature": "Market Aggregates"},
    495: {"rule": "liquidity_analytics", "defaults": {"depth_score": 82, "turnover_score": 74}, "feature": "Liquidity Analytics"},
    496: {"rule": "volatility_analytics", "defaults": {"realized_vol_pct": 58, "lookback_days": 30}, "feature": "Volatility Analytics"},
    497: {"rule": "market_cap_supply", "defaults": {"market_cap_usd": 820e9, "circulating_supply_units": 19.6e6}, "feature": "Market Cap / Supply"},
    498: {"rule": "etf_etp_data", "defaults": {"net_flow_usd": 420e6, "products_tracked": 14}, "feature": "ETF / ETP Data"},
    499: {"rule": "api_coverage_registry", "defaults": {"endpoints_implemented": 156, "endpoints_catalogued": 180}, "feature": "API Coverage Registry"},
    500: {"rule": "data_quality_normalization", "defaults": {"normalization_score": 0.93, "outlier_rejection_pct": 2.4}, "feature": "Data Quality & Normalization"},
}


def compute_semantic_extra(cap_id: int, *, symbol: str, seed: dict[str, Any]) -> dict[str, Any]:
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    inputs = _inputs(seed, cap_id, spec["defaults"])
    transform = RULES[spec["rule"]]
    payload = transform(inputs, symbol.upper())
    payload["feature"] = spec["feature"]
    payload["semantic_rule"] = spec["rule"]
    payload["attribution"] = "BLACKDARK defi/yield intelligence layer"
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
