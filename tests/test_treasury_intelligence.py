"""Tests — #239 Digital Asset Treasury Company Intelligence."""

from __future__ import annotations

import json
from datetime import date

import pytest

from bd_platform import treasury_intelligence as ti


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "treasury_intelligence_seed.json"
    seed.write_text(
        json.dumps({
            "feature_id": 239,
            "methodology_version": "1.0",
            "companies": {
                "MSTR": {
                    "ticker": "MSTR",
                    "name": "MicroStrategy Inc.",
                    "filing": {
                        "source": "SEC",
                        "form": "10-Q",
                        "item": "Item 7",
                        "filed_date": "2026-08-15",
                        "reporting_period": "Q2 2026",
                        "reporting_period_end": "2026-07-31",
                        "next_expected_filing": "2026-11-15",
                    },
                    "holdings": {"asset": "BTC", "disclosed_amount": 10000},
                    "normalized": {
                        "btc_per_share": 0.00015,
                        "pct_of_market_cap": 35.0,
                        "cost_basis_usd": 500000000,
                        "unrealized_pnl_pct": 120.0,
                        "treasury_value_usd": 1100000000,
                        "market_cap_usd": 3140000000,
                    },
                    "crypto_linkage": {
                        "linked_asset": "BTC",
                        "stock_btc_correlation_90d": 0.72,
                        "beta_to_btc": 1.8,
                        "btc_exposure_level": "High",
                    },
                },
                "TSLA": {
                    "ticker": "TSLA",
                    "name": "Tesla Inc.",
                    "filing": {
                        "source": "SEC",
                        "form": "10-Q",
                        "item": "Item 7",
                        "filed_date": "2026-07-24",
                        "reporting_period": "Q2 2026",
                        "reporting_period_end": "2026-06-30",
                        "next_expected_filing": "2026-10-24",
                    },
                    "holdings": {
                        "asset": "BTC",
                        "disclosed_amount": 9720,
                        "estimated_current": 10500,
                        "estimate_confidence": "Low",
                        "estimate_method": "Heuristic",
                    },
                    "normalized": {
                        "btc_per_share": 0.000003,
                        "pct_of_market_cap": 0.8,
                        "cost_basis_usd": 1500000000,
                        "unrealized_pnl_pct": 28.5,
                        "treasury_value_usd": 1040000000,
                        "market_cap_usd": 780000000000,
                    },
                    "crypto_linkage": {
                        "linked_asset": "BTC",
                        "stock_btc_correlation_90d": 0.18,
                        "beta_to_btc": 0.4,
                        "btc_exposure_level": "Low",
                    },
                },
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(ti, "_SEED_PATH", seed)
    return seed


REF = date(2026, 8, 25)


def test_filing_source_timestamps(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    company = seed["companies"]["MSTR"]
    filing = ti.build_filing_block(company["filing"], company["holdings"])
    assert "SEC" in filing["display"]
    assert "10-Q" in filing["display"]
    assert "Filed: 2026-08-15" in filing["display"]
    assert "Reporting Period: Q2 2026" in filing["display"]
    assert "Next Expected Filing: 2026-11-15" in filing["display"]


def test_live_holdings_status(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    company = seed["companies"]["MSTR"]
    status = ti.build_holdings_status(company["holdings"], company["filing"], as_of=REF)
    assert status["freshness"] == "Live"
    assert "Last Disclosed:" in status["display"]
    assert "Live Treasury" not in status["display"]
    assert status["presented_as_live"] is True


def test_stale_holdings_not_presented_as_live(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    company = seed["companies"]["TSLA"]
    status = ti.build_holdings_status(company["holdings"], company["filing"], as_of=REF)
    assert status["freshness"] == "Stale"
    assert status["age_days"] == 56
    assert "Status: Stale" in status["display"]
    assert "Live Treasury" not in status["display"]
    assert status["presented_as_live"] is False
    assert "estimate" in status
    assert "Estimated Current" in status["estimate"]["display"]
    assert "Confidence: Low" in status["estimate"]["display"]


def test_treasury_exposure_normalized(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    exposure = ti.normalize_treasury_exposure(seed["companies"]["MSTR"])
    assert exposure["btc_per_share"] == 0.00015
    assert exposure["pct_of_market_cap"] == 35.0
    assert "BTC per Share:" in exposure["display"]
    assert "Unrealized P&L:" in exposure["display"]


def test_crypto_linkage_visible(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    linkage = ti.build_crypto_linkage(seed["companies"]["MSTR"])
    assert linkage["stock_btc_correlation_90d"] == 0.72
    assert linkage["beta_to_btc"] == 1.8
    assert linkage["btc_exposure_level"] == "High"
    assert "Stock-BTC Correlation (90D):" in linkage["display"]


def test_dashboard_structure(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    card = ti.build_company_dashboard(seed["companies"]["MSTR"], as_of=REF)
    assert "MicroStrategy Inc." in card["company_display"]
    assert card["ticker"] == "MSTR"
    assert "Treasury Value:" in card["dashboard_display"]
    assert "BTC per Share:" in card["dashboard_display"]
    assert "Last Filing:" in card["dashboard_display"]


def test_no_buy_language(isolated_seed):
    seed = json.loads(isolated_seed.read_text())
    card = ti.build_company_dashboard(seed["companies"]["MSTR"], as_of=REF)
    text = json.dumps(card)
    assert "Buy" not in card["context_display"]
    assert "buy this stock" not in text.lower()
    assert "BTC proxy" in card["context_display"]
    assert card["no_buy_language"] is True


def test_disclaimer_non_hideable(isolated_seed):
    card = ti.build_treasury_companies_card("BTC")
    assert card["disclaimer_hideable"] is False
    assert "Not investment advice" in card["disclaimer"]
    company = ti.get_treasury_company("MSTR")
    assert company is not None
    assert company["disclaimer_hideable"] is False


def test_macro_context_only(isolated_seed):
    card = ti.build_treasury_companies_card("BTC")
    assert card["macro_context_only"] is True
    assert card["no_yield_arbitrage"] is True
    assert card["standalone"] is False
    assert "Macro Intelligence Hub" in card["merged_into"]


def test_macro_hub_integration(isolated_seed):
    card = ti.build_treasury_companies_card("BTC")
    assert card["status"] == "live"
    assert card["feature_id"] == 239
    assert card["company_count"] == 2


def test_get_treasury_company(isolated_seed):
    result = ti.get_treasury_company("MSTR")
    assert result is not None
    assert result["ticker"] == "MSTR"
    assert ti.get_treasury_company("UNKNOWN") is None


def test_treasury_intelligence_status(isolated_seed):
    status = ti.treasury_intelligence_status()
    assert status["feature_id"] == 239
    assert status["standalone"] is False
    assert status["acceptance_criteria"]["no_stale_as_live"] is True
    assert status["acceptance_criteria"]["filing_source_timestamps"] is True


def test_classify_freshness():
    assert ti.classify_freshness(30) == "Live"
    assert ti.classify_freshness(45) == "Live"
    assert ti.classify_freshness(46) == "Stale"
    assert ti.classify_freshness(57) == "Stale"


def test_full_seed_coverage_minimum():
    seed = json.loads(ti._SEED_PATH.read_text(encoding="utf-8"))
    assert len(seed["companies"]) >= 20


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/market-radar/treasury-intelligence/status").status_code == 200
    status = c.get("/api/platform/market-radar/treasury-intelligence/status").json()
    assert status["feature_id"] == 239
    assert status["standalone"] is False
    hub = c.get("/api/platform/market-radar/macro-hub/treasury-companies?asset=BTC")
    assert hub.status_code == 200
    assert hub.json()["standalone"] is False
    company = c.get("/api/platform/market-radar/macro-hub/treasury-companies/MSTR")
    assert company.status_code == 200
    assert company.json()["ticker"] == "MSTR"
    assert c.get("/api/platform/market-radar/macro-hub/treasury-companies/FAKE").status_code == 404
