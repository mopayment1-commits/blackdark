"""Tests — #267 Market Cap / Supply merged into #705 + #217."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import canonical_asset_registry as car
from bd_platform import market_cap_supply as mcs
from bd_platform import ohlcv_core_feed as ocf


@pytest.fixture
def isolated_supply(tmp_path, monkeypatch):
    seed = tmp_path / "supply_provenance_seed.json"
    seed.write_text(
        json.dumps({
            "supply_data_version": "3.1",
            "assets": {
                "BTC": {
                    "supply_version": "3.1",
                    "last_verified_utc": "2026-08-25T00:00:00+00:00",
                    "next_verification_utc": "2026-08-26T00:00:00+00:00",
                    "price_methodology": "VWAP 1H",
                    "supplies": [
                        {"supply_type": "circulating", "amount": 19850000, "source": "On-Chain Query", "verified": True},
                        {"supply_type": "total", "amount": 19850000, "source": "On-Chain Query", "verified": True},
                        {"supply_type": "max", "amount": 21000000, "source": "Protocol Docs", "verified": True},
                    ],
                    "self_reported_cross_check": None,
                },
                "ARB": {
                    "supply_version": "3.1",
                    "last_verified_utc": "2026-08-25T00:00:00+00:00",
                    "next_verification_utc": "2026-08-26T00:00:00+00:00",
                    "price_methodology": "VWAP 1H",
                    "supplies": [
                        {"supply_type": "circulating", "amount": 987500, "source": "On-Chain Query", "verified": True},
                        {"supply_type": "total", "amount": 10000000000, "source": "Protocol Docs", "verified": False},
                        {"supply_type": "max", "amount": 10000000000, "source": "Protocol Docs", "verified": False},
                    ],
                    "self_reported_cross_check": {
                        "self_reported": 1000000,
                        "on_chain_verified": 987500,
                        "variance_pct": -1.25,
                        "display": "Self-reported: 1,000,000 | On-chain verified: 987,500 | Variance: -1.25%",
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(mcs, "_SEED_PATH", seed)
    return seed


def test_supply_provenance_types(isolated_supply):
    prov = mcs.get_supply_provenance("BTC")
    assert prov is not None
    types = {s["supply_type"] for s in prov["supplies"]}
    assert types == {"circulating", "total", "max"}
    for s in prov["supplies"]:
        assert s.get("source")
        assert "provenance_display" in s


def test_three_market_caps_not_one(isolated_supply):
    block = mcs.build_market_cap_block("BTC", 100000.0)
    assert block is not None
    assert block["circulating_market_cap_usd"] == 19850000 * 100000.0
    assert block["fdv_usd"] == 19850000 * 100000.0
    assert block["max_supply_market_cap_usd"] == 21000000 * 100000.0
    assert "Circulating Market Cap:" in block["market_cap_display"]
    assert "Fully Diluted Valuation (FDV):" in block["market_cap_display"]
    assert "Max Supply Market Cap:" in block["market_cap_display"]


def test_methodology_documented(isolated_supply):
    block = mcs.build_market_cap_block("BTC", 50000.0)
    assert "VWAP 1H" in block["methodology"]
    assert "Circulating Supply" in block["methodology"]
    assert "daily" in block["methodology"]


def test_self_reported_cross_check(isolated_supply):
    prov = mcs.get_supply_provenance("ARB")
    assert prov["cross_check_display"] is not None
    assert "Self-reported:" in prov["cross_check_display"]
    assert "On-chain verified:" in prov["cross_check_display"]
    assert "Variance:" in prov["cross_check_display"]


def test_version_timestamp(isolated_supply):
    prov = mcs.get_supply_provenance("BTC")
    assert "Supply data v3.1" in prov["version_display"]
    assert "Last verified:" in prov["version_display"]
    assert "Next verification:" in prov["version_display"]


def test_mandatory_disclaimer(isolated_supply):
    block = mcs.build_market_cap_block("BTC", 100000.0)
    assert block["disclaimer_hideable"] is False
    assert "not a valuation metric" in block["disclaimer"].lower()


def test_not_standalone_not_paid_api(isolated_supply):
    block = mcs.build_market_cap_block("BTC", 100000.0)
    assert block["standalone"] is False
    assert block["not_a_paid_api"] is True
    assert block["basic_data_free"] is True
    assert "#705" in block["merged_into"][0] or "#217" in block["merged_into"][1]


def test_canonical_asset_integration(isolated_supply, tmp_path, monkeypatch):
    assets_seed = tmp_path / "canonical_assets_seed.json"
    assets_seed.write_text(
        json.dumps([
            {"stable_id": "asset:btc:bitcoin", "symbol": "BTC", "name": "Bitcoin",
             "lifecycle": "active", "lifecycle_version": 1, "chain": "bitcoin", "canonical": True},
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(car, "_SEED_PATH", assets_seed)
    monkeypatch.setattr(car, "_STORE_PATH", tmp_path / "canonical_assets.json")

    result = car.get_canonical_asset("asset:btc:bitcoin")
    assert result["asset"].get("supply_provenance") is not None
    assert 267 in [int(x.replace("#", "")) for x in result["asset"].get("integrated_features", [])]


def test_ohlcv_integration(isolated_supply, tmp_path, monkeypatch):
    ohlcv_seed = tmp_path / "ohlcv_core_seed.json"
    ohlcv_seed.write_text(
        json.dumps([{
            "id": "btc-test",
            "asset": "BTC",
            "interval": "1h",
            "open_time_utc": "2026-08-25T11:00:00+00:00",
            "close_time_utc": "2026-08-25T12:00:00+00:00",
            "sources": {
                "binance": {"open": 100.0, "high": 110.0, "low": 95.0, "close": 105.0, "volume": 100.0, "available": True},
                "okx": {"open": 101.0, "high": 109.0, "low": 96.0, "close": 104.0, "volume": 90.0, "available": True},
                "bybit": {"open": 100.5, "high": 108.0, "low": 95.5, "close": 104.5, "volume": 95.0, "available": True},
            },
            "onchain_volume_proxy": 280.0,
        }]),
        encoding="utf-8",
    )
    monkeypatch.setattr(ocf, "_SEED_PATH", ohlcv_seed)
    monkeypatch.setattr(ocf, "_STORE_PATH", tmp_path / "ohlcv_core_feed.json")

    result = ocf.get_ohlcv_candle("btc-test")
    mcap = result["candle"].get("market_cap_supply")
    assert mcap is not None
    assert mcap["circulating_market_cap_usd"] is not None
    assert "FDV" in mcap["fdv_display"]


def test_full_seed_exists():
    seed = json.loads(Path("data/supply_provenance_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 267
    assert seed["standalone"] is False
    assert "BTC" in seed["assets"]
