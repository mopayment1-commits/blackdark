"""Tests — #210 ETF Data + #240 ETF Flow Intelligence (ETF Intelligence Module)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import etf_intelligence as etf


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "etf_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "feature_ids": [210, 240],
            "feature_label": "ETF Intelligence Module",
            "standalone": False,
            "module_version": "1.0",
            "last_updated": "2026-08-25",
            "tier": "pro",
            "sources": [
                {
                    "name": "Farside Investors",
                    "url": "https://farside.co.uk/btc/",
                    "verified": True,
                    "last_verified": "2026-08-25",
                    "data_type": "spot_etf_flows",
                },
            ],
            "timezone_alignment": {
                "etf_flow": "Daily close 16:00 EST",
                "crypto_market": "24H UTC",
                "alignment": "EST close + 1H lag",
            },
            "rolling_methodology": "Sum of daily net flows (Creation - Redemption)",
            "missing_day_policy": "No interpolation",
            "assets": {
                "BTC": {
                    "spot_etfs": ["IBIT", "FBTC"],
                    "daily_records": [
                        {"date": "2026-08-18", "status": "valid", "creation_usd": 500000000, "redemption_usd": 100000000, "net_flow_usd": 400000000, "aum_usd": 95000000000},
                        {"date": "2026-08-19", "status": "valid", "creation_usd": 300000000, "redemption_usd": 150000000, "net_flow_usd": 150000000, "aum_usd": 95150000000},
                        {"date": "2026-08-20", "status": "valid", "creation_usd": 200000000, "redemption_usd": 250000000, "net_flow_usd": -50000000, "aum_usd": 95100000000},
                        {"date": "2026-08-21", "status": "valid", "creation_usd": 450000000, "redemption_usd": 120000000, "net_flow_usd": 330000000, "aum_usd": 95430000000},
                        {"date": "2026-08-22", "status": "weekend", "reason": "US Market Closed (Weekend)", "last_valid": "2026-08-21", "next_expected": "2026-08-25"},
                        {"date": "2026-08-23", "status": "weekend", "reason": "US Market Closed (Weekend)", "last_valid": "2026-08-21", "next_expected": "2026-08-25"},
                        {"date": "2026-08-24", "status": "valid", "creation_usd": 500000000, "redemption_usd": 85000000, "net_flow_usd": 415000000, "aum_usd": 95845000000},
                        {"date": "2026-08-25", "status": "valid", "creation_usd": 480000000, "redemption_usd": 95000000, "net_flow_usd": 385000000, "aum_usd": 96230000000},
                    ],
                    "crypto_prices": [
                        {"date": "2026-08-18", "close_usd": 115800, "volume_usd": 30000000000},
                        {"date": "2026-08-19", "close_usd": 115500, "volume_usd": 29000000000},
                        {"date": "2026-08-20", "close_usd": 114900, "volume_usd": 30500000000},
                        {"date": "2026-08-21", "close_usd": 115200, "volume_usd": 29200000000},
                        {"date": "2026-08-24", "close_usd": 116100, "volume_usd": 32800000000},
                        {"date": "2026-08-25", "close_usd": 116500, "volume_usd": 34100000000},
                    ],
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(etf, "_SEED_PATH", seed)
    return seed


def test_official_source_mapping(isolated_seed):
    status = etf.etf_intelligence_status()
    src = status["sources"][0]
    assert src["name"] == "Farside Investors"
    assert src["verified"] is True
    assert "Last Verified" in src["source_display"]
    assert "farside.co.uk" in src["source_display"]


def test_official_source_issuer_sec_bloomberg(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    seed["official_sources"] = {
        "types": ["Issuer Filing", "SEC", "Bloomberg"],
        "display": "Source: Issuer Filing | SEC | Bloomberg",
        "last_verified": "2026-08-25",
    }
    seed["assets"]["BTC"]["etp_products"] = [
        {
            "ticker": "IBIT",
            "name": "iShares Bitcoin Trust",
            "issuer": "BlackRock",
            "official_source": "Issuer Filing | SEC | Bloomberg",
            "aum_usd": 52000000000,
            "daily_flow_usd": 180000000,
            "nav_usd": 38.42,
            "market_price_usd": 38.55,
            "crypto_linkage": {"btc_exposure_pct": 99.8, "eth_exposure_pct": 0.0, "other_exposure_pct": 0.2},
            "as_of": "2026-08-25",
        },
    ]
    seed["assets"]["BTC"]["aggregate_crypto_linkage"] = {
        "btc_exposure_pct": 99.5, "eth_exposure_pct": 0.0, "other_exposure_pct": 0.5,
    }
    isolated_seed.write_text(json.dumps(seed), encoding="utf-8")

    dash = etf.build_etf_intelligence_dashboard("BTC")
    official = dash["official_sources"]
    assert "Issuer Filing" in official["display"]
    assert "SEC" in official["display"]
    assert "Bloomberg" in official["display"]


def test_crypto_linkage_visible(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    seed["official_sources"] = {"types": ["Issuer Filing", "SEC", "Bloomberg"]}
    seed["assets"]["BTC"]["etp_products"] = [
        {
            "ticker": "IBIT", "name": "Test", "issuer": "BlackRock",
            "aum_usd": 1e10, "daily_flow_usd": 1e8, "nav_usd": 38.0, "market_price_usd": 38.2,
            "crypto_linkage": {"btc_exposure_pct": 99.8, "eth_exposure_pct": 0.0, "other_exposure_pct": 0.2},
        },
    ]
    seed["assets"]["BTC"]["aggregate_crypto_linkage"] = {
        "btc_exposure_pct": 99.5, "eth_exposure_pct": 0.0, "other_exposure_pct": 0.5,
    }
    isolated_seed.write_text(json.dumps(seed), encoding="utf-8")

    etp = etf.build_etp_data("BTC")
    assert etp["ok"] is True
    product = etp["products"][0]
    assert "BTC exposure:" in product["crypto_linkage"]["display"]
    assert "ETH:" in product["crypto_linkage"]["display"]
    assert "Other:" in product["crypto_linkage"]["display"]
    assert "99.8%" in product["crypto_linkage"]["display"]


def test_aum_flows_premium_normalized(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    seed["official_sources"] = {"types": ["Issuer Filing", "SEC", "Bloomberg"]}
    seed["assets"]["BTC"]["etp_products"] = [
        {
            "ticker": "IBIT", "name": "Test", "issuer": "BlackRock",
            "aum_usd": 52000000000, "daily_flow_usd": 180000000,
            "nav_usd": 38.42, "market_price_usd": 38.55,
            "crypto_linkage": {"btc_exposure_pct": 99.8, "eth_exposure_pct": 0.0, "other_exposure_pct": 0.2},
        },
    ]
    seed["assets"]["BTC"]["aggregate_crypto_linkage"] = {
        "btc_exposure_pct": 99.5, "eth_exposure_pct": 0.0, "other_exposure_pct": 0.5,
    }
    isolated_seed.write_text(json.dumps(seed), encoding="utf-8")

    etp = etf.build_etp_data("BTC")
    product = etp["products"][0]
    assert product["aum_display"].startswith("$")
    assert "Premium" in product["premium_discount"]["display"] or "Discount" in product["premium_discount"]["display"]
    assert "NAV:" in product["premium_discount"]["display"]
    assert etp["aggregate"]["total_aum_usd"] > 0


def test_etp_disclaimer(isolated_seed):
    etp = etf.build_etp_data("BTC")
    assert "NAV may differ from market price" in etp["disclaimer"]
    assert etp["disclaimer_hideable"] is False
    dash = etf.build_etf_intelligence_dashboard("BTC")
    assert "NAV may differ from market price" in dash["disclaimer"]["text"]


def test_merged_210_240_no_standalone(isolated_seed):
    etp = etf.build_etp_data("BTC")
    assert etp["feature_id"] == 210
    assert 240 in etp["feature_ids"]
    assert etp["standalone"] is False
    assert etp["merged_with"] == "#240 ETF Flow Intelligence"


def test_timezone_alignment(isolated_seed):
    dash = etf.build_etf_intelligence_dashboard("BTC")
    tz = dash["timezone_alignment"]
    assert "16:00 EST" in tz["etf_flow"]
    assert "24H UTC" in tz["crypto_market"]
    assert "1H lag" in tz["alignment"]


def test_missing_day_handling(isolated_seed):
    series = etf.build_etf_flow_series("BTC")
    missing = [d for d in series["daily_flows"] if d.get("missing")]
    assert len(missing) >= 1
    weekend = next(d for d in missing if d["date"] == "2026-08-22")
    assert weekend["interpolated"] is False
    assert "Last Valid" in weekend["missing_display"]
    assert "Next Expected" in weekend["missing_display"]
    assert "2026-08-21" in weekend["missing_display"]


def test_rolling_totals_methodology(isolated_seed):
    dash = etf.build_etf_intelligence_dashboard("BTC")
    rolling = dash["rolling_totals"]
    assert "Methodology" in rolling["rolling_display"]
    assert "Creation - Redemption" in rolling["methodology"]
    assert rolling["7d_net_flow_usd"] != 0
    assert "7D Net Flow" in rolling["7d_display"]


def test_market_context_regime(isolated_seed):
    ctx = etf.build_etf_market_context("BTC")
    assert ctx["regime"] in ("Inflow-Driven", "Price-Driven", "Divergent")
    assert "Flow-BTC Correlation" in ctx["context_display"]
    assert "Regime:" in ctx["context_display"]


def test_aum_flow_price_triangle(isolated_seed):
    dash = etf.build_etf_intelligence_dashboard("BTC")
    tri = dash["aum_flow_price_triangle"]
    assert "AUM:" in tri["triangle_display"]
    assert "Daily Flow:" in tri["triangle_display"]
    assert "Price Change:" in tri["triangle_display"]
    assert "Interpretation:" in tri["triangle_display"]
    assert tri["aum_usd"] > 0


def test_no_buy_signal_language(isolated_seed):
    dash = etf.build_etf_intelligence_dashboard("BTC")
    text = json.dumps(dash)
    assert "Buy BTC" not in text
    assert "buy now" not in text.lower()
    assert dash["not_buy_sell_signal"] is True
    if dash.get("inflow_context"):
        assert "Context:" in dash["inflow_context"]


def test_disclaimer_non_hideable(isolated_seed):
    dash = etf.build_etf_intelligence_dashboard("BTC")
    assert dash["disclaimer"]["hideable"] is False
    assert dash["disclaimer"]["collapsible"] is False
    assert dash["disclaimer_top"] == dash["disclaimer_bottom"]
    assert "not predictive" in dash["disclaimer"]["text"].lower()


def test_not_standalone_merged(isolated_seed):
    status = etf.etf_intelligence_status()
    assert status["standalone"] is False
    assert 210 in status["feature_ids"]
    assert 240 in status["feature_ids"]
    assert status["merged_into"] == "ETF Intelligence Module"


def test_macro_context_only(isolated_seed):
    dash = etf.build_etf_intelligence_dashboard("BTC")
    assert dash["macro_context_only"] is True
    assert dash["not_a_recommendation"] is True


def test_flow_series_valid_counts(isolated_seed):
    series = etf.build_etf_flow_series("BTC")
    assert series["valid_day_count"] == 6
    assert series["missing_day_count"] == 2


def test_divergent_interpretation(isolated_seed):
    interp = etf._triangle_interpretation(95_000_000_000, 500_000_000, -1.5)
    assert "distribution pressure" in interp


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/etf-intelligence/status").status_code == 200
    status = c.get("/api/platform/market-radar/etf-intelligence/status").json()
    assert 210 in status["feature_ids"]
    assert 240 in status["feature_ids"]
    dash = c.get("/api/platform/market-radar/etf-intelligence/dashboard?asset=BTC")
    assert dash.status_code == 200
    body = dash.json()
    assert body["aum_flow_price_triangle"]["aum_usd"] > 0
    assert c.get("/api/platform/market-radar/etf-intelligence/flows?asset=BTC").status_code == 200
    assert c.get("/api/platform/market-radar/etf-intelligence/market-context?asset=BTC").status_code == 200
    etp = c.get("/api/platform/market-radar/etf-intelligence/etp-data?asset=BTC")
    assert etp.status_code == 200
    assert etp.json()["feature_id"] == 210


def test_full_seed_exists():
    seed = json.loads(Path("data/etf_intelligence_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_ids"] == [210, 240]
    assert seed["standalone"] is False
    assert "BTC" in seed["assets"]
    assert len(seed["sources"]) >= 1
    assert "official_sources" in seed
    assert "Issuer Filing" in seed["official_sources"]["display"]
    assert len(seed["assets"]["BTC"].get("etp_products", [])) >= 4
