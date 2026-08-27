"""Tests — #660 DeFi Risk Passport, #659 Protocol Activity, #661 Radar, #672 Lending Risk."""

from __future__ import annotations

from pathlib import Path

import pytest

from bd_platform import alert_engine as ae
from bd_platform import defi_opportunity_scanner as dos
from bd_platform import defi_risk_passport as drp


@pytest.fixture
def passport_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_risk_passport_seed.json"
    p.write_text(Path("data/defi_risk_passport_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(drp, "_SEED_PATH", p)
    return p


@pytest.fixture
def defi_seed(tmp_path, monkeypatch):
    p = tmp_path / "defi_opportunity_scanner_seed.json"
    p.write_text(Path("data/defi_opportunity_scanner_seed.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(dos, "_SEED_PATH", p)
    return p


def test_660_passport_ok(passport_seed):
    passport = drp.score_protocol_risk_passport("aave_v3")
    assert passport["ok"] is True
    assert passport["no_hidden_score"] is True
    assert passport["risk_grade"] in {"A+", "A", "B", "C", "D", "F"}


def test_660_breakdown_transparent(passport_seed):
    passport = drp.score_protocol_risk_passport("aave_v3")
    bd = passport["breakdown"]
    assert bd["tvl_concentration_pct"] is not None
    assert bd["oracle_health"]["type"] == "multi_source"
    assert bd["bridge_dependency"]["has_bridge_dependency"] is False
    assert bd["liquidity_depth"]["exit_slippage_bps_1m_usd"] is not None


def test_660_exploit_source_links(passport_seed):
    risky = drp.score_protocol_risk_passport("risky_protocol")
    incidents = risky["breakdown"]["exploit_history"]["incidents"]
    assert len(incidents) >= 2
    assert all(i.get("source_link") for i in incidents)
    assert risky["risk_grade"] == "F"


def test_660_passport_card(passport_seed):
    card = drp.build_risk_passport_card("aave_v3")
    assert card["card_type"] == "passport"
    assert card["route"] == "/protocol/aave_v3/risk"
    assert len(card["historical_trend"]) >= 2


def test_661_risk_radar(passport_seed):
    radar = drp.build_defi_risk_radar()
    assert radar["ok"] is True
    assert radar["route"] == "/defi-risk"
    assert radar["count"] >= 3
    assert (radar.get("alerts_484") or {}).get("ok") is True


def test_672_lending_risk_metrics(passport_seed):
    lending = drp.build_lending_risk_dashboard("aave_v3")
    assert lending["ok"] is True
    m = lending["mandatory_metrics"]
    assert len(m) == 5
    assert lending["protocol_semantics"] == "aave_v3_liquidation"
    assert lending["protocol_version"] == "v3"


def test_672_utilization_alert_410(passport_seed):
    lending = drp.build_lending_risk_dashboard("high_util_lending")
    assert lending["utilization_alert_410"] is True


def test_410_portfolio_alert(passport_seed):
    alert = drp.build_portfolio_passport_alert_410()
    assert alert["ok"] is True
    assert alert["unhealthy_exposure"] is True
    assert len(alert["alerts"]) >= 1


def test_438_cancel_below_c(passport_seed):
    opps = drp.cancel_opportunities_by_passport_grade([{"protocol_id": "risky_protocol"}])
    assert opps[0]["passport_cancelled_660"] is True
    assert opps[0]["risk_passport_660"]["grade"] == "F"


def test_652_lending_contagion_trigger(passport_seed):
    trigger = drp.get_lending_contagion_trigger_652("high_util_lending")
    assert trigger["contagion_trigger"] is True


def test_659_activity_dashboard(defi_seed):
    activity = dos.build_protocol_activity_dashboard("aave_v3_ethereum")
    assert activity["ok"] is True
    entry = activity["dashboards"][0]
    assert entry["contract_version_mapping"]["version"] == "v3"
    assert entry["liquidation_semantics_validated"] is True
    assert "Aave v3 Ethereum" in entry["protocol_coverage_display"]


def test_659_liquidation_spike_contagion(defi_seed):
    trigger = dos.get_liquidation_contagion_trigger_652("compound_iii_ethereum")
    assert trigger["ok"] is True
    assert trigger["contagion_trigger"] is True


def test_659_defi_panel_integration(defi_seed, passport_seed):
    panel = dos.build_defi_panel()
    assert panel.get("protocol_activity_659", {}).get("ok") is True
    assert panel.get("defi_risk_passport_660", {}).get("ok") is True


def test_484_defi_risk_spike_alerts(passport_seed):
    panel = ae.build_alert_engine_panel()
    alerts = panel.get("defi_risk_spike_alerts_660") or {}
    assert alerts.get("ok") is True
    assert alerts.get("alert_count", 0) >= 1


def test_660_reconciliation(passport_seed):
    result = drp.run_reconciliation_tests()
    assert result["ok"] is True


def test_659_reconciliation(defi_seed):
    result = dos.run_reconciliation_tests()
    assert result["ok"] is True
    ids = {c["id"] for c in result["checks"] if c["passed"]}
    assert "protocol_activity_659" in ids
