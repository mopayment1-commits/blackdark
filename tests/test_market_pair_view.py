"""Tests — #270 Market Pair Intelligence archived; view over #268."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from blackdark.data import market_pair_view as mpv


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "market_pair_view_seed.json"
    seed.write_text(
        json.dumps({
            "sla": {"mapping_accuracy_pct": 99.5, "stale_detection_hours": 1},
            "pairs": [
                {
                    "instrument_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "venue": "binance",
                    "base": "BTC",
                    "quote": "USDT",
                    "asset_class": "spot",
                    "last_trade_utc": "2026-08-25T20:55:00+00:00",
                    "listed_at_utc": "2017-08-17T00:00:00+00:00",
                    "daily_volume_usd": 28500000000,
                    "premium_discount_pct": 0.02,
                    "vwap_reference_usd": 116850,
                },
                {
                    "instrument_id": "e5f6a7b8-c9d0-1234-ef01-345678901234",
                    "venue": "kraken",
                    "base": "SOL",
                    "quote": "USD",
                    "asset_class": "spot",
                    "last_trade_utc": "2026-08-24T08:00:00+00:00",
                    "listed_at_utc": "2021-06-17T00:00:00+00:00",
                    "daily_volume_usd": 45000000,
                    "premium_discount_pct": -0.08,
                    "vwap_reference_usd": 185.5,
                },
                {
                    "instrument_id": "f6a7b8c9-d0e1-2345-f012-456789012345",
                    "venue": "gateio",
                    "base": "ALT",
                    "quote": "USDT",
                    "asset_class": "spot",
                    "last_trade_utc": "2026-08-25T19:00:00+00:00",
                    "listed_at_utc": "2026-08-20T00:00:00+00:00",
                    "daily_volume_usd": 850,
                    "premium_discount_pct": 1.2,
                    "vwap_reference_usd": 0.042,
                },
            ],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(mpv, "_SEED_PATH", seed)
    return seed


def test_rejected_standalone(isolated_seed):
    status = mpv.market_pair_view_status()
    assert status["feature_id"] == 270
    assert status["rejected_as_backend"] is True
    assert status["archived_standalone_ticket"] is True
    assert status["no_separate_pipeline"] is True
    assert status["no_separate_database"] is True


def test_pair_view_uses_268_mapping(isolated_seed):
    view = mpv.build_pair_view(json.loads(isolated_seed.read_text())["pairs"][0])
    assert view["instrument_id_268"] is not None
    assert view["no_separate_pipeline"] is True
    assert view["source"] == "instrument_master_268"
    assert "Pair ID: BTC/USDT" in view["display"]


def test_stale_market_flagged(isolated_seed):
    view = mpv.build_pair_view(json.loads(isolated_seed.read_text())["pairs"][1])
    assert view["stale"] is True
    assert "stale" in view["flags"]


def test_low_volume_greyed_out(isolated_seed):
    view = mpv.build_pair_view(json.loads(isolated_seed.read_text())["pairs"][2])
    assert view["low_volume"] is True
    assert view["greyed_out"] is True
    assert view["confidence_warning"] is True
    assert view["is_new"] is True


def test_premium_discount_documented(isolated_seed):
    view = mpv.build_pair_view(json.loads(isolated_seed.read_text())["pairs"][0])
    assert "Premium/discount vs VWAP reference" in view["premium_display"]


def test_compare_across_venues(isolated_seed):
    result = mpv.compare_pairs_across_venues("BTC", quote="USDT")
    assert result["ok"] is True
    assert result["venue_count"] >= 1
    assert "asset:BTC → pairs → venues" in result["e2e_journey"]


def test_list_pairs_no_stale_filter(isolated_seed):
    all_pairs = mpv.list_pair_views(include_stale=True)
    active_only = mpv.list_pair_views(include_stale=False)
    assert all_pairs["count"] >= active_only["count"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/v1/data/market-pairs/status").status_code == 200
    status = c.get("/api/v1/data/market-pairs/status").json()
    assert status["rejected_as_backend"] is True
    assert c.get("/api/v1/data/market-pairs?base=BTC").status_code == 200
    assert c.get("/api/v1/data/market-pairs/compare/BTC").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/market_pair_view_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 270
    assert seed["rejected_as_backend"] is True
    assert len(seed["pairs"]) >= 3
