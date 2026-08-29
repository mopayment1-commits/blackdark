"""Tests — Intelligence & Analysis (#153–#163)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import intelligence_analysis_layer as ia


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset():
    ia.reset_intelligence_analysis_state()
    yield
    ia.reset_intelligence_analysis_state()


def test_153_arbitrage_mind(seed):
    arb = ia.analyze_arbitrage_opportunity_153(seed=seed)
    assert arb["no_execution"] is True
    assert arb["cost_breakdown"]["net_spread_pct"] is not None
    assert arb["venues"]["binance"]["liquidity_tier"] == "large"


def test_154_financial_brain_merged(seed):
    fb = ia.financial_brain_status_154(seed=seed)
    assert fb["activation_not_build"] is True
    assert "multi_dim_analysis_73" in fb["merged_into"]


def test_155_stat_arb_rejected_execution(seed):
    stat = ia.stat_arb_insight_155(seed=seed)
    assert stat["no_entry_signal"] is True
    assert stat["no_exit_signal"] is True
    assert stat["z_score"] == 2.3


def test_156_asset_registry_105(seed):
    reg = ia.asset_registry_105_coins_156(seed=seed)
    assert reg["actual_count"] == 105
    assert reg["criteria_visible"] is True
    assert reg["assets"][0]["registry_id"]


def test_157_onchain_advanced_merged(seed):
    oc = ia.onchain_advanced_status_157(seed=seed)
    assert oc["no_duplicate_pricing"] is True
    assert "whale_narrative_71" in oc["merged_into"]


def test_158_multi_venue_websocket(seed):
    from bd_platform.infra_intelligence_layer import streaming_stack_status_96

    ws = ia.multi_venue_websocket_status_158(seed=seed)
    assert ws["deduplication_required"] is True
    assert len(ws["venues"]) >= 4
    stream = streaming_stack_status_96(seed=seed)
    assert "multi_venue_websocket" in stream


def test_159_gas_profile(seed):
    gas = ia.compute_gas_volatility_profile_159(current_gwei=18.0, seed=seed)
    assert gas["no_execution"] is True
    assert gas["optimal_windows"]


def test_160_volatility_squeeze(seed):
    squeeze = ia.detect_volatility_squeeze_160(seed=seed)
    assert squeeze["formula_visible"] is True
    assert "bollinger_width" in squeeze


def test_161_alert_delivery(seed):
    delivery = ia.alert_delivery_status_161(channel="discord", user_tier="institution", seed=seed)
    assert delivery["no_execution_buttons"] is True
    assert delivery["priority_queue"] == 1


def test_162_data_grid_ui(seed):
    grid = ia.data_grid_ui_status_162(seed=seed)
    assert "virtual_scrolling" in grid["optimizations"]
    assert grid["target_fps"] == 60


def test_163_institutional_insight_report(seed):
    report = ia.build_institutional_insight_report_163(asset="ETH", seed=seed)
    assert report["alpha_language_rejected"] is True
    assert report["predictive_language_rejected"] is True
    assert "sections" in report


def test_intelligence_analysis_e2e(seed):
    assert ia.run_intelligence_analysis_e2e_153_163(seed=seed)["all_passed"] is True
