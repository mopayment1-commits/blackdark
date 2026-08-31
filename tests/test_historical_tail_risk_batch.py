"""Tests — #503 + #504 Historical Tail Risk Metrics (VaR/CVaR merged)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import historical_tail_risk_metrics as htrm


@pytest.fixture
def tail_risk_seed(tmp_path, monkeypatch):
    p = tmp_path / "historical_tail_risk_metrics_seed.json"
    p.write_text(json.dumps({
        "legal_review": {"complete": True},
        "formula": {
            "confidence_levels": [0.90, 0.95, 0.99],
            "lookback_days_default": 252,
        },
        "backtest": {
            "observations_tested": 100,
            "var_accuracy_pct": 96.0,
            "cvar_accuracy_pct": 95.5,
        },
        "assets": {
            "BTC": {
                "lookback_days": 50,
                "historical_daily_returns": [
                    -0.05, -0.03, 0.02, 0.01, -0.04, 0.03, -0.02, 0.01, -0.06, 0.02,
                    -0.01, 0.04, -0.03, 0.02, -0.05, 0.01, -0.02, 0.03, -0.04, 0.02,
                ],
            },
        },
        "portfolios": {
            "demo_balanced": {
                "name": "Demo Balanced",
                "notional_usd": 50000,
                "networks_supported": 22,
                "holdings": [{"asset": "BTC", "weight": 1.0}],
                "historical_daily_returns": [
                    -0.04, -0.02, 0.01, 0.02, -0.03, 0.02, -0.01, 0.01, -0.05, 0.01,
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(htrm, "_SEED_PATH", p)
    return p


def test_503_504_merged_renamed(tail_risk_seed):
    panel = htrm.build_historical_tail_risk_panel(asset="BTC")
    assert panel["title"] == "Historical Tail Risk Estimates (VaR/CVaR)"
    assert panel["historical_estimates_mandatory"] is True
    assert panel["not_maximum_potential_loss"] is True
    assert panel["standalone_rejected"] is True
    assert "503" in panel["absorbed_tickets"]
    assert "504" in panel["absorbed_tickets"]
    assert panel["risk_metrics_layer"] == "Risk Metrics Layer"
    assert panel["sibling_feature_id"] == 501


def test_historical_var_cvar_formula(tail_risk_seed):
    returns = [-0.05, -0.03, 0.02, 0.01, -0.04, 0.03, -0.02, 0.01, -0.06, 0.02]
    var = htrm.compute_historical_var(returns, confidence=0.90)
    assert var["ok"] is True
    assert var["not_maximum_potential_loss"] is True
    assert var["descriptive_statistic_only"] is True
    assert "worst" in var["framing"].lower()

    cvar = htrm.compute_historical_cvar(returns, confidence=0.90)
    assert cvar["ok"] is True
    assert cvar["not_forecast"] is True
    assert cvar["historical_cvar_return"] <= cvar["historical_var_return"]


def test_no_advisory_language_and_disclaimer(tail_risk_seed):
    panel = htrm.build_historical_tail_risk_panel(asset="BTC")
    assert "Statistical estimate only" in panel["disclaimer"]
    assert "Not a prediction" in panel["disclaimer"]
    assert "No guarantee" in panel["disclaimer"]
    assert panel["disclaimer_on_every_output"] is True
    analysis = panel["analysis"]
    assert analysis["no_advisory_language"] is True
    assert analysis["not_investment_advice"] is True
    estimates = analysis["estimates"]
    assert estimates["not_maximum_potential_loss"] is True
    assert "worst" in estimates["summary_framing"].lower()


def test_portfolio_scope_absorbs_504(tail_risk_seed):
    panel = htrm.build_historical_tail_risk_panel(portfolio_id="demo_balanced")
    assert panel["scope"] == "portfolio"
    analysis = panel["analysis"]
    assert analysis["portfolio_id"] == "demo_balanced"
    assert analysis["networks_supported"] >= 20
    assert analysis["notional_usd"] == 50000


def test_legal_review_and_no_ml(tail_risk_seed):
    status = htrm.historical_tail_risk_metrics_status()
    assert status["legal_review_gate"]["legal_review_mandatory"] is True
    assert status["ml_deferred_until_compliance"] is True
    assert status["formula"]["no_ml"] is True
    assert status["acceptance_criteria"]["no_advisory_language"] is True


def test_banned_terms_not_in_user_facing_output(tail_risk_seed):
    panel = htrm.build_historical_tail_risk_panel(asset="BTC")
    analysis = panel["analysis"]
    estimates = analysis["estimates"]
    user_facing = " ".join([
        estimates["summary_framing"],
        estimates["historical_var"]["display"],
        estimates["historical_var"]["framing"],
        estimates["historical_cvar"]["display"],
        estimates["historical_cvar"]["framing"],
        estimates["notional_scaling"]["var"]["display"],
        estimates["notional_scaling"]["cvar"]["display"],
        panel["disclaimer"],
    ]).lower()
    for term in htrm._BANNED_TERMS:
        assert term not in user_facing


def test_api_routes(tail_risk_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/data-layer/tail-risk-metrics/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/data-layer/tail-risk-metrics?asset=BTC").status_code == 200
    assert c.get(
        "/api/platform/intelligence-ledger/data-layer/tail-risk-metrics?portfolio_id=demo_balanced"
    ).status_code == 200


def test_full_seed_exists():
    data = json.loads(Path("data/historical_tail_risk_metrics_seed.json").read_text())
    assert data["standalone_rejected"] is True
    assert 503 in data["feature_ids"]
    assert 504 in data["feature_ids"]
    assert data["risk_metrics_layer"] == "Risk Metrics Layer"
    assert data["legal_review"]["complete"] is True
