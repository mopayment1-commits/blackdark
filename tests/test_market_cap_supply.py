"""Tests — #266 Market Cap & FDV Intelligence merged into #705 + #217 (replaces #267)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import canonical_asset_registry as car
from bd_platform import market_cap_supply as mcv
from bd_platform import ohlcv_core_feed as ocf


@pytest.fixture
def isolated_supply(tmp_path, monkeypatch):
    seed = tmp_path / "supply_provenance_seed.json"
    seed.write_text(
        json.dumps({
            "feature_id": 266,
            "replaces": 267,
            "supply_data_version": "2.1",
            "methodology_version": "2.0",
            "last_updated": "2026-08-25",
            "assets": {
                "BTC": {
                    "supply_version": "2.1",
                    "last_verified_utc": "2026-08-25T00:00:00+00:00",
                    "next_verification_utc": "2026-08-26T00:00:00+00:00",
                    "price_methodology": "VWAP 1H",
                    "last_price_usd": 100000,
                    "supplies": [
                        {
                            "supply_type": "circulating",
                            "amount": 19850000,
                            "source": "On-chain query + issuer docs",
                            "verified": True,
                        },
                        {
                            "supply_type": "total",
                            "amount": 19850000,
                            "source": "On-chain query + issuer docs",
                            "verified": True,
                        },
                        {
                            "supply_type": "max",
                            "amount": 21000000,
                            "source": "Protocol Docs",
                            "verified": True,
                        },
                    ],
                    "dominance": {
                        "dominance_pct": 52.3,
                        "method": "BTC Market Cap / Total Crypto Market Cap",
                        "source": "BLACKDARK aggregated",
                    },
                    "historical_qa": {
                        "date": "2024-01-01",
                        "market_cap_usd": 850000000000,
                        "sources_verified": 3,
                        "variance_pct": 0.3,
                        "variance_threshold_pct": 0.5,
                    },
                    "historical_series": {
                        "period": "1Y",
                        "market_cap_usd": [720000000000, 920000000000, 2320000000000],
                        "fdv_usd": [760000000000, 960000000000, 2450000000000],
                        "dominance_pct": [48.5, 52.0, 52.3],
                    },
                    "self_reported_cross_check": None,
                },
                "ETH": {
                    "supply_version": "2.1",
                    "last_verified_utc": "2026-08-25T00:00:00+00:00",
                    "next_verification_utc": "2026-08-26T00:00:00+00:00",
                    "price_methodology": "VWAP 1H",
                    "last_price_usd": 4500,
                    "supplies": [
                        {
                            "supply_type": "circulating",
                            "amount": 120300000,
                            "source": "On-chain query + issuer docs",
                            "verified": True,
                        },
                        {
                            "supply_type": "total",
                            "amount": 120300000,
                            "source": "On-chain query + issuer docs",
                            "verified": True,
                        },
                        {
                            "supply_type": "max",
                            "amount": None,
                            "source": "Protocol Docs",
                            "verified": True,
                            "note": "unlimited tokenomics",
                        },
                    ],
                    "dominance": {
                        "dominance_pct": 18.5,
                        "method": "ETH Market Cap / Total Crypto Market Cap",
                        "source": "BLACKDARK aggregated",
                    },
                    "historical_series": {
                        "period": "1Y",
                        "market_cap_usd": [220000000000, 547000000000],
                        "fdv_usd": [220000000000, 547000000000],
                        "dominance_pct": [17.2, 18.5],
                    },
                },
                "ARB": {
                    "supply_version": "2.1",
                    "last_verified_utc": "2026-08-25T00:00:00+00:00",
                    "next_verification_utc": "2026-08-26T00:00:00+00:00",
                    "price_methodology": "VWAP 1H",
                    "last_price_usd": 0.82,
                    "supplies": [
                        {
                            "supply_type": "circulating",
                            "amount": 987500,
                            "source": "On-chain query + issuer docs",
                            "verified": True,
                        },
                        {
                            "supply_type": "total",
                            "amount": 10000000000,
                            "source": "Protocol Docs",
                            "verified": False,
                        },
                        {
                            "supply_type": "max",
                            "amount": 10000000000,
                            "source": "Protocol Docs",
                            "verified": False,
                        },
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
    monkeypatch.setattr(mcv, "_SEED_PATH", seed)
    return seed


def test_supply_source_documented(isolated_supply):
    prov = mcv.get_supply_provenance("BTC")
    assert prov is not None
    circulating = next(s for s in prov["supplies"] if s["supply_type"] == "circulating")
    assert "Circulating Supply:" in circulating["display"]
    assert "Source:" in circulating["display"]
    assert "Version: 2.1" in circulating["display"]
    assert "Last Verified:" in circulating["display"]


def test_three_market_caps_not_one(isolated_supply):
    block = mcv.build_market_cap_block("BTC", 100000.0)
    assert block is not None
    assert block["circulating_market_cap_usd"] == 19850000 * 100000.0
    assert block["fdv_usd"] == 19850000 * 100000.0
    assert block["max_supply_market_cap_usd"] == 21000000 * 100000.0
    assert "Circulating Market Cap:" in block["market_cap_display"]
    assert "Fully Diluted Valuation (FDV):" in block["market_cap_display"]
    assert "Max Supply Market Cap:" in block["market_cap_display"]
    assert block["fdv_not_equal_market_cap"] is True


def test_missing_supply_not_fabricated(isolated_supply):
    block = mcv.build_market_cap_block("ETH", 4500.0)
    assert block is not None
    assert "N/A" in block["max_supply_display"]
    assert block.get("missing_supply_handling") is not None
    assert block["missing_supply_handling"]["not_fabricated"] is True


def test_historical_qa(isolated_supply):
    block = mcv.build_market_cap_block("BTC", 100000.0)
    qa = block["historical_qa"]
    assert qa["qa_passed"] is True
    assert "Market Cap (2024-01-01):" in qa["display"]
    assert "Verified against 3 sources" in qa["display"]
    assert "Variance:" in qa["display"]


def test_dominance_descriptive_only(isolated_supply):
    block = mcv.build_market_cap_block("BTC", 100000.0)
    dom = block["dominance"]
    assert "BTC Dominance: 52.3%" in dom["display"]
    assert "BLACKDARK aggregated" in dom["display"]
    assert dom["descriptive_only"] is True
    assert dom["no_buy_signal"] is True
    assert "buy" not in dom["display"].lower() or "BLACKDARK" in dom["display"]


def test_historical_trends_not_snapshot(isolated_supply):
    block = mcv.build_market_cap_block("BTC", 100000.0)
    trends = block["historical_trends"]
    assert "Market Cap Trend (1Y):" in trends["display"]
    assert "FDV Trend (1Y):" in trends["display"]
    assert "Dominance Trend (1Y):" in trends["display"]
    assert trends["not_snapshot_only"] is True


def test_methodology_versioned(isolated_supply):
    block = mcv.build_market_cap_block("BTC", 100000.0)
    meth = block["methodology_block"]
    assert "Valuation Methodology v2.0" in meth["display"]
    assert "Historical QA: Enabled" in meth["display"]


def test_self_reported_cross_check(isolated_supply):
    prov = mcv.get_supply_provenance("ARB")
    assert prov["cross_check_display"] is not None
    assert "Self-reported:" in prov["cross_check_display"]
    assert "On-chain verified:" in prov["cross_check_display"]


def test_mandatory_disclaimer(isolated_supply):
    block = mcv.build_market_cap_block("BTC", 100000.0)
    assert block["disclaimer_hideable"] is False
    assert "dominance measures relative size" in block["disclaimer"].lower()


def test_not_standalone_replaces_267(isolated_supply):
    block = mcv.build_market_cap_block("BTC", 100000.0)
    assert block["standalone"] is False
    assert block["feature_id"] == 266
    assert block["replaces"] == 267
    assert "#705" in block["merged_into"][0]


def test_valuation_profile(isolated_supply):
    profile = mcv.build_valuation_profile("BTC")
    assert profile["ok"] is True
    assert profile["feature_id"] == 266
    assert profile["market_cap"] is not None
    assert profile["dominance"] is not None


def test_canonical_asset_integration(isolated_supply, tmp_path, monkeypatch):
    assets_seed = tmp_path / "canonical_assets_seed.json"
    assets_seed.write_text(
        json.dumps([
            {
                "stable_id": "asset:btc:bitcoin",
                "symbol": "BTC",
                "name": "Bitcoin",
                "lifecycle": "active",
                "lifecycle_version": 1,
                "chain": "bitcoin",
                "canonical": True,
            },
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(car, "_SEED_PATH", assets_seed)
    monkeypatch.setattr(car, "_STORE_PATH", tmp_path / "canonical_assets.json")

    result = car.get_canonical_asset("asset:btc:bitcoin")
    assert result["asset"].get("market_cap_valuation") is not None
    assert 266 in [int(x.replace("#", "")) for x in result["asset"].get("integrated_features", [])]


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
    assert mcap["feature_id"] == 266
    assert "FDV" in mcap["fdv_display"]


def test_status(isolated_supply):
    status = mcv.market_cap_valuation_status()
    assert status["feature_id"] == 266
    assert status["replaces"] == 267
    assert status["acceptance_criteria"]["replaces_267"] is True
    assert status["acceptance_criteria"]["historical_qa"] is True


def test_api_routes(isolated_supply):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/valuation/status").status_code == 200
    resp = c.get("/api/platform/valuation/BTC")
    assert resp.status_code == 200
    body = resp.json()
    assert body["feature_id"] == 266
    assert body["market_cap"]["dominance"] is not None


def test_full_seed_exists():
    seed = json.loads(Path("data/supply_provenance_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 266
    assert seed["replaces"] == 267
    assert seed["standalone"] is False
    assert "BTC" in seed["assets"]
    assert "dominance" in seed["assets"]["BTC"]
    assert "historical_qa" in seed["assets"]["BTC"]
