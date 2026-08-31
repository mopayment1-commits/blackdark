"""Tests — #717 Portfolio Diversification + #109 + #199 merged."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import portfolio_diversification as pd


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "portfolio_diversification_seed.json"
    seed.write_text(
        json.dumps({
            "portfolios": {
                "default": {
                    "visible_asset_count": 3,
                    "holdings": [
                        {"asset": "BTC", "weight_pct": 50, "value_usd": 5000, "cost_basis_usd": 4000, "avg_correlation": 0.4},
                        {"asset": "ETH", "weight_pct": 30, "value_usd": 3000, "cost_basis_usd": 2500, "avg_correlation": 0.7, "correlation": 0.75, "correlated_with": "BTC"},
                        {"asset": "AAVE", "weight_pct": 20, "value_usd": 2000, "cost_basis_usd": 1800, "avg_correlation": 0.5},
                    ],
                    "sectors": {"L1": 80, "DeFi": 20},
                    "chains": {"Ethereum": 100},
                    "market_cap_tiers": {"Large": 80, "Mid": 20},
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(pd, "_SEED_PATH", seed)
    return seed


def test_no_entropy_in_ui(isolated_seed):
    status = pd.portfolio_diversification_status()
    assert status["no_entropy_in_ui"] is True
    assert status["ui_label"] == "Diversification Score"


def test_diversification_score_label(isolated_seed):
    panel = pd.build_portfolio_health_panel("default")
    assert "Diversification Score" in panel["smart_diversification"]["ui_label"]
    assert panel["smart_diversification"]["no_entropy_label"] is True
    assert "entropy" not in panel["smart_diversification"]["ui_label"].lower()


def test_correlation_risk_109(isolated_seed):
    panel = pd.build_portfolio_health_panel("default")
    assert panel["correlation_risk"]["sub_task"] == "#109"
    assert panel["correlation_risk"]["avg_correlation"] > 0


def test_pnl_drift_199(isolated_seed):
    panel = pd.build_portfolio_health_panel("default")
    assert panel["pnl"]["sub_task"] == "#199"
    assert panel["pnl"]["pnl_accuracy_tolerance_pct"] == 0.1


def test_sector_concentration(isolated_seed):
    panel = pd.build_portfolio_health_panel("default")
    assert panel["sector_concentration"]["max_sector_pct"] == 80.0


def test_heatmap(isolated_seed):
    panel = pd.build_portfolio_health_panel("default")
    assert "by_sector" in panel["heatmap"]
    assert "by_chain" in panel["heatmap"]


def test_export_and_max_assets(isolated_seed):
    panel = pd.build_portfolio_health_panel("default")
    assert panel["export"]["pdf_available"] is True
    assert panel["max_assets_supported"] == 1000


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/portfolio-health/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-health").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/portfolio_diversification_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 717
    assert 109 in seed["merged_with"]
