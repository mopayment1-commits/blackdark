"""Focused tests for B1-R capability provenance contract."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from capability_provenance.contract import (
    ARTIFACT_GENERATION_STAMP_CLASS,
    CONTRACT_PATH,
    LEGACY_AMBIGUOUS_CLASS,
    VERIFICATION_BOUND_CLASS,
    load_contract,
)
from capability_provenance.verify import classify_tested_source_sha, verify_capability_record, verify_ssot_artifact
from capability_provenance.writers import (
    ProvenanceWriteError,
    VerificationEvent,
    record_artifact_composition,
    record_live_applicability_correction,
    record_semantic_correction,
    record_verification_event,
)

ROOT = Path(__file__).resolve().parents[1]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"


def _good_event(**overrides):
    base = {
        "event_type": "ACTUAL_VERIFICATION",
        "source_sha": "a" * 40,
        "verification": {"verdict": "SEMANTIC_VERIFIED", "runtime_path_verified": True},
        "evidence_refs": ("tests/cap978/test_phase2_semantic_remediation.py",),
        "executed_at": "2026-09-15T12:00:00+00:00",
    }
    base.update(overrides)
    return VerificationEvent(**base)


def test_contract_file_loads():
    contract = load_contract()
    assert contract["artifact"] == "CAPABILITY_PROVENANCE_CONTRACT"
    assert contract["tested_source_sha"]["write_requires_actual_verification"] is True
    assert CONTRACT_PATH.is_file()


def test_artifact_composition_does_not_write_tested_source_sha():
    cap = {"capability_id": "CAP-TEST", "tested_source_sha": "b" * 40}
    ssot = {"git": {}, "canonical_capabilities": [cap]}
    record_artifact_composition(ssot, "c" * 40, "2026-09-15T12:00:00+00:00")
    assert cap["tested_source_sha"] == "b" * 40
    assert ssot["git"]["current_head_sha"] == "c" * 40


def test_artifact_generation_sha_rejected_for_actual_test_field():
    cap = {"capability_id": "CAP-TEST"}
    with pytest.raises(ProvenanceWriteError):
        record_verification_event(
            cap,
            _good_event(verification={"verdict": "UNKNOWN"}),
        )


def test_valid_verification_event_writes_actual_test_provenance():
    cap = {"capability_id": "CAP-TEST", "engineering_status": "PARTIAL"}
    event = _good_event()
    record_verification_event(
        cap,
        event,
        status_change_extra={"previous_status": "PARTIAL", "new_status": "PASS_ENGINEERING", "phase": "TEST"},
    )
    assert cap["tested_source_sha"] == event.source_sha
    assert cap["status_change"]["tested_sha"] == event.source_sha
    assert cap["status_change"]["verification"]["verdict"] == "SEMANTIC_VERIFIED"
    assert cap["status_change"]["provenance_contract_version"].startswith("B1-R")


def test_manual_restamp_path_rejected():
    with pytest.raises(ProvenanceWriteError):
        VerificationEvent(
            event_type="ACTUAL_VERIFICATION",
            source_sha="short",
            verification={"verdict": "SEMANTIC_VERIFIED"},
            evidence_refs=("x",),
        )


def test_semantic_correction_preserves_tested_source_sha():
    cap = {"capability_id": "CAP-TEST", "tested_source_sha": "d" * 40}
    record_semantic_correction(
        cap,
        head_sha="e" * 40,
        prior_artifact_sha="d" * 40,
        provenance="POST_RECONCILIATION_ARTIFACT_ONLY_HEAD_ADVANCE",
    )
    assert cap["tested_source_sha"] == "d" * 40
    assert cap["semantic_correction"]["head_sha"] == "e" * 40


def test_live_applicability_correction_preserves_tested_source_sha():
    cap = {"capability_id": "CAP-TEST", "tested_source_sha": "f" * 40}
    record_live_applicability_correction(
        cap,
        head_sha="g" * 40,
        previous_live_status="NOT_APPLICABLE_INTERNAL_ONLY",
        new_live_status="LIVE_VALIDATION_PENDING",
        reason="test",
    )
    assert cap["tested_source_sha"] == "f" * 40
    assert "composition_head_sha" in cap["status_change"]["live_applicability_correction"]


def test_legacy_values_not_auto_normalized():
    if not SSOT_PATH.is_file():
        pytest.skip("SSOT not present")
    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    sample = copy.deepcopy(ssot["canonical_capabilities"][0])
    original_sha = sample["tested_source_sha"]
    cls = classify_tested_source_sha(sample)
    assert cls in {LEGACY_AMBIGUOUS_CLASS, ARTIFACT_GENERATION_STAMP_CLASS, VERIFICATION_BOUND_CLASS}
    assert sample["tested_source_sha"] == original_sha


def test_verifier_does_not_use_pass_label_as_proof():
    cap = {
        "capability_id": "CAP-TEST",
        "engineering_status": "PASS_ENGINEERING",
        "tested_source_sha": "h" * 40,
        "status_change": {"tested_sha": "i" * 40, "verification": {"verdict": "SEMANTIC_VERIFIED"}},
    }
    violations = verify_capability_record(cap)
    assert any("INV-003" in v for v in violations)


def test_generator_verifier_schema_share_semantics():
    contract = load_contract()
    assert contract["tested_source_sha"]["canonical_meaning"] == "ACTUAL_VERIFICATION_PROVENANCE_ONLY"
    event = _good_event()
    cap = {"capability_id": "CAP-TEST"}
    record_verification_event(cap, event)
    violations = verify_capability_record(cap, strict_post_b1r=True)
    assert violations == []


def test_ssot_scan_allows_legacy_ambiguity_without_mutation():
    if not SSOT_PATH.is_file():
        pytest.skip("SSOT not present")
    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    before = {c["capability_id"]: c.get("tested_source_sha") for c in ssot["canonical_capabilities"]}
    result = verify_ssot_artifact(ssot)
    after = {c["capability_id"]: c.get("tested_source_sha") for c in ssot["canonical_capabilities"]}
    assert before == after
    assert result["legacy_classification_counts"]


def test_validated_through_not_used():
    contract = load_contract()
    assert contract["provenance_concepts"]["validated_through"]["field_paths"] == []
