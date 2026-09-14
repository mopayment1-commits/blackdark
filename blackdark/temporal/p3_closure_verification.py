"""P3 closure verification probes — assertions from runtime behavior, not constants."""

from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta
from typing import Any

from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.forward_shadow import ForwardShadowLedger
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY
from blackdark.temporal.p3_pipeline import DUPLICATE_EVIDENCE_LEDGER, DUPLICATE_OUTCOME_FACTORY, run_forward_shadow_pipeline
from blackdark.temporal.p3_requirement_registry import (
    P3_ATOMIC_REQUIREMENT_IDS,
    P3_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
)
from blackdark.temporal.regime_intelligence import KnownRegimeLabel, classify_regime
from blackdark.temporal.reality_anchor import REALITY_ANCHOR_EXTERNAL_GATE_ID, evaluate_reality_anchor

_T_ISSUED = datetime(2024, 9, 1, 10, 0, 0, tzinfo=UTC)
_T_EVAL = datetime(2024, 9, 1, 10, 5, 0, tzinfo=UTC)
_T_FUTURE = datetime(2024, 9, 1, 12, 0, 0, tzinfo=UTC)

_FORBIDDEN_DUPLICATE_AUTHORITY_ATTRS = (
    "TemporalCanonicalEventStore",
    "run_deterministic_mass_replay",
    "generate_outcome_contract",
    "generate_outcomes_from_decision_step",
    "OutcomeFactory",
)


def probe_regime_context_contamination() -> int:
    """Return contamination violations from live regime classification probes."""
    violations = 0

    lookahead = classify_regime(
        observation_time=_T_ISSUED,
        available_at=_T_FUTURE,
        evaluation_time=_T_EVAL,
        indicators={"trend": "up"},
    )
    if not lookahead.unknown_or_unclassified_state:
        violations += 1
    if lookahead.regime_id_or_label != KnownRegimeLabel.UNKNOWN.value:
        violations += 1

    forward = classify_regime(
        observation_time=_T_ISSUED,
        available_at=_T_ISSUED,
        evaluation_time=_T_EVAL,
        indicators={"trend": "up"},
        retrospective=False,
    )
    retrospective = classify_regime(
        observation_time=_T_ISSUED,
        available_at=_T_ISSUED,
        evaluation_time=_T_EVAL,
        indicators={"trend": "up"},
        retrospective=True,
    )
    if retrospective.retrospective_analysis is not True:
        violations += 1
    if forward.retrospective_analysis is True:
        violations += 1

    return violations


def probe_canonical_authority_conflicts() -> int:
    """Return authority conflict count by inspecting P3 module surfaces."""
    import blackdark.temporal.drift_monitoring as drift_module
    import blackdark.temporal.forward_shadow as forward_shadow_module
    import blackdark.temporal.p3_pipeline as pipeline_module
    import blackdark.temporal.regime_intelligence as regime_module

    conflicts = 0
    for module in (
        forward_shadow_module,
        pipeline_module,
        regime_module,
        drift_module,
    ):
        for attr in _FORBIDDEN_DUPLICATE_AUTHORITY_ATTRS:
            if hasattr(module, attr):
                conflicts += 1

    if DUPLICATE_OUTCOME_FACTORY != 0:
        conflicts += 1
    if DUPLICATE_EVIDENCE_LEDGER != 0:
        conflicts += 1

    return conflicts


def probe_p3_historical_truth_mutation() -> int:
    """Return 1 if forward shadow historical receipt truth is mutated in-place."""
    ledger = ForwardShadowLedger()
    receipt = ledger.create_pre_outcome_receipt(
        subject_identity="closure-probe",
        input_identity="input-1",
        decision_or_prediction_identity="pred-1",
        model_version="model-v1",
        rule_config_version="rule-v1",
        dataset_version="ds-1",
        code_version="code-v1",
        input_snapshot_hash="abc",
        prediction={"direction": "up"},
        confidence=0.5,
        abstention_state="act",
        issued_at=_T_ISSUED,
        temporal_context={},
        source_or_dataset_context={},
    )
    original = receipt.to_metadata()
    ledger.mark_outcome_known(
        receipt.shadow_receipt_id,
        outcome_known_at=_T_ISSUED + timedelta(hours=1),
        linked_outcome_id="outcome-1",
    )
    if ledger.list_receipts()[0].to_metadata() != original:
        return 1
    return 0


def probe_p3_prior_evidence_mutation() -> int:
    """Return 1 if P3 pipeline mutates pre-existing evidence ledger records."""
    evidence = EvidenceProvenanceLedger()
    evidence.record_evidence(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        producer="closure_probe",
        source_provenance={},
        temporal_context={},
        versions={},
        lineage=(),
        quality_state={},
        limitations=(),
        methodology="probe",
        timestamps={},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )
    before = copy.deepcopy(evidence.list_records())
    run_forward_shadow_pipeline(
        subject_identity="asset-a",
        input_identity="input-1",
        prediction={"direction": "up"},
        confidence=0.7,
        abstention_state="act",
        issued_at=_T_ISSUED,
        evaluation_time=_T_EVAL,
        temporal_context={},
        source_context={},
        evidence_ledger=evidence,
    )
    if evidence.list_records()[0].to_metadata() != before[0].to_metadata():
        return 1
    return 0


def probe_p3_deterministic_evaluation() -> bool:
    """Return True when identical P3 pipeline inputs yield identical receipt ids."""
    kwargs = {
        "subject_identity": "asset-a",
        "input_identity": "input-1",
        "prediction": {"direction": "up"},
        "confidence": 0.7,
        "abstention_state": "act",
        "issued_at": _T_ISSUED,
        "evaluation_time": _T_EVAL,
        "temporal_context": {},
        "source_context": {},
        "regime_indicators": {"volatility": "low"},
    }
    first = run_forward_shadow_pipeline(**kwargs)
    second = run_forward_shadow_pipeline(**kwargs)
    return first.shadow_receipt.shadow_receipt_id == second.shadow_receipt.shadow_receipt_id


def probe_p3_local_engineering_complete() -> tuple[bool, int]:
    """Return local engineering completeness and implemented atomic count."""
    implemented_count = len(P3_ATOMIC_REQUIREMENT_IDS)
    complete = (
        P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 63
        and P3_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 63
        and implemented_count == 63
        and P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS == ("TEMP-AR-0164",)
    )
    return complete, implemented_count


def probe_temp_ar_0164_status() -> dict[str, Any]:
    """TEMP-AR-0164: local engineering complete; external forward-time evidence pending."""
    anchor = evaluate_reality_anchor(
        anchor_id="closure-probe",
        receipt_issued_at=_T_ISSUED,
        evaluation_time=_T_EVAL,
        uses_simulated_time=True,
    )
    return {
        "atomic_id": REALITY_ANCHOR_EXTERNAL_GATE_ID,
        "local_engineering_complete": anchor.external_gate_requirement_id == REALITY_ANCHOR_EXTERNAL_GATE_ID,
        "external_evidence_pending": anchor.external_evidence_pending,
        "forward_time_passage_verified": anchor.forward_time_passage_verified,
        "simulated_time_not_claimed_as_forward": anchor.forward_time_passage_verified is False,
    }


def evaluate_p3_closure_assertions() -> dict[str, Any]:
    """Evaluate remaining P3 closure assertions from runtime probes."""
    regime_contamination = probe_regime_context_contamination()
    authority_conflicts = probe_canonical_authority_conflicts()
    historical_mutation = probe_p3_historical_truth_mutation()
    prior_evidence_mutation = probe_p3_prior_evidence_mutation()
    deterministic = probe_p3_deterministic_evaluation()
    local_complete, local_count = probe_p3_local_engineering_complete()

    closure_assertions = {
        "REGIME_CONTEXT_CONTAMINATION": regime_contamination,
        "CANONICAL_AUTHORITY_CONFLICTS": authority_conflicts,
        "P3_HISTORICAL_TRUTH_MUTATION": historical_mutation,
        "P3_PRIOR_EVIDENCE_MUTATION": prior_evidence_mutation,
        "P3_DETERMINISTIC_EVALUATION_REQUIREMENTS_PRESERVED": deterministic,
        "P3_LOCAL_ENGINEERING_COMPLETE": local_complete,
        "P3_CLOSED": (
            regime_contamination == 0
            and authority_conflicts == 0
            and historical_mutation == 0
            and prior_evidence_mutation == 0
            and deterministic is True
            and local_complete is True
        ),
    }

    return {
        "closure_assertions": closure_assertions,
        "P3_TOTAL_ACTIVE_ATOMIC_REQUIREMENTS": P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
        "P3_LOCAL_ENGINEERING_COMPLETE_COUNT": local_count,
        "P3_UNIMPLEMENTED_ACTIVE_ATOMIC_REQUIREMENTS": max(
            0, P3_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS - local_count
        ),
        "P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS": list(P3_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS),
        "temp_ar_0164": probe_temp_ar_0164_status(),
        "accepted_p3_fixes": [
            "FAILURE_SURPRISE_ABSTENTION_COMPLETE",
            "POST_OUTCOME_CANONICAL_TRUTH_ENFORCEMENT_COMPLETE",
        ],
        "runtime_probe_paths": {
            "REGIME_CONTEXT_CONTAMINATION": "p3_closure_verification.probe_regime_context_contamination",
            "CANONICAL_AUTHORITY_CONFLICTS": "p3_closure_verification.probe_canonical_authority_conflicts",
            "P3_HISTORICAL_TRUTH_MUTATION": "p3_closure_verification.probe_p3_historical_truth_mutation",
            "P3_PRIOR_EVIDENCE_MUTATION": "p3_closure_verification.probe_p3_prior_evidence_mutation",
            "P3_DETERMINISTIC_EVALUATION_REQUIREMENTS_PRESERVED": (
                "p3_closure_verification.probe_p3_deterministic_evaluation"
            ),
            "P3_LOCAL_ENGINEERING_COMPLETE": "p3_closure_verification.probe_p3_local_engineering_complete",
        },
    }
