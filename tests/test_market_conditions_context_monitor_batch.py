"""Tests — Market Conditions Context Monitor #565."""

from __future__ import annotations

import json

import pytest

from bd_platform import market_conditions_context_monitor as mccm


@pytest.fixture
def market_seed(tmp_path, monkeypatch):
    p = tmp_path / "market_conditions_context_monitor_seed.json"
    p.write_text(json.dumps({
        "formula": {"expression": "test_formula"},
        "lens_definitions": {
            "liquidity": {"baseline": 1.0, "scale": 0.5},
            "volatility": {"baseline": 50.0, "scale": 25.0},
        },
        "markets": {
            "test_market": {
                "name": "Test Market",
                "lenses": {
                    "liquidity": {
                        "raw_value": 1.5,
                        "base_confidence": 0.9,
                        "freshness_seconds": 300,
                        "source": "test",
                    },
                    "volatility": {
                        "raw_value": 70.0,
                        "base_confidence": 0.85,
                        "freshness_seconds": 5000,
                        "source": "test",
                    },
                },
            },
        },
        "backtest": {"periods_tested": 12, "label_consistency_pct": 90},
    }), encoding="utf-8")
    monkeypatch.setattr(mccm, "_SEED_PATH", p)
    return p


def test_status_renamed_no_compass(market_seed):
    status = mccm.market_conditions_context_monitor_status()
    assert status["feature_id"] == 565
    assert status["renamed_from"] == "Market Compass / Market Regime Engine"
    assert status["title"] == "Market Conditions Context Monitor"
    assert status["acceptance_criteria"]["no_unified_regime_score"] is True


def test_no_unified_regime_score(market_seed):
    analysis = mccm.build_market_conditions_analysis("test_market")
    assert analysis["ok"] is True
    assert analysis["no_unified_regime_score"] is True
    assert analysis["no_buy_sell_claim"] is True
    assert len(analysis["factor_alignment_indicators"]) == 2


def test_stale_data_penalty(market_seed):
    analysis = mccm.build_market_conditions_analysis("test_market")
    vol_lens = next(
        l for l in analysis["factor_alignment_indicators"] if l["lens"] == "volatility"
    )
    assert vol_lens["freshness"]["stale_data_penalty_applied"] is True
    assert vol_lens["adjusted_confidence"] < vol_lens["base_confidence"]


def test_descriptive_condition_labels(market_seed):
    analysis = mccm.build_market_conditions_analysis("test_market")
    label = analysis["observed_conditions"]["observed_condition_label"]
    assert label in (
        "defensive_conditions_observed",
        "neutral_conditions_observed",
        "expansion_conditions_observed",
    )
    assert "Risk-On" not in analysis["observed_conditions"]["display_label"]
    assert "Risk-Off" not in analysis["observed_conditions"]["display_label"]


def test_deterministic_hash(market_seed):
    a1 = mccm.build_market_conditions_analysis("test_market")
    a2 = mccm.build_market_conditions_analysis("test_market")
    assert a1["deterministic_output_hash"] == a2["deterministic_output_hash"]


def test_formula_documented(market_seed):
    formula = mccm.build_formula_documentation()
    assert formula["formula_version"] == "1.0"
    assert formula["deterministic"] is True
    assert formula["no_unified_regime_score"] is True


def test_panel_and_reconciliation(market_seed):
    panel = mccm.build_market_conditions_panel("test_market")
    assert panel["ok"] is True
    result = mccm.run_reconciliation_tests()
    assert result["all_passed"] is True


def test_api_routes(market_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/market-conditions/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/market-conditions?market_id=test_market").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/intelligence-layer/market-conditions/reconciliation-tests").status_code == 200
