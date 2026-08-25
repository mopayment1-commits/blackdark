"""Tests — #723 + #724 + #746 Portfolio Risk Analytics Suite."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import portfolio_risk_analytics as pra


@pytest.fixture
def isolated_risk_seed(tmp_path, monkeypatch):
    seed = tmp_path / "portfolio_risk_analytics_seed.json"
    seed.write_text(
        json.dumps({
            "universe": ["BTC", "ETH"],
            "change_24h_pct": {"BTC": 1.0, "ETH": -0.5},
            "return_series": {
                "BTC": [0.01, -0.01, 0.02, 0.005, -0.008] * 6,
                "ETH": [0.012, -0.009, 0.018, 0.006, -0.01] * 6,
            },
            "backtest_accuracy": {"period_months": 12, "accuracy_pct": 72},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(pra, "_SEED_PATH", seed)
    return seed


def test_correlation_matrix(isolated_risk_seed):
    result = pra.build_correlation_matrix(["BTC", "ETH"])
    assert result["feature"] == 723
    assert result["matrix"]["BTC"]["BTC"] == 1.0
    assert "ETH" in result["matrix"]["BTC"]


def test_return_breadth(isolated_risk_seed):
    result = pra.compute_return_breadth(["BTC", "ETH"])
    assert result["feature"] == 724
    assert result["positive_count"] == 1
    assert result["breadth_pct"] == 50.0


def test_risk_scenario_simulator(isolated_risk_seed):
    holdings = [{"symbol": "BTC", "amount_usd": 60000}, {"symbol": "ETH", "amount_usd": 40000}]
    result = pra.run_risk_scenario_simulation(holdings, iterations=2000)
    assert result["ok"] is True
    assert result["feature"] == 746
    assert result["not_a_prediction"] is True
    assert "monte" not in json.dumps(result).lower()
    assert "not a prediction" in result["disclaimer"].lower()
    sim = result["simulation"]
    assert "value_at_risk" in sim
    assert "confidence_intervals" in sim
    assert sim["iterations"] == 2000
    assert result["sla_met"] is True


def test_historical_backtest_not_accuracy_guarantee(isolated_risk_seed):
    result = pra.run_risk_scenario_simulation(
        [{"symbol": "BTC", "amount_usd": 10000}], iterations=1000,
    )
    backtest = result["historical_backtest"]
    assert "not forward accuracy guarantee" in backtest["note"].lower()


def test_unified_dashboard(isolated_risk_seed):
    holdings = [{"symbol": "BTC", "amount_usd": 50000}]
    dash = pra.get_portfolio_risk_analytics(holdings, iterations=1000)
    assert dash["ok"] is True
    assert 723 in dash["integrated_features"]
    assert 724 in dash["integrated_features"]
    assert 746 in dash["integrated_features"]
    assert dash["disclaimer_hideable"] is False


def test_status_flags(isolated_risk_seed):
    status = pra.portfolio_risk_analytics_status()
    assert status["standalone"] is False
    assert status["tier_required"] == "pro"
    assert status["not_a_prediction"] is True


def test_api_public_routes(isolated_risk_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/portfolio/risk-analytics/status").status_code == 200
    assert c.get("/api/platform/portfolio/risk-analytics/correlation").status_code == 200
    assert c.get("/api/platform/portfolio/risk-analytics/breadth").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/portfolio_risk_analytics_seed.json").read_text(encoding="utf-8"))
    assert len(seed["universe"]) >= 6
    assert "BTC" in seed["return_series"]
