"""Batch14 (651–700) capability-specific semantic transforms for extension analytics shared core."""

from __future__ import annotations

from typing import Any, Callable

from bd_platform.batch_semantic_primitives import ratio as _ratio, semantic_inputs as _inputs, spread as _spread, weighted as _weighted

TransformFn = Callable[[dict[str, float], str], dict[str, Any]]

def _airdrop_incentive_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['events_30d'], i['participants']), 4)
    return {
        "airdrop_incentive_intelligence": primary,
        "events_30d": i["events_30d"],
        "value_usd_m": i["value_usd_m"],
        "participants": i["participants"],
        "symbol_focus": symbol.upper(),
    }

def _alerts_from_query_results(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['metric_a'], i['metric_c']), 4)
    return {
        "alerts_from_query_results": primary,
        "metric_a": i["metric_a"],
        "metric_b": i["metric_b"],
        "metric_c": i["metric_c"],
        "symbol_focus": symbol.upper(),
    }

def _borrowing_rates(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['apy_pct'], i['risk_score']), 4)
    return {
        "borrowing_rates": primary,
        "apy_pct": i["apy_pct"],
        "tvl_usd": i["tvl_usd"],
        "risk_score": i["risk_score"],
        "symbol_focus": symbol.upper(),
    }

def _bridges_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['supply_usd_b'], i['flow_usd_24h']), 4)
    return {
        "bridges_intelligence": primary,
        "supply_usd_b": i["supply_usd_b"],
        "flow_usd_24h": i["flow_usd_24h"],
        "peg_deviation_bps": i["peg_deviation_bps"],
        "symbol_focus": symbol.upper(),
    }

def _capital_formation_radar(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['endpoints_active'], i['error_rate_pct']), 4)
    return {
        "capital_formation_radar": primary,
        "endpoints_active": i["endpoints_active"],
        "requests_24h": i["requests_24h"],
        "error_rate_pct": i["error_rate_pct"],
        "symbol_focus": symbol.upper(),
    }

def _comparable_company_protocol_analysis(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['sources_cited'], i['coverage_score']), 4)
    return {
        "comparable_company_protocol_analysis": primary,
        "sources_cited": i["sources_cited"],
        "confidence_pct": i["confidence_pct"],
        "coverage_score": i["coverage_score"],
        "symbol_focus": symbol.upper(),
    }

def _consensus_estimates(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['metric_a'], i['metric_c']), 4)
    return {
        "consensus_estimates": primary,
        "metric_a": i["metric_a"],
        "metric_b": i["metric_b"],
        "metric_c": i["metric_c"],
        "symbol_focus": symbol.upper(),
    }

def _cross_chain_fundamentals(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['tvl_usd_b'], i['change_7d_pct']), 4)
    return {
        "cross_chain_fundamentals": primary,
        "tvl_usd_b": i["tvl_usd_b"],
        "protocols_count": i["protocols_count"],
        "change_7d_pct": i["change_7d_pct"],
        "symbol_focus": symbol.upper(),
    }

def _cross_defi_decision_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['risk_flags'], i['mitigation_score']), 4)
    return {
        "cross_defi_decision_intelligence": primary,
        "risk_flags": i["risk_flags"],
        "exposure_usd": i["exposure_usd"],
        "mitigation_score": i["mitigation_score"],
        "symbol_focus": symbol.upper(),
    }

def _dashboard_from_prompt(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['agent_sessions'], i['latency_ms']), 4)
    return {
        "dashboard_from_prompt": primary,
        "agent_sessions": i["agent_sessions"],
        "tool_calls": i["tool_calls"],
        "latency_ms": i["latency_ms"],
        "symbol_focus": symbol.upper(),
    }

def _dashboards(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['agent_sessions'], i['latency_ms']), 4)
    return {
        "dashboards": primary,
        "agent_sessions": i["agent_sessions"],
        "tool_calls": i["tool_calls"],
        "latency_ms": i["latency_ms"],
        "symbol_focus": symbol.upper(),
    }

def _defi_opportunity_screener(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['risk_flags'], i['mitigation_score']), 4)
    return {
        "defi_opportunity_screener": primary,
        "risk_flags": i["risk_flags"],
        "exposure_usd": i["exposure_usd"],
        "mitigation_score": i["mitigation_score"],
        "symbol_focus": symbol.upper(),
    }

def _defi_risk_passport(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['risk_flags'], 0.5), (i['exposure_usd'], 0.3), (i['mitigation_score'], 0.2))
    return {
        "defi_risk_passport": primary,
        "risk_flags": i["risk_flags"],
        "exposure_usd": i["exposure_usd"],
        "mitigation_score": i["mitigation_score"],
        "symbol_focus": symbol.upper(),
    }

def _developer_activity(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['commits_90d'], 0.5), (i['active_devs'], 0.3), (i['growth_pct'], 0.2))
    return {
        "developer_activity": primary,
        "commits_90d": i["commits_90d"],
        "active_devs": i["active_devs"],
        "growth_pct": i["growth_pct"],
        "symbol_focus": symbol.upper(),
    }

def _dex_volume(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['volume_usd_24h'], i['venues']), 4)
    return {
        "dex_volume": primary,
        "volume_usd_24h": i["volume_usd_24h"],
        "venues": i["venues"],
        "share_pct": i["share_pct"],
        "symbol_focus": symbol.upper(),
    }

def _equities_crypto_research(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['sources_cited'], 0.5), (i['confidence_pct'], 0.3), (i['coverage_score'], 0.2))
    return {
        "equities_crypto_research": primary,
        "sources_cited": i["sources_cited"],
        "confidence_pct": i["confidence_pct"],
        "coverage_score": i["coverage_score"],
        "symbol_focus": symbol.upper(),
    }

def _fees_revenue(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['metric_a'], i['metric_c']), 4)
    return {
        "fees_revenue": primary,
        "metric_a": i["metric_a"],
        "metric_b": i["metric_b"],
        "metric_c": i["metric_c"],
        "symbol_focus": symbol.upper(),
    }

def _investor_profiles(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['metric_a'], i['metric_c']), 4)
    return {
        "investor_profiles": primary,
        "metric_a": i["metric_a"],
        "metric_b": i["metric_b"],
        "metric_c": i["metric_c"],
        "symbol_focus": symbol.upper(),
    }

def _liquid_staking_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['apy_pct'], i['risk_score']), 4)
    return {
        "liquid_staking_intelligence": primary,
        "apy_pct": i["apy_pct"],
        "tvl_usd": i["tvl_usd"],
        "risk_score": i["risk_score"],
        "symbol_focus": symbol.upper(),
    }

def _mcp_for_ai_agents(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['agent_sessions'], i['latency_ms']), 4)
    return {
        "mcp_for_ai_agents": primary,
        "agent_sessions": i["agent_sessions"],
        "tool_calls": i["tool_calls"],
        "latency_ms": i["latency_ms"],
        "symbol_focus": symbol.upper(),
    }

def _on_chain_usage_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['tvl_usd_b'], i['change_7d_pct']), 4)
    return {
        "on_chain_usage_intelligence": primary,
        "tvl_usd_b": i["tvl_usd_b"],
        "protocols_count": i["protocols_count"],
        "change_7d_pct": i["change_7d_pct"],
        "symbol_focus": symbol.upper(),
    }

def _options_volume(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['volume_usd_24h'], i['venues']), 4)
    return {
        "options_volume": primary,
        "volume_usd_24h": i["volume_usd_24h"],
        "venues": i["venues"],
        "share_pct": i["share_pct"],
        "symbol_focus": symbol.upper(),
    }

def _perps_volume(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['volume_usd_24h'], i['venues']), 4)
    return {
        "perps_volume": primary,
        "volume_usd_24h": i["volume_usd_24h"],
        "venues": i["venues"],
        "share_pct": i["share_pct"],
        "symbol_focus": symbol.upper(),
    }

def _prompt_to_sql_agent(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['agent_sessions'], i['latency_ms']), 4)
    return {
        "prompt_to_sql_agent": primary,
        "agent_sessions": i["agent_sessions"],
        "tool_calls": i["tool_calls"],
        "latency_ms": i["latency_ms"],
        "symbol_focus": symbol.upper(),
    }

def _protocol_directory(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['metric_a'], i['metric_c']), 4)
    return {
        "protocol_directory": primary,
        "metric_a": i["metric_a"],
        "metric_b": i["metric_b"],
        "metric_c": i["metric_c"],
        "symbol_focus": symbol.upper(),
    }

def _protocol_fundamentals(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['commits_90d'], i['growth_pct']), 4)
    return {
        "protocol_fundamentals": primary,
        "commits_90d": i["commits_90d"],
        "active_devs": i["active_devs"],
        "growth_pct": i["growth_pct"],
        "symbol_focus": symbol.upper(),
    }

def _raises_funding_rounds(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['events_30d'], i['participants']), 4)
    return {
        "raises_funding_rounds": primary,
        "events_30d": i["events_30d"],
        "value_usd_m": i["value_usd_m"],
        "participants": i["participants"],
        "symbol_focus": symbol.upper(),
    }

def _research_templates(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['sources_cited'], 0.5), (i['confidence_pct'], 0.3), (i['coverage_score'], 0.2))
    return {
        "research_templates": primary,
        "sources_cited": i["sources_cited"],
        "confidence_pct": i["confidence_pct"],
        "coverage_score": i["coverage_score"],
        "symbol_focus": symbol.upper(),
    }

def _rwa_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['metric_a'], i['metric_c']), 4)
    return {
        "rwa_intelligence": primary,
        "metric_a": i["metric_a"],
        "metric_b": i["metric_b"],
        "metric_c": i["metric_c"],
        "symbol_focus": symbol.upper(),
    }

def _scheduled_queries(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['metric_a'], i['metric_c']), 4)
    return {
        "scheduled_queries": primary,
        "metric_a": i["metric_a"],
        "metric_b": i["metric_b"],
        "metric_c": i["metric_c"],
        "symbol_focus": symbol.upper(),
    }

def _sector_ecosystem_comparables(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['sources_cited'], i['coverage_score']), 4)
    return {
        "sector_ecosystem_comparables": primary,
        "sources_cited": i["sources_cited"],
        "confidence_pct": i["confidence_pct"],
        "coverage_score": i["coverage_score"],
        "symbol_focus": symbol.upper(),
    }

def _stablecoin_activity_breakdown(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['supply_usd_b'], i['flow_usd_24h']), 4)
    return {
        "stablecoin_activity_breakdown": primary,
        "supply_usd_b": i["supply_usd_b"],
        "flow_usd_24h": i["flow_usd_24h"],
        "peg_deviation_bps": i["peg_deviation_bps"],
        "symbol_focus": symbol.upper(),
    }

def _stablecoin_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['supply_usd_b'], i['flow_usd_24h']), 4)
    return {
        "stablecoin_intelligence": primary,
        "supply_usd_b": i["supply_usd_b"],
        "flow_usd_24h": i["flow_usd_24h"],
        "peg_deviation_bps": i["peg_deviation_bps"],
        "symbol_focus": symbol.upper(),
    }

def _stablecoin_payment_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['supply_usd_b'], i['flow_usd_24h']), 4)
    return {
        "stablecoin_payment_intelligence": primary,
        "supply_usd_b": i["supply_usd_b"],
        "flow_usd_24h": i["flow_usd_24h"],
        "peg_deviation_bps": i["peg_deviation_bps"],
        "symbol_focus": symbol.upper(),
    }

def _stablecoins_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['supply_usd_b'], i['flow_usd_24h']), 4)
    return {
        "stablecoins_intelligence": primary,
        "supply_usd_b": i["supply_usd_b"],
        "flow_usd_24h": i["flow_usd_24h"],
        "peg_deviation_bps": i["peg_deviation_bps"],
        "symbol_focus": symbol.upper(),
    }

def _thesis_research_workspace(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = _weighted((i['sources_cited'], 0.5), (i['confidence_pct'], 0.3), (i['coverage_score'], 0.2))
    return {
        "thesis_research_workspace": primary,
        "sources_cited": i["sources_cited"],
        "confidence_pct": i["confidence_pct"],
        "coverage_score": i["coverage_score"],
        "symbol_focus": symbol.upper(),
    }

def _treasury_intelligence(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['events_30d'], i['participants']), 4)
    return {
        "treasury_intelligence": primary,
        "events_30d": i["events_30d"],
        "value_usd_m": i["value_usd_m"],
        "participants": i["participants"],
        "symbol_focus": symbol.upper(),
    }

def _yield_history(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['apy_pct'], i['tvl_usd']), 4)
    return {
        "yield_history": primary,
        "apy_pct": i["apy_pct"],
        "tvl_usd": i["tvl_usd"],
        "risk_score": i["risk_score"],
        "symbol_focus": symbol.upper(),
    }

def _yields_screener(i: dict[str, float], symbol: str) -> dict[str, Any]:
    primary = round(_ratio(i['apy_pct'], i['tvl_usd']), 4)
    return {
        "yields_screener": primary,
        "apy_pct": i["apy_pct"],
        "tvl_usd": i["tvl_usd"],
        "risk_score": i["risk_score"],
        "symbol_focus": symbol.upper(),
    }


CAPABILITY_SEMANTIC_SPECS: dict[int, dict[str, Any]] = {
    651: {"rule": "mcp_for_ai_agents", "defaults": {'agent_sessions': 42.0, 'tool_calls': 128.0, 'latency_ms': 240.0}, "feature": 'MCP for AI Agents'},
    652: {"rule": "prompt_to_sql_agent", "defaults": {'agent_sessions': 42.0, 'tool_calls': 128.0, 'latency_ms': 240.0}, "feature": 'Prompt-to-SQL Agent'},
    653: {"rule": "dashboard_from_prompt", "defaults": {'agent_sessions': 42.0, 'tool_calls': 128.0, 'latency_ms': 240.0}, "feature": 'Dashboard-from-Prompt'},
    654: {"rule": "scheduled_queries", "defaults": {'metric_a': 100.0, 'metric_b': 50.0, 'metric_c': 25.0}, "feature": 'Scheduled Queries'},
    655: {"rule": "alerts_from_query_results", "defaults": {'metric_a': 100.0, 'metric_b': 50.0, 'metric_c': 25.0}, "feature": 'Alerts from Query Results'},
    662: {"rule": "protocol_directory", "defaults": {'metric_a': 100.0, 'metric_b': 50.0, 'metric_c': 25.0}, "feature": 'Protocol Directory'},
    663: {"rule": "fees_revenue", "defaults": {'metric_a': 100.0, 'metric_b': 50.0, 'metric_c': 25.0}, "feature": 'Fees & Revenue'},
    664: {"rule": "dex_volume", "defaults": {'volume_usd_24h': 850000000.0, 'venues': 24.0, 'share_pct': 18.5}, "feature": 'DEX Volume'},
    665: {"rule": "perps_volume", "defaults": {'volume_usd_24h': 850000000.0, 'venues': 24.0, 'share_pct': 18.5}, "feature": 'Perps Volume'},
    666: {"rule": "options_volume", "defaults": {'volume_usd_24h': 850000000.0, 'venues': 24.0, 'share_pct': 18.5}, "feature": 'Options Volume'},
    667: {"rule": "stablecoins_intelligence", "defaults": {'supply_usd_b': 125.0, 'flow_usd_24h': 4200000000.0, 'peg_deviation_bps': 4.2}, "feature": 'Stablecoins Intelligence'},
    668: {"rule": "bridges_intelligence", "defaults": {'supply_usd_b': 125.0, 'flow_usd_24h': 4200000000.0, 'peg_deviation_bps': 4.2}, "feature": 'Bridges Intelligence'},
    669: {"rule": "yields_screener", "defaults": {'apy_pct': 8.4, 'tvl_usd': 420000000.0, 'risk_score': 32.0}, "feature": 'Yields Screener'},
    670: {"rule": "yield_history", "defaults": {'apy_pct': 8.4, 'tvl_usd': 420000000.0, 'risk_score': 32.0}, "feature": 'Yield History'},
    671: {"rule": "borrowing_rates", "defaults": {'apy_pct': 8.4, 'tvl_usd': 420000000.0, 'risk_score': 32.0}, "feature": 'Borrowing Rates'},
    672: {"rule": "liquid_staking_intelligence", "defaults": {'apy_pct': 8.4, 'tvl_usd': 420000000.0, 'risk_score': 32.0}, "feature": 'Liquid Staking Intelligence'},
    673: {"rule": "rwa_intelligence", "defaults": {'metric_a': 100.0, 'metric_b': 50.0, 'metric_c': 25.0}, "feature": 'RWA Intelligence'},
    674: {"rule": "raises_funding_rounds", "defaults": {'events_30d': 18.0, 'value_usd_m': 420.0, 'participants': 1250.0}, "feature": 'Raises / Funding Rounds'},
    675: {"rule": "investor_profiles", "defaults": {'metric_a': 100.0, 'metric_b': 50.0, 'metric_c': 25.0}, "feature": 'Investor Profiles'},
    677: {"rule": "treasury_intelligence", "defaults": {'events_30d': 18.0, 'value_usd_m': 420.0, 'participants': 1250.0}, "feature": 'Treasury Intelligence'},
    678: {"rule": "airdrop_incentive_intelligence", "defaults": {'events_30d': 18.0, 'value_usd_m': 420.0, 'participants': 1250.0}, "feature": 'Airdrop / Incentive Intelligence'},
    679: {"rule": "capital_formation_radar", "defaults": {'endpoints_active': 42.0, 'requests_24h': 125000.0, 'error_rate_pct': 0.8}, "feature": 'Capital Formation Radar'},
    680: {"rule": "defi_opportunity_screener", "defaults": {'risk_flags': 6.0, 'exposure_usd': 2500000.0, 'mitigation_score': 78.0}, "feature": 'DeFi Opportunity Screener'},
    681: {"rule": "defi_risk_passport", "defaults": {'risk_flags': 6.0, 'exposure_usd': 2500000.0, 'mitigation_score': 78.0}, "feature": 'DeFi Risk Passport'},
    683: {"rule": "cross_defi_decision_intelligence", "defaults": {'risk_flags': 6.0, 'exposure_usd': 2500000.0, 'mitigation_score': 78.0}, "feature": 'Cross-DeFi Decision Intelligence'},
    684: {"rule": "cross_chain_fundamentals", "defaults": {'tvl_usd_b': 42.0, 'protocols_count': 128.0, 'change_7d_pct': 3.2}, "feature": 'Cross-Chain Fundamentals'},
    685: {"rule": "protocol_fundamentals", "defaults": {'commits_90d': 420.0, 'active_devs': 86.0, 'growth_pct': 12.5}, "feature": 'Protocol Fundamentals'},
    686: {"rule": "stablecoin_intelligence", "defaults": {'supply_usd_b': 125.0, 'flow_usd_24h': 4200000000.0, 'peg_deviation_bps': 4.2}, "feature": 'Stablecoin Intelligence'},
    687: {"rule": "stablecoin_activity_breakdown", "defaults": {'supply_usd_b': 125.0, 'flow_usd_24h': 4200000000.0, 'peg_deviation_bps': 4.2}, "feature": 'Stablecoin Activity Breakdown'},
    688: {"rule": "developer_activity", "defaults": {'commits_90d': 420.0, 'active_devs': 86.0, 'growth_pct': 12.5}, "feature": 'Developer Activity'},
    689: {"rule": "sector_ecosystem_comparables", "defaults": {'sources_cited': 24.0, 'confidence_pct': 72.0, 'coverage_score': 0.84}, "feature": 'Sector/Ecosystem Comparables'},
    690: {"rule": "equities_crypto_research", "defaults": {'sources_cited': 24.0, 'confidence_pct': 72.0, 'coverage_score': 0.84}, "feature": 'Equities + Crypto Research'},
    691: {"rule": "consensus_estimates", "defaults": {'metric_a': 100.0, 'metric_b': 50.0, 'metric_c': 25.0}, "feature": 'Consensus Estimates'},
    693: {"rule": "thesis_research_workspace", "defaults": {'sources_cited': 24.0, 'confidence_pct': 72.0, 'coverage_score': 0.84}, "feature": 'Thesis Research Workspace'},
    694: {"rule": "comparable_company_protocol_analysis", "defaults": {'sources_cited': 24.0, 'confidence_pct': 72.0, 'coverage_score': 0.84}, "feature": 'Comparable Company / Protocol Analysis'},
    697: {"rule": "research_templates", "defaults": {'sources_cited': 24.0, 'confidence_pct': 72.0, 'coverage_score': 0.84}, "feature": 'Research Templates'},
    698: {"rule": "dashboards", "defaults": {'agent_sessions': 42.0, 'tool_calls': 128.0, 'latency_ms': 240.0}, "feature": 'Dashboards'},
    699: {"rule": "stablecoin_payment_intelligence", "defaults": {'supply_usd_b': 125.0, 'flow_usd_24h': 4200000000.0, 'peg_deviation_bps': 4.2}, "feature": 'Stablecoin Payment Intelligence'},
    700: {"rule": "on_chain_usage_intelligence", "defaults": {'tvl_usd_b': 42.0, 'protocols_count': 128.0, 'change_7d_pct': 3.2}, "feature": 'On-Chain Usage Intelligence'},
}


RULES: dict[str, TransformFn] = {
    "airdrop_incentive_intelligence": _airdrop_incentive_intelligence,
    "alerts_from_query_results": _alerts_from_query_results,
    "borrowing_rates": _borrowing_rates,
    "bridges_intelligence": _bridges_intelligence,
    "capital_formation_radar": _capital_formation_radar,
    "comparable_company_protocol_analysis": _comparable_company_protocol_analysis,
    "consensus_estimates": _consensus_estimates,
    "cross_chain_fundamentals": _cross_chain_fundamentals,
    "cross_defi_decision_intelligence": _cross_defi_decision_intelligence,
    "dashboard_from_prompt": _dashboard_from_prompt,
    "dashboards": _dashboards,
    "defi_opportunity_screener": _defi_opportunity_screener,
    "defi_risk_passport": _defi_risk_passport,
    "developer_activity": _developer_activity,
    "dex_volume": _dex_volume,
    "equities_crypto_research": _equities_crypto_research,
    "fees_revenue": _fees_revenue,
    "investor_profiles": _investor_profiles,
    "liquid_staking_intelligence": _liquid_staking_intelligence,
    "mcp_for_ai_agents": _mcp_for_ai_agents,
    "on_chain_usage_intelligence": _on_chain_usage_intelligence,
    "options_volume": _options_volume,
    "perps_volume": _perps_volume,
    "prompt_to_sql_agent": _prompt_to_sql_agent,
    "protocol_directory": _protocol_directory,
    "protocol_fundamentals": _protocol_fundamentals,
    "raises_funding_rounds": _raises_funding_rounds,
    "research_templates": _research_templates,
    "rwa_intelligence": _rwa_intelligence,
    "scheduled_queries": _scheduled_queries,
    "sector_ecosystem_comparables": _sector_ecosystem_comparables,
    "stablecoin_activity_breakdown": _stablecoin_activity_breakdown,
    "stablecoin_intelligence": _stablecoin_intelligence,
    "stablecoin_payment_intelligence": _stablecoin_payment_intelligence,
    "stablecoins_intelligence": _stablecoins_intelligence,
    "thesis_research_workspace": _thesis_research_workspace,
    "treasury_intelligence": _treasury_intelligence,
    "yield_history": _yield_history,
    "yields_screener": _yields_screener,
}


def compute_semantic_extra(cap_id: int, *, symbol: str, seed: dict[str, Any]) -> dict[str, Any]:
    spec = CAPABILITY_SEMANTIC_SPECS[cap_id]
    inputs = _inputs(seed, cap_id, spec["defaults"])
    transform = RULES[spec["rule"]]
    payload = transform(inputs, symbol.upper())
    payload["feature"] = spec["feature"]
    payload["semantic_rule"] = spec["rule"]
    payload["attribution"] = "BLACKDARK batch14 extension analytics layer"
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

