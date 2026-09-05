"""Tests — Feed Latency / Data Freshness (#111)."""

from __future__ import annotations

import pytest

from bd_platform.feed_latency_intelligence import (
    FEED_PROFILES,
    _build_venue_row,
    _headline,
    compare_feed_latency,
    enrich_market_radar,
)


def test_headline_behind_live_data():
    h = _headline("gateio", -0.31, feed_age_ms=3200.0)
    assert "0.31%" in h
    assert "behind" in h
    assert "Gateio" in h or "gateio" in h.lower()


def test_headline_no_exploitation_wording():
    h = _headline("kucoin", -0.5, feed_age_ms=2000.0)
    assert "استغلال" not in h
    assert "arbitrage" not in h.lower()
    assert "profit" not in h.lower()


def test_build_venue_row_informational():
    row = _build_venue_row(
        exchange="gateio",
        mid=100.3,
        ref_mid=100.0,
        source="gateio_rest",
        feed_age_ms=3000,
        tier="slow",
    )
    assert row["informational_only"] is True
    assert row["lag_pct"] == pytest.approx(0.3, abs=0.01)
    assert "headline" in row
    assert row["tier"] == "slow"


def test_feed_profiles_fast_vs_slow():
    assert FEED_PROFILES["binance"]["tier"] == "fast"
    assert FEED_PROFILES["gateio"]["tier"] == "slow"
    assert FEED_PROFILES["binance"]["typical_interval_ms"] < FEED_PROFILES["mexc"]["typical_interval_ms"]


@pytest.mark.asyncio
async def test_compare_feed_latency_mock(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "bd_platform.feed_latency_intelligence._CACHE_PATH",
        tmp_path / "cache.json",
    )

    async def fake_ref(asset):
        return {
            "exchange": "binance",
            "mid": 100.0,
            "source": "test_ws",
            "feed_age_ms": 50.0,
            "tier": "fast",
        }, "live_book_hub"

    async def fake_gate(asset):
        return {"exchange": "gateio", "mid": 99.7, "source": "gateio_rest", "fetched_at": "t"}

    monkeypatch.setattr("bd_platform.feed_latency_intelligence._resolve_reference", fake_ref)
    monkeypatch.setattr("bd_platform.feed_latency_intelligence._fetch_gateio", fake_gate)
    monkeypatch.setattr(
        "bd_platform.feed_latency_intelligence._fetch_coinbase",
        lambda a: None,
    )
    monkeypatch.setattr(
        "bd_platform.feed_latency_intelligence._fetch_kucoin",
        lambda a: None,
    )

    out = await compare_feed_latency("BTC", exchanges=["gateio"])
    assert out["ok"] is True
    assert out["feature_id"] == 111
    assert out["product_name"] == "Data Freshness / Feed Latency"
    assert out["mode"] == "informational_only"
    assert "disclaimer" in out
    assert out["sla_met"] is True
    assert "behind" in out["summary"].lower() or "aligned" in out["summary"].lower()


@pytest.mark.asyncio
async def test_cache_hit(monkeypatch, tmp_path):
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("bd_platform.feed_latency_intelligence._CACHE_PATH", cache_path)

    call_count = 0

    async def fake_ref(asset):
        nonlocal call_count
        call_count += 1
        return {"exchange": "binance", "mid": 50.0, "tier": "fast"}, "live_book_hub"

    monkeypatch.setattr("bd_platform.feed_latency_intelligence._resolve_reference", fake_ref)

    first = await compare_feed_latency("ETH")
    second = await compare_feed_latency("ETH")
    assert first["ok"] is True
    assert second.get("cache_hit") is True
    assert call_count == 1


def test_enrich_market_radar():
    radar = {"summary": "test", "sectors": []}
    feed = {"ok": True, "summary": "Price on Gate.io is 0.3% behind live data", "max_lag_pct": 0.3, "alerts": []}
    out = enrich_market_radar(radar, feed)
    assert out["feed_latency"]["enabled"] is True
    assert "0.3%" in out["feed_latency"]["summary"]
