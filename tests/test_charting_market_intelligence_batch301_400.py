"""Tests — Charting & Market Intelligence (#301–#400 generated surfaces)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import charting_market_intelligence_layer as cmi


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "cap_id,fn_name,field",
    [
        (301, "multi_chart_layouts_301", "multi_chart"),
        (302, "technical_indicator_library_302", "technical_indicator"),
        (303, "custom_indicator_scripting_303", "custom_indicator"),
        (304, "strategy_backtesting_304", "strategy_backtesting"),
        (305, "market_screener_305", "market_screener"),
        (306, "pine_style_screener_306", "pine_style"),
        (307, "smart_alerts_307", "smart_alerts"),
        (308, "watchlists_308", "watchlists"),
        (309, "economic_calendar_309", "economic_calendar"),
        (310, "crypto_calendar_events_310", "crypto_calendar"),
        (311, "news_integration_311", "news_integration"),
        (312, "heatmaps_312", "heatmaps"),
        (313, "technical_ratings_313", "technical_ratings"),
        (314, "drawing_tools_314", "drawing_tools"),
        (315, "replay_mode_315", "replay_mode"),
        (317, "community_scripts_317", "community_scripts"),
        (318, "broker_comparison_318", "broker_comparison"),
        (319, "paper_trading_simulation_319", "paper_trading"),
        (320, "cross_market_workspace_320", "cross_market"),
        (321, "custom_intelligence_screener_321", "custom_intelligence"),
        (322, "decision_first_mode_322", "decision_first"),
        (323, "institutional_l1_l2_market_data_323", "institutional_l"),
        (324, "reference_data_registry_324", "reference_data"),
        (325, "spot_derivatives_coverage_325", "spot_derivatives"),
        (326, "defi_market_data_326", "defi_market"),
        (327, "market_depth_liquidity_intelligence_327", "market_depth"),
        (328, "fair_market_value_pricing_328", "fair_market"),
        (329, "best_execution_pricing_329", "best_execution"),
        (332, "commodity_tradfi_reference_rates_332", "commodity_tradfi"),
        (333, "indices_333", "indices"),
        (334, "risk_analytics_334", "risk_analytics"),
        (335, "derivatives_listing_analytics_335", "derivatives_listing"),
        (336, "market_surveillance_336", "market_surveillance"),
        (337, "aml_cft_on_chain_monitoring_337", "aml_cft"),
        (338, "data_quality_pipeline_338", "data_quality"),
        (340, "real_time_rest_grpc_streaming_340", "real_time"),
        (341, "historical_data_archive_341", "historical_data"),
        (342, "venue_quality_ranking_342", "venue_quality"),
        (343, "execution_quality_analytics_343", "execution_quality"),
        (344, "institutional_sla_monitoring_344", "institutional_sla"),
        (345, "cross_market_institutional_decision_layer_345", "cross_market"),
        (346, "standardized_financial_metrics_346", "standardized_financial"),
        (347, "fees_intelligence_347", "fees_intelligence"),
        (348, "revenue_intelligence_348", "revenue_intelligence"),
        (349, "token_incentives_349", "token_incentives"),
        (350, "earnings_economic_profit_proxy_350", "earnings_economic"),
        (351, "active_users_351", "active_users"),
        (352, "core_developers_352", "core_developers"),
        (353, "code_commits_353", "code_commits"),
        (354, "tvl_intelligence_354", "tvl_intelligence"),
        (355, "borrowed_loans_outstanding_355", "borrowed_loans"),
        (357, "stablecoin_supply_357", "stablecoin_supply"),
        (358, "valuation_multiples_358", "valuation_multiples"),
        (359, "growth_metrics_359", "growth_metrics"),
        (360, "margins_take_rate_360", "margins_take"),
        (361, "project_comparables_361", "project_comparables"),
        (362, "sector_comparables_362", "sector_comparables"),
        (363, "tokenized_asset_coverage_363", "tokenized_asset"),
        (364, "fundamental_screener_364", "fundamental_screener"),
        (365, "financial_statement_view_365", "financial_statement"),
        (366, "data_methodology_registry_366", "data_methodology"),
        (367, "source_data_provenance_367", "source_data"),
        (368, "api_data_export_368", "api_data"),
        (369, "cross_fundamental_decision_intelligence_369", "cross_fundamental"),
        (370, "sql_on_chain_query_workspace_370", "sql_on"),
        (371, "curated_data_models_371", "curated_data"),
        (372, "decoded_smart_contract_tables_372", "decoded_smart"),
        (373, "cross_chain_data_warehouse_373", "cross_chain"),
        (374, "visualization_builder_374", "visualization_builder"),
        (375, "dashboard_builder_375", "dashboard_builder"),
        (376, "public_dashboard_sharing_376", "public_dashboard"),
        (377, "community_discovery_377", "community_discovery"),
        (383, "bi_connectors_383", "bi_connectors"),
        (384, "mcp_for_ai_agents_384", "mcp_for"),
        (385, "prompt_to_sql_agent_385", "prompt_to"),
        (386, "dashboard_from_prompt_386", "dashboard_from"),
        (387, "scheduled_queries_387", "scheduled_queries"),
        (388, "alerts_from_query_results_388", "alerts_from"),
        (389, "data_lineage_389", "data_lineage"),
        (391, "white_label_embedded_analytics_391", "white_label"),
        (392, "cross_domain_decision_layer_392", "cross_domain"),
        (394, "chain_tvl_comparison_394", "chain_tvl"),
        (395, "protocol_directory_395", "protocol_directory"),
        (397, "dex_volume_397", "dex_volume"),
        (398, "perps_volume_398", "perps_volume"),
        (399, "options_volume_399", "options_volume"),
        (400, "stablecoins_intelligence_400", "stablecoins_intelligence"),
    ],
)
def test_charting_market_capability(cap_id: int, fn_name: str, field: str, seed: dict):
    fn = getattr(cmi, fn_name)
    out = fn(symbol="BTC", seed=seed)
    assert out["ok"] is True
    assert out["capability_id"] == cap_id
    assert field in out
    assert out["analysis_only"] is True


def test_e2e_batch_smoke(seed: dict):
    out = cmi.run_charting_market_intelligence_e2e_batch(seed=seed)
    assert out["ok"] is True
    assert out["sample_ok"] is True
