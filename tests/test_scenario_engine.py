"""Tests — #751 Scenario Engine (probabilistic scenarios, Enterprise tier)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import scenario_engine as se


@pytest.fixture
def isolated_scenario_seed(tmp_path, monkeypatch):
    seed = tmp_path / "scenario_engine_seed.json"
    seed.write_text(
        json.dumps({
            "version": "2.1",
            "updated_at": "2026-08-25",
            "assumptions": ["Fed rate unchanged"],
            "calibration": {
                "period": "2023-2025",
                "brier_score": 0.182,
                "out_of_sample_tested": True,
                "display": "Calibration tested on 2023-2025 data | Brier Score: 0.182",
            },
            "scenario_templates": {
                "BTC": {
                    "scenarios": [
                        {
                            "id": "a", "label": "A — Test", "base_probability_pct": 30.0,
                            "narrative": "Likely continuation",
                            "drivers": ["driver1"],
                            "invalidation_conditions": ["BTC breaks below support threshold"],
                        },
                        {
                            "id": "b", "label": "B — Test", "base_probability_pct": 45.0,
                            "narrative": "Probability favors expansion",
                            "drivers": ["driver2"],
                            "invalidation_conditions": ["resistance on weekly close"],
                        },
                        {
                            "id": "c", "label": "C — Test", "base_probability_pct": 25.0,
                            "narrative": "Likely correction",
                            "drivers": ["driver3"],
                            "invalidation_conditions": ["all-time high"],
                        },
                    ],
                    "price_thresholds": {"support_usd": 90000, "resistance_usd": 100000, "ath_usd": 110000},
                    "sensitivity_shocks": [
                        {
                            "shock": "Fed cuts 25bps",
                            "shifts": {"a": 5.0, "b": -3.0, "c": -2.0},
                            "display": "If Fed cuts 25bps → Probability shifts: A +5% | B -3% | C -2%",
                        },
                    ],
                },
            },
            "regime_adjustments": {"neutral": {}},
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(se, "_SEED_PATH", seed)
    return seed


@pytest.fixture
def mock_market_context(monkeypatch):
    async def fake_ctx(asset):
        return {"regime": "neutral", "price": 100000.0}

    monkeypatch.setattr(se, "_fetch_market_context", fake_ctx)


@pytest.mark.asyncio
async def test_probabilities_sum_coherently(isolated_scenario_seed, mock_market_context):
    result = await se.generate_scenarios("BTC")
    assert result["ok"] is True
    assert result["probabilities_sum_coherently"] is True
    total = sum(s["probability_pct"] for s in result["scenarios"])
    assert abs(total - 100.0) < 1.0
    assert "Sum: 100" in result["probability_sum_display"]


@pytest.mark.asyncio
async def test_calibration_documented(isolated_scenario_seed, mock_market_context):
    result = await se.generate_scenarios("BTC")
    assert "Brier Score" in result["calibration"]["calibration_display"]
    assert result["calibration"]["out_of_sample_tested"] is True


@pytest.mark.asyncio
async def test_no_certainty_language(isolated_scenario_seed, mock_market_context):
    result = await se.generate_scenarios("BTC")
    assert result["no_certainty_language"] is True
    assert result["not_a_prediction"] is True
    for s in result["scenarios"]:
        assert "Probability:" in s["probability_display"]
        assert " will " not in s["narrative"].lower()


@pytest.mark.asyncio
async def test_assumptions_version_recorded(isolated_scenario_seed, mock_market_context):
    result = await se.generate_scenarios("BTC")
    assert result["assumptions"]["version"] == "2.1"
    assert "Version: 2.1" in result["assumptions"]["assumptions_display"]


@pytest.mark.asyncio
async def test_invalidation_conditions(isolated_scenario_seed, mock_market_context):
    result = await se.generate_scenarios("BTC")
    inv = result["scenarios"][0]["invalidation_conditions"][0]
    assert "invalidates if" in inv.lower()
    assert "$90,000" in inv


@pytest.mark.asyncio
async def test_sensitivity_analysis(isolated_scenario_seed):
    result = se.run_sensitivity_analysis("BTC", "Fed cuts 25bps")
    assert result["ok"] is True
    assert "Fed cuts 25bps" in result["sensitivity_display"]
    assert result["probability_sum_display"]


@pytest.mark.asyncio
async def test_mandatory_disclaimer(isolated_scenario_seed, mock_market_context):
    result = await se.generate_scenarios("BTC")
    assert result["disclaimer_hideable"] is False
    assert "probabilistic exercises" in result["disclaimer"].lower()
    assert "not investment advice" in result["disclaimer"].lower()


def test_status_enterprise_tier(isolated_scenario_seed):
    status = se.scenario_engine_status()
    assert status["feature_id"] == 751
    assert status["tier_required"] == "institutional"
    assert status["sensitivity_analysis"] is True


def test_calibration_endpoint(isolated_scenario_seed):
    cal = se.get_calibration()
    assert cal["out_of_sample_tested"] is True


def test_api_status_route(isolated_scenario_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    r = c.get("/api/platform/scenario-engine/status")
    assert r.status_code == 200
    assert r.json()["feature_id"] == 751


def test_full_seed_exists():
    seed = json.loads(Path("data/scenario_engine_seed.json").read_text(encoding="utf-8"))
    assert seed["version"] == "2.1"
    assert "BTC" in seed["scenario_templates"]
    assert seed["calibration"]["brier_score"] == 0.182
