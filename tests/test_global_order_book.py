"""Tests — #249 Global Order Book Metrics merged into Market Radar."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import global_order_book as gob


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "global_order_book_seed.json"
    seed.write_text(
        json.dumps({
            "methodology_version": "1.3",
            "last_updated": "2026-08-25",
            "venue_weights": {
                "method": "30D volume-weighted",
                "version": "1.2",
                "weights": {
                    "Binance": 35,
                    "Coinbase": 25,
                    "Kraken": 20,
                    "OKX": 15,
                    "Bybit": 5,
                },
            },
            "assets": {
                "BTC": {
                    "levels": 10,
                    "venue_depths": {
                        "Binance": {"bid_usd": 285000000, "ask_usd": 245000000},
                        "Coinbase": {"bid_usd": 198000000, "ask_usd": 172000000},
                        "Kraken": {"bid_usd": 142000000, "ask_usd": 128000000},
                        "OKX": {"bid_usd": 98000000, "ask_usd": 88000000},
                        "Bybit": {"bid_usd": 42000000, "ask_usd": 38000000},
                    },
                    "sequence_gaps": [
                        {
                            "venue": "Binance",
                            "sequence_start": 1450,
                            "sequence_end": 1452,
                            "interpolated": True,
                        },
                    ],
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(gob, "_SEED_PATH", seed)
    return seed


def test_venue_weights_documented(isolated_seed):
    weights = gob.build_venue_weights(
        {"Binance": 35, "Coinbase": 25, "Kraken": 20, "OKX": 15, "Bybit": 5},
        method="30D volume-weighted",
        version="1.2",
    )
    assert "Binance: 35%" in weights["display"]
    assert "30D volume-weighted" in weights["display"]
    assert weights["no_equal_weight_without_reason"] is True


def test_sequence_gaps_handled(isolated_seed):
    gaps = [
        {"venue": "Binance", "sequence_start": 1450, "sequence_end": 1452, "interpolated": True},
    ]
    result = gob.build_sequence_gaps(gaps, venues_active=4, venues_total=5)
    assert result["gaps_detected"] is True
    assert "Sequence gap detected" in result["gaps"][0]["display"]
    assert "interpolated" in result["gaps"][0]["display"]
    assert "Coverage: 4/5" in result["coverage_display"]
    assert result["no_hidden_gaps"] is True


def test_per_venue_breakdown(isolated_seed):
    asset = json.loads(isolated_seed.read_text())["assets"]["BTC"]
    depth = gob.build_per_venue_depth(asset["venue_depths"])
    assert "Binance:" in depth["display"]
    assert "Global:" in depth["display"]
    assert depth["no_total_without_breakdown"] is True


def test_global_depth_descriptive(isolated_seed):
    depth = gob.build_global_depth(500_000_000, 400_000_000, levels=10)
    assert "Global Bid Depth" in depth["display"]
    assert "Imbalance:" in depth["display"]
    assert depth["descriptive_only"] is True
    assert depth["no_buy_signal"] is True


def test_imbalance_context_not_signal(isolated_seed):
    ctx = gob.build_imbalance_context(12.0)
    assert "Bid-Ask Imbalance:" in ctx["display"]
    assert "Not: Bullish signal" in ctx["display"]
    assert ctx["context_not_signal"] is True


def test_update_frequency_by_tier(isolated_seed):
    free = gob._update_frequency_display("free")
    pro = gob._update_frequency_display("pro")
    ent = gob._update_frequency_display("institutional")
    assert "30 seconds" in free["display"]
    assert "5 seconds" in pro["display"]
    assert "1 second" in ent["display"]
    assert free["no_instant_claim"] is True


def test_no_opportunity_language(isolated_seed):
    panel = gob.build_global_order_book_panel("BTC", tier="pro")
    assert panel["ok"] is True
    assert panel["no_opportunity_language"] is True
    assert panel["not_arbitrage_signal"] is True
    assert "arbitrage" not in panel["volume_display"].lower()


def test_disclaimer_non_hideable(isolated_seed):
    panel = gob.build_global_order_book_panel("BTC")
    assert panel["disclaimer_hideable"] is False
    assert "not future direction" in panel["disclaimer"]["text"].lower()


def test_methodology_versioned(isolated_seed):
    meth = gob.build_methodology_block(json.loads(isolated_seed.read_text()))
    assert "Global Order Book Methodology v1.3" in meth["display"]
    assert "Gap Handling: Interpolation + Alert" in meth["display"]


def test_technical_context_only(isolated_seed):
    panel = gob.build_global_order_book_panel("BTC")
    assert panel["technical_context_only"] is True
    assert panel["standalone"] is False
    assert panel["merged_into"] == "market_radar"
    assert panel["replaces"] == 227


def test_status(isolated_seed):
    status = gob.global_order_book_status()
    assert status["feature_id"] == 249
    assert status["replaces"] == 227
    assert status["acceptance_criteria"]["sequence_gaps_handled"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/order-book/status").status_code == 200
    resp = c.get("/api/platform/market-radar/order-book?asset=BTC&tier=pro")
    assert resp.status_code == 200
    assert resp.json()["tab"] == "Global Order Book"


def test_full_seed_exists():
    seed = json.loads(Path("data/global_order_book_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 249
    assert seed["replaces"] == 227
    assert len(seed["assets"]) >= 3
