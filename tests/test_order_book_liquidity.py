"""Tests — #269 Order Book & Liquidity Data Layer merged into Wave 01 Data Engine."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import order_book_liquidity as obl


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "order_book_liquidity_seed.json"
    seed.write_text(
        json.dumps({
            "sla": {
                "gap_detection_latency_min": 5,
                "replay_coverage_pairs": 100,
                "spread_variance_bps": 1.0,
            },
            "retention": {"top_50_days": 365, "other_days": 30},
            "gaps": [
                {
                    "timestamp": "2026-08-25T14:32:00+00:00",
                    "venue": "binance",
                    "pair": "BTC/USDT",
                    "expected_depth_usd": 530000000,
                    "actual_depth_usd": 412000000,
                    "duration_seconds": 180,
                    "root_cause": "API_down",
                    "alert_threshold_pct": 10,
                },
                {
                    "timestamp": "2026-08-25T18:00:00+00:00",
                    "venue": "kraken",
                    "pair": "SOL/USD",
                    "expected_depth_usd": 52000000,
                    "actual_depth_usd": 51500000,
                    "duration_seconds": 30,
                    "root_cause": "venue_maintenance",
                    "alert_threshold_pct": 10,
                },
            ],
            "replay_tests": [
                {
                    "pair": "BTC/USDT",
                    "venue": "binance",
                    "test_date": "2026-08-25",
                    "expected_spread_bps": 2.1,
                    "replayed_spread_bps": 2.08,
                    "variance_threshold_bps": 1.0,
                    "passed": True,
                },
                {
                    "pair": "SOL/USDT",
                    "venue": "bybit",
                    "test_date": "2026-08-24",
                    "expected_spread_bps": 4.5,
                    "replayed_spread_bps": 5.8,
                    "variance_threshold_bps": 1.0,
                    "passed": False,
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(obl, "_SEED_PATH", seed)
    return seed


def test_scope_lock(isolated_seed):
    scope = obl.build_scope_lock_display()
    assert "Crypto spot + perp order books only" in scope["display"]
    assert "DEX liquidity (AMM pools) = separate pipeline" in scope["display"]
    assert "daily batch" in scope["display"]
    assert scope["no_ui_in_sprint_1"] is True


def test_gap_detection_schema(isolated_seed):
    gaps = obl.list_gaps()
    gap = gaps["gaps"][0]
    assert "Gap:" in gap["display"]
    assert "root_cause: API_down" in gap["display"]
    assert gap["alert_fired"] is True
    assert gap["no_alert_fatigue"] is True


def test_no_alert_on_small_gap(isolated_seed):
    gaps = obl.list_gaps(venue="kraken")
    gap = gaps["gaps"][0]
    assert gap["alert_fired"] is False


def test_replay_test_passed(isolated_seed):
    tests = obl.list_replay_tests()
    passed = [t for t in tests["tests"] if t["passed"]]
    assert len(passed) >= 1
    assert "QA: Passed" in passed[0]["display"]
    assert passed[0]["daily_batch"] is True
    assert passed[0]["not_realtime"] is True


def test_replay_test_failed(isolated_seed):
    tests = obl.list_replay_tests(passed_only=False)
    failed = [t for t in tests["tests"] if not t["passed"]]
    assert len(failed) >= 1
    assert "QA: Failed" in failed[0]["display"]


def test_separation_of_concerns(isolated_seed):
    sep = obl.build_separation_of_concerns()
    assert "Data Engine" in sep["ingestion_layer"]
    assert "Intelligence Ledger" in sep["analytics_layer"]
    assert sep["backend_not_product"] is True
    assert "No UI now" in sep["display"]


def test_cost_gate_retention(isolated_seed):
    gate = obl.build_cost_gate()
    assert gate["top_50_pairs_retention_days"] == 365
    assert gate["other_pairs_retention_days"] == 30
    assert gate["compression_mandatory"] is True
    assert gate["no_unbounded_storage"] is True


def test_acceptance_criteria_expanded(isolated_seed):
    criteria = obl.build_acceptance_criteria()
    assert criteria["gap_detection_latency_minutes"] == 5
    assert criteria["replay_coverage_pairs"] == 100
    assert criteria["spread_variance_bps"] == 1.0


def test_not_standalone_merged(isolated_seed):
    status = obl.order_book_liquidity_status()
    assert status["feature_id"] == 269
    assert status["standalone"] is False
    assert status["archived_standalone_ticket"] is True
    assert status["reused_table"] == "order_books"


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/v1/data/order-book-liquidity/status").status_code == 200
    status = c.get("/api/v1/data/order-book-liquidity/status").json()
    assert status["feature_id"] == 269
    assert c.get("/api/v1/data/order-book-liquidity/gaps").status_code == 200
    assert c.get("/api/v1/data/order-book-liquidity/replay-tests").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/order_book_liquidity_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 269
    assert len(seed["gaps"]) >= 2
    assert len(seed["replay_tests"]) >= 2
