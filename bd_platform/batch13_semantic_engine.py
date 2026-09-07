"""Batch13 (601–650) capability-specific semantic transforms for operational intelligence shared core."""

from __future__ import annotations

from typing import Any, Callable

from bd_platform.batch_semantic_primitives import ratio as _ratio, semantic_inputs as _inputs, spread as _spread, weighted as _weighted

TransformFn = Callable[[dict[str, float], str], dict[str, Any]]

def _cross_chain_liquidity_flow(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['cross_chain_flow_usd_24h'], i['bridges_monitored']), 4)
    return {
        "cross_chain_liquidity_flow": primary,
        "cross_chain_flow_usd_24h": i["cross_chain_flow_usd_24h"],
        "bridges_monitored": i["bridges_monitored"],
        "chain_pairs": i["chain_pairs"],
        "symbol_focus": symbol.upper(),
    }

def _custom_ratio_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['ratio_numerator'], i['ratio_denominator'])
    return {
        "custom_ratio_engine": primary,
        "ratio_numerator": i["ratio_numerator"],
        "ratio_denominator": i["ratio_denominator"],
        "custom_ratio_count": i["custom_ratio_count"],
        "symbol_focus": symbol.upper(),
    }

def _dev_health_score(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['active_contributors'], 0.5), (i['repo_commits_90d'], 0.3), (i['issue_resolution_days'], 0.2))
    return {
        "dev_health_score": primary,
        "active_contributors": i["active_contributors"],
        "repo_commits_90d": i["repo_commits_90d"],
        "issue_resolution_days": i["issue_resolution_days"],
        "symbol_focus": symbol.upper(),
    }

def _developer_wallet_tracker(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['dev_wallets_tracked'], i['transfer_events_24h']), 4)
    return {
        "developer_wallet_tracker": primary,
        "dev_wallets_tracked": i["dev_wallets_tracked"],
        "commit_velocity_30d": i["commit_velocity_30d"],
        "transfer_events_24h": i["transfer_events_24h"],
        "symbol_focus": symbol.upper(),
    }

def _dex_liquidity_listener(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['dex_pool_tvl_usd'], i['liquidity_delta_pct']), 4)
    return {
        "dex_liquidity_listener": primary,
        "dex_pool_tvl_usd": i["dex_pool_tvl_usd"],
        "pool_count": i["pool_count"],
        "liquidity_delta_pct": i["liquidity_delta_pct"],
        "symbol_focus": symbol.upper(),
    }

def _end_to_end_decision_traceability(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['trace_steps'], 0.5), (i['provenance_links'], 0.3), (i['decision_chain_depth'], 0.2))
    return {
        "end_to_end_decision_traceability": primary,
        "trace_steps": i["trace_steps"],
        "provenance_links": i["provenance_links"],
        "decision_chain_depth": i["decision_chain_depth"],
        "symbol_focus": symbol.upper(),
    }

def _execution_latency_monitor(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['p50_latency_ms'], i['execution_nodes']), 4)
    return {
        "execution_latency_monitor": primary,
        "p50_latency_ms": i["p50_latency_ms"],
        "p99_latency_ms": i["p99_latency_ms"],
        "execution_nodes": i["execution_nodes"],
        "symbol_focus": symbol.upper(),
    }

def _financial_health_scoring(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['liquidity_score'], 0.5), (i['revenue_runway_months'], 0.3), (i['debt_ratio_pct'], 0.2))
    return {
        "financial_health_scoring": primary,
        "liquidity_score": i["liquidity_score"],
        "revenue_runway_months": i["revenue_runway_months"],
        "debt_ratio_pct": i["debt_ratio_pct"],
        "symbol_focus": symbol.upper(),
    }

def _funding_arbitrage_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['long_funding_bps'], i['arb_spread_bps']), 4)
    return {
        "funding_arbitrage_engine": primary,
        "long_funding_bps": i["long_funding_bps"],
        "short_funding_bps": i["short_funding_bps"],
        "arb_spread_bps": i["arb_spread_bps"],
        "symbol_focus": symbol.upper(),
    }

def _funding_rate_heatmap_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['heatmap_cells'], i['min_funding_bps']), 4)
    return {
        "funding_rate_heatmap_engine": primary,
        "heatmap_cells": i["heatmap_cells"],
        "max_funding_bps": i["max_funding_bps"],
        "min_funding_bps": i["min_funding_bps"],
        "symbol_focus": symbol.upper(),
    }

def _funding_rate_listener(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['funding_rate_bps'], i['alert_latency_sec']), 4)
    return {
        "funding_rate_listener": primary,
        "funding_rate_bps": i["funding_rate_bps"],
        "venues_monitored": i["venues_monitored"],
        "alert_latency_sec": i["alert_latency_sec"],
        "symbol_focus": symbol.upper(),
    }

def _gas_cost_predictor(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['gas_gwei_predicted'], i['base_fee_gwei']), 4)
    return {
        "gas_cost_predictor": primary,
        "gas_gwei_predicted": i["gas_gwei_predicted"],
        "mempool_pending": i["mempool_pending"],
        "base_fee_gwei": i["base_fee_gwei"],
        "symbol_focus": symbol.upper(),
    }

def _governance_sentiment_monitor(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['proposals_30d'], i['governance_sentiment']), 4)
    return {
        "governance_sentiment_monitor": primary,
        "proposals_30d": i["proposals_30d"],
        "vote_participation_pct": i["vote_participation_pct"],
        "governance_sentiment": i["governance_sentiment"],
        "symbol_focus": symbol.upper(),
    }

def _institutional_dashboard(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['dashboard_widgets'], 0.5), (i['data_feeds_live'], 0.3), (i['refresh_sec'], 0.2))
    return {
        "institutional_dashboard": primary,
        "dashboard_widgets": i["dashboard_widgets"],
        "data_feeds_live": i["data_feeds_live"],
        "refresh_sec": i["refresh_sec"],
        "symbol_focus": symbol.upper(),
    }

def _liquidation_screener(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['liquidation_usd_24h'], i['at_risk_positions']), 4)
    return {
        "liquidation_screener": primary,
        "liquidation_usd_24h": i["liquidation_usd_24h"],
        "at_risk_positions": i["at_risk_positions"],
        "screener_hits": i["screener_hits"],
        "symbol_focus": symbol.upper(),
    }

def _liquidity_full_fill_feasibility(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['fill_probability_pct'], i['slippage_bps']), 4)
    return {
        "liquidity_full_fill_feasibility": primary,
        "fill_probability_pct": i["fill_probability_pct"],
        "slippage_bps": i["slippage_bps"],
        "depth_usd": i["depth_usd"],
        "symbol_focus": symbol.upper(),
    }

def _low_latency_execution_node(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['orders_routed'], i['node_uptime_pct']), 4)
    return {
        "low_latency_execution_node": primary,
        "orders_routed": i["orders_routed"],
        "fill_rate_pct": i["fill_rate_pct"],
        "node_uptime_pct": i["node_uptime_pct"],
        "symbol_focus": symbol.upper(),
    }

def _market_data_drift_monitoring(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['drift_events_24h'], 0.5), (i['features_monitored'], 0.3), (i['baseline_deviation_pct'], 0.2))
    return {
        "market_data_drift_monitoring": primary,
        "drift_events_24h": i["drift_events_24h"],
        "features_monitored": i["features_monitored"],
        "baseline_deviation_pct": i["baseline_deviation_pct"],
        "symbol_focus": symbol.upper(),
    }

def _miner_flow_monitor(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['miner_outflow_btc'], i['hash_rate_eh']), 4)
    return {
        "miner_flow_monitor": primary,
        "miner_outflow_btc": i["miner_outflow_btc"],
        "active_pools": i["active_pools"],
        "hash_rate_eh": i["hash_rate_eh"],
        "symbol_focus": symbol.upper(),
    }

def _mtf_core_logic(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['timeframes_active'], i['signal_consensus']), 4)
    return {
        "mtf_core_logic": primary,
        "timeframes_active": i["timeframes_active"],
        "alignment_score": i["alignment_score"],
        "signal_consensus": i["signal_consensus"],
        "symbol_focus": symbol.upper(),
    }

def _multi_tier_data_storage(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['hot_gb'], i['cold_tb']), 4)
    return {
        "multi_tier_data_storage": primary,
        "hot_gb": i["hot_gb"],
        "warm_tb": i["warm_tb"],
        "cold_tb": i["cold_tb"],
        "symbol_focus": symbol.upper(),
    }

def _pattern_recognition_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['patterns_detected'], 0.5), (i['confidence_pct'], 0.3), (i['lookback_bars'], 0.2))
    return {
        "pattern_recognition_engine": primary,
        "patterns_detected": i["patterns_detected"],
        "confidence_pct": i["confidence_pct"],
        "lookback_bars": i["lookback_bars"],
        "symbol_focus": symbol.upper(),
    }

def _prediction_trend_analyzer(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['prediction_drift_score'], 0.5), (i['trend_accuracy_pct'], 0.3), (i['samples_30d'], 0.2))
    return {
        "prediction_trend_analyzer": primary,
        "prediction_drift_score": i["prediction_drift_score"],
        "trend_accuracy_pct": i["trend_accuracy_pct"],
        "samples_30d": i["samples_30d"],
        "symbol_focus": symbol.upper(),
    }

def _rust_execution_module(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['rust_modules_active'], i['memory_mb']), 4)
    return {
        "rust_execution_module": primary,
        "rust_modules_active": i["rust_modules_active"],
        "throughput_ops_sec": i["throughput_ops_sec"],
        "memory_mb": i["memory_mb"],
        "symbol_focus": symbol.upper(),
    }

def _spread_calculation_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['bid_spread_bps'], i['ask_spread_bps'])
    return {
        "spread_calculation_engine": primary,
        "bid_spread_bps": i["bid_spread_bps"],
        "ask_spread_bps": i["ask_spread_bps"],
        "cross_venue_spread_bps": i["cross_venue_spread_bps"],
        "symbol_focus": symbol.upper(),
    }

def _token_unlock_forecaster(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['unlock_usd_30d'], i['cliff_events']), 4)
    return {
        "token_unlock_forecaster": primary,
        "unlock_usd_30d": i["unlock_usd_30d"],
        "cliff_events": i["cliff_events"],
        "vesting_remaining_pct": i["vesting_remaining_pct"],
        "symbol_focus": symbol.upper(),
    }

def _trend_metric_collector(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['trend_metrics_collected'], i['coverage_pct']), 4)
    return {
        "trend_metric_collector": primary,
        "trend_metrics_collected": i["trend_metrics_collected"],
        "anomaly_flags_24h": i["anomaly_flags_24h"],
        "coverage_pct": i["coverage_pct"],
        "symbol_focus": symbol.upper(),
    }

def _unified_arbitrage_opportunity_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['opportunities_found'], i['net_edge_bps']), 4)
    return {
        "unified_arbitrage_opportunity_engine": primary,
        "opportunities_found": i["opportunities_found"],
        "net_edge_bps": i["net_edge_bps"],
        "venues_scanned": i["venues_scanned"],
        "symbol_focus": symbol.upper(),
    }

def _viral_intelligence_distribution_loop(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['share_velocity'], 0.5), (i['referral_conversions'], 0.3), (i['loop_completion_pct'], 0.2))
    return {
        "viral_intelligence_distribution_loop": primary,
        "share_velocity": i["share_velocity"],
        "referral_conversions": i["referral_conversions"],
        "loop_completion_pct": i["loop_completion_pct"],
        "symbol_focus": symbol.upper(),
    }

def _visual_transaction_graph(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['graph_nodes'], i['flow_depth_hops']), 4)
    return {
        "visual_transaction_graph": primary,
        "graph_nodes": i["graph_nodes"],
        "graph_edges": i["graph_edges"],
        "flow_depth_hops": i["flow_depth_hops"],
        "symbol_focus": symbol.upper(),
    }

def _yield_arbitrage_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['yield_spread_bps'], i['routes_evaluated'])
    return {
        "yield_arbitrage_engine": primary,
        "yield_spread_bps": i["yield_spread_bps"],
        "routes_evaluated": i["routes_evaluated"],
        "capital_usd": i["capital_usd"],
        "symbol_focus": symbol.upper(),
    }

def _yield_delta_listener(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['yield_delta_bps'], i['delta_velocity']), 4)
    return {
        "yield_delta_listener": primary,
        "yield_delta_bps": i["yield_delta_bps"],
        "pools_tracked": i["pools_tracked"],
        "delta_velocity": i["delta_velocity"],
        "symbol_focus": symbol.upper(),
    }

def _yield_optimization_module(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['optimized_yield_pct'], i['rebalance_events']), 4)
    return {
        "yield_optimization_module": primary,
        "optimized_yield_pct": i["optimized_yield_pct"],
        "baseline_yield_pct": i["baseline_yield_pct"],
        "rebalance_events": i["rebalance_events"],
        "symbol_focus": symbol.upper(),
    }


CAPABILITY_SEMANTIC_SPECS: dict[int, dict[str, Any]] = {
    601: {"rule": "visual_transaction_graph", "defaults": {'graph_nodes': 420, 'graph_edges': 1850, 'flow_depth_hops': 6}, "feature": 'Visual_Transaction_Graph'},
    602: {"rule": "developer_wallet_tracker", "defaults": {'dev_wallets_tracked': 48, 'commit_velocity_30d': 126, 'transfer_events_24h': 38}, "feature": 'Developer_Wallet_Tracker'},
    603: {"rule": "miner_flow_monitor", "defaults": {'miner_outflow_btc': 820.5, 'active_pools': 14, 'hash_rate_eh': 612.0}, "feature": 'Miner_Flow_Monitor'},
    604: {"rule": "token_unlock_forecaster", "defaults": {'unlock_usd_30d': 125000000.0, 'cliff_events': 8, 'vesting_remaining_pct': 42.0}, "feature": 'Token_Unlock_Forecaster'},
    605: {"rule": "governance_sentiment_monitor", "defaults": {'proposals_30d': 12, 'vote_participation_pct': 68.5, 'governance_sentiment': 0.62}, "feature": 'Governance_Sentiment_Monitor'},
    606: {"rule": "dev_health_score", "defaults": {'active_contributors': 86, 'repo_commits_90d': 420, 'issue_resolution_days': 4.2}, "feature": 'Dev_Health_Score'},
    607: {"rule": "financial_health_scoring", "defaults": {'liquidity_score': 74.0, 'revenue_runway_months': 18.0, 'debt_ratio_pct': 22.0}, "feature": 'Financial_Health_Scoring'},
    608: {"rule": "custom_ratio_engine", "defaults": {'ratio_numerator': 1.42, 'ratio_denominator': 0.98, 'custom_ratio_count': 12}, "feature": 'Custom_Ratio_Engine'},
    609: {"rule": "funding_rate_listener", "defaults": {'funding_rate_bps': 8.5, 'venues_monitored': 16, 'alert_latency_sec': 12}, "feature": 'Funding_Rate_Listener'},
    610: {"rule": "funding_arbitrage_engine", "defaults": {'long_funding_bps': 12.4, 'short_funding_bps': -3.2, 'arb_spread_bps': 15.6}, "feature": 'Funding_Arbitrage_Engine'},
    611: {"rule": "funding_rate_heatmap_engine", "defaults": {'heatmap_cells': 240, 'max_funding_bps': 18.2, 'min_funding_bps': -6.4}, "feature": 'Funding_Rate_Heatmap_Engine'},
    612: {"rule": "spread_calculation_engine", "defaults": {'bid_spread_bps': 4.2, 'ask_spread_bps': 4.8, 'cross_venue_spread_bps': 9.1}, "feature": 'Spread_Calculation_Engine'},
    613: {"rule": "liquidation_screener", "defaults": {'liquidation_usd_24h': 85000000.0, 'at_risk_positions': 420, 'screener_hits': 18}, "feature": 'Liquidation_Screener'},
    614: {"rule": "dex_liquidity_listener", "defaults": {'dex_pool_tvl_usd': 420000000.0, 'pool_count': 86, 'liquidity_delta_pct': 3.4}, "feature": 'DEX_Liquidity_Listener'},
    615: {"rule": "gas_cost_predictor", "defaults": {'gas_gwei_predicted': 42.0, 'mempool_pending': 125000, 'base_fee_gwei': 28.5}, "feature": 'Gas_Cost_Predictor'},
    616: {"rule": "yield_delta_listener", "defaults": {'yield_delta_bps': 18.0, 'pools_tracked': 64, 'delta_velocity': 2.4}, "feature": 'Yield_Delta_Listener'},
    617: {"rule": "yield_arbitrage_engine", "defaults": {'yield_spread_bps': 42.0, 'routes_evaluated': 128, 'capital_usd': 2500000.0}, "feature": 'Yield_Arbitrage_Engine'},
    618: {"rule": "yield_optimization_module", "defaults": {'optimized_yield_pct': 8.4, 'baseline_yield_pct': 6.2, 'rebalance_events': 6}, "feature": 'Yield_Optimization_Module'},
    619: {"rule": "trend_metric_collector", "defaults": {'trend_metrics_collected': 420, 'anomaly_flags_24h': 9, 'coverage_pct': 92.0}, "feature": 'Trend_Metric_Collector'},
    620: {"rule": "mtf_core_logic", "defaults": {'timeframes_active': 6, 'alignment_score': 0.78, 'signal_consensus': 0.64}, "feature": 'MTF_Core_Logic'},
    621: {"rule": "pattern_recognition_engine", "defaults": {'patterns_detected': 24, 'confidence_pct': 72.0, 'lookback_bars': 240}, "feature": 'Pattern_Recognition_Engine'},
    622: {"rule": "prediction_trend_analyzer", "defaults": {'prediction_drift_score': 0.18, 'trend_accuracy_pct': 61.0, 'samples_30d': 420}, "feature": 'Prediction_Trend_Analyzer'},
    623: {"rule": "execution_latency_monitor", "defaults": {'p50_latency_ms': 18.0, 'p99_latency_ms': 86.0, 'execution_nodes': 8}, "feature": 'Execution_Latency_Monitor'},
    624: {"rule": "low_latency_execution_node", "defaults": {'orders_routed': 1250, 'fill_rate_pct': 94.0, 'node_uptime_pct': 99.6}, "feature": 'Low_Latency_Execution_Node'},
    625: {"rule": "rust_execution_module", "defaults": {'rust_modules_active': 12, 'throughput_ops_sec': 42000, 'memory_mb': 256.0}, "feature": 'Rust_Execution_Module'},
    626: {"rule": "institutional_dashboard", "defaults": {'dashboard_widgets': 18, 'data_feeds_live': 42, 'refresh_sec': 5}, "feature": 'Institutional_Dashboard'},
    628: {"rule": "viral_intelligence_distribution_loop", "defaults": {'share_velocity': 420.0, 'referral_conversions': 86, 'loop_completion_pct': 38.0}, "feature": 'Viral_Intelligence_Distribution_Loop'},
    632: {"rule": "multi_tier_data_storage", "defaults": {'hot_gb': 420.0, 'warm_tb': 12.0, 'cold_tb': 86.0}, "feature": 'Multi-Tier Data Storage'},
    633: {"rule": "cross_chain_liquidity_flow", "defaults": {'cross_chain_flow_usd_24h': 125000000.0, 'bridges_monitored': 18, 'chain_pairs': 42}, "feature": 'Cross-Chain Liquidity Flow'},
    634: {"rule": "liquidity_full_fill_feasibility", "defaults": {'fill_probability_pct': 88.0, 'slippage_bps': 12.0, 'depth_usd': 4200000.0}, "feature": 'Liquidity/Full-Fill Feasibility'},
    635: {"rule": "unified_arbitrage_opportunity_engine", "defaults": {'opportunities_found': 24, 'net_edge_bps': 18.0, 'venues_scanned': 16}, "feature": 'Unified Arbitrage Opportunity Engine'},
    636: {"rule": "market_data_drift_monitoring", "defaults": {'drift_events_24h': 6, 'features_monitored': 420, 'baseline_deviation_pct': 2.8}, "feature": 'Market/Data Drift Monitoring'},
    643: {"rule": "end_to_end_decision_traceability", "defaults": {'trace_steps': 12, 'provenance_links': 28, 'decision_chain_depth': 6}, "feature": 'End-to-End Decision Traceability'},
}


RULES: dict[str, TransformFn] = {
    "cross_chain_liquidity_flow": _cross_chain_liquidity_flow,
    "custom_ratio_engine": _custom_ratio_engine,
    "dev_health_score": _dev_health_score,
    "developer_wallet_tracker": _developer_wallet_tracker,
    "dex_liquidity_listener": _dex_liquidity_listener,
    "end_to_end_decision_traceability": _end_to_end_decision_traceability,
    "execution_latency_monitor": _execution_latency_monitor,
    "financial_health_scoring": _financial_health_scoring,
    "funding_arbitrage_engine": _funding_arbitrage_engine,
    "funding_rate_heatmap_engine": _funding_rate_heatmap_engine,
    "funding_rate_listener": _funding_rate_listener,
    "gas_cost_predictor": _gas_cost_predictor,
    "governance_sentiment_monitor": _governance_sentiment_monitor,
    "institutional_dashboard": _institutional_dashboard,
    "liquidation_screener": _liquidation_screener,
    "liquidity_full_fill_feasibility": _liquidity_full_fill_feasibility,
    "low_latency_execution_node": _low_latency_execution_node,
    "market_data_drift_monitoring": _market_data_drift_monitoring,
    "miner_flow_monitor": _miner_flow_monitor,
    "mtf_core_logic": _mtf_core_logic,
    "multi_tier_data_storage": _multi_tier_data_storage,
    "pattern_recognition_engine": _pattern_recognition_engine,
    "prediction_trend_analyzer": _prediction_trend_analyzer,
    "rust_execution_module": _rust_execution_module,
    "spread_calculation_engine": _spread_calculation_engine,
    "token_unlock_forecaster": _token_unlock_forecaster,
    "trend_metric_collector": _trend_metric_collector,
    "unified_arbitrage_opportunity_engine": _unified_arbitrage_opportunity_engine,
    "viral_intelligence_distribution_loop": _viral_intelligence_distribution_loop,
    "visual_transaction_graph": _visual_transaction_graph,
    "yield_arbitrage_engine": _yield_arbitrage_engine,
    "yield_delta_listener": _yield_delta_listener,
    "yield_optimization_module": _yield_optimization_module,
}


def compute_semantic_extra(cap_id: int, *, symbol: str, seed: dict[str, Any]) -> dict[str, Any]:
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    inputs = _inputs(seed, cap_id, spec["defaults"])
    transform = RULES[spec["rule"]]
    payload = transform(inputs, symbol.upper())
    payload["feature"] = spec["feature"]
    payload["semantic_rule"] = spec["rule"]
    payload["attribution"] = "BLACKDARK batch13 operational intelligence layer"
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

