"""Tests — #350 Strategy Validation Engine, #352 Leverage Context, #356 Liquidation Risk Context."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import derivatives_market_state as dms
from bd_platform import liquidation_cluster_analytics as lca
from bd_platform import strategy_validation_engine as sve


@pytest.fixture
def sve_seed(tmp_path, monkeypatch):
    p = tmp_path / "strategy_validation_engine_seed.json"
    p.write_text(json.dumps({
        "cost_models": {"fee_model": {"taker_pct": 0.05}},
        "regression_fixtures": [
            {"fixture_id": "rf1", "description": "no lookahead", "passed": True, "reproducible": True},
            {"fixture_id": "rf2", "description": "survivorship", "passed": True, "reproducible": True},
        ],
        "validations": [{
            "validation_id": "v1", "strategy_id": "test_strat",
            "reproducibility_seed": 42, "start_date": "2024-01-01", "end_date": "2026-01-01",
            "walk_forward": True, "out_of_sample": True,
            "no_look_ahead_verified": True, "survivorship_controlled": True,
            "validation_passed": True, "events_replayed": 1000,
            "cost_attribution": {"fees_pct": 0.1},
        }],
    }), encoding="utf-8")
    monkeypatch.setattr(sve, "_SEED_PATH", p)
    return p


@pytest.fixture
def dms_seed(tmp_path, monkeypatch):
    p = tmp_path / "derivatives_market_state_seed.json"
    p.write_text(json.dumps({
        "legal_review": {"complete": True},
        "backtest": {"false_positive_rate_pct": 20},
        "assets": {
            "BTC": {
                "components": {
                    "funding_rate": 0.0005, "funding_z": 2.0,
                    "oi_change_pct": 8, "oi_z": 1.5,
                    "liquidation_usd_24h": 5e7, "liquidation_z": 2.0,
                    "spot_price": 64000, "perp_price": 64500,
                    "leverage_ratio": 1.3, "price_change_24h_pct": 2.0,
                    "funding_rate_source": "Binance",
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(dms, "_SEED_PATH", p)
    return p


@pytest.fixture
def lca_seed(tmp_path, monkeypatch):
    p = tmp_path / "liquidation_cluster_analytics_seed.json"
    p.write_text(json.dumps({
        "legal_review": {"complete": True},
        "assets": {
            "BTC": {
                "sources": [{"venue": "binance", "confidence": "high"}],
                "risk_context": {
                    "historical_cascade_frequency": 0.05,
                    "walk_forward_validation": {"completed": True, "events_tested": 10, "out_of_sample_pct": 30},
                    "historical_patterns": [{
                        "pattern_id": "hp1", "event_date": "2024-01-01",
                        "historical_liquidation_usd": 1e9, "volatility_at_event": 0.04,
                        "leverage_context": "elevated", "positioning_context": "long",
                    }],
                },
                "clusters": [{
                    "cluster_id": "c1", "price_level": 60000, "side": "long",
                    "historical_liquidation_usd": 1e8, "current_open_interest_usd": 2e8,
                    "venue": "binance", "source": "API", "confidence": "high",
                    "estimated_levels": [],
                }],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(lca, "_SEED_PATH", p)
    return p


def test_350_renamed_internal_only(sve_seed):
    status = sve.strategy_validation_engine_status()
    assert status["renamed_from"] == "High_Precision_Backtesting"
    assert status["title"] == "Strategy Validation Engine"
    assert status["internal_only"] is True
    assert status["user_facing"] is False
    assert status["no_high_precision_in_name"] is True
    assert status["no_dashboard"] is True


def test_350_no_lookahead_and_fixtures(sve_seed):
    result = sve.run_strategy_validation()
    assert result["internal_only"] is True
    assert result["no_lookahead_lock"]["no_look_ahead"] is True
    assert result["regression_fixtures"]["automated"] is True
    assert result["regression_fixtures"]["all_passed"] is True
    run = result["validation_runs"][0]
    assert run["no_equity_curve_for_user"] is True
    assert run["no_hit_rate_for_user"] is True
    assert run["reproducible"] is True


def test_352_leverage_context_no_score(dms_seed):
    panel = dms.build_derivatives_market_state_panel("BTC")
    lci = panel["leverage_context_indicator"]
    assert lci["sub_task"] == "#352"
    assert lci["title"] == "Leverage Context Indicator"
    assert lci["no_score_in_output"] is True
    assert lci["no_pressure_alert"] is True
    assert lci["no_ranking_by_pressure"] is True
    assert "open_interest" in lci["components"]
    assert "funding" in lci["components"]
    assert "liquidations" in lci["components"]
    assert lci["no_opaque_score"] is True
    assert lci["legal_review"]["mandatory"] is True


def test_356_liquidation_risk_context_no_probability(lca_seed):
    panel = lca.build_liquidation_cluster_panel("BTC")
    risk = panel["liquidation_risk_context"]
    assert risk["sub_task"] == "#356"
    assert risk["title"] == "Liquidation Risk Context"
    assert risk["no_model_in_name"] is True
    assert risk["no_probability_output"] is True
    assert risk["no_cascade_probability_alert"] is True
    assert risk["output_format"] == "historical_liquidation_pattern_analysis"
    assert risk["historical_patterns"][0]["no_probability_output"] is True
    assert risk["walk_forward_validation"]["required"] is True
    assert risk["legal_review"]["mandatory"] is True


def test_api_routes(sve_seed, dms_seed, lca_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/internal/strategy-validation/status").status_code == 200
    assert c.get("/api/platform/internal/strategy-validation").status_code == 200
    dms_panel = c.get("/api/platform/intelligence-ledger/derivatives-market-state?asset=BTC")
    assert dms_panel.status_code == 200
    assert "leverage_context_indicator" in dms_panel.json()
    lca_panel = c.get("/api/platform/intelligence-ledger/liquidation-clusters?asset=BTC")
    assert lca_panel.status_code == 200
    assert "liquidation_risk_context" in lca_panel.json()


def test_full_seeds_exist():
    sve_data = json.loads(Path("data/strategy_validation_engine_seed.json").read_text())
    assert sve_data["renamed_from"] == "High_Precision_Backtesting"
    assert sve_data["internal_only"] is True
    dms_data = json.loads(Path("data/derivatives_market_state_seed.json").read_text())
    assert "352" in dms_data.get("absorbed_tickets", {})
    lca_data = json.loads(Path("data/liquidation_cluster_analytics_seed.json").read_text())
    assert "356" in lca_data.get("absorbed_tickets", {})
