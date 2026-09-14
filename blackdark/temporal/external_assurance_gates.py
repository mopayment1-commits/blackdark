"""Acceptance boundary / external assurance gates (TEMP-AR-0431..0436, 0460..0463)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from blackdark.temporal.external_gate_requirement_registry import (
    EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS,
    EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS,
)

EXTERNAL_ASSURANCE_GATE_CONTRACT_VERSION = "external_assurance_gate.1.0"
DOCUMENT_APPROVAL_INSUFFICIENT_FOR_ASSURANCE = True


class AssuranceClaimLevel(str, Enum):
    PASS_ENGINEERING = "PASS_ENGINEERING"
    PASS_LIVE = "PASS_LIVE"
    ASSURANCE_READY = "ASSURANCE_READY"
    PRODUCTION_ALIGNED = "PRODUCTION_ALIGNED"
    INDEPENDENT_VERIFICATION = "INDEPENDENT_VERIFICATION"


class EvidenceBasis(str, Enum):
    DOCUMENT_APPROVAL = "DOCUMENT_APPROVAL"
    PHASE_CLOSURE_EVIDENCE = "PHASE_CLOSURE_EVIDENCE"
    RUNTIME_ENGINEERING_PROBE = "RUNTIME_ENGINEERING_PROBE"
    LIVE_PRODUCTION_OBSERVATION = "LIVE_PRODUCTION_OBSERVATION"
    INDEPENDENT_AUDIT = "INDEPENDENT_AUDIT"


ATOMIC_TO_ASSURANCE_LEVEL: dict[str, AssuranceClaimLevel] = {
    "TEMP-AR-0431": AssuranceClaimLevel.PASS_ENGINEERING,
    "TEMP-AR-0432": AssuranceClaimLevel.PASS_ENGINEERING,
    "TEMP-AR-0433": AssuranceClaimLevel.PASS_LIVE,
    "TEMP-AR-0434": AssuranceClaimLevel.ASSURANCE_READY,
    "TEMP-AR-0435": AssuranceClaimLevel.PRODUCTION_ALIGNED,
    "TEMP-AR-0436": AssuranceClaimLevel.INDEPENDENT_VERIFICATION,
    "TEMP-AR-0460": AssuranceClaimLevel.PASS_LIVE,
    "TEMP-AR-0461": AssuranceClaimLevel.ASSURANCE_READY,
    "TEMP-AR-0462": AssuranceClaimLevel.PRODUCTION_ALIGNED,
    "TEMP-AR-0463": AssuranceClaimLevel.INDEPENDENT_VERIFICATION,
}

_REQUIRED_EVIDENCE_BY_LEVEL: dict[AssuranceClaimLevel, frozenset[EvidenceBasis]] = {
    AssuranceClaimLevel.PASS_ENGINEERING: frozenset(
        {EvidenceBasis.PHASE_CLOSURE_EVIDENCE, EvidenceBasis.RUNTIME_ENGINEERING_PROBE}
    ),
    AssuranceClaimLevel.PASS_LIVE: frozenset({EvidenceBasis.LIVE_PRODUCTION_OBSERVATION}),
    AssuranceClaimLevel.ASSURANCE_READY: frozenset({EvidenceBasis.INDEPENDENT_AUDIT}),
    AssuranceClaimLevel.PRODUCTION_ALIGNED: frozenset(
        {EvidenceBasis.LIVE_PRODUCTION_OBSERVATION, EvidenceBasis.INDEPENDENT_AUDIT}
    ),
    AssuranceClaimLevel.INDEPENDENT_VERIFICATION: frozenset({EvidenceBasis.INDEPENDENT_AUDIT}),
}


@dataclass(frozen=True, slots=True)
class AssuranceClaimEvaluation:
    atomic_requirement_id: str
    assurance_level: AssuranceClaimLevel
    claim_granted: bool
    document_approval_only: bool
    local_engineering_complete: bool
    external_assurance_verified: bool
    external_runtime_gate_pending: bool
    evidence_bases: tuple[str, ...]
    rejection_reason: str | None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "atomic_requirement_id": self.atomic_requirement_id,
            "assurance_level": self.assurance_level.value,
            "claim_granted": self.claim_granted,
            "document_approval_only": self.document_approval_only,
            "local_engineering_complete": self.local_engineering_complete,
            "external_assurance_verified": self.external_assurance_verified,
            "external_runtime_gate_pending": self.external_runtime_gate_pending,
            "evidence_bases": list(self.evidence_bases),
            "rejection_reason": self.rejection_reason,
        }


def _normalize_evidence_bases(evidence_bases: Sequence[str | EvidenceBasis]) -> frozenset[EvidenceBasis]:
    normalized: set[EvidenceBasis] = set()
    for basis in evidence_bases:
        if isinstance(basis, EvidenceBasis):
            normalized.add(basis)
        else:
            normalized.add(EvidenceBasis(str(basis)))
    return frozenset(normalized)


def evaluate_assurance_claim(
    *,
    atomic_requirement_id: str,
    evidence_bases: Sequence[str | EvidenceBasis],
    uses_simulated_time: bool = False,
    independent_audit_present: bool = False,
    live_production_observation_present: bool = False,
) -> AssuranceClaimEvaluation:
    """Evaluate an assurance claim against acceptance-boundary gates."""
    if atomic_requirement_id not in ATOMIC_TO_ASSURANCE_LEVEL:
        raise ValueError(f"Unknown external gate atomic: {atomic_requirement_id}")

    level = ATOMIC_TO_ASSURANCE_LEVEL[atomic_requirement_id]
    bases = _normalize_evidence_bases(evidence_bases)
    document_only = bases == frozenset({EvidenceBasis.DOCUMENT_APPROVAL})
    required = _REQUIRED_EVIDENCE_BY_LEVEL[level]

    # Simulated or replay-derived evidence cannot satisfy live/external gates.
    if uses_simulated_time and level in {
        AssuranceClaimLevel.PASS_LIVE,
        AssuranceClaimLevel.PRODUCTION_ALIGNED,
    }:
        live_production_observation_present = False

    if not independent_audit_present and EvidenceBasis.INDEPENDENT_AUDIT in bases:
        bases = bases - {EvidenceBasis.INDEPENDENT_AUDIT}
    if not live_production_observation_present and EvidenceBasis.LIVE_PRODUCTION_OBSERVATION in bases:
        bases = bases - {EvidenceBasis.LIVE_PRODUCTION_OBSERVATION}

    local_complete = DOCUMENT_APPROVAL_INSUFFICIENT_FOR_ASSURANCE and bool(required)
    rejection_reason: str | None = None
    claim_granted = False
    external_verified = False

    if document_only:
        rejection_reason = "document_approval_insufficient_for_assurance_claim"
    elif bases >= required:
        if level == AssuranceClaimLevel.PASS_ENGINEERING:
            claim_granted = True
            external_verified = False
        elif level == AssuranceClaimLevel.PASS_LIVE:
            claim_granted = live_production_observation_present and not uses_simulated_time
            external_verified = claim_granted
            if not claim_granted:
                rejection_reason = "live_production_observation_required"
        elif level == AssuranceClaimLevel.ASSURANCE_READY:
            claim_granted = independent_audit_present
            external_verified = claim_granted
            if not claim_granted:
                rejection_reason = "independent_audit_required"
        elif level == AssuranceClaimLevel.PRODUCTION_ALIGNED:
            claim_granted = live_production_observation_present and independent_audit_present
            external_verified = claim_granted
            if not claim_granted:
                rejection_reason = "production_alignment_external_evidence_required"
        elif level == AssuranceClaimLevel.INDEPENDENT_VERIFICATION:
            claim_granted = independent_audit_present
            external_verified = claim_granted
            if not claim_granted:
                rejection_reason = "independent_verification_required"
    else:
        rejection_reason = "insufficient_implementation_evidence_for_assurance_level"

    external_pending = (
        atomic_requirement_id in EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS
        or atomic_requirement_id in EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS
    ) and not external_verified

    return AssuranceClaimEvaluation(
        atomic_requirement_id=atomic_requirement_id,
        assurance_level=level,
        claim_granted=claim_granted,
        document_approval_only=document_only,
        local_engineering_complete=local_complete,
        external_assurance_verified=external_verified,
        external_runtime_gate_pending=external_pending,
        evidence_bases=tuple(sorted(b.value for b in bases)),
        rejection_reason=rejection_reason,
    )


def evaluate_document_approval_prohibition(atomic_requirement_id: str) -> dict[str, Any]:
    """Probe: document approval alone must not grant the mapped assurance claim."""
    result = evaluate_assurance_claim(
        atomic_requirement_id=atomic_requirement_id,
        evidence_bases=(EvidenceBasis.DOCUMENT_APPROVAL,),
    )
    return {
        "atomic_id": atomic_requirement_id,
        "assurance_level": result.assurance_level.value,
        "document_approval_rejected": result.claim_granted is False and result.document_approval_only,
        "local_engineering_complete": result.local_engineering_complete,
        "external_assurance_verified": result.external_assurance_verified,
        "external_runtime_gate_pending": result.external_runtime_gate_pending,
    }


def evaluate_evidence_gate_requirement(atomic_requirement_id: str) -> dict[str, Any]:
    """Probe: assurance level requires its own evidence bundle, not document approval."""
    doc_only = evaluate_assurance_claim(
        atomic_requirement_id=atomic_requirement_id,
        evidence_bases=(EvidenceBasis.DOCUMENT_APPROVAL,),
    )
    engineering = evaluate_assurance_claim(
        atomic_requirement_id=atomic_requirement_id,
        evidence_bases=(
            EvidenceBasis.PHASE_CLOSURE_EVIDENCE,
            EvidenceBasis.RUNTIME_ENGINEERING_PROBE,
        ),
    )
    return {
        "atomic_id": atomic_requirement_id,
        "assurance_level": doc_only.assurance_level.value,
        "document_approval_rejected": doc_only.claim_granted is False,
        "own_evidence_gate_defined": doc_only.assurance_level in _REQUIRED_EVIDENCE_BY_LEVEL,
        "engineering_evidence_admitted_for_pass_engineering_only": (
            atomic_requirement_id == "TEMP-AR-0432" and engineering.claim_granted is True
        ),
        "external_evidence_required_for_claim": atomic_requirement_id != "TEMP-AR-0432",
        "local_engineering_complete": doc_only.local_engineering_complete,
        "external_assurance_verified": False,
        "external_runtime_gate_pending": True,
    }


def probe_external_gate_atomic_status(atomic_requirement_id: str) -> dict[str, Any]:
    if atomic_requirement_id in EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS:
        return evaluate_document_approval_prohibition(atomic_requirement_id)
    if atomic_requirement_id in EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS:
        return evaluate_evidence_gate_requirement(atomic_requirement_id)
    raise ValueError(f"Unknown external gate atomic: {atomic_requirement_id}")


def assess_acceptance_boundary_governance(
    runtime_signals: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize acceptance-boundary gate enforcement across all 10 atomics."""
    signals = dict(runtime_signals or {})
    per_atomic = {
        aid: probe_external_gate_atomic_status(aid)
        for aid in sorted(ATOMIC_TO_ASSURANCE_LEVEL)
    }
    document_prohibitions_enforced = all(
        per_atomic[aid]["document_approval_rejected"]
        for aid in EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS
    )
    evidence_gates_defined = all(
        per_atomic[aid]["own_evidence_gate_defined"]
        for aid in EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS
    )
    return {
        "contract_version": EXTERNAL_ASSURANCE_GATE_CONTRACT_VERSION,
        "document_approval_insufficient": DOCUMENT_APPROVAL_INSUFFICIENT_FOR_ASSURANCE,
        "document_prohibitions_enforced": document_prohibitions_enforced,
        "evidence_gates_defined": evidence_gates_defined,
        "p6_baseline_closed": bool(signals.get("p6_baseline_closed", False)),
        "per_atomic": per_atomic,
    }
