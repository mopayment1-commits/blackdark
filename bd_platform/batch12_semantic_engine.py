"""Batch12 (551–600) capability-specific semantic transforms for institutional delivery shared core."""

from __future__ import annotations

from typing import Any, Callable

TransformFn = Callable[[dict[str, float], str], dict[str, Any]]


from bd_platform.batch_semantic_primitives import ratio as _ratio, semantic_inputs as _inputs, spread as _spread, weighted as _weighted

def _futures_volume(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['futures_volume_usd'], i['spot_volume_usd']), 4)
    return {
        "futures_volume": primary,
        "futures_volume_usd": i["futures_volume_usd"],
        "spot_volume_usd": i["spot_volume_usd"],
        "venue_count": i["venue_count"],
        "symbol_focus": symbol.upper(),
    }

def _basis_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['perp_price'], i['spot_price'])
    return {
        "basis_intelligence": primary,
        "perp_price": i["perp_price"],
        "spot_price": i["spot_price"],
        "basis_bps": i["basis_bps"],
        "symbol_focus": symbol.upper(),
    }

def _spot_market_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['tick_rate_hz'], 0.5), (i['symbols_covered'], 0.3), (100 - i['latency_ms'], 0.2))
    return {
        "spot_market_data": primary,
        "tick_rate_hz": i["tick_rate_hz"],
        "symbols_covered": i["symbols_covered"],
        "latency_ms": i["latency_ms"],
        "symbol_focus": symbol.upper(),
    }

def _options_analytics(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['contracts_tracked'] * i['greeks_fields'] * i['expiry_buckets'] / 100, 4)
    return {
        "options_analytics": primary,
        "contracts_tracked": i["contracts_tracked"],
        "greeks_fields": i["greeks_fields"],
        "expiry_buckets": i["expiry_buckets"],
        "symbol_focus": symbol.upper(),
    }

def _options_iv_surface(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['atm_iv_pct'], i['realized_vol_pct']), 4)
    return {
        "options_iv_surface": primary,
        "atm_iv_pct": i["atm_iv_pct"],
        "realized_vol_pct": i["realized_vol_pct"],
        "surface_nodes": i["surface_nodes"],
        "symbol_focus": symbol.upper(),
    }

def _options_skew(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['put_iv_pct'], i['call_iv_pct'])
    return {
        "options_skew": primary,
        "put_iv_pct": i["put_iv_pct"],
        "call_iv_pct": i["call_iv_pct"],
        "skew_strikes": i["skew_strikes"],
        "symbol_focus": symbol.upper(),
    }

def _options_term_structure(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['front_iv_pct'], 0.5), (i['back_iv_pct'], 0.3), (100 - i['tenor_days'], 0.2))
    return {
        "options_term_structure": primary,
        "front_iv_pct": i["front_iv_pct"],
        "back_iv_pct": i["back_iv_pct"],
        "tenor_days": i["tenor_days"],
        "symbol_focus": symbol.upper(),
    }

def _tradfi_context(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['macro_signals'], i['risk_events_24h']), 4)
    return {
        "tradfi_context": primary,
        "macro_signals": i["macro_signals"],
        "risk_events_24h": i["risk_events_24h"],
        "equity_beta": i["equity_beta"],
        "symbol_focus": symbol.upper(),
    }

def _multi_indicator_workspace(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['indicators_active'] * i['panes_count'] * i['refresh_hz'] / 100, 4)
    return {
        "multi_indicator_workspace": primary,
        "indicators_active": i["indicators_active"],
        "panes_count": i["panes_count"],
        "refresh_hz": i["refresh_hz"],
        "symbol_focus": symbol.upper(),
    }

def _real_time_prices(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['updates_per_sec'] / max(i['latency_ms'], 1.0), 4)
    return {
        "real_time_prices": primary,
        "updates_per_sec": i["updates_per_sec"],
        "latency_ms": i["latency_ms"],
        "venues_streaming": i["venues_streaming"],
        "symbol_focus": symbol.upper(),
    }

def _historical_data(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['bars_available'], i['bars_expected']), 4)
    return {
        "historical_data": primary,
        "bars_available": i["bars_available"],
        "bars_expected": i["bars_expected"],
        "interval_minutes": i["interval_minutes"],
        "symbol_focus": symbol.upper(),
    }

def _api_data_access(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['endpoint_count'], 0.5), (i['sla_uptime_pct'], 0.3), (100 - i['p95_latency_ms'], 0.2))
    return {
        "api_data_access": primary,
        "endpoint_count": i["endpoint_count"],
        "sla_uptime_pct": i["sla_uptime_pct"],
        "p95_latency_ms": i["p95_latency_ms"],
        "symbol_focus": symbol.upper(),
    }

def _news_context(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['articles_24h'] * i['sentiment_score'] * i['entity_tags'] / 100, 4)
    return {
        "news_context": primary,
        "articles_24h": i["articles_24h"],
        "sentiment_score": i["sentiment_score"],
        "entity_tags": i["entity_tags"],
        "symbol_focus": symbol.upper(),
    }

def _cross_asset_correlation(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(abs(_spread(i['btc_correlation'], i['eth_correlation'])), 4)
    return {
        "cross_asset_correlation": primary,
        "btc_correlation": i["btc_correlation"],
        "eth_correlation": i["eth_correlation"],
        "lookback_days": i["lookback_days"],
        "symbol_focus": symbol.upper(),
    }

def _derivatives_regime_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['trend_score'], 0.5), (i['vol_regime_score'], 0.3), (100 - i['funding_regime_score'], 0.2))
    return {
        "derivatives_regime_engine": primary,
        "trend_score": i["trend_score"],
        "vol_regime_score": i["vol_regime_score"],
        "funding_regime_score": i["funding_regime_score"],
        "symbol_focus": symbol.upper(),
    }

def _cross_market_decision_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['spot_signal'], 0.34), (i['perp_signal'], 0.33), (i['options_signal'], 0.33))
    return {
        "cross_market_decision_intelligence": primary,
        "spot_signal": i["spot_signal"],
        "perp_signal": i["perp_signal"],
        "options_signal": i["options_signal"],
        "symbol_focus": symbol.upper(),
    }

def _security_first_architecture(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['controls_passed'], i['controls_total']), 4)
    return {
        "security_first_architecture": primary,
        "controls_passed": i["controls_passed"],
        "controls_total": i["controls_total"],
        "audit_findings": i["audit_findings"],
        "symbol_focus": symbol.upper(),
    }

def _api_security_encryption(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['tls_coverage_pct'], 0.5), (i['key_rotation_days'], 0.3), (100 - i['auth_strength_score'], 0.2))
    return {
        "api_security_encryption": primary,
        "tls_coverage_pct": i["tls_coverage_pct"],
        "key_rotation_days": i["key_rotation_days"],
        "auth_strength_score": i["auth_strength_score"],
        "symbol_focus": symbol.upper(),
    }

def _high_availability_architecture(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['healthy_nodes'], i['total_nodes']), 4)
    return {
        "high_availability_architecture": primary,
        "healthy_nodes": i["healthy_nodes"],
        "total_nodes": i["total_nodes"],
        "failover_seconds": i["failover_seconds"],
        "symbol_focus": symbol.upper(),
    }

def _infrastructure_uptime_shield(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['uptime_pct'], 0.5), (i['incidents_30d'], 0.3), (100 - i['mttr_minutes'], 0.2))
    return {
        "infrastructure_uptime_shield": primary,
        "uptime_pct": i["uptime_pct"],
        "incidents_30d": i["incidents_30d"],
        "mttr_minutes": i["mttr_minutes"],
        "symbol_focus": symbol.upper(),
    }

def _institutional_data_architecture(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['data_domains'] * i['pipelines_active'] * i['retention_years'] / 100, 4)
    return {
        "institutional_data_architecture": primary,
        "data_domains": i["data_domains"],
        "pipelines_active": i["pipelines_active"],
        "retention_years": i["retention_years"],
        "symbol_focus": symbol.upper(),
    }

def _flexible_connector_microservice(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['connectors_live'], i['connectors_planned']), 4)
    return {
        "flexible_connector_microservice": primary,
        "connectors_live": i["connectors_live"],
        "connectors_planned": i["connectors_planned"],
        "avg_latency_ms": i["avg_latency_ms"],
        "symbol_focus": symbol.upper(),
    }

def _institutional_api_gateway(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['requests_per_sec'] / max(i['p99_latency_ms'], 1.0), 4)
    return {
        "institutional_api_gateway": primary,
        "requests_per_sec": i["requests_per_sec"],
        "p99_latency_ms": i["p99_latency_ms"],
        "routes_configured": i["routes_configured"],
        "symbol_focus": symbol.upper(),
    }

def _api_data_pipe(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['throughput_mbps'], 0.5), (i['error_rate_pct'], 0.3), (100 - i['batch_jobs_24h'], 0.2))
    return {
        "api_data_pipe": primary,
        "throughput_mbps": i["throughput_mbps"],
        "error_rate_pct": i["error_rate_pct"],
        "batch_jobs_24h": i["batch_jobs_24h"],
        "symbol_focus": symbol.upper(),
    }

def _developer_sdk(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['sdk_methods'] * i['language_bindings'] * i['downloads_30d'] / 100, 4)
    return {
        "developer_sdk": primary,
        "sdk_methods": i["sdk_methods"],
        "language_bindings": i["language_bindings"],
        "downloads_30d": i["downloads_30d"],
        "symbol_focus": symbol.upper(),
    }

def _pro_developer_sandbox(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['sandbox_runs_24h'], i['quota_runs']), 4)
    return {
        "pro_developer_sandbox": primary,
        "sandbox_runs_24h": i["sandbox_runs_24h"],
        "quota_runs": i["quota_runs"],
        "avg_runtime_sec": i["avg_runtime_sec"],
        "symbol_focus": symbol.upper(),
    }

def _global_asset_tracker(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['assets_tracked'], 0.5), (i['chains_covered'], 0.3), (100 - i['sync_latency_sec'], 0.2))
    return {
        "global_asset_tracker": primary,
        "assets_tracked": i["assets_tracked"],
        "chains_covered": i["chains_covered"],
        "sync_latency_sec": i["sync_latency_sec"],
        "symbol_focus": symbol.upper(),
    }

def _multi_account_sync(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['accounts_synced'], i['accounts_total']), 4)
    return {
        "multi_account_sync": primary,
        "accounts_synced": i["accounts_synced"],
        "accounts_total": i["accounts_total"],
        "drift_events_24h": i["drift_events_24h"],
        "symbol_focus": symbol.upper(),
    }

def _on_chain_balance_monitor(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['wallets_monitored'] / max(i['alert_latency_sec'], 1.0), 4)
    return {
        "on_chain_balance_monitor": primary,
        "wallets_monitored": i["wallets_monitored"],
        "alert_latency_sec": i["alert_latency_sec"],
        "chains_watched": i["chains_watched"],
        "symbol_focus": symbol.upper(),
    }

def _profitability_analyzer(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['realized_pnl_usd'], i['unrealized_pnl_usd'])
    return {
        "profitability_analyzer": primary,
        "realized_pnl_usd": i["realized_pnl_usd"],
        "unrealized_pnl_usd": i["unrealized_pnl_usd"],
        "trade_count_30d": i["trade_count_30d"],
        "symbol_focus": symbol.upper(),
    }

def _margin_risk_calculator(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['margin_usage_pct'], 0.5), (i['liquidation_buffer_pct'], 0.3), (100 - i['leverage_ratio'], 0.2))
    return {
        "margin_risk_calculator": primary,
        "margin_usage_pct": i["margin_usage_pct"],
        "liquidation_buffer_pct": i["liquidation_buffer_pct"],
        "leverage_ratio": i["leverage_ratio"],
        "symbol_focus": symbol.upper(),
    }

def _volatility_scoring_system(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['vol_score'], i['max_score']), 4)
    return {
        "volatility_scoring_system": primary,
        "vol_score": i["vol_score"],
        "max_score": i["max_score"],
        "lookback_days": i["lookback_days"],
        "symbol_focus": symbol.upper(),
    }

def _volatility_surface_analyzer(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['surface_points'] * i['atm_iv_pct'] * i['term_buckets'] / 100, 4)
    return {
        "volatility_surface_analyzer": primary,
        "surface_points": i["surface_points"],
        "atm_iv_pct": i["atm_iv_pct"],
        "term_buckets": i["term_buckets"],
        "symbol_focus": symbol.upper(),
    }

def _delta_neutral_calculator(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(abs(_spread(i['portfolio_delta'], i['target_delta'])), 4)
    return {
        "delta_neutral_calculator": primary,
        "portfolio_delta": i["portfolio_delta"],
        "target_delta": i["target_delta"],
        "hedge_legs": i["hedge_legs"],
        "symbol_focus": symbol.upper(),
    }

def _high_precision_backtesting(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['trades_simulated'] / max(i['runtime_sec'], 1.0), 4)
    return {
        "high_precision_backtesting": primary,
        "trades_simulated": i["trades_simulated"],
        "runtime_sec": i["runtime_sec"],
        "precision_bps": i["precision_bps"],
        "symbol_focus": symbol.upper(),
    }

def _strategy_vetting_algorithm(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['sharpe_ratio'], 0.5), (i['max_drawdown_pct'], 0.3), (100 - i['win_rate_pct'], 0.2))
    return {
        "strategy_vetting_algorithm": primary,
        "sharpe_ratio": i["sharpe_ratio"],
        "max_drawdown_pct": i["max_drawdown_pct"],
        "win_rate_pct": i["win_rate_pct"],
        "symbol_focus": symbol.upper(),
    }

def _ai_quant_rating_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['momentum_score'], 0.34), (i['value_score'], 0.33), (i['risk_score'], 0.33))
    return {
        "ai_quant_rating_engine": primary,
        "momentum_score": i["momentum_score"],
        "value_score": i["value_score"],
        "risk_score": i["risk_score"],
        "symbol_focus": symbol.upper(),
    }

def _sentiment_analysis_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['positive_mentions'], i['total_mentions']), 4)
    return {
        "sentiment_analysis_engine": primary,
        "positive_mentions": i["positive_mentions"],
        "total_mentions": i["total_mentions"],
        "confidence_pct": i["confidence_pct"],
        "symbol_focus": symbol.upper(),
    }

def _social_sentiment_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _spread(i['bullish_posts_24h'], i['bearish_posts_24h'])
    return {
        "social_sentiment_engine": primary,
        "bullish_posts_24h": i["bullish_posts_24h"],
        "bearish_posts_24h": i["bearish_posts_24h"],
        "influencer_weight": i["influencer_weight"],
        "symbol_focus": symbol.upper(),
    }

def _social_hype_analyzer(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['hype_index'] * i['mention_velocity'] * i['unique_authors'] / 100, 4)
    return {
        "social_hype_analyzer": primary,
        "hype_index": i["hype_index"],
        "mention_velocity": i["mention_velocity"],
        "unique_authors": i["unique_authors"],
        "symbol_focus": symbol.upper(),
    }

def _narrative_alert_system(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['narrative_strength'], 0.5), (i['alert_triggers_24h'], 0.3), (100 - i['source_diversity'], 0.2))
    return {
        "narrative_alert_system": primary,
        "narrative_strength": i["narrative_strength"],
        "alert_triggers_24h": i["alert_triggers_24h"],
        "source_diversity": i["source_diversity"],
        "symbol_focus": symbol.upper(),
    }

def _ai_digest_generator(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['digest_sections'] / max(i['generation_sec'], 1.0), 4)
    return {
        "ai_digest_generator": primary,
        "digest_sections": i["digest_sections"],
        "generation_sec": i["generation_sec"],
        "sources_synthesized": i["sources_synthesized"],
        "symbol_focus": symbol.upper(),
    }

def _ai_agent_consultant(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['sessions_24h'] * i['avg_turns'] * i['resolution_score'] / 100, 4)
    return {
        "ai_agent_consultant": primary,
        "sessions_24h": i["sessions_24h"],
        "avg_turns": i["avg_turns"],
        "resolution_score": i["resolution_score"],
        "symbol_focus": symbol.upper(),
    }

def _natural_language_interpreter(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['parsed_intents'], i['queries_24h']), 4)
    return {
        "natural_language_interpreter": primary,
        "parsed_intents": i["parsed_intents"],
        "queries_24h": i["queries_24h"],
        "ambiguity_pct": i["ambiguity_pct"],
        "symbol_focus": symbol.upper(),
    }

def _wallet_shadowing(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['shadowed_wallets'], 0.5), (i['copy_latency_sec'], 0.3), (100 - i['match_rate_pct'], 0.2))
    return {
        "wallet_shadowing": primary,
        "shadowed_wallets": i["shadowed_wallets"],
        "copy_latency_sec": i["copy_latency_sec"],
        "match_rate_pct": i["match_rate_pct"],
        "symbol_focus": symbol.upper(),
    }

def _entity_tagging_system(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['entities_tagged'], i['entities_total']), 4)
    return {
        "entity_tagging_system": primary,
        "entities_tagged": i["entities_tagged"],
        "entities_total": i["entities_total"],
        "tag_confidence_pct": i["tag_confidence_pct"],
        "symbol_focus": symbol.upper(),
    }

def _whale_clustering_engine(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(i['whale_clusters'] * i['tracked_whales'] * i['flow_usd_24h'] / 100, 4)
    return {
        "whale_clustering_engine": primary,
        "whale_clusters": i["whale_clusters"],
        "tracked_whales": i["tracked_whales"],
        "flow_usd_24h": i["flow_usd_24h"],
        "symbol_focus": symbol.upper(),
    }

RULES: dict[str, TransformFn] = {
    "futures_volume": _futures_volume,
    "basis_intelligence": _basis_intelligence,
    "spot_market_data": _spot_market_data,
    "options_analytics": _options_analytics,
    "options_iv_surface": _options_iv_surface,
    "options_skew": _options_skew,
    "options_term_structure": _options_term_structure,
    "tradfi_context": _tradfi_context,
    "multi_indicator_workspace": _multi_indicator_workspace,
    "real_time_prices": _real_time_prices,
    "historical_data": _historical_data,
    "api_data_access": _api_data_access,
    "news_context": _news_context,
    "cross_asset_correlation": _cross_asset_correlation,
    "derivatives_regime_engine": _derivatives_regime_engine,
    "cross_market_decision_intelligence": _cross_market_decision_intelligence,
    "security_first_architecture": _security_first_architecture,
    "api_security_encryption": _api_security_encryption,
    "high_availability_architecture": _high_availability_architecture,
    "infrastructure_uptime_shield": _infrastructure_uptime_shield,
    "institutional_data_architecture": _institutional_data_architecture,
    "flexible_connector_microservice": _flexible_connector_microservice,
    "institutional_api_gateway": _institutional_api_gateway,
    "api_data_pipe": _api_data_pipe,
    "developer_sdk": _developer_sdk,
    "pro_developer_sandbox": _pro_developer_sandbox,
    "global_asset_tracker": _global_asset_tracker,
    "multi_account_sync": _multi_account_sync,
    "on_chain_balance_monitor": _on_chain_balance_monitor,
    "profitability_analyzer": _profitability_analyzer,
    "margin_risk_calculator": _margin_risk_calculator,
    "volatility_scoring_system": _volatility_scoring_system,
    "volatility_surface_analyzer": _volatility_surface_analyzer,
    "delta_neutral_calculator": _delta_neutral_calculator,
    "high_precision_backtesting": _high_precision_backtesting,
    "strategy_vetting_algorithm": _strategy_vetting_algorithm,
    "ai_quant_rating_engine": _ai_quant_rating_engine,
    "sentiment_analysis_engine": _sentiment_analysis_engine,
    "social_sentiment_engine": _social_sentiment_engine,
    "social_hype_analyzer": _social_hype_analyzer,
    "narrative_alert_system": _narrative_alert_system,
    "ai_digest_generator": _ai_digest_generator,
    "ai_agent_consultant": _ai_agent_consultant,
    "natural_language_interpreter": _natural_language_interpreter,
    "wallet_shadowing": _wallet_shadowing,
    "entity_tagging_system": _entity_tagging_system,
    "whale_clustering_engine": _whale_clustering_engine,
}

CAPABILITY_SEMANTIC_SPECS: dict[int, dict[str, Any]] = {
    552: {"rule": "futures_volume", "defaults": {'futures_volume_usd': 1250000000.0, 'spot_volume_usd': 980000000.0, 'venue_count': 14}, "feature": "Futures Volume"},
    553: {"rule": "basis_intelligence", "defaults": {'perp_price': 42150.5, 'spot_price': 42080.2, 'basis_bps': 16.8}, "feature": "Basis Intelligence"},
    554: {"rule": "spot_market_data", "defaults": {'tick_rate_hz': 420, 'symbols_covered': 380, 'latency_ms': 18}, "feature": "Spot Market Data"},
    555: {"rule": "options_analytics", "defaults": {'contracts_tracked': 520, 'greeks_fields': 7, 'expiry_buckets': 9}, "feature": "Options Analytics"},
    556: {"rule": "options_iv_surface", "defaults": {'atm_iv_pct': 62.5, 'realized_vol_pct': 48.2, 'surface_nodes': 36}, "feature": "Options IV Surface"},
    557: {"rule": "options_skew", "defaults": {'put_iv_pct': 68.4, 'call_iv_pct': 54.1, 'skew_strikes': 24}, "feature": "Options Skew"},
    558: {"rule": "options_term_structure", "defaults": {'front_iv_pct': 58.0, 'back_iv_pct': 52.5, 'tenor_days': 90}, "feature": "Options Term Structure"},
    559: {"rule": "tradfi_context", "defaults": {'macro_signals': 12, 'risk_events_24h': 4, 'equity_beta': 0.72}, "feature": "TradFi Context"},
    560: {"rule": "multi_indicator_workspace", "defaults": {'indicators_active': 18, 'panes_count': 6, 'refresh_hz': 3}, "feature": "Multi-Indicator Workspace"},
    561: {"rule": "real_time_prices", "defaults": {'updates_per_sec': 960, 'latency_ms': 14, 'venues_streaming': 16}, "feature": "Real-Time Prices"},
    562: {"rule": "historical_data", "defaults": {'bars_available': 8760, 'bars_expected': 9000, 'interval_minutes': 60}, "feature": "Historical Data"},
    563: {"rule": "api_data_access", "defaults": {'endpoint_count': 84, 'sla_uptime_pct': 99.4, 'p95_latency_ms': 92}, "feature": "API Data Access"},
    564: {"rule": "news_context", "defaults": {'articles_24h': 145, 'sentiment_score': 0.62, 'entity_tags': 28}, "feature": "News Context"},
    565: {"rule": "cross_asset_correlation", "defaults": {'btc_correlation': 0.78, 'eth_correlation': 0.65, 'lookback_days': 30}, "feature": "Cross-Asset Correlation"},
    566: {"rule": "derivatives_regime_engine", "defaults": {'trend_score': 72, 'vol_regime_score': 68, 'funding_regime_score': 61}, "feature": "Derivatives Regime Engine"},
    567: {"rule": "cross_market_decision_intelligence", "defaults": {'spot_signal': 0.64, 'perp_signal': 0.58, 'options_signal': 0.51}, "feature": "Cross-Market Decision Intelligence"},
    568: {"rule": "security_first_architecture", "defaults": {'controls_passed': 46, 'controls_total': 50, 'audit_findings': 2}, "feature": "Security First Architecture"},
    569: {"rule": "api_security_encryption", "defaults": {'tls_coverage_pct': 99.8, 'key_rotation_days': 28, 'auth_strength_score': 88}, "feature": "API Security Encryption"},
    570: {"rule": "high_availability_architecture", "defaults": {'healthy_nodes': 11, 'total_nodes': 12, 'failover_seconds': 18}, "feature": "High Availability Architecture"},
    571: {"rule": "infrastructure_uptime_shield", "defaults": {'uptime_pct': 99.92, 'incidents_30d': 1, 'mttr_minutes': 12}, "feature": "Infrastructure Uptime Shield"},
    572: {"rule": "institutional_data_architecture", "defaults": {'data_domains': 14, 'pipelines_active': 36, 'retention_years': 7}, "feature": "Institutional Data Architecture"},
    573: {"rule": "flexible_connector_microservice", "defaults": {'connectors_live': 22, 'connectors_planned': 26, 'avg_latency_ms': 45}, "feature": "Flexible Connector Microservice"},
    574: {"rule": "institutional_api_gateway", "defaults": {'requests_per_sec': 1850, 'p99_latency_ms': 48, 'routes_configured': 120}, "feature": "Institutional API Gateway"},
    575: {"rule": "api_data_pipe", "defaults": {'throughput_mbps': 420, 'error_rate_pct': 0.12, 'batch_jobs_24h': 86}, "feature": "API Data Pipe"},
    576: {"rule": "developer_sdk", "defaults": {'sdk_methods': 128, 'language_bindings': 5, 'downloads_30d': 4200}, "feature": "Developer SDK"},
    577: {"rule": "pro_developer_sandbox", "defaults": {'sandbox_runs_24h': 240, 'quota_runs': 300, 'avg_runtime_sec': 18}, "feature": "Pro Developer Sandbox"},
    579: {"rule": "global_asset_tracker", "defaults": {'assets_tracked': 420, 'chains_covered': 18, 'sync_latency_sec': 22}, "feature": "Global Asset Tracker"},
    580: {"rule": "multi_account_sync", "defaults": {'accounts_synced': 14, 'accounts_total': 16, 'drift_events_24h': 1}, "feature": "Multi Account Sync"},
    581: {"rule": "on_chain_balance_monitor", "defaults": {'wallets_monitored': 860, 'alert_latency_sec': 28, 'chains_watched': 12}, "feature": "On Chain Balance Monitor"},
    582: {"rule": "profitability_analyzer", "defaults": {'realized_pnl_usd': 125000.0, 'unrealized_pnl_usd': 42000.0, 'trade_count_30d': 186}, "feature": "Profitability Analyzer"},
    583: {"rule": "margin_risk_calculator", "defaults": {'margin_usage_pct': 62, 'liquidation_buffer_pct': 18, 'leverage_ratio': 4.2}, "feature": "Margin Risk Calculator"},
    585: {"rule": "volatility_scoring_system", "defaults": {'vol_score': 74, 'max_score': 100, 'lookback_days': 14}, "feature": "Volatility Scoring System"},
    586: {"rule": "volatility_surface_analyzer", "defaults": {'surface_points': 240, 'atm_iv_pct': 59.5, 'term_buckets': 8}, "feature": "Volatility Surface Analyzer"},
    587: {"rule": "delta_neutral_calculator", "defaults": {'portfolio_delta': 0.18, 'target_delta': 0.0, 'hedge_legs': 6}, "feature": "Delta Neutral Calculator"},
    588: {"rule": "high_precision_backtesting", "defaults": {'trades_simulated': 125000, 'runtime_sec': 420, 'precision_bps': 0.5}, "feature": "High Precision Backtesting"},
    589: {"rule": "strategy_vetting_algorithm", "defaults": {'sharpe_ratio': 1.42, 'max_drawdown_pct': 12.5, 'win_rate_pct': 58}, "feature": "Strategy Vetting Algorithm"},
    590: {"rule": "ai_quant_rating_engine", "defaults": {'momentum_score': 0.71, 'value_score': 0.64, 'risk_score': 0.58}, "feature": "AI Quant Rating Engine"},
    591: {"rule": "sentiment_analysis_engine", "defaults": {'positive_mentions': 420, 'total_mentions': 680, 'confidence_pct': 82}, "feature": "Sentiment Analysis Engine"},
    592: {"rule": "social_sentiment_engine", "defaults": {'bullish_posts_24h': 1240, 'bearish_posts_24h': 860, 'influencer_weight': 1.35}, "feature": "Social Sentiment Engine"},
    593: {"rule": "social_hype_analyzer", "defaults": {'hype_index': 0.78, 'mention_velocity': 420, 'unique_authors': 1850}, "feature": "Social Hype Analyzer"},
    594: {"rule": "narrative_alert_system", "defaults": {'narrative_strength': 0.72, 'alert_triggers_24h': 9, 'source_diversity': 14}, "feature": "Narrative Alert System"},
    595: {"rule": "ai_digest_generator", "defaults": {'digest_sections': 12, 'generation_sec': 18, 'sources_synthesized': 28}, "feature": "AI Digest Generator"},
    596: {"rule": "ai_agent_consultant", "defaults": {'sessions_24h': 86, 'avg_turns': 7, 'resolution_score': 0.84}, "feature": "AI Agent Consultant"},
    597: {"rule": "natural_language_interpreter", "defaults": {'parsed_intents': 940, 'queries_24h': 1020, 'ambiguity_pct': 8.5}, "feature": "Natural Language Interpreter"},
    598: {"rule": "wallet_shadowing", "defaults": {'shadowed_wallets': 48, 'copy_latency_sec': 22, 'match_rate_pct': 91}, "feature": "Wallet Shadowing"},
    599: {"rule": "entity_tagging_system", "defaults": {'entities_tagged': 4200, 'entities_total': 4500, 'tag_confidence_pct': 88}, "feature": "Entity Tagging System"},
    600: {"rule": "whale_clustering_engine", "defaults": {'whale_clusters': 18, 'tracked_whales': 240, 'flow_usd_24h': 85000000.0}, "feature": "Whale Clustering Engine"},
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
