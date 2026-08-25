"""Tests — #256 + #257 + #258 unified Order Book Feed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import order_book_feed as obf


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "order_book_feed_seed.json"
    seed.write_text(
        json.dumps({
            "methodology_version": "1.0",
            "last_updated": "2026-08-25",
            "venue_list": ["binance", "coinbase"],
            "assets": {
                "BTC": {
                    "venues": {
                        "binance": {
                            "failover": {"primary": "Binance", "fallback": "Coinbase", "status": "Active"},
                            "sequence_qa": {
                                "sequence": 145230001,
                                "timestamp_utc": "2026-08-25T20:58:12.450Z",
                                "latency_ms": 120,
                                "gap": "None",
                            },
                            "l1": {
                                "bid_usd": 108520.50,
                                "ask_usd": 108521.00,
                                "bid_size": 2.45,
                                "ask_size": 1.82,
                            },
                            "l2": {
                                "levels": 20,
                                "total_bid_usd": 285000000,
                                "total_ask_usd": 245000000,
                            },
                            "l2_gap": {
                                "sequence_start": 145230001,
                                "sequence_end": 145230045,
                                "messages_missed": 44,
                                "reconnect": "Auto",
                                "backfill": "Last 100ms",
                                "status": "Recovered",
                            },
                            "reconnect": {
                                "disconnect_detected": True,
                                "reconnect_seconds": 2,
                                "sequence_verified": True,
                            },
                            "l3": {
                                "available": True,
                                "order_tracking": {
                                    "order_id": "ABC-123",
                                    "queue_position": "45/200",
                                    "lifecycle": "New → Partial Fill → Fill",
                                    "integrity": "Verified",
                                },
                                "events": [
                                    {
                                        "order_id": "ABC-123",
                                        "event": "New Order",
                                        "price_usd": 108520.50,
                                        "size": 2.45,
                                        "side": "Bid",
                                    },
                                ],
                                "queue_integrity": {
                                    "missing": "None",
                                    "reconstructed": True,
                                },
                                "retention": {
                                    "display": "Enterprise: 7 days hot | 30 days warm | 90 days cold",
                                },
                            },
                        },
                        "coinbase": {
                            "sequence_qa": {"sequence": 1, "latency_ms": 100, "gap": "None"},
                            "l1": {"bid_usd": 108518, "ask_usd": 108522, "bid_size": 1, "ask_size": 1},
                            "l2": {"levels": 20, "total_bid_usd": 100, "total_ask_usd": 100},
                            "l3": {"available": False},
                        },
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(obf, "_SEED_PATH", seed)
    return seed


def test_l1_sequence_time_qa(isolated_seed):
    result = obf.get_order_book_feed("BTC", level="L1", venue="binance")
    feed = result["feed"]
    assert "Sequence:" in feed["sequence_time_qa"]["display"]
    assert "Latency:" in feed["sequence_time_qa"]["display"]
    assert feed["sequence_time_qa"]["sequence_tracking_required"] is True


def test_l1_top_of_book_only(isolated_seed):
    feed = obf.get_order_book_feed("BTC", level="L1")["feed"]
    assert "Best Bid:" in feed["feed_display"]
    assert feed["no_extra_depth"] is True
    assert "L1 Feed:" in feed["l1_feed_display"]


def test_l1_failover(isolated_seed):
    feed = obf.get_order_book_feed("BTC", level="L1")["feed"]
    assert "Primary:" in feed["failover"]["display"]
    assert feed["failover"]["no_single_point_of_failure"] is True


def test_l1_normalization(isolated_seed):
    feed = obf.get_order_book_feed("BTC", level="L1")["feed"]
    assert "Normalized: Yes" in feed["normalized_quote"]["display"]
    assert "Spread:" in feed["normalized_quote"]["display"]


def test_l2_gap_reconnect(isolated_seed):
    feed = obf.get_order_book_feed("BTC", level="L2")["feed"]
    assert "Gap detected" in feed["sequence_gap"]["display"]
    assert feed["sequence_gap"]["no_hidden_gaps"] is True
    assert "Reconnect:" in feed["reconnect_logic"]["display"]


def test_l2_depth_levels(isolated_seed):
    feed = obf.get_order_book_feed("BTC", level="L2")["feed"]
    assert feed["depth_levels"] == 20
    assert "Depth: 20 levels" in feed["feed_display"]


def test_l3_order_id_integrity(isolated_seed):
    feed = obf.get_order_book_feed("BTC", level="L3", tier="institutional")["feed"]
    assert feed["ok"] is True
    assert "Order ID:" in feed["order_tracking"]["display"]
    assert feed["queue_integrity"]["integrity_verified"] is True
    assert "bot detection" in feed["integrations"]["bot_activity_721"]


def test_l3_enterprise_only(isolated_seed):
    result = obf.get_order_book_feed("BTC", level="L3", tier="free")
    assert result["feed"]["ok"] is False
    assert result["feed"]["error"] == "l3_enterprise_only"


def test_l3_venue_availability(isolated_seed):
    result = obf.get_order_book_feed("BTC", level="L3", venue="coinbase", tier="institutional")
    assert result["feed"]["ok"] is False
    assert result["feed"]["error"] == "l3_not_available"


def test_no_signal_language(isolated_seed):
    for level in ("L1", "L2"):
        feed = obf.get_order_book_feed("BTC", level=level)["feed"]
        assert feed["no_signal_language"] is True
        assert "buy now" not in str(feed).lower()


def test_latency_tiers(isolated_seed):
    l1_free = obf._latency_tier("L1", "free")
    l1_ent = obf._latency_tier("L1", "institutional")
    assert "2s" in l1_free["display"]
    assert "100ms" in l1_ent["display"]
    assert l1_free["no_instant_claim"] is True


def test_unified_feed_status(isolated_seed):
    status = obf.order_book_feed_status()
    assert status["merged"] is True
    assert status["modes"]["L1"]["feature_id"] == 256
    assert status["modes"]["L2"]["feature_id"] == 257
    assert status["modes"]["L3"]["feature_id"] == 258
    assert status["acceptance_criteria"]["single_unified_feed"] is True


def test_powers_249(isolated_seed):
    result = obf.get_order_book_feed("BTC", level="L2")
    assert result["powers_analysis"]["global_order_book_249"] is True


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/order-book-feed/status").status_code == 200
    resp = c.get("/api/platform/order-book-feed?asset=BTC&level=L1&venue=binance")
    assert resp.status_code == 200
    assert resp.json()["level"] == "L1"


def test_full_seed_exists():
    seed = json.loads(Path("data/order_book_feed_seed.json").read_text(encoding="utf-8"))
    assert 256 in seed["feature_ids"]
    assert len(seed["venue_list"]) >= 5
