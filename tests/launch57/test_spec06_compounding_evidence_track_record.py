"""SPEC_06 — Compounding Evidence Track Record adversarial tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from launch57.compounding_evidence_track_record_spec_common import (
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


def test_outcome_resolution_gate_blocks_unresolved():
    from launch57.compounding_evidence_common import verify_outcome_resolution_gate

    resolved = verify_outcome_resolution_gate(
        {"label": "correct", "outcome_time": "2026-01-01T00:00:00Z", "resolved": True}
    )
    unresolved = verify_outcome_resolution_gate({"label": "correct"})
    assert resolved["accuracy_claim_allowed"] is True
    assert unresolved["fail_closed_without_resolution"] is True
    assert unresolved["accuracy_claim_allowed"] is False


def test_sim_cannot_contaminate_live_accuracy():
    from launch57.compounding_evidence_common import (
        attach_compounding_evidence_envelope,
        verify_live_sim_separation,
    )

    live = verify_live_sim_separation(evidence_label="LIVE", presented_as_live=True)
    sim = verify_live_sim_separation(
        evidence_label="SIM", presented_as_live=True, raw_evidence_class="SIMULATED"
    )
    assert live["live_sim_separated"] is True
    assert sim["sim_cannot_contaminate_live"] is False
    assert sim["fail_closed_on_contamination"] is True

    envelope = attach_compounding_evidence_envelope(
        {"launch_item_id": 4, "presented_as_live": True, "evidence_class": "SIMULATED"},
        launch_item_id=4,
    )
    sep = envelope["launch57_compounding_evidence"]["live_sim_separation"]
    assert sep["fail_closed_on_contamination"] is True


def test_unresolved_outcomes_do_not_inflate_accuracy():
    from launch57.compounding_evidence_common import verify_accuracy_claim_honesty

    honesty = verify_accuracy_claim_honesty(
        [
            {"prediction_id": 1, "label": "correct", "resolved": True, "outcome_time": "2026-01-01T00:00:00Z"},
            {"prediction_id": 2, "label": "correct"},
        ]
    )
    assert honesty["unresolved_accuracy_claims"] == 1
    assert honesty["honest_accuracy_reporting"] is False

    clean = verify_accuracy_claim_honesty(
        [
            {"prediction_id": 1, "label": "correct", "resolved": True, "outcome_time": "2026-01-01T00:00:00Z"},
        ]
    )
    assert clean["honest_accuracy_reporting"] is True


def test_track_record_append_only_integrity():
    from launch57.compounding_evidence_common import verify_track_record_integrity

    integrity = verify_track_record_integrity()
    assert integrity["append_only"] is True
    assert integrity["tamper_evident"] is True
    assert integrity.get("chain_valid") is not False


def test_file02_public_guest_trust_allowed():
    from launch57.anonymous_visitor_common import verify_anonymous_eligibility

    assert verify_anonymous_eligibility(4)["eligible"] is True
    assert verify_anonymous_eligibility(46)["eligible"] is True
    assert verify_anonymous_eligibility(49)["eligible"] is False


def test_file03_unverified_tier_cannot_unlock_history():
    from launch57.billing_entitlement_common import enforce_launch57_entitlement

    blocked = enforce_launch57_entitlement(
        launch_item_id=49,
        params={"tier": "pro", "user_key": "user-1", "subject_id": "user-1"},
    )
    assert blocked["allowed"] is False


def test_file02_file03_compounding_alignment():
    from launch57.compounding_evidence_common import verify_file02_file03_compounding_alignment

    alignment = verify_file02_file03_compounding_alignment()
    assert alignment["aligned"] is True
    assert alignment["file02_public_accuracy_anonymous"] is True
    assert alignment["file02_private_history_anonymous_denied"] is True
    assert alignment["file03_unverified_tier_cannot_unlock_history"] is True


def test_machine_readable_track_record_export():
    from launch57.compounding_evidence_common import build_machine_readable_track_record_export

    export = build_machine_readable_track_record_export()
    assert export["artifact"] == "LAUNCH57_COMPOUNDING_TRACK_RECORD_EXPORT"
    assert export["track_record_integrity"]
    assert export["evidence_lineage_index"]
    assert export["pass_live_not_claimed"] is True
    assert export["launch_scope"] == "LAUNCH57"


def test_no_parked_track_record_as_launch_primary():
    from launch57.compounding_evidence_common import verify_compounding_scope

    parked = verify_compounding_scope(999)
    assert parked["parked_contamination"] is True
    assert parked["in_launch57_scope"] is False


def test_non_selective_accuracy_metrics():
    from launch57.compounding_evidence_common import verify_non_selective_accuracy_metrics

    metrics = verify_non_selective_accuracy_metrics(
        {"metrics_scope": "live_only", "live_only_primary": True, "unresolved_excluded": True}
    )
    assert metrics["non_selective_ok"] is True
    assert metrics["unresolved_excluded_from_primary"] is True


def test_acceptance_criteria_all_pass():
    from launch57.compounding_evidence_common import acceptance_criteria_status

    ac = acceptance_criteria_status()
    required = (
        "ac05_public_accuracy_live_only",
        "ac06_live_delayed_sim_separated",
        "ac07_pit_integrity_holds",
        "ac22_no_false_pass_live",
        "unresolved_cannot_inflate_accuracy",
        "file02_file03_aligned",
        "append_only_integrity",
        "sim_cannot_contaminate_live",
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
    assert status["evidence_class_integrity_ok"] is True
    assert status["launch57_only_ok"] is True
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True


def test_spec06_artifact_paths_exist():
    gov = Path("governance/launch57/SPEC_06_COMPOUNDING_EVIDENCE_TRACK_RECORD")
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
