"""Independent reference oracles for Batch12 parameterized semantics (552–600).

Deliberately does NOT import bd_platform.batch12_semantic_engine RULES or compute_semantic_extra.
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
    "ai_agent_consultant": "ai_agent_consultant",
    "ai_digest_generator": "ai_digest_generator",
    "ai_quant_rating_engine": "ai_quant_rating_engine",
    "api_data_access": "api_data_access",
    "api_data_pipe": "api_data_pipe",
    "api_security_encryption": "api_security_encryption",
    "basis_intelligence": "basis_intelligence",
    "cross_asset_correlation": "cross_asset_correlation",
    "cross_market_decision_intelligence": "cross_market_decision_intelligence",
    "delta_neutral_calculator": "delta_neutral_calculator",
    "derivatives_regime_engine": "derivatives_regime_engine",
    "developer_sdk": "developer_sdk",
    "entity_tagging_system": "entity_tagging_system",
    "flexible_connector_microservice": "flexible_connector_microservice",
    "futures_volume": "futures_volume",
    "global_asset_tracker": "global_asset_tracker",
    "high_availability_architecture": "high_availability_architecture",
    "high_precision_backtesting": "high_precision_backtesting",
    "historical_data": "historical_data",
    "infrastructure_uptime_shield": "infrastructure_uptime_shield",
    "institutional_api_gateway": "institutional_api_gateway",
    "institutional_data_architecture": "institutional_data_architecture",
    "margin_risk_calculator": "margin_risk_calculator",
    "multi_account_sync": "multi_account_sync",
    "multi_indicator_workspace": "multi_indicator_workspace",
    "narrative_alert_system": "narrative_alert_system",
    "natural_language_interpreter": "natural_language_interpreter",
    "news_context": "news_context",
    "on_chain_balance_monitor": "on_chain_balance_monitor",
    "options_analytics": "options_analytics",
    "options_iv_surface": "options_iv_surface",
    "options_skew": "options_skew",
    "options_term_structure": "options_term_structure",
    "pro_developer_sandbox": "pro_developer_sandbox",
    "profitability_analyzer": "profitability_analyzer",
    "real_time_prices": "real_time_prices",
    "security_first_architecture": "security_first_architecture",
    "sentiment_analysis_engine": "sentiment_analysis_engine",
    "social_hype_analyzer": "social_hype_analyzer",
    "social_sentiment_engine": "social_sentiment_engine",
    "spot_market_data": "spot_market_data",
    "strategy_vetting_algorithm": "strategy_vetting_algorithm",
    "tradfi_context": "tradfi_context",
    "volatility_scoring_system": "volatility_scoring_system",
    "volatility_surface_analyzer": "volatility_surface_analyzer",
    "wallet_shadowing": "wallet_shadowing",
    "whale_clustering_engine": "whale_clustering_engine",
}


def independent_primary(rule: str, inputs: dict[str, float], symbol: str = "ETH") -> float:
    i = inputs
    if rule == "futures_volume":
        primary = round(_ratio(i['futures_volume_usd'], i['spot_volume_usd']), 4)
        return primary
    if rule == "basis_intelligence":
        primary = _spread(i['perp_price'], i['spot_price'])
        return primary
    if rule == "spot_market_data":
        primary = _weighted((i['tick_rate_hz'], 0.5), (i['symbols_covered'], 0.3), (100 - i['latency_ms'], 0.2))
        return primary
    if rule == "options_analytics":
        primary = round(i['contracts_tracked'] * i['greeks_fields'] * i['expiry_buckets'] / 100, 4)
        return primary
    if rule == "options_iv_surface":
        primary = round(_ratio(i['atm_iv_pct'], i['realized_vol_pct']), 4)
        return primary
    if rule == "options_skew":
        primary = _spread(i['put_iv_pct'], i['call_iv_pct'])
        return primary
    if rule == "options_term_structure":
        primary = _weighted((i['front_iv_pct'], 0.5), (i['back_iv_pct'], 0.3), (100 - i['tenor_days'], 0.2))
        return primary
    if rule == "tradfi_context":
        primary = round(_ratio(i['macro_signals'], i['risk_events_24h']), 4)
        return primary
    if rule == "multi_indicator_workspace":
        primary = round(i['indicators_active'] * i['panes_count'] * i['refresh_hz'] / 100, 4)
        return primary
    if rule == "real_time_prices":
        primary = round(i['updates_per_sec'] / max(i['latency_ms'], 1.0), 4)
        return primary
    if rule == "historical_data":
        primary = round(_ratio(i['bars_available'], i['bars_expected']), 4)
        return primary
    if rule == "api_data_access":
        primary = _weighted((i['endpoint_count'], 0.5), (i['sla_uptime_pct'], 0.3), (100 - i['p95_latency_ms'], 0.2))
        return primary
    if rule == "news_context":
        primary = round(i['articles_24h'] * i['sentiment_score'] * i['entity_tags'] / 100, 4)
        return primary
    if rule == "cross_asset_correlation":
        primary = round(abs(_spread(i['btc_correlation'], i['eth_correlation'])), 4)
        return primary
    if rule == "derivatives_regime_engine":
        primary = _weighted((i['trend_score'], 0.5), (i['vol_regime_score'], 0.3), (100 - i['funding_regime_score'], 0.2))
        return primary
    if rule == "cross_market_decision_intelligence":
        primary = _weighted((i['spot_signal'], 0.34), (i['perp_signal'], 0.33), (i['options_signal'], 0.33))
        return primary
    if rule == "security_first_architecture":
        primary = round(_ratio(i['controls_passed'], i['controls_total']), 4)
        return primary
    if rule == "api_security_encryption":
        primary = _weighted((i['tls_coverage_pct'], 0.5), (i['key_rotation_days'], 0.3), (100 - i['auth_strength_score'], 0.2))
        return primary
    if rule == "high_availability_architecture":
        primary = round(_ratio(i['healthy_nodes'], i['total_nodes']), 4)
        return primary
    if rule == "infrastructure_uptime_shield":
        primary = _weighted((i['uptime_pct'], 0.5), (i['incidents_30d'], 0.3), (100 - i['mttr_minutes'], 0.2))
        return primary
    if rule == "institutional_data_architecture":
        primary = round(i['data_domains'] * i['pipelines_active'] * i['retention_years'] / 100, 4)
        return primary
    if rule == "flexible_connector_microservice":
        primary = round(_ratio(i['connectors_live'], i['connectors_planned']), 4)
        return primary
    if rule == "institutional_api_gateway":
        primary = round(i['requests_per_sec'] / max(i['p99_latency_ms'], 1.0), 4)
        return primary
    if rule == "api_data_pipe":
        primary = _weighted((i['throughput_mbps'], 0.5), (i['error_rate_pct'], 0.3), (100 - i['batch_jobs_24h'], 0.2))
        return primary
    if rule == "developer_sdk":
        primary = round(i['sdk_methods'] * i['language_bindings'] * i['downloads_30d'] / 100, 4)
        return primary
    if rule == "pro_developer_sandbox":
        primary = round(_ratio(i['sandbox_runs_24h'], i['quota_runs']), 4)
        return primary
    if rule == "global_asset_tracker":
        primary = _weighted((i['assets_tracked'], 0.5), (i['chains_covered'], 0.3), (100 - i['sync_latency_sec'], 0.2))
        return primary
    if rule == "multi_account_sync":
        primary = round(_ratio(i['accounts_synced'], i['accounts_total']), 4)
        return primary
    if rule == "on_chain_balance_monitor":
        primary = round(i['wallets_monitored'] / max(i['alert_latency_sec'], 1.0), 4)
        return primary
    if rule == "profitability_analyzer":
        primary = _spread(i['realized_pnl_usd'], i['unrealized_pnl_usd'])
        return primary
    if rule == "margin_risk_calculator":
        primary = _weighted((i['margin_usage_pct'], 0.5), (i['liquidation_buffer_pct'], 0.3), (100 - i['leverage_ratio'], 0.2))
        return primary
    if rule == "volatility_scoring_system":
        primary = round(_ratio(i['vol_score'], i['max_score']), 4)
        return primary
    if rule == "volatility_surface_analyzer":
        primary = round(i['surface_points'] * i['atm_iv_pct'] * i['term_buckets'] / 100, 4)
        return primary
    if rule == "delta_neutral_calculator":
        primary = round(abs(_spread(i['portfolio_delta'], i['target_delta'])), 4)
        return primary
    if rule == "high_precision_backtesting":
        primary = round(i['trades_simulated'] / max(i['runtime_sec'], 1.0), 4)
        return primary
    if rule == "strategy_vetting_algorithm":
        primary = _weighted((i['sharpe_ratio'], 0.5), (i['max_drawdown_pct'], 0.3), (100 - i['win_rate_pct'], 0.2))
        return primary
    if rule == "ai_quant_rating_engine":
        primary = _weighted((i['momentum_score'], 0.34), (i['value_score'], 0.33), (i['risk_score'], 0.33))
        return primary
    if rule == "sentiment_analysis_engine":
        primary = round(_ratio(i['positive_mentions'], i['total_mentions']), 4)
        return primary
    if rule == "social_sentiment_engine":
        primary = _spread(i['bullish_posts_24h'], i['bearish_posts_24h'])
        return primary
    if rule == "social_hype_analyzer":
        primary = round(i['hype_index'] * i['mention_velocity'] * i['unique_authors'] / 100, 4)
        return primary
    if rule == "narrative_alert_system":
        primary = _weighted((i['narrative_strength'], 0.5), (i['alert_triggers_24h'], 0.3), (100 - i['source_diversity'], 0.2))
        return primary
    if rule == "ai_digest_generator":
        primary = round(i['digest_sections'] / max(i['generation_sec'], 1.0), 4)
        return primary
    if rule == "ai_agent_consultant":
        primary = round(i['sessions_24h'] * i['avg_turns'] * i['resolution_score'] / 100, 4)
        return primary
    if rule == "natural_language_interpreter":
        primary = round(_ratio(i['parsed_intents'], i['queries_24h']), 4)
        return primary
    if rule == "wallet_shadowing":
        primary = _weighted((i['shadowed_wallets'], 0.5), (i['copy_latency_sec'], 0.3), (100 - i['match_rate_pct'], 0.2))
        return primary
    if rule == "entity_tagging_system":
        primary = round(_ratio(i['entities_tagged'], i['entities_total']), 4)
        return primary
    if rule == "whale_clustering_engine":
        primary = round(i['whale_clusters'] * i['tracked_whales'] * i['flow_usd_24h'] / 100, 4)
        return primary

