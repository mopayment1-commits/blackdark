"""Batch09 (401–450) capability-specific semantic transforms for defi/yield shared core."""

from __future__ import annotations

from typing import Any, Callable

TransformFn = Callable[[dict[str, float], str], dict[str, Any]]


from bd_platform.batch_semantic_primitives import ratio as _ratio, semantic_inputs as _inputs, spread as _spread, weighted as _weighted


def _bridge_flow_ratio(i: dict[str, float], symbol: str) -> dict[str, Any]:
    score = _ratio(i["bridge_volume_usd"], i["tvl_usd"]) + i["flow_7d_change_pct"] * 0.15
    return {
        "bridges_intelligence": score,
        "bridge_flow_ratio_pct": _ratio(i["bridge_volume_usd"], i["tvl_usd"]),
        "flow_7d_change_pct": i["flow_7d_change_pct"],
        "symbol_focus": symbol.upper(),
    }


def _yield_screener_rank(i: dict[str, float], symbol: str) -> dict[str, Any]:
    spread = i["top_pool_apy_pct"] - i["median_pool_apy_pct"]
    return {
        "yields_screener": round(spread * i["pool_count"], 4),
        "top_pool_apy_pct": i["top_pool_apy_pct"],
        "median_pool_apy_pct": i["median_pool_apy_pct"],
        "rank_spread_bps": round(spread * 100, 2),
    }


def _yield_history_trend(i: dict[str, float], symbol: str) -> dict[str, Any]:
    slope = (i["apy_day0_pct"] - i["apy_day30_pct"]) / 30.0
    return {
        "yield_history": round(slope * 100 + i["volatility_pct"], 4),
        "apy_slope_per_day": round(slope, 4),
        "lookback_days": 30,
    }


def _borrow_lend_spread(i: dict[str, float], symbol: str) -> dict[str, Any]:
    spread = _spread(i["borrow_rate_bps"], i["supply_rate_bps"])
    return {
        "borrowing_rates": spread,
        "borrow_supply_spread_bps": spread,
        "utilization_pct": i["utilization_pct"],
    }


def _liquid_staking_yield(i: dict[str, float], symbol: str) -> dict[str, Any]:
    score = i["staked_ratio_pct"] * i["validator_yield_pct"] / 100.0
    return {
        "liquid_staking_intelligence": round(score, 4),
        "staked_ratio_pct": i["staked_ratio_pct"],
        "validator_yield_pct": i["validator_yield_pct"],
    }


def _rwa_allocation(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "rwa_intelligence": round(i["rwa_allocation_pct"] * i["tokenized_tvl_usd"] / 1e6, 4),
        "rwa_allocation_pct": i["rwa_allocation_pct"],
        "tokenized_tvl_musd": round(i["tokenized_tvl_usd"] / 1e6, 2),
    }


def _funding_velocity(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "raises_funding_rounds": round(i["rounds_90d"] * i["median_raise_usd"] / 1e6, 4),
        "rounds_90d": i["rounds_90d"],
        "median_raise_musd": round(i["median_raise_usd"] / 1e6, 2),
    }


def _investor_breadth(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "investor_profiles": round(i["unique_investors"] * i["avg_ticket_usd"] / 1e6, 4),
        "unique_investors": i["unique_investors"],
        "avg_ticket_musd": round(i["avg_ticket_usd"] / 1e6, 2),
    }


def _treasury_runway(i: dict[str, float], symbol: str) -> dict[str, Any]:
    runway = i["treasury_usd"] / max(i["monthly_burn_usd"], 1.0)
    return {
        "treasury_intelligence": round(runway, 4),
        "runway_months": round(runway, 2),
        "treasury_musd": round(i["treasury_usd"] / 1e6, 2),
    }


def _airdrop_pressure(i: dict[str, float], symbol: str) -> dict[str, Any]:
    pressure = i["pending_airdrop_usd"] / max(i["circulating_mcap_usd"], 1.0) * 100
    return {
        "airdrop_incentive_intelligence": round(pressure, 4),
        "airdrop_pressure_pct": round(pressure, 2),
        "eligible_wallets": i["eligible_wallets"],
    }


def _capital_formation(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "capital_formation_radar": round(i["new_capital_usd"] / max(i["sector_tvl_usd"], 1.0) * 100, 4),
        "new_capital_musd": round(i["new_capital_usd"] / 1e6, 2),
        "sector": i.get("sector_score", 1.0),
    }


def _defi_opportunity(i: dict[str, float], symbol: str) -> dict[str, Any]:
    score = _weighted((i["apy_pct"], 0.5), (i["tvl_usd"], 0.3), (100 - i["risk_score"], 0.2))
    return {"defi_opportunity_screener": score, "risk_adjusted_rank": score}


def _risk_passport(i: dict[str, float], symbol: str) -> dict[str, Any]:
    grade = _weighted((i["audit_score"], 0.4), (100 - i["exploit_history"], 0.35), (i["tvl_stability"], 0.25))
    return {"defi_risk_passport": grade, "passport_grade": grade}


def _api_aggregation(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "api_aggregation_layer": round(i["endpoint_count"] * i["freshness_score"], 4),
        "endpoint_count": i["endpoint_count"],
        "freshness_score": i["freshness_score"],
    }


def _cross_defi_decision(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "cross_defi_decision_intelligence": round(i["signal_a"] * 0.4 + i["signal_b"] * 0.35 + i["signal_c"] * 0.25, 4),
        "composite_signal": round(i["signal_a"] + i["signal_b"] + i["signal_c"], 4),
    }


def _cross_chain_fundamentals(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "cross_chain_fundamentals": round(i["active_chains"] * i["avg_tvl_per_chain_usd"] / 1e8, 4),
        "active_chains": i["active_chains"],
    }


def _protocol_fundamentals(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "protocol_fundamentals": round(i["revenue_usd"] / max(i["tvl_usd"], 1.0) * 10000, 4),
        "revenue_to_tvl_bps": round(i["revenue_usd"] / max(i["tvl_usd"], 1.0) * 10000, 2),
    }


def _stablecoin_intel(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "stablecoin_intelligence": round(i["peg_deviation_bps"] + i["supply_change_7d_pct"], 4),
        "peg_deviation_bps": i["peg_deviation_bps"],
    }


def _stablecoin_activity(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "stablecoin_activity_breakdown": round(i["transfer_volume_usd"] / max(i["supply_usd"], 1.0) * 100, 4),
        "velocity_ratio_pct": round(i["transfer_volume_usd"] / max(i["supply_usd"], 1.0) * 100, 2),
    }


def _developer_activity(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "developer_activity": round(i["commits_30d"] * i["contributor_count"] ** 0.5, 4),
        "commits_30d": i["commits_30d"],
        "contributor_count": i["contributor_count"],
    }


def _sector_comparables(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "sector_ecosystem_comparables": round(i["sector_mcap_usd"] / max(i["peer_mcap_usd"], 1.0), 4),
        "relative_mcap_ratio": round(i["sector_mcap_usd"] / max(i["peer_mcap_usd"], 1.0), 2),
    }


def _equities_crypto(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "equities_crypto_research": round(i["equity_beta"] * i["crypto_correlation"], 4),
        "equity_beta": i["equity_beta"],
        "crypto_correlation": i["crypto_correlation"],
    }


def _consensus_estimates(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "consensus_estimates": round(i["estimate_high"] - i["estimate_low"], 4),
        "estimate_spread": round(i["estimate_high"] - i["estimate_low"], 2),
    }


def _ai_analyst(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "ai_analyst": round(i["confidence"] * i["signal_strength"], 4),
        "narrative_confidence": i["confidence"],
        "signal_strength": i["signal_strength"],
        "consumer_mode": "AI/copilot synthesis",
    }


def _thesis_workspace(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "thesis_research": round(i["thesis_score"] * i["evidence_count"] ** 0.5, 4),
        "thesis_score": i["thesis_score"],
        "evidence_count": i["evidence_count"],
        "consumer_mode": "research workspace",
    }


def _comparable_company(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "comparable_company": round(i["target_metric"] / max(i["peer_median"], 1.0), 4),
        "peer_relative_multiple": round(i["target_metric"] / max(i["peer_median"], 1.0), 2),
    }


def _excel_sheets(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "excel_sheets": round(i["export_rows"] * i["refresh_minutes"] ** -0.5, 4),
        "export_rows": i["export_rows"],
        "refresh_minutes": i["refresh_minutes"],
        "consumer_mode": "Excel/Sheets connector export",
    }


def _api_data_platform(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "api_data": round(i["daily_api_calls"] / max(i["quota_calls"], 1.0) * 100, 4),
        "quota_utilization_pct": round(i["daily_api_calls"] / max(i["quota_calls"], 1.0) * 100, 2),
        "consumer_mode": "institutional API data platform",
    }


def _research_templates(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "research_templates": round(i["template_count"] * i["coverage_score"], 4),
        "template_count": i["template_count"],
    }


def _dashboards(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "dashboards": round(i["widget_count"] * i["freshness_score"], 4),
        "widget_count": i["widget_count"],
        "consumer_mode": "dashboard UI widgets",
    }


def _stablecoin_payment(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "stablecoin_payment": round(i["payment_volume_usd"] / max(i["merchant_count"], 1.0) / 1e3, 4),
        "avg_ticket_kusd": round(i["payment_volume_usd"] / max(i["merchant_count"], 1.0) / 1e3, 2),
    }


def _on_chain_usage(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "on_chain": round(i["daily_active_addresses"] * i["tx_per_user"], 4),
        "daily_active_addresses": i["daily_active_addresses"],
    }


def _revenue_fees(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "revenue_fees": round(i["fees_24h_usd"] / max(i["tvl_usd"], 1.0) * 10000, 4),
        "fee_yield_bps": round(i["fees_24h_usd"] / max(i["tvl_usd"], 1.0) * 10000, 2),
    }


def _cross_market_copilot(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "cross_market": round(i["equity_signal"] * 0.45 + i["crypto_signal"] * 0.55, 4),
        "copilot_blend_score": round(i["equity_signal"] * 0.45 + i["crypto_signal"] * 0.55, 2),
        "consumer_mode": "cross-market research copilot",
    }


def _investment_thesis(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "investment_thesis": round(_weighted((i["growth_score"], 0.35), (i["risk_score"], 0.25), (i["moat_score"], 0.4)), 4),
        "thesis_composite": round(i["growth_score"] + i["moat_score"] - i["risk_score"], 2),
    }


def _lending_market_risk(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "lending_market": round(i["utilization_pct"] * i["liquidation_buffer_pct"] ** -1, 4),
        "utilization_pct": i["utilization_pct"],
    }


def _collateral_risk(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "collateral_risk": round(i["collateral_factor"] * i["price_volatility_pct"], 4),
        "health_factor_proxy": round(i["collateral_factor"] / max(i["price_volatility_pct"], 0.1), 2),
    }


def _liquidation_risk(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "liquidation_risk": round(i["near_liq_positions"] / max(i["open_positions"], 1.0) * 100, 4),
        "near_liquidation_pct": round(i["near_liq_positions"] / max(i["open_positions"], 1.0) * 100, 2),
    }


def _liquidity_risk(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "liquidity_risk": round(i["bid_ask_bps"] * i["depth_usd"] ** -0.5 * 1000, 4),
        "depth_musd": round(i["depth_usd"] / 1e6, 2),
    }


def _protocol_exploit(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "protocol_exploit": round(i["exploit_incidents_12m"] * i["tvl_at_risk_usd"] / 1e8, 4),
        "exploit_incidents_12m": i["exploit_incidents_12m"],
    }


def _stablecoin_risk(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "stablecoin_risk": round(i["depeg_events_12m"] * 10 + i["reserve_transparency_score"], 4),
        "depeg_events_12m": i["depeg_events_12m"],
    }


def _defi_strategy_risk(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "defi_strategy": round(i["leverage_ratio"] * i["strategy_var_pct"], 4),
        "leverage_ratio": i["leverage_ratio"],
    }


def _real_time_alerts(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "real_time": round(i["alert_count_24h"] * i["severity_weight"], 4),
        "alert_count_24h": i["alert_count_24h"],
        "consumer_mode": "alert/event path",
    }


def _dao_treasury(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "dao_treasury": round(i["treasury_usd"] / max(i["token_holders"], 1.0), 4),
        "treasury_per_holder_usd": round(i["treasury_usd"] / max(i["token_holders"], 1.0), 2),
    }


def _institutional_risk_api(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "institutional_risk_api": round(i["risk_score"] * i["coverage_pct"] / 100.0, 4),
        "coverage_pct": i["coverage_pct"],
        "consumer_mode": "institutional risk API",
    }


def _curated_dashboards(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "curated_on_chain_dashboards": round(i["dashboard_count"] * i["metric_freshness_min"] ** -0.5, 4),
        "dashboard_count": i["dashboard_count"],
    }


def _narrative_research(i: dict[str, float], symbol: str) -> dict[str, Any]:
    return {
        "narrative_driven_research": round(i["narrative_strength"] * i["social_velocity"], 4),
        "narrative_strength": i["narrative_strength"],
    }


RULES: dict[str, TransformFn] = {
    "bridge_flow_ratio": _bridge_flow_ratio,
    "yield_screener_rank": _yield_screener_rank,
    "yield_history_trend": _yield_history_trend,
    "borrow_lend_spread": _borrow_lend_spread,
    "liquid_staking_yield": _liquid_staking_yield,
    "rwa_allocation": _rwa_allocation,
    "funding_velocity": _funding_velocity,
    "investor_breadth": _investor_breadth,
    "treasury_runway": _treasury_runway,
    "airdrop_pressure": _airdrop_pressure,
    "capital_formation": _capital_formation,
    "defi_opportunity": _defi_opportunity,
    "risk_passport": _risk_passport,
    "api_aggregation": _api_aggregation,
    "cross_defi_decision": _cross_defi_decision,
    "cross_chain_fundamentals": _cross_chain_fundamentals,
    "protocol_fundamentals": _protocol_fundamentals,
    "stablecoin_intel": _stablecoin_intel,
    "stablecoin_activity": _stablecoin_activity,
    "developer_activity": _developer_activity,
    "sector_comparables": _sector_comparables,
    "equities_crypto": _equities_crypto,
    "consensus_estimates": _consensus_estimates,
    "ai_analyst": _ai_analyst,
    "thesis_workspace": _thesis_workspace,
    "comparable_company": _comparable_company,
    "excel_sheets": _excel_sheets,
    "api_data_platform": _api_data_platform,
    "research_templates": _research_templates,
    "dashboards": _dashboards,
    "stablecoin_payment": _stablecoin_payment,
    "on_chain_usage": _on_chain_usage,
    "revenue_fees": _revenue_fees,
    "cross_market_copilot": _cross_market_copilot,
    "investment_thesis": _investment_thesis,
    "lending_market_risk": _lending_market_risk,
    "collateral_risk": _collateral_risk,
    "liquidation_risk": _liquidation_risk,
    "liquidity_risk": _liquidity_risk,
    "protocol_exploit": _protocol_exploit,
    "stablecoin_risk": _stablecoin_risk,
    "defi_strategy_risk": _defi_strategy_risk,
    "real_time_alerts": _real_time_alerts,
    "dao_treasury": _dao_treasury,
    "institutional_risk_api": _institutional_risk_api,
    "curated_dashboards": _curated_dashboards,
    "narrative_research": _narrative_research,
}


CAPABILITY_SEMANTIC_SPECS: dict[int, dict[str, Any]] = {
    401: {"rule": "bridge_flow_ratio", "defaults": {"bridge_volume_usd": 1.2e9, "tvl_usd": 4.5e9, "flow_7d_change_pct": 2.3}, "feature": "Bridges Intelligence"},
    402: {"rule": "yield_screener_rank", "defaults": {"top_pool_apy_pct": 8.2, "median_pool_apy_pct": 3.1, "pool_count": 42}, "feature": "Yields Screener"},
    403: {"rule": "yield_history_trend", "defaults": {"apy_day0_pct": 5.5, "apy_day30_pct": 4.1, "volatility_pct": 1.2}, "feature": "Yield History"},
    404: {"rule": "borrow_lend_spread", "defaults": {"borrow_rate_bps": 450, "supply_rate_bps": 180, "utilization_pct": 72}, "feature": "Borrowing Rates"},
    405: {"rule": "liquid_staking_yield", "defaults": {"staked_ratio_pct": 62, "validator_yield_pct": 3.8}, "feature": "Liquid Staking Intelligence"},
    406: {"rule": "rwa_allocation", "defaults": {"rwa_allocation_pct": 12.5, "tokenized_tvl_usd": 2.1e9}, "feature": "RWA Intelligence"},
    407: {"rule": "funding_velocity", "defaults": {"rounds_90d": 6, "median_raise_usd": 18e6}, "feature": "Raises / Funding Rounds"},
    408: {"rule": "investor_breadth", "defaults": {"unique_investors": 28, "avg_ticket_usd": 2.5e6}, "feature": "Investor Profiles"},
    410: {"rule": "treasury_runway", "defaults": {"treasury_usd": 85e6, "monthly_burn_usd": 4.2e6}, "feature": "Treasury Intelligence"},
    411: {"rule": "airdrop_pressure", "defaults": {"pending_airdrop_usd": 12e6, "circulating_mcap_usd": 420e6, "eligible_wallets": 15000}, "feature": "Airdrop / Incentive Intelligence"},
    412: {"rule": "capital_formation", "defaults": {"new_capital_usd": 55e6, "sector_tvl_usd": 8e9, "sector_score": 1.0}, "feature": "Capital Formation Radar"},
    413: {"rule": "defi_opportunity", "defaults": {"apy_pct": 7.4, "tvl_usd": 1.1e9, "risk_score": 35}, "feature": "DeFi Opportunity Screener"},
    414: {"rule": "risk_passport", "defaults": {"audit_score": 82, "exploit_history": 15, "tvl_stability": 78}, "feature": "DeFi Risk Passport"},
    415: {"rule": "api_aggregation", "defaults": {"endpoint_count": 12, "freshness_score": 0.91}, "feature": "API Aggregation Layer"},
    416: {"rule": "cross_defi_decision", "defaults": {"signal_a": 0.62, "signal_b": 0.55, "signal_c": 0.48}, "feature": "Cross-DeFi Decision Intelligence"},
    417: {"rule": "cross_chain_fundamentals", "defaults": {"active_chains": 7, "avg_tvl_per_chain_usd": 2.5e8}, "feature": "Cross-Chain Fundamentals"},
    418: {"rule": "protocol_fundamentals", "defaults": {"revenue_usd": 1.8e6, "tvl_usd": 3.2e9}, "feature": "Protocol Fundamentals"},
    419: {"rule": "stablecoin_intel", "defaults": {"peg_deviation_bps": 3.5, "supply_change_7d_pct": 1.2}, "feature": "Stablecoin Intelligence"},
    420: {"rule": "stablecoin_activity", "defaults": {"transfer_volume_usd": 4.5e9, "supply_usd": 32e9}, "feature": "Stablecoin Activity Breakdown"},
    421: {"rule": "developer_activity", "defaults": {"commits_30d": 145, "contributor_count": 22}, "feature": "Developer Activity"},
    422: {"rule": "sector_comparables", "defaults": {"sector_mcap_usd": 12e9, "peer_mcap_usd": 9e9}, "feature": "Sector / Ecosystem Comparables"},
    423: {"rule": "equities_crypto", "defaults": {"equity_beta": 1.15, "crypto_correlation": 0.68}, "feature": "Equities × Crypto Research"},
    424: {"rule": "consensus_estimates", "defaults": {"estimate_high": 125, "estimate_low": 98}, "feature": "Consensus Estimates"},
    425: {"rule": "ai_analyst", "defaults": {"confidence": 0.78, "signal_strength": 0.65}, "feature": "AI Analyst"},
    426: {"rule": "thesis_workspace", "defaults": {"thesis_score": 0.72, "evidence_count": 14}, "feature": "Thesis Research Workspace"},
    427: {"rule": "comparable_company", "defaults": {"target_metric": 18.5, "peer_median": 14.2}, "feature": "Comparable Company / Protocol Analysis"},
    428: {"rule": "excel_sheets", "defaults": {"export_rows": 2500, "refresh_minutes": 15}, "feature": "Excel / Sheets Integration"},
    429: {"rule": "api_data_platform", "defaults": {"daily_api_calls": 125000, "quota_calls": 250000}, "feature": "API Data Platform"},
    430: {"rule": "research_templates", "defaults": {"template_count": 18, "coverage_score": 0.84}, "feature": "Research Templates"},
    431: {"rule": "dashboards", "defaults": {"widget_count": 24, "freshness_score": 0.88}, "feature": "Dashboards"},
    432: {"rule": "stablecoin_payment", "defaults": {"payment_volume_usd": 850e6, "merchant_count": 4200}, "feature": "Stablecoin Payment Intelligence"},
    433: {"rule": "on_chain_usage", "defaults": {"daily_active_addresses": 125000, "tx_per_user": 2.4}, "feature": "On-Chain Usage Intelligence"},
    434: {"rule": "revenue_fees", "defaults": {"fees_24h_usd": 420000, "tvl_usd": 1.5e9}, "feature": "Revenue / Fees / Economic Activity"},
    435: {"rule": "cross_market_copilot", "defaults": {"equity_signal": 0.58, "crypto_signal": 0.71}, "feature": "Cross-Market Research Copilot"},
    436: {"rule": "investment_thesis", "defaults": {"growth_score": 72, "risk_score": 28, "moat_score": 65}, "feature": "Investment Thesis Scoring"},
    438: {"rule": "lending_market_risk", "defaults": {"utilization_pct": 81, "liquidation_buffer_pct": 12}, "feature": "Lending Market Risk"},
    439: {"rule": "collateral_risk", "defaults": {"collateral_factor": 0.78, "price_volatility_pct": 22}, "feature": "Collateral Risk"},
    440: {"rule": "liquidation_risk", "defaults": {"near_liq_positions": 145, "open_positions": 3200}, "feature": "Liquidation Risk"},
    442: {"rule": "liquidity_risk", "defaults": {"bid_ask_bps": 8.5, "depth_usd": 12e6}, "feature": "Liquidity Risk"},
    443: {"rule": "protocol_exploit", "defaults": {"exploit_incidents_12m": 2, "tvl_at_risk_usd": 450e6}, "feature": "Protocol Exploit Intelligence"},
    444: {"rule": "stablecoin_risk", "defaults": {"depeg_events_12m": 1, "reserve_transparency_score": 88}, "feature": "Stablecoin Risk Intelligence"},
    445: {"rule": "defi_strategy_risk", "defaults": {"leverage_ratio": 2.4, "strategy_var_pct": 18}, "feature": "DeFi Strategy Risk"},
    446: {"rule": "real_time_alerts", "defaults": {"alert_count_24h": 37, "severity_weight": 1.6}, "feature": "Real-Time Risk Alerts"},
    447: {"rule": "dao_treasury", "defaults": {"treasury_usd": 120e6, "token_holders": 45000}, "feature": "DAO Treasury Risk"},
    448: {"rule": "institutional_risk_api", "defaults": {"risk_score": 42, "coverage_pct": 93}, "feature": "Institutional Risk API"},
    449: {"rule": "curated_dashboards", "defaults": {"dashboard_count": 9, "metric_freshness_min": 12}, "feature": "Curated On-Chain Dashboards"},
    450: {"rule": "narrative_research", "defaults": {"narrative_strength": 0.74, "social_velocity": 1.35}, "feature": "Narrative-Driven Research"},
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
