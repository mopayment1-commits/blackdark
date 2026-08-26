"""Tests — #716 Strategy Lab + #712 QA gate merged."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import strategy_lab as sl


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "strategy_lab_seed.json"
    seed.write_text(
        json.dumps({
            "as_of_timestamp_utc": "2026-08-26T00:00:00+00:00",
            "qa_gate": {
                "coverage_pct": 85.0,
                "reproducible_tests": True,
                "sandbox_before_production": True,
                "uncontrolled_blast_radius": False,
                "backtest_years": 2,
            },
            "strategies": {
                "liquidity_inflow_alert": {
                    "name": "Liquidity Inflow Alert Buy",
                    "description": "test",
                    "tier_required": "pro",
                    "no_curve_fitting": True,
                    "simulated_runtime_sec": 4.0,
                    "historical_metrics": {
                        "win_rate_pct": 62,
                        "average_return_pct": 8.0,
                        "max_drawdown_pct": 12.0,
                        "backtest_months": 18,
                        "backtest_years": 2,
                        "trade_count": 47,
                    },
                    "walk_forward": {"folds": 5, "out_of_sample_pct": 30},
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(sl, "_SEED_PATH", seed)
    return seed


def test_712_merged_internal_qa_gate(isolated_seed):
    gate = sl.build_qa_verification_gate()
    assert gate["feature_id"] == 712
    assert gate["internal_only"] is True
    assert gate["user_visible"] is False
    assert gate["qa_gate_passed"] is True
    assert gate["coverage_met"] is True


def test_model_verified_badge_only_user_visible(isolated_seed):
    badge = sl.build_model_verified_badge()
    assert badge["verified"] is True
    assert badge["badge"] == "✓ Model Verified"
    assert badge["internal_details_hidden"] is True


def test_reproducible_backtest(isolated_seed):
    r1 = sl.run_historical_backtest("liquidity_inflow_alert")
    r2 = sl.run_historical_backtest("liquidity_inflow_alert")
    assert r1["backtest_hash"] == r2["backtest_hash"]
    assert r1["same_strategy_same_data_same_result"] is True


def test_historical_simulation_not_prediction(isolated_seed):
    result = sl.run_historical_backtest("liquidity_inflow_alert")
    assert result["historical_simulation"] is True
    assert result["not_future_prediction"] is True
    assert result["no_blast_radius"] is True


def test_speed_target(isolated_seed):
    result = sl.run_historical_backtest("liquidity_inflow_alert")
    assert result["performance"]["speed_target_met"] is True
    assert result["performance"]["runtime_sec"] < 10


def test_walk_forward(isolated_seed):
    result = sl.run_historical_backtest("liquidity_inflow_alert")
    assert result["walk_forward_analysis"]["enabled"] is True
    assert result["walk_forward_analysis"]["folds"] >= 5


def test_strategy_lab_panel(isolated_seed):
    panel = sl.build_strategy_lab_panel("liquidity_inflow_alert")
    assert panel["ok"] is True
    assert panel["model_verified_badge"]["verified"] is True
    assert "Win Rate" in panel["backtest"]["results"]["display"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/strategy-lab/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/strategy-lab/verified-badge").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/strategy_lab_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 716
    assert 712 in seed["feature_ids"]
