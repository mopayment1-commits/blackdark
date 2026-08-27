"""Tests — #665 Financial Statement, #666 Health Scoring, #667 DeFi Security Monitor."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import alert_engine as ae
from bd_platform import defi_opportunity_scanner as dos
from bd_platform import defi_risk_passport as drp
from bd_platform import on_chain_financials as ocf


@pytest.fixture
def fin_seed(tmp_path, monkeypatch):
    p = tmp_path / "on_chain_financials_seed.json"
    p.write_text(Path("data/on_chain_financials_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(ocf, "_SEED_PATH", p)
    return p


@pytest.fixture
def passport_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_risk_passport_seed.json"
    p.write_text(Path("data/defi_risk_passport_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(drp, "_SEED_PATH", p)
    return p


def test_665_statement_template(fin_seed):
    stmt = ocf.build_financial_statement_view("uniswap")
    assert stmt["ok"] is True
    assert stmt["definitions_plus_evidence_per_line"] is True
    assert len(stmt["sections"]) == 3
    income = stmt["sections"][0]
    assert income["section"] == "income_statement"
    assert len(income["lines"]) == 3


def test_665_evidence_per_line(fin_seed):
    stmt = ocf.build_financial_statement_view("uniswap")
    for section in stmt["sections"]:
        for line in section["lines"]:
            assert line.get("definition")
            assert line.get("evidence", {}).get("source_link")
            assert line.get("evidence", {}).get("contract_address")
            assert line.get("evidence", {}).get("block_number") is not None


def test_665_route(fin_seed):
    page = ocf.build_protocol_financials_page("uniswap")
    assert page["route"] == "/protocol/uniswap/financials"
    assert page["ui_sections"] == ["statement", "health_card", "peer_comparison", "historical_trend"]


def test_666_health_score_factors(fin_seed):
    health = ocf.build_financial_health_score("uniswap")
    assert health["ok"] is True
    assert 0 <= health["health_score"] <= 100
    assert health["health_grade"] in {"A", "B", "C", "D", "F"}
    assert len(health["factor_breakdown"]) == 4
    assert health["no_arbitrary_universal_threshold"] is True


def test_666_protocol_caveat(fin_seed):
    dex = ocf.build_financial_health_score("uniswap")
    lending = ocf.build_financial_health_score("aave")
    assert "DEX" in dex.get("protocol_specific_caveat", "")
    assert "Lending" in lending.get("protocol_specific_caveat", "")


def test_666_peer_relative(fin_seed):
    health = ocf.build_financial_health_score("aave")
    assert health.get("peer_relative_percentile") is not None
    assert health["factor_breakdown"]["peer_relative"]["definition"]


def test_666_thesis_dimension(fin_seed):
    dim = ocf.score_on_chain_financials_dimension("UNI")
    assert dim["thesis_dimension_number"] == 7
    assert dim.get("financial_statement_grade") is not None
    assert dim.get("no_arbitrary_universal_threshold") is True


def test_666_cancel_438(fin_seed):
    opps = ocf.cancel_opportunities_by_financial_health_438([{"asset": "MKR"}])
    assert opps[0].get("financial_health_666") is not None


def test_667_security_monitor(passport_seed):
    monitor = drp.build_defi_security_monitor_dashboard("risky_protocol")
    assert monitor["ok"] is True
    assert monitor["legal_name"] == "DeFi Security Monitor"
    assert monitor["no_flash_loan_branding"] is True
    assert monitor["active_threat"] is True


def test_667_known_patterns(passport_seed):
    monitor = drp.build_defi_security_monitor_dashboard("risky_protocol")
    assert len(monitor["known_patterns_monitored"]) >= 3
    assert len(monitor["detected_patterns"]) >= 1
    assert "immunefi" in monitor["monitoring_sources"]


def test_667_alerts_484(passport_seed):
    alerts = drp.build_defi_security_alerts_484()
    assert alerts["ok"] is True
    assert alerts["alert_count"] >= 1
    assert alerts["alerts"][0]["alert_type"] == "defi_security_monitor"


def test_667_portfolio_410(passport_seed):
    alert = drp.build_portfolio_security_alert_410()
    assert alert["threatened_exposure"] is True
    assert len(alert["alerts"]) >= 1


def test_667_contagion_652(passport_seed):
    trigger = drp.get_security_contagion_trigger_652("risky_protocol")
    assert trigger["contagion_trigger"] is True
    assert trigger["trigger_type"] == "security_incident"


def test_667_cancel_438(passport_seed):
    opps = drp.cancel_opportunities_by_security_monitor([{"protocol_id": "risky_protocol"}])
    assert opps[0]["security_cancelled_667"] is True


def test_667_alert_engine_panel(passport_seed):
    panel = ae.build_alert_engine_panel()
    sec = panel.get("defi_security_monitor_alerts_667")
    assert sec is not None
    assert sec.get("ok") is True


def test_641_665_666_reconciliation(fin_seed):
    result = ocf.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"] if c["passed"]}
    assert "665_statement" in ids
    assert "666_health_score" in ids


def test_660_667_reconciliation(passport_seed):
    result = drp.run_reconciliation_tests()
    ids = {c["id"] for c in result["checks"] if c["passed"]}
    assert "security_monitor_667" in ids
    assert "security_cancel_438" in ids
