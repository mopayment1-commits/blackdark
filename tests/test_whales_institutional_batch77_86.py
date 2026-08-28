"""Tests — Whales & Institutional (#77–#86)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import whales_institutional_layer as whales


@pytest.fixture
def seed() -> dict:
    return json.loads(Path("data/legal_retail_commercial_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset(seed):
    whales.reset_whales_institutional_state()
    yield
    whales.reset_whales_institutional_state()


def test_77_advanced_risk(seed):
    holdings = [
        {"symbol": "BTC", "value_usd": 80000, "btc_beta": 1.0},
        {"symbol": "ETH", "value_usd": 20000, "btc_beta": 0.8},
    ]
    report = whales.build_advanced_risk_report_77(holdings, seed=seed)
    assert report["report_type"] == "risk_insight_not_protection"
    assert len(report["exposure"]) == 2
    assert len(report["stress_scenarios"]) >= 1


def test_78_execution_rejected(seed):
    status = whales.execution_routing_status_78(seed=seed)
    assert status["rejected"] is True
    impact = whales.build_impact_analysis_78(order_usd=500_000, seed=seed)
    assert impact["no_routing"] is True


def test_79_surveillance(seed):
    result = whales.analyze_wallet_surveillance_79(
        wallet="0x1234567890abcdef", suspicious_query_count=4, seed=seed
    )
    assert result["surveillance_detected"] is True
    assert result["no_auto_protection"] is True


def test_80_exchange_health(seed):
    health = whales.build_exchange_health_80(exchange="binance", seed=seed)
    assert health["health_score"] > 0
    assert "indicators" in health


def test_81_unified_portfolio(seed):
    view = whales.build_unified_portfolio_view_81(seed=seed)
    assert view["non_custodial"] is True
    assert "advanced_risk_tab" in view


def test_82_liquidation_alert(seed):
    alert = whales.evaluate_liquidation_alert_82(
        price=62500, liquidation_level=62000, open_interest_usd=200_000_000, seed=seed
    )
    assert alert["no_auto_action"] is True
    assert "cascade_risk" in alert


def test_83_deferred(seed):
    status = whales.smb_institution_status_83(seed=seed)
    assert status["status"] == "deferred"
    assert status["wave"] == 3


def test_84_performance_ledger(seed):
    whales.record_performance_entry_84(
        asset="BTC", insight="test", risk_score=6, confidence=7, seed=seed
    )
    view = whales.build_performance_ledger_view_84(seed=seed)
    assert view["total_recorded"] >= 1
    assert view["due_diligence_ready"] is True


def test_85_openapi(seed):
    status = whales.openapi_documentation_status_85(seed=seed)
    assert status["spec_version"] == "3.0+"
    enriched = whales.enrich_openapi_with_fee_metadata_85({"info": {}, "paths": {"/test": {"get": {}}}})
    assert enriched["info"].get("x-blackdark-fee-transparency") is True


def test_86_methodology(seed):
    docs = whales.build_methodology_docs_86(seed=seed)
    assert docs["rule_based_only_sprint_2"] is True
    payload = whales.attach_methodology_to_insight_86({"ok": True})
    assert "methodology" in payload


def test_portfolio_attach(seed):
    out = whales.attach_portfolio_whale_layers_77_86(
        {"holdings": [{"symbol": "BTC", "value_usd": 1000, "btc_beta": 1}]},
        seed=seed,
    )
    assert "advanced_risk_tab" in out
    assert "methodology" in out


def test_whales_e2e(seed):
    assert whales.run_whales_institutional_e2e_77_86(seed=seed)["all_passed"] is True
