"""Runtime tests for EXTERNAL_OR_LIVE_GATE acceptance boundary atomics."""

from __future__ import annotations

from blackdark.temporal.external_assurance_gates import (
    DOCUMENT_APPROVAL_INSUFFICIENT_FOR_ASSURANCE,
    AssuranceClaimLevel,
    EvidenceBasis,
    evaluate_assurance_claim,
    evaluate_document_approval_prohibition,
    evaluate_evidence_gate_requirement,
    probe_external_gate_atomic_status,
)
from blackdark.temporal.external_gate_requirement_registry import (
    EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS,
    EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS,
    EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS,
    EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
)


def test_registry_covers_all_ten_atomics() -> None:
    assert EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 10
    assert len(EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS) == 10
    assert len(EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS) == 5
    assert len(EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS) == 5


def test_document_approval_insufficient_constant() -> None:
    assert DOCUMENT_APPROVAL_INSUFFICIENT_FOR_ASSURANCE is True


def test_temp_ar_0431_document_approval_not_pass_engineering() -> None:
    result = evaluate_document_approval_prohibition("TEMP-AR-0431")
    assert result["assurance_level"] == AssuranceClaimLevel.PASS_ENGINEERING.value
    assert result["document_approval_rejected"] is True
    assert result["external_runtime_gate_pending"] is True


def test_temp_ar_0460_document_approval_not_pass_live() -> None:
    result = evaluate_document_approval_prohibition("TEMP-AR-0460")
    assert result["assurance_level"] == AssuranceClaimLevel.PASS_LIVE.value
    assert result["document_approval_rejected"] is True


def test_temp_ar_0461_document_approval_not_assurance_ready() -> None:
    result = evaluate_document_approval_prohibition("TEMP-AR-0461")
    assert result["assurance_level"] == AssuranceClaimLevel.ASSURANCE_READY.value
    assert result["document_approval_rejected"] is True


def test_temp_ar_0462_document_approval_not_production_aligned() -> None:
    result = evaluate_document_approval_prohibition("TEMP-AR-0462")
    assert result["assurance_level"] == AssuranceClaimLevel.PRODUCTION_ALIGNED.value
    assert result["document_approval_rejected"] is True


def test_temp_ar_0463_document_approval_not_independent_verification() -> None:
    result = evaluate_document_approval_prohibition("TEMP-AR-0463")
    assert result["assurance_level"] == AssuranceClaimLevel.INDEPENDENT_VERIFICATION.value
    assert result["document_approval_rejected"] is True


def test_temp_ar_0432_pass_engineering_requires_own_evidence() -> None:
    doc_only = evaluate_assurance_claim(
        atomic_requirement_id="TEMP-AR-0432",
        evidence_bases=(EvidenceBasis.DOCUMENT_APPROVAL,),
    )
    with_evidence = evaluate_assurance_claim(
        atomic_requirement_id="TEMP-AR-0432",
        evidence_bases=(
            EvidenceBasis.PHASE_CLOSURE_EVIDENCE,
            EvidenceBasis.RUNTIME_ENGINEERING_PROBE,
        ),
    )
    assert doc_only.claim_granted is False
    assert with_evidence.claim_granted is True
    assert with_evidence.external_assurance_verified is False


def test_temp_ar_0433_pass_live_requires_external_evidence() -> None:
    result = evaluate_evidence_gate_requirement("TEMP-AR-0433")
    assert result["document_approval_rejected"] is True
    assert result["external_runtime_gate_pending"] is True
    live = evaluate_assurance_claim(
        atomic_requirement_id="TEMP-AR-0433",
        evidence_bases=(EvidenceBasis.LIVE_PRODUCTION_OBSERVATION,),
        live_production_observation_present=True,
    )
    assert live.claim_granted is True
    assert live.external_assurance_verified is True


def test_temp_ar_0434_assurance_ready_requires_independent_audit() -> None:
    result = evaluate_evidence_gate_requirement("TEMP-AR-0434")
    assert result["document_approval_rejected"] is True
    assert result["external_runtime_gate_pending"] is True
    ready = evaluate_assurance_claim(
        atomic_requirement_id="TEMP-AR-0434",
        evidence_bases=(EvidenceBasis.INDEPENDENT_AUDIT,),
        independent_audit_present=True,
    )
    assert ready.claim_granted is True
    assert ready.external_assurance_verified is True


def test_temp_ar_0435_production_aligned_requires_external_evidence() -> None:
    result = evaluate_evidence_gate_requirement("TEMP-AR-0435")
    assert result["document_approval_rejected"] is True
    assert result["external_runtime_gate_pending"] is True
    aligned = evaluate_assurance_claim(
        atomic_requirement_id="TEMP-AR-0435",
        evidence_bases=(
            EvidenceBasis.LIVE_PRODUCTION_OBSERVATION,
            EvidenceBasis.INDEPENDENT_AUDIT,
        ),
        live_production_observation_present=True,
        independent_audit_present=True,
    )
    assert aligned.claim_granted is True


def test_temp_ar_0436_independent_verification_requires_audit() -> None:
    result = evaluate_evidence_gate_requirement("TEMP-AR-0436")
    assert result["document_approval_rejected"] is True
    assert result["external_runtime_gate_pending"] is True
    verified = evaluate_assurance_claim(
        atomic_requirement_id="TEMP-AR-0436",
        evidence_bases=(EvidenceBasis.INDEPENDENT_AUDIT,),
        independent_audit_present=True,
    )
    assert verified.claim_granted is True


def test_simulated_time_cannot_close_pass_live() -> None:
    claim = evaluate_assurance_claim(
        atomic_requirement_id="TEMP-AR-0433",
        evidence_bases=(EvidenceBasis.LIVE_PRODUCTION_OBSERVATION,),
        uses_simulated_time=True,
        live_production_observation_present=True,
    )
    assert claim.claim_granted is False


def test_all_atomics_have_probe_status() -> None:
    for aid in EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS:
        status = probe_external_gate_atomic_status(aid)
        assert status["atomic_id"] == aid
        assert status["local_engineering_complete"] is True
