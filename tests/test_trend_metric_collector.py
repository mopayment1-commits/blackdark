"""Tests — #299 Trend Metric Collector."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import trend_metric_collector as tmc


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "trend_metric_collector_seed.json"
    seed.write_text(
        json.dumps({
            "as_of_timestamp_utc": "2026-08-26T00:00:00+00:00",
            "universe": {"version": "2026.08.1", "asset_count": 2, "as_of": "2026-08-26"},
            "assets": {
                "BTC": {
                    "trend_score": 0.8,
                    "universe_version": "2026.08.1",
                    "data_cutoff_utc": "2026-08-26T00:00:00+00:00",
                    "returns": {"1d": 0.01, "7d": 0.04, "30d": 0.08},
                    "volume_current": 1000,
                    "volume_baseline": 800,
                    "timeframes": {"1d": {"momentum": 0.01, "volume_accel": 0.1, "liquidity_score": 0.9}},
                },
                "ETH": {
                    "trend_score": 0.6,
                    "universe_version": "2026.08.1",
                    "data_cutoff_utc": "2026-08-26T00:00:00+00:00",
                    "returns": {"1d": 0.005, "7d": 0.02, "30d": 0.05},
                    "volume_current": 500,
                    "volume_baseline": 450,
                    "timeframes": {"1d": {"momentum": 0.005, "volume_accel": 0.05, "liquidity_score": 0.85}},
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(tmc, "_SEED_PATH", seed)
    return seed


def test_infrastructure_layer(isolated_seed):
    status = tmc.trend_metric_collector_status()
    assert status["feature_id"] == 299
    assert status["infrastructure_layer"] is True


def test_point_in_time_controls(isolated_seed):
    controls = tmc.build_point_in_time_controls()
    assert controls["no_lookahead"] is True
    assert controls["unit_tests_for_lookahead_bias"] is True


def test_no_lookahead_enforcement(isolated_seed):
    result = tmc.compute_momentum_score(
        {"1d": 0.01, "7d": 0.04, "30d": 0.08},
        as_of_timestamp="2026-08-27T00:00:00+00:00",
        available_data_cutoff="2026-08-26T00:00:00+00:00",
    )
    assert result["lookahead_violation"] is True
    assert result["score"] is None


def test_cross_sectional_rank(isolated_seed):
    panel = tmc.build_trend_metric_panel("BTC")
    rank = panel["trend"]["cross_sectional_rank"]
    assert rank["deterministic"] is True
    assert rank["percentile"] >= 0


def test_universe_versioned(isolated_seed):
    universe = tmc.build_universe_block()
    assert universe["versioned"] is True
    assert universe["re_rank_frequency"] == "daily"


def test_timeframe_breakdown(isolated_seed):
    panel = tmc.build_trend_metric_panel("BTC")
    assert "1d" in panel["trend"]["timeframe_breakdown"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/trend-metrics/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/trend-metrics?asset=BTC").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/trend_metric_collector_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 299
    assert seed["universe"]["version"]
