"""Tests — #295 Spot Metrics & Venue Quality + #294 absorbed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import spot_metrics_venue_quality as sm


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "spot_metrics_venue_quality_seed.json"
    seed.write_text(
        json.dumps({
            "venues": [
                {"venue": "binance", "quality_score": 98, "status": "active",
                 "warmup_days_remaining": 0, "staleness_sec": 2,
                 "source": "binance", "timestamp_utc": "2026-08-26T00:00:00+00:00"},
                {"venue": "stale", "quality_score": 60, "status": "active",
                 "warmup_days_remaining": 0, "staleness_sec": 300,
                 "source": "stale", "timestamp_utc": "2026-08-25T23:00:00+00:00"},
            ],
            "symbols": {
                "BTC/USDT": {
                    "venues": [
                        {"venue": "binance", "last_price": 95000, "volume_24h": 1e9,
                         "return_1d_pct": 1.0, "volatility_7d_pct": 3.5, "spread_bps": 1.2,
                         "source": "binance", "timestamp_utc": "2026-08-26T00:00:00+00:00"},
                        {"venue": "okx", "last_price": 95010, "volume_24h": 5e8,
                         "return_1d_pct": 1.1, "volatility_7d_pct": 3.6, "spread_bps": 1.5,
                         "source": "okx", "timestamp_utc": "2026-08-26T00:00:00+00:00"},
                        {"venue": "outlier", "last_price": 99000, "volume_24h": 1e6,
                         "return_1d_pct": 5.0, "volatility_7d_pct": 8.0, "spread_bps": 15,
                         "source": "outlier", "timestamp_utc": "2026-08-26T00:00:00+00:00"},
                    ],
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(sm, "_SEED_PATH", seed)
    return seed


def test_294_rejected_standalone(isolated_seed):
    status = sm.spot_metrics_status()
    assert 294 in status["rejected_standalone_tickets"]
    assert status["spot_overview_sub_task"] == "#294 absorbed into #295 spot overview"


def test_no_separate_pipeline(isolated_seed):
    status = sm.spot_metrics_status()
    assert status["no_separate_pipeline"] is True
    assert status["dashboard_deferred"] == "Sprint 2 Intelligence Ledger spot dashboard"


def test_venue_normalization(isolated_seed):
    norm = sm.build_venue_normalization()
    assert norm["timestamp_alignment"] == "UTC"
    assert norm["outlier_zscore_threshold"] == 3.0
    assert norm["source_provenance"]


def test_outlier_stale_filtered(isolated_seed):
    panel = sm.build_spot_metrics_panel("BTC/USDT")
    filtered = panel["aggregated"]["filtered"]
    assert filtered["outlier_stale_filtered"] is True
    excluded = [v["venue"] for v in filtered["excluded_venues"]]
    assert "outlier" in excluded


def test_spot_overview_sub_task_294(isolated_seed):
    panel = sm.build_spot_metrics_panel("BTC/USDT")
    overview = panel["spot_overview"]
    assert overview["sub_task"] == "#294"
    assert overview["archived_standalone"] is True
    assert overview["outlier_stale_filtered"] is True


def test_scope_lock(isolated_seed):
    scope = sm.build_scope_lock()
    assert scope["max_venues"] == 50
    assert scope["new_venue_warmup_days"] == 7


def test_venue_quality_rankings(isolated_seed):
    rankings = sm.list_venue_quality_rankings()
    assert rankings["max_venues"] == 50
    assert rankings["rankings"][0]["quality_score_documented"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/v1/data/spot-metrics/status").status_code == 200
    resp = c.get("/api/v1/data/spot-metrics?symbol=BTC/USDT")
    assert resp.status_code == 200
    assert resp.json()["spot_overview"]["sub_task"] == "#294"


def test_full_seed_exists():
    seed = json.loads(Path("data/spot_metrics_venue_quality_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 295
    assert 294 in seed["rejected_standalone_tickets"]
