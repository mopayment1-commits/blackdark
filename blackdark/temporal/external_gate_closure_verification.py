"""EXTERNAL_OR_LIVE_GATE closure verification probes."""

from __future__ import annotations

import importlib
from typing import Any

from blackdark.temporal.external_assurance_gates import (
    DOCUMENT_APPROVAL_INSUFFICIENT_FOR_ASSURANCE,
    assess_acceptance_boundary_governance,
    evaluate_assurance_claim,
    EvidenceBasis,
    probe_external_gate_atomic_status,
)
from blackdark.temporal.external_gate_requirement_registry import (
    EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS,
    EXTERNAL_GATE_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS,
    EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS,
    EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    EXTERNAL_GATE_EXTERNAL_ASSURANCE_ATOMIC_IDS,
)

_EXTERNAL_GATE_MODULE_PATHS = (
    "blackdark.temporal.external_assurance_gates",
    "blackdark.temporal.external_gate_requirement_registry",
)


def probe_external_gate_module_surfaces() -> int:
    missing = 0
    for path in _EXTERNAL_GATE_MODULE_PATHS:
        try:
            importlib.import_module(path)
        except ImportError:
            missing += 1
    return missing


def probe_document_approval_prohibitions() -> bool:
    return all(
        probe_external_gate_atomic_status(aid)["document_approval_rejected"]
        for aid in EXTERNAL_GATE_DOCUMENT_APPROVAL_PROHIBITION_IDS
    )


def probe_evidence_gate_requirements() -> bool:
    return all(
        probe_external_gate_atomic_status(aid)["own_evidence_gate_defined"]
        for aid in EXTERNAL_GATE_EVIDENCE_REQUIREMENT_IDS
    )


def probe_simulated_time_cannot_close_live_gate() -> bool:
    live_claim = evaluate_assurance_claim(
        atomic_requirement_id="TEMP-AR-0433",
        evidence_bases=(
            EvidenceBasis.LIVE_PRODUCTION_OBSERVATION,
            EvidenceBasis.PHASE_CLOSURE_EVIDENCE,
        ),
        uses_simulated_time=True,
        live_production_observation_present=True,
    )
    return live_claim.claim_granted is False and live_claim.external_runtime_gate_pending is True


def probe_pass_engineering_local_evidence_only() -> bool:
    eng = evaluate_assurance_claim(
        atomic_requirement_id="TEMP-AR-0432",
        evidence_bases=(
            EvidenceBasis.PHASE_CLOSURE_EVIDENCE,
            EvidenceBasis.RUNTIME_ENGINEERING_PROBE,
        ),
    )
    return eng.claim_granted is True and eng.external_assurance_verified is False


def probe_external_gate_local_engineering_complete() -> tuple[bool, int]:
    implemented_count = len(EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS)
    complete = (
        EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 10
        and EXTERNAL_GATE_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 10
        and implemented_count == 10
        and len(EXTERNAL_GATE_EXTERNAL_ASSURANCE_ATOMIC_IDS) == 10
        and DOCUMENT_APPROVAL_INSUFFICIENT_FOR_ASSURANCE is True
    )
    return complete, implemented_count


def evaluate_external_gate_closure_assertions(
    runtime_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    module_surfaces = probe_external_gate_module_surfaces()
    doc_prohibitions = probe_document_approval_prohibitions()
    evidence_gates = probe_evidence_gate_requirements()
    simulated_blocked = probe_simulated_time_cannot_close_live_gate()
    pass_eng_local = probe_pass_engineering_local_evidence_only()
    local_complete, local_count = probe_external_gate_local_engineering_complete()
    boundary = assess_acceptance_boundary_governance(runtime_signals=runtime_signals)

    closure_assertions = {
        "EXTERNAL_GATE_MODULE_SURFACES": module_surfaces,
        "DOCUMENT_APPROVAL_PROHIBITIONS": doc_prohibitions,
        "EVIDENCE_GATE_REQUIREMENTS": evidence_gates,
        "SIMULATED_TIME_CANNOT_CLOSE_LIVE_GATE": simulated_blocked,
        "PASS_ENGINEERING_LOCAL_EVIDENCE_ONLY": pass_eng_local,
        "EXTERNAL_GATE_LOCAL_ENGINEERING_COMPLETE": local_complete,
        "EXTERNAL_GATE_SCOPE_CLOSED": (
            module_surfaces == 0
            and doc_prohibitions is True
            and evidence_gates is True
            and simulated_blocked is True
            and pass_eng_local is True
            and local_complete is True
        ),
    }

    per_atomic_status = {
        aid: probe_external_gate_atomic_status(aid) for aid in EXTERNAL_GATE_ATOMIC_REQUIREMENT_IDS
    }

    return {
        "closure_assertions": closure_assertions,
        "EXTERNAL_GATE_TOTAL_ACTIVE_ATOMIC_REQUIREMENTS": EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
        "EXTERNAL_GATE_LOCAL_ENGINEERING_COMPLETE_COUNT": local_count,
        "EXTERNAL_GATE_UNIMPLEMENTED_ACTIVE_ATOMIC_REQUIREMENTS": max(
            0, EXTERNAL_GATE_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS - local_count
        ),
        "EXTERNAL_GATE_EXTERNAL_ASSURANCE_ATOMIC_IDS": list(EXTERNAL_GATE_EXTERNAL_ASSURANCE_ATOMIC_IDS),
        "acceptance_boundary_governance": boundary,
        "per_atomic_status": per_atomic_status,
        "runtime_probe_paths": {
            "EXTERNAL_GATE_MODULE_SURFACES": "external_gate_closure_verification.probe_external_gate_module_surfaces",
            "DOCUMENT_APPROVAL_PROHIBITIONS": "external_gate_closure_verification.probe_document_approval_prohibitions",
            "EVIDENCE_GATE_REQUIREMENTS": "external_gate_closure_verification.probe_evidence_gate_requirements",
            "SIMULATED_TIME_CANNOT_CLOSE_LIVE_GATE": "external_gate_closure_verification.probe_simulated_time_cannot_close_live_gate",
            "PASS_ENGINEERING_LOCAL_EVIDENCE_ONLY": "external_gate_closure_verification.probe_pass_engineering_local_evidence_only",
            "EXTERNAL_GATE_LOCAL_ENGINEERING_COMPLETE": "external_gate_closure_verification.probe_external_gate_local_engineering_complete",
        },
    }
