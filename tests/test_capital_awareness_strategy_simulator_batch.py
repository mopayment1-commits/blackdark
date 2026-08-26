"""Tests — #410 Capital Awareness Controls + #411 Strategy Simulator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import capital_protection_controls as cac
from bd_platform import strategy_simulator as ss


@pytest.fixture
def cac_seed(tmp_path, monkeypatch):
    main = Path("data/capital_protection_controls_seed.json")
    p = tmp_path / "capital_protection_controls_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(cac, "_SEED_PATH", p)
    return p


@pytest.fixture
def ss_seed(tmp_path, monkeypatch):
    main = Path("data/strategy_simulator_seed.json")
    p = tmp_path / "strategy_simulator_seed.json"
    p.write_text(main.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ss, "_SEED_PATH", p)
    return p


# --- #410 ---


def test_410_status_non_executive(cac_seed):
    status = cac.capital_protection_controls_status()
    assert status["feature_id"] == 410
    assert status["standalone"] is False
    assert status["non_executive"] is True
    assert status["no_automatic_fund_movement"] is True
    assert status["legal_name"] == "Risk Awareness Layer"


def test_410_sla_no_auto_movement(cac_seed):
    panel = cac.build_capital_awareness_panel()
    sla = panel["sla_terms"]
    assert sla["no_automatic_fund_movement"] is True
    assert "never moves funds automatically" in sla["legal_text"].lower()


def test_410_risk_score_per_position(cac_seed):
    panel = cac.build_capital_awareness_panel()
    scores = panel["position_risk_scores"]
    assert "pos_btc_001" in scores
    assert 0 <= scores["pos_btc_001"]["risk_score"] <= 100
    assert scores["pos_btc_001"]["analytics_only"] is True


def test_410_scenario_stress_five_types(cac_seed):
    panel = cac.build_capital_awareness_panel()
    stress = panel["scenario_stress"]
    assert stress["scenario_count"] == 5
    types = {s["scenario_type"] for s in stress["scenarios"]}
    assert types == {
        "max_drawdown", "correlation_shock", "liquidity_freeze",
        "stablecoin_depeg", "exchange_insolvency",
    }


def test_453_portfolio_stress_test(cac_seed):
    result = cac.run_portfolio_stress_test()
    assert result["ok"] is True
    assert result["metrics"]["coverage_pct"] >= 80
    assert result["metrics"]["repeatable"] is True
    assert result["metrics"]["controlled_blast_radius"] is True
    assert "AI" not in result["stress_summary"]["title"]


def test_463_correlation_matrix(cac_seed):
    matrix = cac.build_correlation_matrix()
    assert matrix["lookback_days"] == 30
    assert len(matrix["assets"]) >= 3


def test_463_contagion_risk(cac_seed):
    contagion = cac.analyze_contagion_risk()
    assert contagion["contagion_score"] is not None
    assert "sector_exposure" in contagion


def test_462_collateral_grade_alerts(cac_seed):
    alerts = cac.build_collateral_grade_alerts()
    assert alerts["threshold_grade"] == "B"


def test_410_risk_budget(cac_seed):
    panel = cac.build_capital_awareness_panel()
    budget = panel["risk_budget"]
    assert budget["risk_budget"] is True
    assert budget["user_configured_max_loss_pct"] == 8.0
    assert budget["no_automatic_action"] is True


def test_410_portfolio_ai_alerts(cac_seed):
    panel = cac.build_capital_awareness_panel()
    alerts = panel["portfolio_ai_alerts"]
    assert alerts["non_executive"] is True
    assert alerts["alert_count"] >= 1


def test_410_intelligence_ledger_risk_assessment(cac_seed):
    assessment = cac.build_signal_risk_assessment("sig_btc_momentum")
    assert assessment["risk_assessment_mandatory"] is True
    assert assessment["no_automatic_fund_movement"] is True
    assert assessment["position_risk_score"]["risk_score"] is not None


def test_410_reconciliation(cac_seed):
    result = cac.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]


# --- #411 ---


def test_411_status_simulation_only(ss_seed):
    status = ss.strategy_simulator_status()
    assert status["feature_id"] == 411
    assert status["standalone"] is False
    assert status["real_money_blocked"] is True
    assert status["ems_name_forbidden"] is True
    assert status["legal_name"] == "Paper Portfolio"


def test_411_live_order_blocked(ss_seed):
    blocked = ss._block_live_order({"status": "live_submitted"})
    assert blocked["blocked"] is True
    assert blocked["simulation_only"] is True


def test_411_paper_order(ss_seed):
    order = ss.build_paper_order(symbol="BTC", side="buy", quantity=0.1, price=65000)
    assert order["ok"] is True
    assert order["order"]["simulation_only"] is True
    assert order["order"]["status"] == "paper_filled"


def test_411_breakeven_integration_404(ss_seed):
    panel = ss.build_strategy_simulator_panel()
    be = panel["breakeven_integration"]
    assert be["ok"] is True
    assert "BTC" in be["positions"]
    assert be["simulation_only"] is True


def test_411_risk_budget_integration_410(ss_seed):
    panel = ss.build_strategy_simulator_panel()
    rb = panel["risk_budget_integration"]
    assert rb["ok"] is True
    assert rb["feature_id"] == 410


def test_411_backtest_30d(ss_seed):
    panel = ss.build_strategy_simulator_panel()
    bt = panel["backtest_30d"]
    assert bt["ok"] is True
    assert bt["simulation_only"] is True
    assert bt["period"]["days"] == 30


def test_411_apply_signal(ss_seed):
    result = ss.apply_signal_to_paper_portfolio("sig_btc_momentum")
    assert result["ok"] is True
    assert result["simulation_only"] is True
    assert "SIMULATION" in result["display"]


def test_411_reconciliation(ss_seed):
    result = ss.run_reconciliation_tests()
    assert result["ok"] is True
    assert result["passed"] == result["total"]


def test_410_411_api_routes(cac_seed, ss_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/capital-awareness/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/capital-awareness").status_code == 200
    r = c.get("/api/platform/intelligence-ledger/intelligence-layer/capital-awareness/risk-assessment?signal_id=sig_btc_momentum")
    assert r.status_code == 200
    assert r.json()["risk_assessment_mandatory"] is True
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/strategy-simulator").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/apply-signal?signal_id=sig_btc_momentum").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/backtest-30d").status_code == 200
    tests_410 = c.get("/api/platform/intelligence-ledger/portfolio-ai/capital-awareness/reconciliation-tests")
    tests_411 = c.get("/api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/reconciliation-tests")
    assert tests_410.json()["ok"] is True
    assert tests_411.json()["ok"] is True
