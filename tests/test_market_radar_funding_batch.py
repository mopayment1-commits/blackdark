"""Tests — #331 Derivatives Venue Feed + #333 Funding Rate Context Panel (absorbed into #274)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from bd_platform import market_data_engine as mde


@pytest.fixture
def mde_seed(tmp_path, monkeypatch):
    now = datetime.now(UTC)
    fresh = (now - timedelta(minutes=30)).isoformat()
    p = tmp_path / "market_data_engine_seed.json"
    p.write_text(json.dumps({
        "provider_semantics": {
            "schema_version": "1.0",
            "freshness_sla_seconds": 3600,
            "fallback_sources": {"binance": "bybit"},
        },
        "weighting": {
            "formula": "weighted_funding = Σ(funding_rate × oi_weight) / Σ(oi_weight)",
            "outlier_threshold_z": 3.0,
            "settlement_sync_logic": "align_to_utc_funding_interval_boundary",
        },
        "venues": {
            "BTC": {
                "persistence": {"hours_positive": 12, "hours_negative": 0},
                "crowding_state": "elevated_long_funding",
                "venue_list": [
                    {
                        "venue": "binance", "asset": "BTC", "funding_rate": 0.0005,
                        "open_interest_usd": 1e10, "liquidation_usd_24h": 4e7,
                        "volume_24h_usd": 3e10, "funding_timestamp_utc": fresh,
                        "settlement_time_utc": fresh, "provider": "Binance API",
                        "fallback_provider": "Bybit API",
                    },
                    {
                        "venue": "bybit", "asset": "BTC", "funding_rate": 0.0003,
                        "open_interest_usd": 5e9, "liquidation_usd_24h": 2e7,
                        "volume_24h_usd": 1e10, "funding_timestamp_utc": fresh,
                        "settlement_time_utc": fresh, "provider": "Bybit API",
                        "fallback_provider": "OKX API",
                    },
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(mde, "_SEED_PATH", p)
    return p


def test_331_derivatives_venue_feed_absorbed(mde_seed):
    feed = mde.build_derivatives_venue_feed("BTC")
    assert feed["sub_task"] == "#331"
    assert feed["standalone_rejected"] is True
    assert feed["title"] == "Derivatives Venue Feed"
    assert feed["surface"] == "market_data_display"
    assert feed["no_dashboard"] is True
    assert feed["feeds_engine"] is True
    assert feed["no_trading_signal_mask"] is True
    assert feed["venue_count"] == 2
    assert "Funding Rate =" in feed["venue_metrics"][0]["funding_rate_display"]


def test_331_provider_semantics_lock(mde_seed):
    feed = mde.build_derivatives_venue_feed("BTC")
    ps = feed["provider_semantics"]
    assert ps["unified_schema_per_venue"] is True
    assert ps["freshness_sla_seconds"] == 3600
    assert "binance" in ps["fallback_sources"]


def test_331_no_signal_language(mde_seed):
    feed = mde.build_derivatives_venue_feed("BTC")
    assert feed["no_squeeze_language"] is True
    assert feed["no_opportunity_language"] is True
    assert feed["raw_display_only"] is True
    for row in feed["venue_metrics"]:
        assert "Short Squeeze" not in row["display"]
        assert row["raw_display_only"] is True


def test_333_funding_rate_context_panel_renamed(mde_seed):
    panel = mde.build_funding_rate_context_panel("BTC")
    assert panel["sub_task"] == "#333"
    assert panel["title"] == "Funding Rate Context Panel"
    assert panel["renamed_from"] == "Funding Rate Intelligence"
    assert panel["no_intelligence_in_name"] is True
    assert panel["standalone_rejected"] is True
    assert panel["surface"] == "market_data_display"


def test_333_weighting_documented(mde_seed):
    panel = mde.build_funding_rate_context_panel("BTC")
    w = panel["weighting"]
    assert w["weighting_documented"] is True
    assert "oi_weight" in w["formula"]
    assert w["outlier_threshold_z"] == 3.0
    assert w["settlement_timing_aligned"] is True
    assert panel["weighted_funding"]["weighted_funding_rate"] is not None
    assert "Weighted Funding Rate =" in panel["weighted_funding"]["weighted_funding_display"]


def test_333_no_trading_signal_mask(mde_seed):
    panel = mde.build_funding_rate_context_panel("BTC")
    assert panel["no_trading_signal_mask"] is True
    assert panel["crowding_not_signal"] is True
    assert panel["no_squeeze_language"] is True


def test_274_status_absorbed_tickets(mde_seed):
    status = mde.market_data_engine_status()
    assert status["feature_id"] == 274
    assert status["standalone"] is False
    assert 331 in status["absorbed_tickets"]
    assert 333 in status["absorbed_tickets"]
    assert status["no_separate_sprint"] is True
    assert status["apis_counted_as_cogs"] is True


def test_api_routes(mde_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/market-radar/derivatives-venue-feed/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/derivatives-venue-feed?asset=BTC").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/funding-rate-context/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/market-radar/funding-rate-context?asset=BTC").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/market_data_engine_seed.json").read_text())
    assert seed["feature_id"] == 274
    assert "331" in seed.get("absorbed_tickets", {})
    assert "333" in seed.get("absorbed_tickets", {})
