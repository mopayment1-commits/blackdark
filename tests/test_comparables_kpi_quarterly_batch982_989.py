"""Tests — Batch 35: #982 Comparables, #984 Exploits, #985+#986 KPIs, #989 Quarterly Reports."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import intelligence_ledger_project_comparables as comparables
from bd_platform import onchain_intelligence_extension as onchain
from bd_platform import protocol_kpi_intelligence as kpi
from bd_platform import research_intelligence_portal as portal


@pytest.fixture
def comparables_seed() -> dict:
    return json.loads(Path("data/intelligence_ledger_project_comparables_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def onchain_seed() -> dict:
    return json.loads(Path("data/onchain_intelligence_extension_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def kpi_seed() -> dict:
    return json.loads(Path("data/protocol_kpi_intelligence_seed.json").read_text(encoding="utf-8"))


@pytest.fixture
def portal_seed() -> dict:
    return json.loads(Path("data/research_intelligence_portal_seed.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_portal_state():
    portal.reset_research_portal_state()
    yield
    portal.reset_research_portal_state()


# --- #982 Project Comparables ---


def test_982_status(comparables_seed):
    status = comparables.project_comparables_status_982(seed=comparables_seed)
    assert status["standalone_rejected"] is True
    assert status["peer_membership_transparent"] is True
    assert len(status["standardized_metrics"]) >= 5


def test_982_peer_criteria_visible(comparables_seed):
    criteria = comparables.get_peer_selection_criteria_982("aave", seed=comparables_seed)
    assert criteria["criteria_visible"] is True
    assert criteria["taxonomy_ref"] == 927


def test_982_comparable_explorer(comparables_seed):
    explorer = comparables.build_comparable_explorer_982("aave", seed=comparables_seed)
    assert explorer["peer_count"] >= 2
    assert explorer["peer_membership_transparent"] is True
    assert explorer["ranking"]["documented"] is True


def test_982_na_not_estimated(comparables_seed):
    explorer = comparables.build_comparable_explorer_982("aave", seed=comparables_seed)
    morpho = next(p for p in explorer["peers"] if p["protocol_id"] == "morpho")
    assert morpho["metrics"]["growth"]["value"] == "N/A"


def test_982_e2e(comparables_seed):
    e2e = comparables.run_project_comparables_e2e_982(seed=comparables_seed)
    assert e2e["all_passed"] is True


# --- #984 Protocol Exploit Intelligence ---


def test_984_status(onchain_seed):
    status = onchain.security_incidents_status_984(seed=onchain_seed)
    assert status["no_rumors"] is True
    assert status["losses_at_event_time"] is True
    assert status["source_documented"] is True


def test_984_exploit_dashboard(onchain_seed):
    dash = onchain.build_exploit_dashboard_984(seed=onchain_seed)
    assert dash["incident_count"] >= 2
    assert all(i["source_documented"] for i in dash["incidents"])


def test_984_incident_details(onchain_seed):
    incident = onchain.get_incident_details_984("euler_finance_2023", seed=onchain_seed)
    assert incident["cause_classification"] == "reentrancy"
    assert incident["status_transitions_logged"] is True
    assert incident["no_retrospective_revaluation"] is True


def test_984_onchain_e2e_includes_984(onchain_seed):
    e2e = onchain.run_onchain_extension_e2e(seed=onchain_seed)
    assert e2e["all_passed"] is True
    assert 984 in e2e["feature_refs"]


# --- #985+#986 Protocol KPI Intelligence ---


def test_986_fundamentals_merged(kpi_seed):
    status = kpi.protocol_kpi_status_986(seed=kpi_seed)
    assert status["fundamentals_merged"] is True
    assert status["fundamentals_ref"] == 985
    assert "volume" in status["core_metrics"]
    assert "growth" in status["core_metrics"]


def test_986_protocol_type_schema(kpi_seed):
    schema = kpi.get_protocol_type_schema_986("lending", seed=kpi_seed)
    assert schema["ok"] is True
    assert len(schema["kpi_schema"]) >= 5


def test_986_source_parity(kpi_seed):
    parity = kpi.run_source_parity_test_986(seed=kpi_seed)
    assert parity["source_methodology_parity"] is True
    assert parity["ok"] is True


def test_986_historical_qa(kpi_seed):
    qa = kpi.run_historical_qa_986("aave", seed=kpi_seed)
    assert qa["no_silent_mutation"] is True
    assert qa["backfill_complete"] is True


def test_986_e2e_includes_985(kpi_seed):
    e2e = kpi.run_protocol_kpi_e2e(seed=kpi_seed)
    assert e2e["all_passed"] is True
    assert 985 in e2e["feature_refs"]


# --- #989 Quarterly Protocol Performance Reports ---


def test_989_quarterly_report(portal_seed):
    report = portal.generate_quarterly_report_989("aave", quarter="Q2-2026", seed=portal_seed)
    assert report["ok"] is True
    assert len(report["sections"]) == 5
    assert report["all_claims_reproducible"] is True
    assert report["immutable_snapshot"] is True
    assert report["verification_id"] is not None


def test_989_charts_reproducible(portal_seed):
    report = portal.generate_quarterly_report_989("aave", seed=portal_seed)
    kpi_section = report["sections"]["kpi_trends"]
    assert all(c.get("generated_from_metrics") for c in kpi_section["charts"])


def test_989_archive(portal_seed):
    archive = portal.list_quarterly_report_archive_989(seed=portal_seed)
    assert archive["count"] >= 2
    assert archive["immutable_snapshots"] is True


def test_989_e2e(portal_seed):
    e2e = portal.run_quarterly_report_e2e_989(seed=portal_seed)
    assert e2e["all_passed"] is True


def test_997_portal_e2e_includes_989(portal_seed):
    e2e = portal.run_research_portal_e2e(seed=portal_seed)
    assert e2e["all_passed"] is True
    assert 989 in e2e["feature_refs"]


# --- Regression batch 34 ---


def test_batch34_narrative_e2e_regression():
    from bd_platform.market_radar_narrative_sector import run_narrative_sector_e2e_974

    e2e = run_narrative_sector_e2e_974()
    assert e2e["all_passed"] is True
