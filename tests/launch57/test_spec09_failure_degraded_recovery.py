"""SPEC_09 — Failure Degraded Recovery adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.failure_degraded_recovery_spec_common import (
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


def test_upstream_failure_not_fake_success():
    from launch57.failure_recovery_common import verify_upstream_failure_not_fake_success

    check = verify_upstream_failure_not_fake_success()
    assert check["upstream_honest"] is True
    assert check["success_remains_false"] is True
    assert check["canonical_error_present"] is True


def test_partial_data_labeled_degraded():
    from launch57.failure_recovery_common import verify_partial_data_labeled_degraded

    check = verify_partial_data_labeled_degraded()
    assert check["labeled_honestly"] is True
    assert check["partial_flagged"] is True


def test_recovery_path_stays_honest():
    from launch57.failure_recovery_common import verify_recovery_path_honest

    check = verify_recovery_path_honest()
    assert check["recovery_honest"] is True
    assert check["stale_cannot_appear_live"] is True


def test_entitlement_auth_failure_distinct_from_data():
    from launch57.failure_recovery_common import verify_entitlement_auth_failure_distinct

    check = verify_entitlement_auth_failure_distinct()
    assert check["distinct_failure_classes"] is True
    assert check["no_entitlement_from_uncertain"] is True


def test_file01_file07_file08_alignment():
    from launch57.failure_recovery_common import verify_file01_file07_file08_alignment

    alignment = verify_file01_file07_file08_alignment()
    assert alignment["aligned"] is True
    assert alignment["file01_stale_command_path_honest"] is True
    assert alignment["file08_insufficient_fail_closed"] is True


def test_runtime_failure_paths_wired():
    from launch57.failure_recovery_common import verify_runtime_failure_path_wiring

    wiring = verify_runtime_failure_path_wiring()
    assert wiring["runtime_enforcement_ok"] is True
    assert wiring["wired_paths"]["command_home_stale_gate"] is True
    assert wiring["wired_paths"]["decision_common_failure_envelope"] is True


def test_injected_failure_not_silent_success():
    from launch57.failure_recovery_common import attach_failure_recovery_envelope

    body = attach_failure_recovery_envelope(
        {
            "launch_item_id": 42,
            "success": False,
            "error": "injected_upstream_failure",
            "freshness_state": "UNKNOWN",
        },
        launch_item_id=42,
    )
    assert body["success"] is False
    assert body["launch57_failure_recovery"]["canonical_error"] is not None
    assert body["launch57_failure_recovery"]["false_success_blocked"] is True


def test_stale_gate_command_home_path_honest():
    from launch57.decision_common import stale_gate_body

    body = stale_gate_body(
        capability_id=1,
        launch_item_id=1,
        surface="six_heroes_command_home",
        symbol="BTC",
        spine={"freshness_state": "STALE", "data_spine": {}},
        entrypoint="six_heroes_command_home",
    )
    assert body["success"] is False
    assert body["presented_as_live"] is False
    assert "launch57_failure_recovery" in body


def test_no_parked_failure_scope():
    from launch57.failure_recovery_common import verify_launch57_failure_scope

    parked = verify_launch57_failure_scope(999)
    assert parked["parked_contamination"] is True
    assert parked["in_launch57_scope"] is False


def test_machine_readable_failure_recovery_export():
    from launch57.failure_recovery_common import build_machine_readable_failure_recovery_export

    export = build_machine_readable_failure_recovery_export()
    assert export["artifact"] == "LAUNCH57_FAILURE_DEGRADED_RECOVERY_EXPORT"
    assert export["degrade_honesty_ok"] is True
    assert export["pass_live_not_claimed"] is True


def test_acceptance_criteria_all_pass():
    from launch57.failure_recovery_common import acceptance_criteria_status

    ac = acceptance_criteria_status()
    required = (
        "ac03_stale_cannot_appear_live",
        "ac05_abstain_reachable",
        "upstream_not_fake_success",
        "partial_data_labeled",
        "runtime_paths_wired",
        "file01_file07_file08_aligned",
        "ac21_no_false_pass_live",
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
    assert status["degrade_honesty_ok"] is True
    assert status["launch57_only_ok"] is True
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True


def test_spec09_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_09_FAILURE_DEGRADED_RECOVERY")
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
