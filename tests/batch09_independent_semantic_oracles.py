"""Independent reference oracles for Batch09 parameterized semantics (401–450).

Deliberately does NOT import bd_platform.batch09_semantic_engine RULES or compute_semantic_extra.
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


# rule -> primary semantic output field used for oracle cross-check
PRIMARY_FIELD: dict[str, str] = {
    "bridge_flow_ratio": "bridges_intelligence",
    "yield_screener_rank": "yields_screener",
    "yield_history_trend": "yield_history",
    "borrow_lend_spread": "borrowing_rates",
    "liquid_staking_yield": "liquid_staking_intelligence",
    "rwa_allocation": "rwa_intelligence",
    "funding_velocity": "raises_funding_rounds",
    "investor_breadth": "investor_profiles",
    "treasury_runway": "treasury_intelligence",
    "airdrop_pressure": "airdrop_incentive_intelligence",
    "capital_formation": "capital_formation_radar",
    "defi_opportunity": "defi_opportunity_screener",
    "risk_passport": "defi_risk_passport",
    "api_aggregation": "api_aggregation_layer",
    "cross_defi_decision": "cross_defi_decision_intelligence",
    "cross_chain_fundamentals": "cross_chain_fundamentals",
    "protocol_fundamentals": "protocol_fundamentals",
    "stablecoin_intel": "stablecoin_intelligence",
    "stablecoin_activity": "stablecoin_activity_breakdown",
    "developer_activity": "developer_activity",
    "sector_comparables": "sector_ecosystem_comparables",
    "equities_crypto": "equities_crypto_research",
    "consensus_estimates": "consensus_estimates",
    "ai_analyst": "ai_analyst",
    "thesis_workspace": "thesis_research",
    "comparable_company": "comparable_company",
    "excel_sheets": "excel_sheets",
    "api_data_platform": "api_data",
    "research_templates": "research_templates",
    "dashboards": "dashboards",
    "stablecoin_payment": "stablecoin_payment",
    "on_chain_usage": "on_chain",
    "revenue_fees": "revenue_fees",
    "cross_market_copilot": "cross_market",
    "investment_thesis": "investment_thesis",
    "lending_market_risk": "lending_market",
    "collateral_risk": "collateral_risk",
    "liquidation_risk": "liquidation_risk",
    "liquidity_risk": "liquidity_risk",
    "protocol_exploit": "protocol_exploit",
    "stablecoin_risk": "stablecoin_risk",
    "defi_strategy_risk": "defi_strategy",
    "real_time_alerts": "real_time",
    "dao_treasury": "dao_treasury",
    "institutional_risk_api": "institutional_risk_api",
    "curated_dashboards": "curated_on_chain_dashboards",
    "narrative_research": "narrative_driven_research",
}


def independent_primary(rule: str, inputs: dict[str, float], symbol: str = "ETH") -> float:
    i = inputs
    sym = symbol.upper()
    if rule == "bridge_flow_ratio":
        return _ratio(i["bridge_volume_usd"], i["tvl_usd"]) + i["flow_7d_change_pct"] * 0.15
    if rule == "yield_screener_rank":
        spread = i["top_pool_apy_pct"] - i["median_pool_apy_pct"]
        return round(spread * i["pool_count"], 4)
    if rule == "yield_history_trend":
        slope = (i["apy_day0_pct"] - i["apy_day30_pct"]) / 30.0
        return round(slope * 100 + i["volatility_pct"], 4)
    if rule == "borrow_lend_spread":
        return _spread(i["borrow_rate_bps"], i["supply_rate_bps"])
    if rule == "liquid_staking_yield":
        return round(i["staked_ratio_pct"] * i["validator_yield_pct"] / 100.0, 4)
    if rule == "rwa_allocation":
        return round(i["rwa_allocation_pct"] * i["tokenized_tvl_usd"] / 1e6, 4)
    if rule == "funding_velocity":
        return round(i["rounds_90d"] * i["median_raise_usd"] / 1e6, 4)
    if rule == "investor_breadth":
        return round(i["unique_investors"] * i["avg_ticket_usd"] / 1e6, 4)
    if rule == "treasury_runway":
        return round(i["treasury_usd"] / max(i["monthly_burn_usd"], 1.0), 4)
    if rule == "airdrop_pressure":
        return round(i["pending_airdrop_usd"] / max(i["circulating_mcap_usd"], 1.0) * 100, 4)
    if rule == "capital_formation":
        return round(i["new_capital_usd"] / max(i["sector_tvl_usd"], 1.0) * 100, 4)
    if rule == "defi_opportunity":
        return _weighted((i["apy_pct"], 0.5), (i["tvl_usd"], 0.3), (100 - i["risk_score"], 0.2))
    if rule == "risk_passport":
        return _weighted((i["audit_score"], 0.4), (100 - i["exploit_history"], 0.35), (i["tvl_stability"], 0.25))
    if rule == "api_aggregation":
        return round(i["endpoint_count"] * i["freshness_score"], 4)
    if rule == "cross_defi_decision":
        return round(i["signal_a"] * 0.4 + i["signal_b"] * 0.35 + i["signal_c"] * 0.25, 4)
    if rule == "cross_chain_fundamentals":
        return round(i["active_chains"] * i["avg_tvl_per_chain_usd"] / 1e8, 4)
    if rule == "protocol_fundamentals":
        return round(i["revenue_usd"] / max(i["tvl_usd"], 1.0) * 10000, 4)
    if rule == "stablecoin_intel":
        return round(i["peg_deviation_bps"] + i["supply_change_7d_pct"], 4)
    if rule == "stablecoin_activity":
        return round(i["transfer_volume_usd"] / max(i["supply_usd"], 1.0) * 100, 4)
    if rule == "developer_activity":
        return round(i["commits_30d"] * i["contributor_count"] ** 0.5, 4)
    if rule == "sector_comparables":
        return round(i["sector_mcap_usd"] / max(i["peer_mcap_usd"], 1.0), 4)
    if rule == "equities_crypto":
        return round(i["equity_beta"] * i["crypto_correlation"], 4)
    if rule == "consensus_estimates":
        return round(i["estimate_high"] - i["estimate_low"], 4)
    if rule == "ai_analyst":
        return round(i["confidence"] * i["signal_strength"], 4)
    if rule == "thesis_workspace":
        return round(i["thesis_score"] * i["evidence_count"] ** 0.5, 4)
    if rule == "comparable_company":
        return round(i["target_metric"] / max(i["peer_median"], 1.0), 4)
    if rule == "excel_sheets":
        return round(i["export_rows"] * i["refresh_minutes"] ** -0.5, 4)
    if rule == "api_data_platform":
        return round(i["daily_api_calls"] / max(i["quota_calls"], 1.0) * 100, 4)
    if rule == "research_templates":
        return round(i["template_count"] * i["coverage_score"], 4)
    if rule == "dashboards":
        return round(i["widget_count"] * i["freshness_score"], 4)
    if rule == "stablecoin_payment":
        return round(i["payment_volume_usd"] / max(i["merchant_count"], 1.0) / 1e3, 4)
    if rule == "on_chain_usage":
        return round(i["daily_active_addresses"] * i["tx_per_user"], 4)
    if rule == "revenue_fees":
        return round(i["fees_24h_usd"] / max(i["tvl_usd"], 1.0) * 10000, 4)
    if rule == "cross_market_copilot":
        return round(i["equity_signal"] * 0.45 + i["crypto_signal"] * 0.55, 4)
    if rule == "investment_thesis":
        return _weighted((i["growth_score"], 0.35), (i["risk_score"], 0.25), (i["moat_score"], 0.4))
    if rule == "lending_market_risk":
        return round(i["utilization_pct"] * i["liquidation_buffer_pct"] ** -1, 4)
    if rule == "collateral_risk":
        return round(i["collateral_factor"] * i["price_volatility_pct"], 4)
    if rule == "liquidation_risk":
        return round(i["near_liq_positions"] / max(i["open_positions"], 1.0) * 100, 4)
    if rule == "liquidity_risk":
        return round(i["bid_ask_bps"] * i["depth_usd"] ** -0.5 * 1000, 4)
    if rule == "protocol_exploit":
        return round(i["exploit_incidents_12m"] * i["tvl_at_risk_usd"] / 1e8, 4)
    if rule == "stablecoin_risk":
        return round(i["depeg_events_12m"] * 10 + i["reserve_transparency_score"], 4)
    if rule == "defi_strategy_risk":
        return round(i["leverage_ratio"] * i["strategy_var_pct"], 4)
    if rule == "real_time_alerts":
        return round(i["alert_count_24h"] * i["severity_weight"], 4)
    if rule == "dao_treasury":
        return round(i["treasury_usd"] / max(i["token_holders"], 1.0), 4)
    if rule == "institutional_risk_api":
        return round(i["risk_score"] * i["coverage_pct"] / 100.0, 4)
    if rule == "curated_dashboards":
        return round(i["dashboard_count"] * i["metric_freshness_min"] ** -0.5, 4)
    if rule == "narrative_research":
        return round(i["narrative_strength"] * i["social_velocity"], 4)
    raise KeyError(f"unknown rule {rule}")


def independent_boundary_primary(rule: str, inputs: dict[str, float]) -> float:
    """Degraded/boundary inputs — independent oracle only."""
    degraded = dict(inputs)
    for key, val in list(degraded.items()):
        if isinstance(val, (int, float)) and val > 0:
            degraded[key] = val * 0.01
    return independent_primary(rule, degraded)


def oracle_437_risk_score(hack_pressure: float, tvl_volatility_pct: float) -> float:
    return round(min(100.0, max(0.0, hack_pressure * 0.55 + abs(tvl_volatility_pct) * 1.25)), 2)


def oracle_441_risk_score(status: str) -> float:
    return 10.0 if status == "fresh" else 55.0 if status == "stale" else 90.0 if status == "critical_stale" else 40.0
