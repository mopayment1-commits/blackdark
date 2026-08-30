"""Tests — Arbitrage, Portfolio & UX (#177–#191)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import arbitrage_portfolio_ux_layer as apu


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset():
    apu.reset_arbitrage_portfolio_ux_state()
    yield
    apu.reset_arbitrage_portfolio_ux_state()


def test_177_arbitrage_cost(seed):
    cost = apu.analyze_arbitrage_cost_177(seed=seed)
    assert cost["no_execution"] is True
    assert "net_spread_pct" in cost["cost_breakdown"]


def test_178_scenario_drawdown(seed):
    scenarios = apu.run_scenario_drawdown_analysis_178(seed=seed)
    assert len(scenarios["scenarios"]) == 3
    assert scenarios["simulation_not_prediction"] is True


def test_178_risk_embed(seed):
    from bd_platform.whales_institutional_layer import build_advanced_risk_report_77

    risk = build_advanced_risk_report_77([{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}], seed=seed)
    assert "scenario_analysis" in risk
    assert 178 in risk["merged_features"]


def test_179_command_center(seed):
    dash = apu.build_command_center_dashboard_179(seed=seed)
    assert dash["route"] == "/dashboard"
    assert len(dash["widgets"]) >= 1


def test_180_whale_visualization(seed):
    from bd_platform.pro_trader_layer import build_whale_narrative_71

    narrative = build_whale_narrative_71(seed=seed)
    assert "visualization" in narrative
    assert 180 in narrative["merged_features"]


def test_181_committee_packets(seed):
    assert apu.committee_packets_status_181(seed=seed)["duplicate_of"] == 87


def test_182_white_label_infra(seed):
    assert apu.white_label_infrastructure_status_182(seed=seed)["wave"] == 3


def test_183_b2b_integration(seed):
    assert apu.b2b_fund_integration_status_183(seed=seed)["no_execution_integration"] is True


def test_184_fund_reporting(seed):
    assert apu.fund_reporting_status_184(seed=seed)["scheduled_ic_reports"] is True


def test_185_acquisition_deferred(seed):
    pkg = apu.acquisition_evidence_package_185(seed=seed)
    assert pkg["not_a_technical_module"] is True


def test_186_continuous_learning(seed):
    assert apu.continuous_learning_status_186(seed=seed)["duplicate_of"] == 97


def test_187_latency_monitoring(seed):
    assert apu.latency_monitoring_status_187(seed=seed)["consolidation_not_build"] is True


def test_188_execution_rejected(seed):
    alert = apu.risk_alert_user_confirmation_188(seed=seed)
    assert alert["controlled_automation_rejected"] is True


def test_189_liquidity_capacity(seed):
    cap = apu.analyze_liquidity_capacity_189(seed=seed)
    assert cap["analytical_not_execution"] is True


def test_190_geographic_arbitrage(seed):
    geo = apu.analyze_geographic_arbitrage_190(seed=seed)
    assert geo["no_exploitation_language"] is True


def test_191_withdrawal_alert(seed):
    alert = apu.withdrawal_suspension_alert_191(seed=seed)
    assert alert["exploitation_language_rejected"] is True


def test_153_arbitrage_extensions(seed):
    from bd_platform.intelligence_analysis_layer import analyze_arbitrage_opportunity_153

    arb = analyze_arbitrage_opportunity_153(seed=seed)
    assert "cost_analysis" in arb
    assert 177 in arb["merged_features"]


def test_arbitrage_portfolio_ux_e2e(seed):
    assert apu.run_arbitrage_portfolio_ux_e2e_177_191(seed=seed)["all_passed"] is True
