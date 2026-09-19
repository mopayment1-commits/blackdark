"""SPEC_08 — Decision Truth adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.decision_truth_spec_common import (
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


def test_insufficient_evidence_abstains_fail_closed():
    from launch57.decision_truth_common import (
        DecisionState,
        verify_insufficient_evidence_fail_closed,
    )

    check = verify_insufficient_evidence_fail_closed()
    assert check["fail_closed"] is True
    assert check["no_silent_success"] is True
    assert check["abstain_or_wait"] is True


def test_stale_sim_not_labeled_live_on_decisions():
    from launch57.decision_truth_common import verify_sim_not_labeled_live_on_decision

    check = verify_sim_not_labeled_live_on_decision()
    assert check["sim_live_contamination_blocked"] is True
    assert check["stale_not_live_on_decision"] is True
    assert check["decision_truth_ok"] is True


def test_certificate_rejects_untrusted_decision_time():
    from launch57.decision_truth_common import verify_certificate_decision_time_gate

    gate = verify_certificate_decision_time_gate()
    assert gate["untrusted_decision_time_rejected"] is True
    assert gate["trusted_decision_time_accepted"] is True
    assert gate["gate_ok"] is True


def test_net_edge_refuses_stale_as_current():
    from launch57.decision_truth_common import verify_net_edge_stale_refusal

    check = verify_net_edge_stale_refusal()
    assert check["refuses_stale_as_current"] is True
    assert check["stale_cost_claim_blocked"] is True


def test_contradiction_blocks_act():
    from launch57.decision_truth_common import (
        DecisionState,
        build_decision_truth_gate,
        evaluate_decision_state,
    )

    gate = build_decision_truth_gate(
        freshness_state="LIVE",
        quality_state="insufficient",
        evidence_label="LIVE",
        conflicting=True,
    )
    result = evaluate_decision_state(gate=gate)
    assert result["decision_state"] == DecisionState.ABSTAIN.value
    assert result["act_allowed"] is False


def test_runtime_decision_paths_wired():
    from launch57.decision_truth_common import verify_runtime_decision_path_wiring

    wiring = verify_runtime_decision_path_wiring()
    assert wiring["runtime_enforcement_ok"] is True
    assert wiring["wired_paths"]["trust_batch1_oracle"] is True
    assert wiring["wired_paths"]["b4_decision_bridge"] is True


def test_file02_file03_decision_alignment():
    from launch57.decision_truth_common import verify_file01_file02_file03_decision_alignment

    alignment = verify_file01_file02_file03_decision_alignment()
    assert alignment["aligned"] is True
    assert alignment["file02_public_accuracy_anonymous"] is True
    assert alignment["file03_unverified_cannot_unlock_history"] is True


def test_file06_file07_alignment():
    from launch57.decision_truth_common import verify_file06_file07_alignment

    alignment = verify_file06_file07_alignment()
    assert alignment["aligned"] is True
    assert alignment["file06_sim_live_blocked"] is True
    assert alignment["file07_stale_not_live"] is True


def test_no_parked_decision_scope():
    from launch57.decision_truth_common import verify_launch57_decision_scope

    parked = verify_launch57_decision_scope(999)
    assert parked["parked_contamination"] is True
    assert parked["in_launch57_scope"] is False


def test_machine_readable_decision_truth_export():
    from launch57.decision_truth_common import build_machine_readable_decision_truth_export

    export = build_machine_readable_decision_truth_export()
    assert export["artifact"] == "LAUNCH57_DECISION_TRUTH_EXPORT"
    assert export["decision_truth_ok"] is True
    assert export["pass_live_not_claimed"] is True


def test_acceptance_criteria_all_pass():
    from launch57.decision_truth_common import acceptance_criteria_status

    ac = acceptance_criteria_status()
    required = (
        "ac07_abstain_reachable",
        "ac09_act_requires_valid_evidence",
        "certificate_decision_time_gate",
        "net_edge_stale_refused",
        "insufficient_evidence_fail_closed",
        "runtime_paths_wired",
        "file02_file03_aligned",
        "file06_file07_aligned",
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
    assert status["decision_truth_ok"] is True
    assert status["launch57_only_ok"] is True
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True


def test_spec08_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_08_DECISION_TRUTH")
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
