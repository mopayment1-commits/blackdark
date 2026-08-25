"""Tests — #232 CVD Intelligence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import cvd_intelligence as cvd


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "cvd_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "feature_id": 232,
            "methodology_version": "1.2",
            "classification": "Taker Side",
            "aggregation": "Volume-Weighted",
            "last_updated": "2026-08-25",
            "exchanges": ["binance", "coinbase", "kraken", "okx", "bybit"],
            "classification_rules": {
                "aggressive_buy": "market buy (taker buy)",
                "aggressive_sell": "market sell (taker sell)",
            },
            "classification_audit": {
                "accuracy_pct": 97.3,
                "trades_tested": 12500,
                "test_date": "2026-08-25",
            },
            "historical_validation": {
                "period_months": 6,
                "divergences_detected": 50,
                "true_positive": 38,
                "false_positive": 12,
                "precision_pct": 76.0,
            },
            "assets": {
                "BTC": {
                    "venues": {
                        "binance": {"status": "down", "gap": True, "gap_reason": "Feed outage", "volume_usd": 0},
                        "coinbase": {"status": "up", "aggressive_buy_usd": 100, "aggressive_sell_usd": 80, "volume_usd": 180, "weight": 0.2},
                        "kraken": {"status": "up", "aggressive_buy_usd": 50, "aggressive_sell_usd": 45, "volume_usd": 95, "weight": 0.1},
                        "okx": {"status": "up", "aggressive_buy_usd": 120, "aggressive_sell_usd": 100, "volume_usd": 220, "weight": 0.4},
                        "bybit": {"status": "up", "aggressive_buy_usd": 90, "aggressive_sell_usd": 85, "volume_usd": 175, "weight": 0.3},
                    },
                    "series": {
                        "1h": {
                            "cvd": [
                                {"ts": "2026-08-25T18:00:00+00:00", "value_usd": 5000000, "interpolated": False},
                                {"ts": "2026-08-25T19:00:00+00:00", "value_usd": 3000000, "interpolated": True, "gap_exchange": "binance"},
                                {"ts": "2026-08-25T20:00:00+00:00", "value_usd": -2000000, "interpolated": False},
                            ],
                            "price": [
                                {"ts": "2026-08-25T18:00:00+00:00", "close_usd": 116000},
                                {"ts": "2026-08-25T19:00:00+00:00", "close_usd": 116400},
                                {"ts": "2026-08-25T20:00:00+00:00", "close_usd": 116800},
                            ],
                        },
                        "4h": {
                            "cvd": [
                                {"ts": "2026-08-25T16:00:00+00:00", "value_usd": 8000000, "interpolated": False},
                                {"ts": "2026-08-25T20:00:00+00:00", "value_usd": -2000000, "interpolated": False},
                            ],
                            "price": [
                                {"ts": "2026-08-25T16:00:00+00:00", "close_usd": 115800},
                                {"ts": "2026-08-25T20:00:00+00:00", "close_usd": 116800},
                            ],
                        },
                        "1d": {
                            "cvd": [
                                {"ts": "2026-08-24T00:00:00+00:00", "value_usd": 50000000, "interpolated": False},
                                {"ts": "2026-08-25T00:00:00+00:00", "value_usd": -2000000, "interpolated": False},
                            ],
                            "price": [
                                {"ts": "2026-08-24T00:00:00+00:00", "close_usd": 115500},
                                {"ts": "2026-08-25T00:00:00+00:00", "close_usd": 116800},
                            ],
                        },
                    },
                    "baseline_30d_usd": 10000000,
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(cvd, "_SEED_PATH", seed)
    return seed


def test_trade_side_classification_rules():
    assert cvd.classify_trade_side(taker_side="buy") == "aggressive_buy"
    assert cvd.classify_trade_side(taker_side="sell") == "aggressive_sell"
    assert cvd.classify_trade_side(is_buyer_maker=False) == "aggressive_buy"
    assert cvd.classify_trade_side(is_buyer_maker=True) == "aggressive_sell"


def test_classification_audit_min_trades():
    sample = cvd.generate_classification_sample(12500)
    audit = cvd.run_classification_audit(sample)
    assert audit["trades_tested"] >= 10000
    assert audit["meets_minimum"] is True
    assert audit["accuracy_pct"] >= 90.0
    assert "Classification Accuracy" in audit["classification_display"]
    assert "Tested on:" in audit["classification_display"]


def test_gap_handling(isolated_seed):
    analysis = cvd.build_cvd_analysis("BTC")
    gap = analysis["gap_handling"]
    assert gap["has_gap"] is True
    assert "Binance down" in gap["gap_display"]
    assert "interpolated" in gap["gap_display"].lower()
    assert "4/5" in gap["gap_display"]
    assert gap["partial_data_warning"] is True


def test_multi_venue_aggregation(isolated_seed):
    analysis = cvd.build_cvd_analysis("BTC")
    mv = analysis["multi_venue"]
    assert mv["coverage_count"] == 4
    assert mv["total_exchanges"] == 5
    assert "Weighted by volume" in mv["aggregation_display"]
    assert "Binance" in mv["aggregation_display"]


def test_bearish_divergence_not_sell_signal(isolated_seed):
    analysis = cvd.build_cvd_analysis("BTC", window="1H")
    div = analysis["divergence_detail"]
    assert div["divergence"] == "Bearish"
    assert "Bearish Divergence" in div["display"]
    assert div["not_a_signal"] is True
    assert "Sell Signal" not in div["display"]
    assert analysis["not_buy_sell_signal"] is True


def test_output_format(isolated_seed):
    analysis = cvd.build_cvd_analysis("BTC")
    assert "CVD Value:" in analysis["cvd_value_display"]
    assert "million USD" in analysis["cvd_value_display"]
    assert analysis["trend"] in ("Rising", "Flat", "Falling")
    assert analysis["divergence"] in ("None", "Bullish", "Bearish")
    assert "Confidence:" in analysis["confidence_display"]
    assert "Coverage:" in analysis["coverage_display"]
    assert "4/5" in analysis["coverage_display"]


def test_disclaimer_non_hideable(isolated_seed):
    analysis = cvd.build_cvd_analysis("BTC")
    assert analysis["disclaimer"]["hideable"] is False
    assert analysis["disclaimer"]["collapsible"] is False
    assert analysis["disclaimer_top"] == analysis["disclaimer_bottom"]
    assert "taker buy vs taker sell" in analysis["disclaimer"]["text"]


def test_no_signal_language(isolated_seed):
    analysis = cvd.build_cvd_analysis("BTC")
    text = json.dumps(analysis)
    assert "sell now" not in text.lower()
    assert "buy now" not in text.lower()
    assert "CVD Analysis:" in analysis["cvd_analysis"]
    assert analysis["technical_context_only"] is True


def test_methodology_version(isolated_seed):
    analysis = cvd.build_cvd_analysis("BTC")
    assert "CVD Methodology v1.2" in analysis["methodology_display"]
    assert "Taker Side" in analysis["methodology_display"]
    assert "Volume-Weighted" in analysis["methodology_display"]


def test_historical_validation_transparency(isolated_seed):
    analysis = cvd.build_cvd_analysis("BTC")
    hist = analysis["historical_validation"]
    assert hist["precision_pct"] == 76.0
    assert "True positive" in hist["display"]
    assert "False positive" in hist["display"]
    assert hist["period_months"] >= 6


def test_chart_interpolated_segments(isolated_seed):
    chart = cvd.build_cvd_chart("BTC", window="1H")
    assert chart["ok"] is True
    assert chart["chart"]["has_interpolated_segments"] is True
    dashed = [p for p in chart["chart"]["cvd"] if p.get("dashed")]
    assert len(dashed) >= 1


def test_divergence_windows(isolated_seed):
    analysis = cvd.build_cvd_analysis("BTC")
    windows = analysis["divergence_windows"]
    assert "1H" in windows
    assert "4H" in windows
    assert "1D" in windows


def test_cvd_delta():
    assert cvd.compute_cvd_delta(100, 60) == 40
    assert cvd.compute_cvd_delta(50, 80) == -30


def test_status(isolated_seed):
    status = cvd.cvd_intelligence_status()
    assert status["feature_id"] == 232
    assert status["standalone"] is False
    assert status["classification_audit"]["trades_tested"] >= 10000


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/cvd/status").status_code == 200
    status = c.get("/api/platform/market-radar/cvd/status").json()
    assert status["feature_id"] == 232
    analysis = c.get("/api/platform/market-radar/cvd/analysis?asset=BTC")
    assert analysis.status_code == 200
    body = analysis.json()
    assert "cvd_value_display" in body
    assert c.get("/api/platform/market-radar/cvd/chart?asset=BTC&window=1H").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/cvd_intelligence_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 232
    assert seed["classification_audit"]["trades_tested"] >= 10000
    assert "BTC" in seed["assets"]
