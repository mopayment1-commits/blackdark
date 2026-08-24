"""Tests — Exchange Quality (#132), Platform Status (#134), Order Flow (#135)."""

from __future__ import annotations

import pytest

from bd_platform.exchange_quality_score import (
    _score_to_grade,
    compute_quality_score,
    score_all_exchanges,
    score_exchange,
)
from bd_platform.exchange_health_monitor import (
    _build_platform_status,
    exchange_trust_dashboard,
)
from bd_platform.order_flow_analytics import analyze_order_book, scan_order_flow


def test_score_to_grade_scale():
    assert _score_to_grade(92) == "A+"
    assert _score_to_grade(87) == "A"
    assert _score_to_grade(82) == "B+"
    assert _score_to_grade(55) == "D"


def test_compute_quality_score_reserves_verified():
    snap = {
        "exchange_id": "binance",
        "health_score": 85,
        "dimensions": {
            "por": 90,
            "withdrawal": 85,
            "regulatory": 88,
            "trust_score": 92,
            "security_history": 80,
            "liquidity": 95,
            "wash_trading_risk": 90,
        },
    }
    out = compute_quality_score(snap, suspension_count=0)
    assert out["feature_id"] == 132
    assert out["quality_score"] >= 85
    assert out["grade"] in {"A+", "A", "B+"}
    assert "Reserves Verified" in out["badge"]
    assert out["badge"].startswith("🟢")
    assert out["methodology"]["proof_of_reserves"]["weight_pct"] == 25


def test_compute_quality_score_withdrawal_suspensions():
    snap = {
        "dimensions": {
            "por": 70,
            "withdrawal": 80,
            "regulatory": 70,
            "trust_score": 60,
            "security_history": 50,
            "liquidity": 60,
            "wash_trading_risk": 55,
        },
    }
    out = compute_quality_score(snap, suspension_count=3)
    assert "Withdrawals Suspended 3x" in out["badge"]
    assert out["withdrawal_suspensions_6mo"] == 3


def test_score_exchange_from_snapshots():
    result = score_exchange("binance")
    assert result["ok"] is True
    assert result["feature_id"] == 132
    assert result["sla_met"] is True
    assert "quality" in result
    assert result["methodology_transparent"] is True


def test_score_all_exchanges():
    result = score_all_exchanges()
    assert result["ok"] is True
    assert result["exchange_count"] >= 1
    assert "methodology" in result


def test_platform_status_134_fields():
    snap = {
        "timestamp": "2026-08-24T00:00:00+00:00",
        "dimensions": {"operational": 80, "withdrawal": 85},
    }
    status = _build_platform_status("binance", snap)
    assert status["feature_id"] == 134
    assert status["api_status"] == "up"
    assert status["withdrawal_status"] == "open"
    assert status["deposit_status"] == "open"
    assert status["trading_status"] == "active"
    assert "history" in status


def test_exchange_trust_dashboard_unified():
    dash = exchange_trust_dashboard()
    assert dash["ok"] is True
    assert "#132" in dash["features"]
    assert "#134" in dash["features"]
    assert dash["sla_met"] is True
    assert dash["exchange_count"] >= 1
    first = dash["exchanges"][0]
    assert "quality" in first
    assert "platform_status" in first


def test_analyze_order_book_buy_wall():
    bids = [[30000, 500], [29990, 10], [29980, 8], [29970, 5], [29960, 4]]
    asks = [[30010, 20], [30020, 15], [30030, 10], [30040, 8], [30050, 5]]
    signals = analyze_order_book(
        exchange="binance",
        asset="BTC",
        price=30000,
        bids=bids,
        asks=asks,
    )
    buy = next(s for s in signals if s["side"] == "buy")
    assert "Buy Wall" in buy["headline"]
    assert buy["strength"] == "strong"
    assert "دعم قوي" in buy["headline_ar"] or "جدار شراء" in buy["headline_ar"]


def test_analyze_order_book_spoofing_detection():
    bids = [[30000, 900], [29990, 5], [29980, 5], [29970, 5], [29960, 5]]
    asks = [[30010, 10], [30020, 10], [30030, 10], [30040, 10], [30050, 10]]
    signals = analyze_order_book(
        exchange="okx",
        asset="BTC",
        price=30000,
        bids=bids,
        asks=asks,
        prev_wall={"max_bid_size": 950},
    )
    buy = next(s for s in signals if s["side"] == "buy")
    assert buy["spoofing_detected"] is True
    assert "Fake Buy Wall" in buy["headline"] or "spoofing" in buy["headline"].lower()


@pytest.mark.asyncio
async def test_scan_order_flow_sla(monkeypatch):
    async def fake_books():
        return {
            "binance": {
                "BTC/USDT": {
                    "bids": [[95000, 100], [94900, 50], [94800, 40]],
                    "asks": [[95100, 30], [95200, 25], [95300, 20]],
                }
            }
        }

    monkeypatch.setattr("database.fetch_latest_order_books", fake_books)
    monkeypatch.setattr(
        "live_book_hub.get_best_price",
        lambda ex, sym: {"mid": 95000, "bid": 94999, "ask": 95001, "bid_qty": 1, "ask_qty": 1},
    )
    monkeypatch.setattr("bd_platform.order_flow_analytics._WALL_HISTORY_PATH", __import__("pathlib").Path("/tmp/of_test.json"))
    monkeypatch.setattr("bd_platform.order_flow_analytics._save_wall_history", lambda data: None)
    monkeypatch.setattr("bd_platform.order_flow_analytics._load_wall_history", lambda: {})

    out = await scan_order_flow("BTC", limit=5)
    assert out["ok"] is True
    assert out["feature_id"] == 135
    assert out["sla_met"] is True
    assert out["signal_count"] >= 1
    assert out["signals"][0].get("user_friendly") is True
