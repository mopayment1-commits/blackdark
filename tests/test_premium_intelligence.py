"""Tests — #255 Korea Premium + #233 Coinbase Premium (Premium Intelligence Module)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from bd_platform import premium_intelligence as pi


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    now = datetime.now(UTC)
    fx_ts = now.isoformat()
    price_ts = now.isoformat()

    seed = tmp_path / "premium_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "weights_version": "1.3",
            "weights_last_rebalanced": "2026-08-01",
            "fx": {
                "KRW/USD": {
                    "rate": 1350.2,
                    "source": "ECB",
                    "timestamp": fx_ts,
                    "update_frequency": "Hourly",
                    "max_age_hours": 2,
                },
            },
            "korea": {
                "venues": {
                    "upbit": {"name": "Upbit", "base_volume_weight": 0.4, "status": "up"},
                    "bithumb": {"name": "Bithumb", "base_volume_weight": 0.35, "status": "up"},
                    "coinone": {"name": "Coinone", "base_volume_weight": 0.25, "status": "up"},
                },
                "global_reference": {
                    "exchange": "binance",
                    "pair": "BTC/USDT",
                    "methodology": "VWAP 1H",
                    "fx_adjusted": True,
                },
                "regime_history": {
                    "BTC": {
                        "percentile_75": 3.5,
                        "percentile_50": 1.8,
                        "percentile_25": 0.5,
                        "current_duration_days": 5,
                    },
                },
                "assets": {
                    "BTC": {
                        "venues": {
                            "upbit": {"price_usd_fx": 98100.0, "timestamp": price_ts},
                            "bithumb": {"price_usd_fx": 98050.0, "timestamp": price_ts},
                            "coinone": {"price_usd_fx": 98080.0, "timestamp": price_ts},
                        },
                        "global_reference_price_usd": 95000.0,
                        "global_reference_timestamp": price_ts,
                        "rolling_premium_pct": [3.0, 3.1, 3.2],
                    },
                },
            },
            "coinbase": {
                "venue": {"name": "Coinbase", "status": "up", "timestamp": price_ts},
                "reference": {
                    "exchange": "binance",
                    "pair": "BTC/USDT",
                    "methodology": "VWAP 1H",
                    "time_alignment": "1-minute bucket",
                },
                "assets": {
                    "BTC": {
                        "coinbase_price_usd": 95150.0,
                        "reference_price_usd": 95000.0,
                        "coinbase_timestamp": price_ts,
                        "reference_timestamp": price_ts,
                        "rolling_premium_pct": [0.14, 0.15, 0.16],
                        "rolling_z_score": [0.6, 0.7, 0.84],
                        "persistence_days": 3,
                        "corroboration": {"causation_claim_allowed": False},
                    },
                },
            },
            "regions": {
                "us": {"feature_id": 233, "label": "US (Coinbase)", "status": "live"},
                "korea": {"feature_id": 255, "label": "Korea", "status": "live"},
                "japan": {"label": "Japan", "status": "planned"},
                "europe": {"label": "Europe", "status": "planned"},
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(pi, "_SEED_PATH", seed)
    return seed


def test_fx_timestamps_visible(isolated_seed):
    result = pi.get_korea_premium("BTC")
    assert "ECB" in result["fx"]["fx_display"]
    assert "Timestamp:" in result["fx"]["fx_display"]
    assert "Update Frequency: Hourly" in result["fx"]["fx_display"]
    assert result["fx"]["premium_available"] is True


def test_fx_stale_premium_na(isolated_seed, monkeypatch):
    stale_ts = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    seed["fx"]["KRW/USD"]["timestamp"] = stale_ts
    isolated_seed.write_text(json.dumps(seed), encoding="utf-8")

    result = pi.get_korea_premium("BTC")
    assert result["fx"]["stale"] is True
    assert result["premium_pct"] is None
    assert "FX Stale | Premium: N/A" in result["premium_display"]


def test_venue_normalization_weights(isolated_seed):
    result = pi.get_korea_premium("BTC")
    display = result["venue_weights_display"]
    assert "Upbit (40% weight)" in display
    assert "Bithumb (35% weight)" in display
    assert "Coinone (25% weight)" in display
    assert "Weights v1.3" in display
    assert "Last Rebalanced: 2026-08-01" in display


def test_outage_recalculates_weights(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    seed["korea"]["venues"]["coinone"]["status"] = "down"
    isolated_seed.write_text(json.dumps(seed), encoding="utf-8")

    result = pi.get_korea_premium("BTC")
    assert "coinone" in result["down_venues"]
    assert "Coinone down" in result["outage_alert"]
    assert "Weights recalculated" in result["outage_alert"]
    assert "Coverage reduced" in result["outage_alert"]
    assert "Upbit 55%" in result["outage_alert"] or "Upbit 53%" in result["outage_alert"]


def test_global_reference_explicit(isolated_seed):
    result = pi.get_korea_premium("BTC")
    ref = result["global_reference_display"]
    assert "Reference: Binance BTC/USDT" in ref
    assert "FX-adjusted: Yes" in ref
    assert "Methodology: VWAP 1H" in ref


def test_regime_detection(isolated_seed):
    result = pi.get_korea_premium("BTC")
    regime = result["regime"]
    assert regime["regime"] == "Premium (Kimchi)"
    assert "Historical Context:" in regime["regime_display"]
    assert "Duration: 5 days" in regime["regime_display"]


def test_not_arbitrage_opportunity(isolated_seed):
    result = pi.get_korea_premium("BTC")
    assert result["not_arbitrage_opportunity"] is True
    assert "local banking" in result["arbitrage_note"].lower()
    assert result["fee_context"]["fee_db_feature_id"] == 130


def test_mandatory_disclaimer(isolated_seed):
    result = pi.get_korea_premium("BTC")
    assert result["disclaimer_hideable"] is False
    assert "not investment advice" in result["disclaimer"].lower()


def test_coinbase_time_alignment(isolated_seed):
    result = pi.get_coinbase_premium("BTC")
    assert result["time_aligned"] is True
    assert "Aligned: Yes" in result["time_alignment_display"]
    assert "Reference: Binance BTC/USDT" in result["reference_display"]


def test_coinbase_no_causation_without_corroboration(isolated_seed):
    result = pi.get_coinbase_premium("BTC")
    assert result["no_causation_without_corroboration"] is True
    assert "not asserted without corroboration" in result["causation_note"].lower()


def test_coinbase_outage_handling(isolated_seed):
    seed = json.loads(isolated_seed.read_text(encoding="utf-8"))
    seed["coinbase"]["venue"]["status"] = "down"
    isolated_seed.write_text(json.dumps(seed), encoding="utf-8")

    result = pi.get_coinbase_premium("BTC")
    assert result["premium_pct"] is None
    assert "venue outage" in result["premium_display"].lower()
    assert "Coverage reduced" in result["outage_alert"]


def test_unified_regional_dashboard(isolated_seed):
    result = pi.get_regional_premiums_dashboard("BTC")
    assert result["standalone"] is False
    assert 255 in result["feature_ids"]
    assert 233 in result["feature_ids"]
    assert len(result["cards"]) == 4
    labels = [c["label"] for c in result["cards"]]
    assert "US (Coinbase)" in labels
    assert "Korea" in labels
    assert "Japan" in labels
    assert "Europe" in labels
    assert "Regional Premiums:" in result["regions_display"]


def test_not_standalone(isolated_seed):
    status = pi.premium_intelligence_status()
    assert status["standalone"] is False
    assert status["feature_ids"] == [255, 233]
    assert "Premium Intelligence Module" in status["merged_into"]


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/premiums/status").status_code == 200
    status = c.get("/api/platform/market-radar/premiums/status").json()
    assert status["feature_ids"] == [255, 233]
    dash = c.get("/api/platform/market-radar/premiums/dashboard?asset=BTC")
    assert dash.status_code == 200
    assert len(dash.json()["cards"]) == 4
    assert c.get("/api/platform/market-radar/premiums/korea?asset=BTC").status_code == 200
    assert c.get("/api/platform/market-radar/premiums/coinbase?asset=BTC").status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/premium_intelligence_seed.json").read_text(encoding="utf-8"))
    assert 255 in seed["feature_ids"]
    assert 233 in seed["feature_ids"]
    assert seed["standalone"] is False
    assert "BTC" in seed["korea"]["assets"]
