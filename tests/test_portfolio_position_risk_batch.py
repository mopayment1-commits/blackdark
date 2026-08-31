"""Tests — #366 Position Stress Scenario, #373 Position Risk Context, #377 blocked."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import portfolio_position_risk as ppr


@pytest.fixture
def ppr_seed(tmp_path, monkeypatch):
    p = tmp_path / "portfolio_position_risk_seed.json"
    p.write_text(json.dumps({
        "legal_review": {"complete": True},
        "venue_rules": {
            "binance": {
                "version": "1.0", "maintenance_margin_pct": 0.5,
                "initial_margin_pct": 1.0, "liquidation_fee_pct": 0.075,
            },
        },
        "blocked_features": {
            "377": {"models_available": 0, "models_required": 3},
        },
        "positions": {
            "pos_001": {
                "asset": "BTC", "venue": "binance", "ltv": 0.35,
                "margin_utilization_pct": 42,
                "liquidation_distance_usd_low": 4500,
                "liquidation_distance_usd_high": 5200,
                "concentration_pct": 35, "hedge_ratio": 0,
                "data_stale": False, "stale_data_penalty_applied": False,
                "stress_scenarios": [{
                    "scenario_id": "s1", "name": "10% drop", "price_drop_pct": 10,
                    "scenario_loss_usd_low": 1000, "scenario_loss_usd_high": 1200,
                }],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(ppr, "_SEED_PATH", p)
    return p


def test_366_position_stress_scenario_absorbed(ppr_seed):
    panel = ppr.build_position_stress_scenario("pos_001")
    assert panel["sub_task"] == "#366"
    assert panel["title"] == "Position Stress Scenario"
    assert panel["no_liquidation_risk_output"] is True
    assert panel["standalone_rejected"] is True
    assert panel["educational_not_advice"] is True
    scenario = panel["stress_scenarios"][0]
    assert scenario["scenario_assumptions_lock"] is True
    assert "If price drops" in scenario["mathematical_result"]["display"]
    assert scenario["no_high_risk_warning"] is True


def test_373_position_risk_context_no_score(ppr_seed):
    panel = ppr.build_position_risk_context("pos_001")
    assert panel["sub_task"] == "#373"
    assert panel["title"] == "Position Risk Context"
    assert panel["no_risk_score_in_output"] is True
    assert panel["no_risk_score_in_name"] is True
    assert panel["output_format"] == "component_breakdown"
    assert "margin_utilization" in panel["components"]
    assert "liquidation_distance" in panel["components"]
    assert "scenario_losses" in panel["components"]
    assert panel["no_false_precision"] is True
    assert panel["legal_review"]["mandatory"] is True


def test_373_venue_rules_versioned(ppr_seed):
    panel = ppr.build_position_risk_context("pos_001")
    rules = panel["venue_rules"]
    assert rules["venue_specific_rules_versioned"] is True
    assert rules["rules_version"] == "1.0"


def test_373_ranges_not_exact(ppr_seed):
    panel = ppr.build_position_risk_context("pos_001")
    dist = panel["components"]["liquidation_distance"]["distance_range"]
    assert dist["no_false_precision"] is True
    assert "–" in dist["range_display"]


def test_377_hold_and_block(ppr_seed):
    status = ppr.build_multi_model_liquidation_blocked_status()
    assert status["feature_id"] == 377
    assert status["status"] == "hold_and_block"
    assert status["engineering_blocked"] is True
    assert status["prerequisites_met"] is False
    assert status["no_consensus_heatmap"] is True
    assert status["models_available"] == 0


def test_status_absorbed_and_blocked(ppr_seed):
    status = ppr.portfolio_position_risk_status()
    assert 366 in status["absorbed_tickets"]
    assert 377 in status["blocked_tickets"]
    assert status["surface"] == "portfolio_ai"


def test_api_routes(ppr_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/position-risk/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/position-stress-scenario").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/portfolio-ai/position-risk-context").status_code == 200
    blocked = c.get("/api/platform/intelligence-ledger/portfolio-ai/multi-model-liquidation/status")
    assert blocked.status_code == 200
    assert blocked.json()["engineering_blocked"] is True


def test_full_seed_exists():
    seed = json.loads(Path("data/portfolio_position_risk_seed.json").read_text())
    assert "366" in seed.get("absorbed_tickets", {})
    assert "373" in seed.get("absorbed_tickets", {})
    assert seed["blocked_features"]["377"]["status"] == "hold_and_block"
