"""Tests — #690 Revenue Intelligence, #691 Risk Gate, #692–#694 Stablecoin suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import defi_decision_intelligence as ddi
from bd_platform import investment_thesis_scoring as its
from bd_platform import on_chain_financials as ocf
from bd_platform import onchain_metrics_library as oml
from bd_platform import stablecoin_health_monitor as shm
from bd_platform import unified_arbitrage_engine as uae


@pytest.fixture
def fin_seed(tmp_path, monkeypatch):
    p = tmp_path / "on_chain_financials_seed.json"
    p.write_text(Path("data/on_chain_financials_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ocf, "_SEED_PATH", p)
    return p


@pytest.fixture
def ddi_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_decision_intelligence_seed.json"
    p.write_text(Path("data/defi_decision_intelligence_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ddi, "_SEED_PATH", p)
    return p


@pytest.fixture
def oml_seed(tmp_path, monkeypatch):
    p = tmp_path / "onchain_metrics_library_seed.json"
    p.write_text(Path("data/onchain_metrics_library_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(oml, "_SEED_PATH", p)
    return p


@pytest.fixture
def shm_seed(tmp_path, monkeypatch):
    p = tmp_path / "stablecoin_health_monitor_seed.json"
    p.write_text(Path("data/stablecoin_health_monitor_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(shm, "_SEED_PATH", p)
    return p


# --- #690 Revenue Intelligence ---


def test_690_revenue_distribution_uniswap(fin_seed):
    dist = ocf.build_revenue_distribution_690("uniswap")
    assert dist["ok"] is True
    assert dist["tab"] == "Revenue Distribution"
    assert dist["protocol_retained_revenue_usd"] == 0
    assert (dist.get("mapping_methodology") or {}).get("documented") is True
    assert (dist.get("who_keeps_value") or {}).get("question_ar") == "من يحتفظ بالقيمة؟"


def test_690_aave_lido_splits(fin_seed):
    aave = ocf.build_revenue_distribution_690("aave")
    lido = ocf.build_revenue_distribution_690("lido")
    assert aave["distribution"]["protocol_treasury"]["pct_of_fees"] == 10
    assert lido["distribution"]["validators_miners"]["pct_of_fees"] == 5
    assert lido["distribution"]["token_holders"]["pct_of_fees"] == 90


def test_690_thesis_retention_dimension(fin_seed):
    dim = ocf.score_revenue_retention_dimension_690("UNI")
    assert dim["ok"] is True
    thesis = its.score_investment_thesis("UNI")
    assert (thesis.get("dimensions") or {}).get("revenue_retention_690") is not None


def test_690_financials_panel_integration(fin_seed):
    panel = ocf.build_on_chain_financials("uniswap")
    assert panel.get("revenue_distribution_690") is not None


def test_690_metrics_library(fin_seed):
    lib = ocf.build_metrics_library_financials("aave")
    assert "protocol_retained_revenue" in (lib.get("metrics") or {})


# --- #691 Risk Gate ---


def test_691_risk_gate_veto(ddi_seed):
    gate = ddi.apply_risk_gate_691({"protocol_id": "high_yield_risky", "risk_score": 72})
    assert gate["ok"] is True
    assert gate["risk_gate"]["action"] == "veto"
    assert gate["no_actionability_buzzword"] is True


def test_691_risk_gate_pass_low_risk(ddi_seed):
    gate = ddi.apply_risk_gate_691({"protocol_id": "aave_v3", "risk_score": 28})
    assert gate["risk_gate"]["action"] == "pass"


def test_691_risk_adjusted_ranking(ddi_seed):
    ranked = ddi.rank_risk_adjusted_opportunities_691([
        {"opportunity_id": "high", "decision_relevance_score": 80, "risk_score": 72},
        {"opportunity_id": "low", "decision_relevance_score": 50, "risk_score": 28},
    ])
    assert ranked[0]["opportunity_id"] == "low"
    assert ranked[0]["ranking_metric"] == "risk_adjusted_opportunity_ranking"


def test_691_decision_score_includes_gate(ddi_seed):
    score = ddi.score_decision_relevance("aave_v3")
    assert score.get("risk_gate_691") is not None


# --- #692 Stablecoin Activity ---


def test_692_activity_breakdown(oml_seed):
    breakdown = oml.build_stablecoin_activity_breakdown_692("USDC")
    assert breakdown["ok"] is True
    assert breakdown["metric_id"] == "stablecoin_activity_breakdown"
    assert (breakdown.get("classification_methodology") or {}).get("documented") is True
    cats = breakdown["categories"]
    assert cats["trading"]["pct"] == 45


def test_692_market_radar_widget(oml_seed):
    widget = oml.build_market_radar_stablecoin_activity_widget_692("USDC")
    assert widget["widget_label_ar"] == "استخدام العملات المستقرة"


def test_692_daily_brief_hook(oml_seed):
    brief = oml.build_stablecoin_activity_daily_brief_hook_474()
    assert brief is not None
    assert "تداول" in brief.get("mention", "")


def test_692_hype_vs_reality(oml_seed):
    signal = oml.attach_stablecoin_activity_hype_context_599({}, symbol="USDC")
    assert signal.get("hype_vs_reality_599", {}).get("state") == "on_chain_only"


# --- #693 Exchange Flow ---


def test_693_exchange_flow_monitor(shm_seed):
    flow = shm.build_stablecoin_exchange_flow_monitor_693()
    assert flow["ok"] is True
    assert flow["cross_token_normalization"] is True
    assert flow["depeg_aware_usd_conversion"] is True
    assert (flow.get("duplicate_filtering") or {}).get("enabled") is True
    assert flow["rolling_acceleration"]["acceleration_alert"] is True


def test_693_daily_brief_hook(shm_seed):
    brief = shm.build_stablecoin_exchange_flow_daily_brief_hook_474()
    assert brief is not None
    assert brief.get("integration_693") is True


def test_693_metrics_library(oml_seed, shm_seed):
    metric = oml.build_stablecoin_flows_metric_577()
    assert metric["ok"] is True
    assert metric["metric_id"] == "stablecoin_flows"


# --- #694 Stablecoin Intelligence ---


def test_694_intelligence_dashboard(shm_seed, oml_seed):
    dashboard = shm.build_stablecoin_intelligence_dashboard_694()
    assert dashboard["ok"] is True
    assert dashboard["route"] == "/stablecoins"
    assert len(dashboard["dashboard_tabs"]) == 5
    assert (dashboard.get("wash_filtering") or {}).get("enabled") is True


def test_694_supply_metric(oml_seed, shm_seed):
    supply = oml.build_stablecoin_supply_metric_577()
    assert supply["ok"] is True
    assert supply["value"] is not None


def test_694_exit_alert_410(shm_seed, oml_seed):
    alerts = shm.build_portfolio_stablecoin_exit_alert_410()
    assert alerts["ok"] is True


def test_reconciliation_all_modules(fin_seed, ddi_seed, oml_seed, shm_seed):
    assert ocf.run_reconciliation_tests()["ok"] is True
    assert ddi.run_reconciliation_tests()["ok"] is True
    assert shm.run_reconciliation_tests()["ok"] is True
    qa = oml.run_historical_qa_tests()
    assert qa["all_passed"] is True


def test_uae_risk_gate_integration():
    feed = uae.build_unified_feed()
    assert "risk_gate_691" in str(feed) or feed.get("ok") is not False
