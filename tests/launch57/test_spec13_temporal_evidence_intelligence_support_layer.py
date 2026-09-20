"""SPEC_13 — Temporal Evidence Intelligence Support Layer adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

from launch57.temporal_evidence_intelligence_support_layer_spec_common import (
    DOMAIN,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    build_specs_13_local_closure_ledger,
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


def test_no_conflict_with_file06_08_11():
    from launch57.teis_support_common import verify_no_conflict_with_file06_08_11

    check = verify_no_conflict_with_file06_08_11()
    assert check["no_conflict_with_06_08_11"] is True
    assert check["file06_sim_contamination_fail_closed"] is True
    assert check["file08_aligned"] is True
    assert check["file11_temporal_aligned"] is True


def test_sim_stale_labeling_consistent():
    from launch57.teis_support_common import verify_sim_stale_labeling_consistent

    check = verify_sim_stale_labeling_consistent()
    assert check["consistent"] is True
    assert check["replay_is_sim"] is True
    assert check["stale_prod_is_delayed"] is True


def test_available_at_not_fabricated():
    from launch57.teis_support_common import verify_available_at_not_fabricated_teis

    check = verify_available_at_not_fabricated_teis()
    assert check["ok"] is True
    assert check["missing_available_at_fail_closed"] is True


def test_support_layer_on_intelligence_paths():
    from launch57.teis_support_common import verify_support_layer_on_intelligence_paths

    paths = verify_support_layer_on_intelligence_paths()
    assert paths["ok"] is True
    assert paths["b4_has_teis_envelope"] is True


def test_runtime_teis_paths_wired():
    from launch57.teis_support_common import verify_runtime_teis_path_wiring

    wiring = verify_runtime_teis_path_wiring()
    assert wiring["runtime_enforcement_ok"] is True
    assert wiring["wired_paths"]["b4_teis_envelope"] is True
    assert wiring["wired_paths"]["decision_common_teis"] is True
    assert wiring["wired_paths"]["b5_teis_envelope"] is True


def test_machine_readable_teis_export():
    from launch57.teis_support_common import build_machine_readable_teis_export

    export = build_machine_readable_teis_export()
    assert export["artifact"] == "LAUNCH57_TEMPORAL_EVIDENCE_INTELLIGENCE_SUPPORT_EXPORT"
    assert export["support_layer_ok"] is True
    assert export["pass_live_not_claimed"] is True


def test_acceptance_criteria_all_pass():
    from launch57.teis_support_common import acceptance_criteria_status

    ac = acceptance_criteria_status()
    required = (
        "evidence_mapping_deterministic",
        "replay_shadow_cannot_become_live",
        "runtime_paths_wired",
        "no_conflict_with_06_08_11",
        "sim_stale_labeling_consistent",
        "support_layer_on_intelligence_paths",
        "available_at_not_fabricated",
        "support_layer_ok",
        "ac30_no_false_pass_live",
    )
    missing = [k for k in required if not ac.get(k)]
    assert not missing, missing


def test_decision_common_attaches_teis():
    from launch57.decision_common import attach_decision_envelope

    out = attach_decision_envelope({"launch_item_id": 7, "success": True})
    assert "teis_support" in out
    assert out["teis_support"]["internal_support_only"] is True


def test_independent_verification_passes():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True
    assert iv["PASS_LIVE_NOT_CLAIMED"] is True


def test_final_status_closed_local():
    status = build_final_status(skip_tests=True)
    assert status["closure_status"] == "CLOSED_LOCAL"
    assert status["PASS_ENGINEERING"] is True
    assert status["LOCAL_ENGINEERING_GAP_COUNT"] == 0
    assert status["support_layer_ok"] is True
    assert status["no_conflict_with_06_08_11"] is True
    assert status["launch57_only_ok"] is True
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True


def test_specs_13_ledger_all_closed_local():
    status = build_final_status(skip_tests=True)
    ledger = build_specs_13_local_closure_ledger(file13_status=status)
    assert ledger["file_count"] >= 13
    assert ledger["all_files_closed_local"] is True
    assert ledger["PASS_LIVE_CLAIMED"] is False
    assert ledger["LIVE_VALIDATION_PENDING"] is True
    for entry in ledger["files"]:
        assert entry["closure_status"] == "CLOSED_LOCAL"
        assert entry["PASS_LIVE"] is False
        assert entry["LIVE_VALIDATION_PENDING"] is True


def test_spec13_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_13_TEMPORAL_EVIDENCE_INTELLIGENCE_SUPPORT_LAYER")
    for name in (
        "REQUIREMENTS_REGISTER.json",
        "RUNTIME_TRUTH_TABLE.md",
        "LOCAL_CLOSURE_REPORT.md",
        "INDEPENDENT_VERIFICATION.json",
        "FINAL_STATUS.json",
    ):
        path = gov / name
        assert path.exists(), f"missing {path}"
        if name == "FINAL_STATUS.json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload.get("domain") == DOMAIN

    ledger = Path("governance/launch57/SPECS_13_LOCAL_CLOSURE_LEDGER.json")
    assert ledger.exists()
    ledger_payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert ledger_payload.get("all_files_closed_local") is True
