"""Tests — Derivatives & On-Chain Intelligence (#262–#300)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import derivatives_onchain_intelligence_layer as doi


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset():
    doi.reset_derivatives_onchain_intelligence_state()
    yield
    doi.reset_derivatives_onchain_intelligence_state()


@pytest.mark.parametrize(
    "cap_id,fn_name,field",
    [
        (262, "options_open_interest_262", "oi_usd"),
        (263, "options_volume_263", "volume_usd"),
        (264, "options_iv_skew_264", "skew"),
        (265, "max_pain_gamma_context_265", "max_pain"),
        (266, "spot_market_intelligence_266", "spot_score"),
        (267, "order_book_market_depth_267", "depth_usd"),
        (268, "historical_derivatives_data_268", "series_points"),
        (269, "exchange_comparison_269", "venues"),
        (270, "liquidation_cascade_proximity_270", "proximity_pct"),
        (271, "leverage_pressure_score_271", "pressure_score"),
        (272, "api_data_platform_status_272", "endpoints"),
        (273, "multi_model_liquidation_comparison_273", "models"),
        (274, "derivatives_alerts_status_274", "channels"),
        (275, "cross_domain_decision_intelligence_275", "domains"),
        (276, "entity_resolution_engine_276", "entities_resolved"),
        (277, "address_labeling_system_277", "labels"),
        (278, "entity_profiles_278", "profiles"),
        (280, "portfolio_holdings_280", "holdings"),
        (281, "balance_history_281", "points"),
        (282, "entity_pnl_282", "pnl_usd"),
        (283, "exchange_usage_intelligence_283", "usage_score"),
        (284, "top_counterparties_284", "counterparties"),
        (285, "network_graph_visualizer_285", "nodes"),
        (286, "automated_trace_path_finding_286", "paths"),
        (287, "cross_chain_trace_287", "chains"),
        (289, "token_exchange_flows_289", "net_flow_usd"),
        (290, "token_transaction_explorer_290", "transactions"),
        (291, "custom_dashboards_status_291", "dashboards"),
        (292, "custom_alerts_status_292", "alerts"),
        (293, "private_labels_status_293", "labels"),
        (294, "portfolio_archive_snapshot_294", "snapshots"),
        (295, "ai_market_insights_295", "insights"),
        (296, "whale_movement_intelligence_296", "movements"),
        (297, "fraud_suspicious_activity_297", "flags"),
        (298, "api_onchain_intelligence_298", "modules"),
        (300, "advanced_multi_asset_charting_300", "panels"),
    ],
)
def test_derivatives_onchain_capability(cap_id: int, fn_name: str, field: str, seed: dict):
    fn = getattr(doi, fn_name)
    if fn_name in {"api_data_platform_status_272", "derivatives_alerts_status_274", "fraud_suspicious_activity_297", "advanced_multi_asset_charting_300"}:
        out = fn(seed=seed)
    else:
        out = fn(symbol="BTC", seed=seed)
    assert out["ok"] is True
    assert out["capability_id"] == cap_id
    assert field in out
    assert out["analysis_only"] is True


def test_274_derivatives_alerts_rejects_auto_trade(seed):
    out = doi.derivatives_alerts_status_274(seed=seed)
    assert out["auto_trade_rejected"] is True


def test_297_fraud_flags(seed):
    out = doi.fraud_suspicious_activity_297(seed=seed)
    assert out["sar_auto_filing_rejected"] is True
    assert len(out["flags"]) >= 1


def test_300_multi_asset_panels(seed):
    out = doi.advanced_multi_asset_charting_300(symbols=["BTC", "ETH"], seed=seed)
    assert out["panels"] == 2
    assert out["multi_asset"] is True


def test_derivatives_onchain_e2e_262_300(seed):
    assert doi.run_derivatives_onchain_intelligence_e2e_262_300(seed=seed)["all_passed"] is True
