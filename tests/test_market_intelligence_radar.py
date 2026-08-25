"""Tests — Market Intelligence features #155, #140, #186, #142, #139."""

from __future__ import annotations

import pytest

from bd_platform import (
    industry_event_monitor as iem,
    liquidity_health_check as lhc,
    macro_events_engine as mee,
    market_radar_infrastructure as mri,
    sentiment_intelligence as si,
)


# ── #155 Market Radar Infrastructure ─────────────────────────────────────────


def test_normalize_asset_symbol():
    assert mri.normalize_asset_symbol("BTCUSDT") == "BTC"
    assert mri.normalize_asset_symbol("BTC-USD") == "BTC"
    assert mri.normalize_asset_symbol("eth") == "ETH"


def test_detect_price_outliers():
    rows = [
        {"price_usd": 100.0, "exchange": "a"},
        {"price_usd": 101.0, "exchange": "b"},
        {"price_usd": 150.0, "exchange": "bad"},
    ]
    clean, outliers = mri.detect_price_outliers(rows, tolerance_pct=3.0)
    assert len(clean) == 2
    assert len(outliers) == 1
    assert outliers[0]["exchange"] == "bad"


def test_market_radar_infrastructure_status():
    status = mri.market_radar_infrastructure_status()
    assert status["feature_id"] == 155
    assert status["user_facing"] is False


# ── #140 Macro Events ────────────────────────────────────────────────────────


def test_classify_macro_impact_fed():
    impact = mee.classify_macro_impact("Fed raises interest rate by 0.25%")
    assert impact["category"] == "monetary_policy"
    assert impact["btc_impact_forecast_24h_pct"] < 0


def test_classify_macro_impact_etf():
    impact = mee.classify_macro_impact("SEC approves spot Bitcoin ETF")
    assert impact["direction"] == "bullish"


# ── #186 Industry Event Monitor ────────────────────────────────────────────────


@pytest.fixture
def isolated_event_paths(tmp_path, monkeypatch):
    feed = tmp_path / "feed.jsonl"
    dedup = tmp_path / "dedup.json"
    monkeypatch.setattr(iem, "_FEED_PATH", feed)
    monkeypatch.setattr(iem, "_DEDUP_PATH", dedup)
    return feed, dedup


def test_categorize_event_hack():
    assert iem.categorize_event("Protocol hacked for $50M") == "hack"


def test_categorize_event_listing():
    assert iem.categorize_event("Binance adds new token listing") == "listing"


def test_ingest_event_deduplication(isolated_event_paths):
    ev1 = iem.ingest_event(title="Major hack on DeFi protocol", source="test", summary="exploit")
    ev2 = iem.ingest_event(title="Major hack on DeFi protocol", source="test", summary="exploit")
    assert ev1 is not None
    assert ev2 is None


def test_significance_high_impact():
    sig = iem.compute_significance(category="hack", affected_assets=["BTC"] * 55)
    assert sig["significance_level"] == "critical"
    assert sig["affected_asset_count"] == 55


# ── #142 Liquidity Health ────────────────────────────────────────────────────


def test_slippage_estimate_increases_with_order_size():
    small = lhc._estimate_slippage_bps(order_usd=1_000, liquidity_usd=1_000_000)
    large = lhc._estimate_slippage_bps(order_usd=100_000, liquidity_usd=1_000_000)
    assert large > small


def test_concentration_risk_high():
    risk = lhc._concentration_risk(50_000, 10_000_000)
    assert risk["concentration_risk"] == "high"


# ── #139 Sentiment Intelligence ──────────────────────────────────────────────


def test_weighted_sentiment():
    scores = [
        {"score": 0.5, "weight": 1.0},
        {"score": -0.5, "weight": 1.0},
    ]
    assert si._weighted_sentiment(scores) == 0.0


def test_sentiment_intelligence_status():
    status = si.sentiment_intelligence_status()
    assert status["feature_id"] == 139
    assert len(status["sources"]) >= 5
