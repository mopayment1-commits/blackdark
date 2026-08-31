"""Tests — #296 Taker Pressure Module (Intelligence Ledger)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import taker_pressure as tp


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "taker_pressure_seed.json"
    seed.write_text(
        json.dumps({
            "classification_tests": [
                {"venue": "binance", "accuracy_pct": 97.0, "passed": True},
                {"venue": "okx", "accuracy_pct": 95.5, "passed": True},
            ],
            "assets": {
                "BTC": {
                    "rolling_window_min": 60,
                    "venues": [
                        {
                            "venue": "binance",
                            "market_type": "cex_spot",
                            "trade_side_available": True,
                            "taker_buy_volume": 1000,
                            "taker_sell_volume": 800,
                            "source": "binance",
                            "timestamp_utc": "2026-08-26T00:00:00+00:00",
                        },
                        {
                            "venue": "coinbase",
                            "market_type": "cex_spot",
                            "trade_side_available": False,
                            "taker_buy_volume": 0,
                            "taker_sell_volume": 0,
                            "source": "coinbase",
                            "timestamp_utc": "2026-08-26T00:00:00+00:00",
                        },
                    ],
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(tp, "_SEED_PATH", seed)
    return seed


def test_sprint_2_orderflow_sub_feature(isolated_seed):
    status = tp.taker_pressure_status()
    assert status["feature_id"] == 296
    assert status["sub_feature_of"] == "Orderflow analytics"
    assert status["sprint"] == 2


def test_classification_tested(isolated_seed):
    controls = tp.build_classification_controls()
    assert controls["classification_tested"] is True
    assert controls["min_accuracy_pct"] == 95.0
    assert controls["venue_coverage_disclosed"] is True


def test_scope_lock_cex_only(isolated_seed):
    scope = tp.build_scope_lock()
    assert scope["cex_spot"] is True
    assert scope["cex_perp"] is True
    assert "no taker" in scope["dex"].lower()


def test_pressure_state(isolated_seed):
    result = tp.compute_pressure_state(1000, 800)
    assert result["state"] == "buy_pressure"
    assert result["buy_ratio"] > 0.5


def test_venue_coverage_disclosed(isolated_seed):
    panel = tp.build_taker_pressure_panel("BTC")
    unavailable = [v for v in panel["venues"] if not v["trade_side_available"]]
    assert len(unavailable) >= 1
    assert panel["aggregate"]["venues_without_trade_side"] >= 1


def test_panel_not_a_signal(isolated_seed):
    panel = tp.build_taker_pressure_panel("BTC")
    assert panel["not_a_signal"] is True
    assert panel["aggregate"]["state"] == "buy_pressure"


def test_classification_tests_endpoint(isolated_seed):
    tests = tp.list_classification_tests()
    assert tests["min_accuracy_pct"] == 95.0
    assert tests["count"] >= 1


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/taker-pressure/status").status_code == 200
    resp = c.get("/api/platform/intelligence-ledger/taker-pressure?asset=BTC")
    assert resp.status_code == 200
    assert resp.json()["aggregate"]["state"] == "buy_pressure"


def test_full_seed_exists():
    seed = json.loads(Path("data/taker_pressure_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 296
    passed = [t for t in seed["classification_tests"] if t["passed"]]
    assert all(t["accuracy_pct"] >= 95 for t in passed)
