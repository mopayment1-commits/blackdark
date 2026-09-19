"""SPEC_07 — Data Intelligence Governance adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.data_intelligence_governance_spec_common import (
    DOMAIN,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    independent_verification,
)


def test_requirements_register_nonempty():
    reqs = build_requirements_register()
    assert len(reqs) >= 20
    assert all(r["mandatory"] for r in reqs)


def test_runtime_truth_all_yes():
    truth = build_runtime_truth_table()
    nos = [r for r in truth if r["status"] != "YES"]
    assert not nos, nos


def test_material_write_without_governance_fails():
    from launch57.data_governance_common import enforce_material_write

    blocked = enforce_material_write({"source": "binance"})
    assert blocked["allowed"] is False
    assert blocked["fail_closed"] is True
    assert blocked["blocked_reason"] == "missing_observation_contract"


def test_material_write_with_contract_passes():
    from launch57.data_governance_common import enforce_material_write
    from launch57.temporal_common import to_rfc3339, utc_now

    now = to_rfc3339(utc_now())
    allowed = enforce_material_write(
        {
            "source": "binance",
            "event_time": now,
            "observed_at": now,
            "freshness_state": "LIVE",
            "quality_state": "decision_grade",
        }
    )
    assert allowed["allowed"] is True


def test_stale_not_presented_as_live():
    from launch57.data_governance_common import verify_stale_not_presented_as_live

    stale = verify_stale_not_presented_as_live(freshness_state="STALE", presented_as_live=True)
    assert stale["stale_not_presented_as_live"] is False
    live = verify_stale_not_presented_as_live(freshness_state="LIVE", presented_as_live=True)
    assert live["stale_not_presented_as_live"] is True


def test_sim_not_promoted_to_production():
    from launch57.data_governance_common import verify_sim_not_promoted_to_production

    sim = verify_sim_not_promoted_to_production(
        evidence_label="SIM", presented_as_live=True, raw_evidence_class="SIMULATED"
    )
    assert sim["promotion_to_production_allowed"] is False
    live = verify_sim_not_promoted_to_production(evidence_label="LIVE", presented_as_live=True)
    assert live["promotion_to_production_allowed"] is True


def test_lineage_provenance_fields_present():
    from launch57.data_governance_common import verify_lineage_provenance_present
    from launch57.temporal_common import to_rfc3339, utc_now

    now = to_rfc3339(utc_now())
    ok = verify_lineage_provenance_present(
        {
            "source": "binance",
            "event_time": now,
            "observed_at": now,
            "freshness_state": "LIVE",
            "quality_state": "decision_grade",
            "provenance_reference": "launch57.provenance_common",
        }
    )
    assert ok["material_fields_ok"] is True
    assert ok["lineage_present"] is True


def test_runtime_paths_wired_not_audit_only():
    from launch57.data_governance_common import verify_runtime_path_wiring

    wiring = verify_runtime_path_wiring()
    assert wiring["runtime_enforcement_ok"] is True
    assert wiring["wired_paths"]["data_batch1_material_observation"] is True
    assert wiring["wired_paths"]["data_batch2_freshness"] is True
    assert wiring["wired_paths"]["decision_common_freshness_spine"] is True


def test_file06_evidence_honesty_alignment():
    from launch57.data_governance_common import verify_file06_evidence_honesty_alignment

    alignment = verify_file06_evidence_honesty_alignment()
    assert alignment["aligned"] is True


def test_no_parked_data_scope():
    from launch57.data_governance_common import verify_launch57_data_scope

    parked = verify_launch57_data_scope(999)
    assert parked["parked_contamination"] is True
    assert parked["in_launch57_scope"] is False


def test_attach_material_observation_sets_write_gate():
    from launch57.data_governance_common import attach_material_observation

    body = attach_material_observation(
        {"symbol": "BTC", "surface": "real_time_prices"},
        source="binance",
        data_type="real_time_price",
        freshness_state="LIVE",
        quality_state="decision_grade",
        raw_value=1.0,
        normalized_value=1.0,
    )
    assert body["material_write_allowed"] is True
    assert body["material_observation_contract"]["material_write_gate"]["allowed"] is True


def test_machine_readable_governance_export():
    from launch57.data_governance_common import build_machine_readable_governance_export

    export = build_machine_readable_governance_export()
    assert export["artifact"] == "LAUNCH57_DATA_INTELLIGENCE_GOVERNANCE_EXPORT"
    assert export["runtime_enforcement_ok"] is True
    assert export["pass_live_not_claimed"] is True
    assert len(export["source_registry"]) >= 6


def test_acceptance_criteria_all_pass():
    from launch57.data_governance_common import acceptance_criteria_status

    ac = acceptance_criteria_status()
    required = (
        "ac05_material_write_gate",
        "ac07_cross_source_no_silent_average",
        "ac08_stale_not_live",
        "ac09_sim_not_production",
        "ac11_runtime_paths_wired",
        "ac12_file06_aligned",
        "ac22_no_false_pass_live",
    )
    missing = [k for k in required if not ac.get(k)]
    assert not missing, missing


def test_independent_verification_passes():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True
    assert iv["PASS_LIVE_NOT_CLAIMED"] is True


def test_final_status_closed_local():
    status = build_final_status(skip_tests=True)
    assert status["closure_status"] == "CLOSED_LOCAL"
    assert status["PASS_ENGINEERING"] is True
    assert status["LOCAL_ENGINEERING_GAP_COUNT"] == 0
    assert status["runtime_enforcement_ok"] is True
    assert status["launch57_only_ok"] is True
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True


def test_spec07_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_07_DATA_INTELLIGENCE_GOVERNANCE")
    for name in (
        "REQUIREMENTS_REGISTER.json",
        "RUNTIME_TRUTH_TABLE.md",
        "LOCAL_CLOSURE_REPORT.md",
        "INDEPENDENT_VERIFICATION.json",
        "FINAL_STATUS.json",
    ):
        path = gov / name
        assert path.exists(), f"missing {path}"
        if name.endswith(".json") and name == "FINAL_STATUS.json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload.get("domain") == DOMAIN
