"""Tests — #317 Funding Rate Analytics, #325 Instrument Master expansion, #328/#329 DMS."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from bd_platform import cross_exchange_funding_rate_analytics as cefra
from bd_platform import derivatives_market_state as dms
from blackdark.data import instrument_master as im


@pytest.fixture
def funding_seed(tmp_path, monkeypatch):
    now = datetime.now(UTC)
    fresh = (now - timedelta(minutes=30)).isoformat()
    stale = (now - timedelta(hours=2)).isoformat()
    p = tmp_path / "cross_exchange_funding_rate_analytics_seed.json"
    p.write_text(json.dumps({
        "fee_model": {"round_trip_pct": 0.10},
        "assets": {
            "BTC": {
                "venues": [
                    {
                        "venue": "binance", "asset_class": "perp", "asset_class_verified": True,
                        "funding_rate": 0.0005, "funding_interval_hours": 8,
                        "funding_timestamp_utc": fresh,
                        "open_interest_usd": 1e10, "volume_24h_usd": 3e10, "spread_bps": 0.5,
                        "confidence": "high", "source": "Binance API",
                    },
                    {
                        "venue": "okx", "asset_class": "perp", "asset_class_verified": True,
                        "funding_rate": 0.0003, "funding_interval_hours": 8,
                        "funding_timestamp_utc": stale,
                        "open_interest_usd": 5e9, "volume_24h_usd": 1e10, "spread_bps": 1.0,
                        "confidence": "medium", "source": "OKX API",
                    },
                    {"venue": "unknown", "unknown_venue": True, "asset_class": "perp"},
                ],
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(cefra, "_SEED_PATH", p)
    return p


@pytest.fixture
def im_seed(tmp_path, monkeypatch):
    p = tmp_path / "instrument_master_seed.json"
    p.write_text(json.dumps({
        "instruments": [
            {
                "instrument_id": "perp-1", "venue": "binance", "venue_type": "CEX",
                "asset_class": "perp", "base": "BTC", "quote": "USDT",
                "contract_symbol": "BTCUSDT", "expiry": None, "funding_interval_hours": 8,
                "index_reference": {"name": "BTCUSDT Index", "source_tag": "binance:index:BTCUSDT"},
                "mapping_confidence_pct": 99, "min_confidence_pct": 80,
                "last_verified": "2026-08-26T00:00:00+00:00", "tier": "hot",
                "daily_volume_usd": 1e10, "source_tag": "binance:futures:BTCUSDT",
            },
            {
                "instrument_id": "spot-1", "venue": "binance", "venue_type": "CEX",
                "asset_class": "spot", "base": "BTC", "quote": "USDT",
                "mapping_confidence_pct": 99, "min_confidence_pct": 80,
                "last_verified": "2026-08-26T00:00:00+00:00", "tier": "hot",
                "daily_volume_usd": 1e10, "source_tag": "binance:spot:BTCUSDT",
            },
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(im, "_SEED_PATH", p)
    return p


@pytest.fixture
def dms_seed(tmp_path, monkeypatch):
    p = tmp_path / "derivatives_market_state_seed.json"
    p.write_text(json.dumps({
        "backtest": {"false_positive_rate_pct": 20, "historical_events_tested": 10, "regime_accuracy_pct": 75},
        "assets": {
            "BTC": {
                "components": {
                    "funding_rate": 0.0005, "funding_z": 2.5, "oi_change_pct": 10, "oi_z": 2.0,
                    "liquidation_usd_24h": 5e7, "liquidation_z": 2.8, "price_change_24h_pct": 2.0,
                    "open_interest_usd": 1e10, "exchange_reserve_usd": 8e9,
                    "reserve_qa": {"verified": True, "method": "on_chain"},
                    "elr_history_90d": [1.0, 1.1, 1.2, 1.25],
                },
            },
            "ETH": {
                "components": {
                    "open_interest_usd": 1e9, "exchange_reserve_usd": 0,
                },
            },
        },
    }), encoding="utf-8")
    monkeypatch.setattr(dms, "_SEED_PATH", p)
    return p


def test_317_renamed_no_arbitrage_language(funding_seed):
    panel = cefra.build_cross_exchange_funding_panel("BTC")
    assert panel["renamed_from"] == "Cross-Exchange Funding Arbitrage Scanner"
    assert panel["no_arbitrage_language"] is True
    assert panel["no_scanner_language"] is True
    assert panel["no_opportunities_language"] is True
    assert panel["no_trade_recommendation"] is True
    table = panel["comparison_table"]
    assert table["output_format"] == "funding_rate_comparison_table"
    assert table["no_opportunities_language"] is True


def test_317_fee_model_and_net_apr(funding_seed):
    panel = cefra.build_cross_exchange_funding_panel("BTC")
    row = panel["comparison_table"]["rows"][0]
    assert row["net_equals_gross_minus_fees"] is True
    assert row["net_apr_pct"] == round(row["gross_apr_pct"] - 0.10, 4)
    assert row["capacity_estimate_usd"] > 0


def test_317_stale_and_unknown_venue(funding_seed):
    panel = cefra.build_cross_exchange_funding_panel("BTC")
    table = panel["comparison_table"]
    stale_rows = [r for r in table["rows"] if r["venue"] == "okx"]
    assert stale_rows[0]["stale_flag"] is True
    assert any(e["reason"] == "unknown_venue_excluded" for e in table["excluded_venues"])


def test_325_derivatives_contract_mapping(im_seed):
    result = im.list_derivatives_contract_mappings()
    assert result["absorbed_feature_id"] == 325
    assert result["standalone_rejected"] is True
    assert result["count"] == 1
    contract = result["contracts"][0]
    assert contract["expiry_normalized"] == "perpetual"
    assert contract["funding_interval_hours"] == 8
    assert contract["index_reference_tagged"] is True
    assert contract["no_separate_pipeline"] is True


def test_325_perp_mapping_includes_derivatives_block(im_seed):
    mapping = im.build_instrument_mapping(
        json.loads(im_seed.read_text())["instruments"][0]
    )
    assert "derivatives_contract" in mapping
    assert mapping["derivatives_contract"]["sub_task"] == "#325"


def test_328_regime_classification_subcomponent(dms_seed):
    panel = dms.build_derivatives_market_state_panel("BTC")
    regime = panel["regime"]
    assert regime["sub_component"] == "Regime Classification Sub-component"
    assert regime["standalone_rejected"] is True
    assert regime["formula_version"] == "1.0"
    assert regime["regime"] in ("crowded", "flush", "normal")


def test_329_elr_formula_and_percentile(dms_seed):
    panel = dms.build_derivatives_market_state_panel("BTC")
    elr = panel["leverage_ratio"]
    assert elr["sub_task"] == "#329"
    assert elr["formula"] == "ELR = OI / Exchange Reserve"
    assert elr["elr"] == round(1e10 / 8e9, 4)
    assert elr["historical_percentile"]["window_days"] == 90
    assert elr["denominator_qa"]["reserve_verified"] is True


def test_329_zero_reserve_protection(dms_seed):
    panel = dms.build_derivatives_market_state_panel("ETH")
    elr = panel["leverage_ratio"]
    assert elr["elr"] is None
    assert elr["warning"] == "Insufficient reserve data"


def test_api_routes(funding_seed, im_seed, dms_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/intelligence-ledger/cross-exchange-funding/status").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/cross-exchange-funding?asset=BTC").status_code == 200
    assert c.get("/api/v1/data/instrument-master/derivatives-contracts").status_code == 200
    assert c.get("/api/platform/intelligence-ledger/derivatives-market-state?asset=BTC").status_code == 200


def test_full_seeds_exist():
    funding = json.loads(Path("data/cross_exchange_funding_rate_analytics_seed.json").read_text())
    assert funding["feature_id"] == 317
    im_data = json.loads(Path("data/instrument_master_seed.json").read_text())
    assert "325" in im_data.get("absorbed_tickets", {})
    dms_data = json.loads(Path("data/derivatives_market_state_seed.json").read_text())
    assert "328" in dms_data.get("absorbed_tickets", {})
