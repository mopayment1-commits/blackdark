"""Tests — #280 Liquidity Intelligence Engine (absorbs #277+#278+#279)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import liquidity_intelligence_engine as lie


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "liquidity_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "pairs": {
                "BTC/USDT": {
                    "binance": {
                        "book_level": "L2",
                        "levels": 5,
                        "bids": [[100.0, 10.0], [99.9, 20.0], [99.8, 15.0], [99.7, 12.0], [99.6, 8.0]],
                        "asks": [[100.1, 12.0], [100.2, 18.0], [100.3, 14.0], [100.4, 10.0], [100.5, 9.0]],
                        "slippage_sizes_usd": [10000, 100000],
                        "freshness": {
                            "latency_ms": 42,
                            "snapshot_age_ms": 180,
                            "exchange_timestamp": "2026-08-25T23:40:00+00:00",
                        },
                        "resilience": {
                            "gap_recovery_rate_pct": 98.5,
                            "depth_stability_score": 0.92,
                            "uptime_pct": 99.95,
                        },
                        "trades": {
                            "buy_volume_usd": 1000000,
                            "sell_volume_usd": 800000,
                            "book_imbalance_at_snapshot": 0.05,
                            "large_trades_count": 2,
                            "window_seconds": 60,
                        },
                    },
                    "broken": {
                        "book_level": "L2",
                        "levels": 2,
                        "bids": [[100.5, 10.0], [100.4, 5.0]],
                        "asks": [[100.3, 8.0], [100.2, 6.0]],
                        "freshness": {"latency_ms": 50, "snapshot_age_ms": 100},
                        "resilience": {"gap_recovery_rate_pct": 50, "depth_stability_score": 0.4, "uptime_pct": 95},
                        "trades": {},
                    },
                },
            },
            "warnings": [
                {
                    "type": "depth_drop",
                    "severity": "high",
                    "pair": "BTC/USDT",
                    "venue": "binance",
                    "timestamp": "2026-08-25T14:32:00+00:00",
                    "message": "Depth dropped 22%",
                    "actionable": True,
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(lie, "_SEED_PATH", seed)
    return seed


def test_crossed_book_detection():
    normal = lie.detect_crossed_book([[100.0, 10]], [[100.1, 12]])
    assert normal["crossed"] is False
    assert normal["snapshot_usable"] is True
    assert normal["action"] == "accept"

    crossed = lie.detect_crossed_book([[100.5, 10]], [[100.3, 8]])
    assert crossed["crossed"] is True
    assert crossed["snapshot_usable"] is False
    assert crossed["action"] == "reject_snapshot"


def test_freshness_visible(isolated_seed):
    freshness = lie.build_freshness_block({"latency_ms": 42, "snapshot_age_ms": 180})
    assert freshness["freshness_visible"] is True
    assert freshness["latency_visible"] is True
    assert freshness["stale"] is False
    assert "Latency:" in freshness["display"]


def test_freshness_stale(isolated_seed):
    freshness = lie.build_freshness_block({"latency_ms": 100, "snapshot_age_ms": 8000})
    assert freshness["stale"] is True


def test_resilience_score(isolated_seed):
    res = lie.build_resilience_score({
        "gap_recovery_rate_pct": 98.5,
        "depth_stability_score": 0.92,
        "uptime_pct": 99.95,
    })
    assert res["resilience_score"] >= 90
    assert res["grade"] == "high"


def test_trade_correlation(isolated_seed):
    tc = lie.build_trade_correlation({
        "buy_volume_usd": 1000000,
        "sell_volume_usd": 800000,
        "book_imbalance_at_snapshot": 0.05,
        "large_trades_count": 2,
    })
    assert tc["trade_imbalance"] > 0
    assert tc["flow_book_aligned"] is True
    assert "Trade flow:" in tc["display"]


def test_intelligence_panel_ok(isolated_seed):
    panel = lie.build_intelligence_panel(pair="BTC/USDT", venue="binance")
    assert panel["ok"] is True
    assert panel["feature_id"] == 280
    assert 277 in panel["absorbed_ids"]
    assert panel["no_standalone_dashboard"] is True
    assert panel["ui_surfaces"] == ["asset page embedded", "Screener filter"]
    venue = panel["venues"][0]
    assert venue["freshness"]["freshness_visible"] is True
    assert venue["crossed_book"]["crossed"] is False
    assert "replay_tests" in panel


def test_crossed_book_rejects_snapshot(isolated_seed):
    panel = lie.build_intelligence_panel(pair="BTC/USDT", venue="broken")
    venue = panel["venues"][0]
    assert venue["crossed_book"]["crossed"] is True
    assert venue["depth"]["snapshot_usable"] is False
    assert any(w["type"] == "crossed_book" for w in venue["warnings"])


def test_liquidity_warnings(isolated_seed):
    warnings = lie.list_liquidity_warnings(pair="BTC/USDT")
    assert warnings["count"] >= 1
    assert warnings["warnings"][0]["type"] == "depth_drop"


def test_absorbs_277_278_279(isolated_seed):
    status = lie.liquidity_intelligence_status()
    assert status["feature_id"] == 280
    assert status["layer_not_dashboard"] is True
    assert status["acceptance_criteria"]["sequence_gap_detection"] is True
    assert status["acceptance_criteria"]["crossed_book_handling"] is True
    assert status["acceptance_criteria"]["latency_freshness_visible"] is True
    assert status["acceptance_criteria"]["replay_tests"] is True
    assert 278 in status["absorbed_ids"]
    assert 279 in status["absorbed_ids"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/v1/data/liquidity-intelligence/status").status_code == 200
    resp = c.get("/api/v1/data/liquidity-intelligence/panel?pair=BTC/USDT&venue=binance")
    assert resp.status_code == 200
    body = resp.json()
    assert body["venues"][0]["freshness"]["freshness_visible"] is True
    assert c.get("/api/v1/data/liquidity-intelligence/warnings?pair=BTC/USDT").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/liquidity_intelligence_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 280
    assert 277 in seed["absorbed_ids"]
    assert "BTC/USDT" in seed["pairs"]
    assert len(seed["warnings"]) >= 1
