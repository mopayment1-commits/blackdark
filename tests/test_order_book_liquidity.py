"""Tests — #269+#277 Order Book & Liquidity + Market Depth merged into Wave 01 Data Engine."""

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
            "sequence_gaps": [
                {
                    "timestamp": "2026-08-25T14:32:05+00:00",
                    "venue": "binance",
                    "pair": "BTC/USDT",
                    "book_level": "L2",
                    "expected_sequence": 100,
                    "received_sequence": 103,
                    "recovered": True,
                    "recovery_method": "snapshot_resync",
                },
            ],
            "sequence_replay_tests": [
                {
                    "pair": "BTC/USDT",
                    "venue": "binance",
                    "test_date": "2026-08-25",
                    "expected_sequences": 1000,
                    "replayed_sequences": 1000,
                    "gaps_detected": 1,
                    "gaps_recovered": 1,
                    "passed": True,
                },
            ],
            "market_depth": {
                "BTC/USDT": {
                    "binance": {
                        "book_level": "L2",
                        "levels": 5,
                        "bids": [[100.0, 10.0], [99.9, 20.0], [99.8, 15.0], [99.7, 12.0], [99.6, 8.0]],
                        "asks": [[100.1, 12.0], [100.2, 18.0], [100.3, 14.0], [100.4, 10.0], [100.5, 9.0]],
                        "slippage_sizes_usd": [10000, 100000],
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(obl, "_SEED_PATH", seed)
    return seed


def test_scope_lock(isolated_seed):
    scope = obl.build_scope_lock_display()
    assert "L2/L3 where available" in scope["display"]
    assert "DEX liquidity (AMM pools) = separate pipeline" in scope["display"]
    assert "Screener panel" in scope["display"]
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
    assert "Market Depth" in sep["depth_engine"]
    assert sep["backend_not_product"] is True
    assert "Screener panel" in sep["display"]


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
    assert len(seed["sequence_gaps"]) >= 1
    assert len(seed["sequence_replay_tests"]) >= 1
    assert "BTC/USDT" in seed["market_depth"]


def test_sequence_gap_detection(isolated_seed):
    gaps = obl.list_sequence_gaps()
    gap = gaps["sequence_gaps"][0]
    assert "Sequence gap:" in gap["display"]
    assert gap["gap_size"] == 2
    assert gap["recovered"] is True
    assert gap["alert_fired"] is True


def test_sequence_replay_passed(isolated_seed):
    tests = obl.list_sequence_replay_tests()
    assert tests["passed_count"] >= 1
    assert "Sequence replay:" in tests["tests"][0]["display"]


def test_market_depth_metrics(isolated_seed):
    panel = obl.build_market_depth_panel(pair="BTC/USDT", venue="binance")
    assert panel["ok"] is True
    assert panel["feature_id"] == 277
    assert panel["heatmap_deferred"] is True
    metrics = panel["metrics"][0]
    assert metrics["spread_bps"] > 0
    assert "imbalance_ratio" in metrics
    assert "$10,000" in metrics["slippage_curve"]
    assert len(metrics["depth_curve"]) > 0


def test_spread_and_imbalance_helpers():
    assert obl.compute_spread_bps(100.0, 100.1) == pytest.approx(9.995, rel=0.01)
    assert obl.compute_imbalance_ratio(600, 400) == pytest.approx(0.2)


def test_merged_277_in_status(isolated_seed):
    status = obl.order_book_liquidity_status()
    assert 277 in status["feature_ids"]
    assert status["acceptance_criteria"]["sequence_gaps_detected"] is True
    assert status["acceptance_criteria"]["sequence_replay_tests"] is True
    assert "Screener" in status["scope_lock"]["display"]


def test_api_routes_market_depth(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/v1/data/order-book-liquidity/sequence-gaps").status_code == 200
    assert c.get("/api/v1/data/order-book-liquidity/sequence-replay-tests").status_code == 200
    resp = c.get("/api/v1/data/order-book-liquidity/market-depth?pair=BTC/USDT&venue=binance")
    assert resp.status_code == 200
    assert resp.json()["heatmap_deferred"] is True
