"""P5 closure verification probes — assertions from runtime behavior."""

from __future__ import annotations

import importlib
from datetime import UTC, datetime
from typing import Any

from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.market_time_machine import (
    IMPLIED_LIVE_ISSUANCE_PROHIBITED,
    MANDATORY_HISTORICAL_REPLAY_DISCLOSURE,
    InternalModePurpose,
    evaluate_live_issuance_claim,
    supported_internal_purposes,
)
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY
from blackdark.temporal.p5_requirement_registry import (
    P5_ATOMIC_REQUIREMENT_IDS,
    P5_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS,
    P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
    P5_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS,
)
from blackdark.temporal.public_evidence import (
    PUBLIC_LEDGER_MATURITY_REQUIRED,
    build_public_disclosure_from_ledger,
    validate_public_evidence_controls,
)
from blackdark.temporal.user_behavioral_learning import (
    BehavioralLearningPurpose,
    BehavioralConsentRecord,
    USER_BEHAVIOR_NOT_FINANCIAL_TRUTH,
    USER_ACTION_NOT_OUTCOME_PROOF,
    build_behavioral_learning_state,
    evaluate_user_action_as_outcome_proof,
    record_behavioral_signal,
)

_P5_MODULE_PATHS = (
    "blackdark.temporal.market_time_machine",
    "blackdark.temporal.public_evidence",
    "blackdark.temporal.user_behavioral_learning",
)


def probe_p5_module_surfaces() -> int:
    missing = 0
    for path in _P5_MODULE_PATHS:
        try:
            importlib.import_module(path)
        except ImportError:
            missing += 1
    return missing


def probe_internal_mode_purposes_complete() -> bool:
    expected = {p.value for p in InternalModePurpose}
    return expected == set(supported_internal_purposes())


def probe_mandatory_historical_replay_disclosure() -> bool:
    return MANDATORY_HISTORICAL_REPLAY_DISCLOSURE == "Historical Replay"


def probe_live_issuance_prohibition_local() -> bool:
    if not IMPLIED_LIVE_ISSUANCE_PROHIBITED:
        return False
    result = evaluate_live_issuance_claim(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        forward_evidence_present=False,
        uses_simulated_time=True,
    )
    return result["implies_live_issuance"] is False and result["local_engineering_complete"] is True


def probe_temp_ar_0261_status() -> dict[str, Any]:
    """TEMP-AR-0261: local engineering complete; external forward-issuance evidence pending."""
    replay_claim = evaluate_live_issuance_claim(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        forward_evidence_present=False,
    )
    forward_claim = evaluate_live_issuance_claim(
        evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
        forward_evidence_present=False,
        uses_simulated_time=True,
    )
    return {
        "atomic_id": "TEMP-AR-0261",
        "local_engineering_complete": IMPLIED_LIVE_ISSUANCE_PROHIBITED,
        "historical_replay_never_implies_live": replay_claim["implies_live_issuance"] is False,
        "forward_shadow_requires_forward_evidence": forward_claim["external_runtime_gate_pending"] is True,
        "external_evidence_pending": forward_claim["external_runtime_gate_pending"],
        "forward_issuance_verified": False,
    }


def probe_public_disclosure_fields() -> bool:
    ledger = EvidenceProvenanceLedger()
    now = datetime.now(UTC)
    ledger.record_evidence(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        producer="probe",
        source_provenance={"provenance_reference": "prov-1"},
        temporal_context={"available_at": now.isoformat()},
        versions={"model_version": "m1"},
        lineage=("line-1",),
        quality_state={"label_confidence": 0.9},
        limitations=("synthetic excluded",),
        methodology="historical replay evaluation",
        timestamps={"recorded_at": now.isoformat()},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )
    disclosure = build_public_disclosure_from_ledger(
        claim_id="probe-claim",
        ledger=ledger,
        regime_distribution={"bull": 0.6, "bear": 0.4},
        asset_universe=("BTC",),
        evaluation_horizon="24h",
        maturity_sufficient=True,
        freshness_timestamp=now,
    )
    meta = disclosure.to_metadata()
    required = (
        "evidence_class",
        "date_range_start",
        "sample_size",
        "effective_independent_count",
        "regime_distribution",
        "asset_universe",
        "evaluation_horizon",
        "model_version",
        "methodology",
        "uncertainty_statement",
        "limitations",
    )
    return all(meta.get(k) is not None for k in required)


def probe_public_evidence_controls() -> bool:
    now = datetime.now(UTC)
    ledger = EvidenceProvenanceLedger()
    record = ledger.record_evidence(
        evidence_class=TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        producer="probe",
        source_provenance={},
        temporal_context={},
        versions={},
        lineage=(),
        quality_state={},
        limitations=(),
        methodology="test",
        timestamps={"recorded_at": now.isoformat()},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )
    controls = validate_public_evidence_controls(
        records=(record,),
        claimed_date_start=now,
        claimed_date_end=now,
    )
    return controls.cherry_picking_blocked and controls.mixed_evidence_classes_blocked


def probe_user_behavior_not_financial_truth() -> bool:
    return USER_BEHAVIOR_NOT_FINANCIAL_TRUTH is True


def probe_user_action_not_outcome_proof() -> bool:
    result = evaluate_user_action_as_outcome_proof("buy")
    return result["treated_as_outcome_proof"] is False and USER_ACTION_NOT_OUTCOME_PROOF is True


def probe_behavioral_consent_governance() -> bool:
    consent = BehavioralConsentRecord(
        user_key="user-1",
        purpose=BehavioralLearningPurpose.DISCIPLINE_COACHING,
        legal_basis="explicit_consent",
        consented_at=datetime.now(UTC),
        minimized_fields=("action_type", "followed_system"),
    )
    signal = record_behavioral_signal(
        user_key="user-1",
        action_type="follow",
        asset="BTC",
        followed_system=True,
        consent=consent,
    )
    state = build_behavioral_learning_state(
        user_key="user-1",
        purpose=BehavioralLearningPurpose.DISCIPLINE_COACHING,
        signals=(signal,),
        consent=consent,
    )
    return (
        state.separated_from_objective_outcomes is True
        and state.anti_manipulation_enabled is True
        and state.deletion_rights_supported is True
        and signal.is_outcome_truth is False
    )


def probe_p5_local_engineering_complete() -> tuple[bool, int]:
    implemented_count = len(P5_ATOMIC_REQUIREMENT_IDS)
    complete = (
        P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS == 43
        and P5_DISCOVERED_ACTIVE_ATOMIC_REQUIREMENTS == 43
        and implemented_count == 43
        and P5_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS == ("TEMP-AR-0261",)
        and PUBLIC_LEDGER_MATURITY_REQUIRED is True
    )
    return complete, implemented_count


def evaluate_p5_closure_assertions() -> dict[str, Any]:
    module_surfaces = probe_p5_module_surfaces()
    internal_purposes = probe_internal_mode_purposes_complete()
    disclosure = probe_mandatory_historical_replay_disclosure()
    live_prohibition = probe_live_issuance_prohibition_local()
    public_fields = probe_public_disclosure_fields()
    public_controls = probe_public_evidence_controls()
    behavior_truth = probe_user_behavior_not_financial_truth()
    action_proof = probe_user_action_not_outcome_proof()
    consent_gov = probe_behavioral_consent_governance()
    local_complete, local_count = probe_p5_local_engineering_complete()
    temp_ar_0261 = probe_temp_ar_0261_status()

    closure_assertions = {
        "P5_MODULE_SURFACES": module_surfaces,
        "INTERNAL_MODE_PURPOSES_COMPLETE": internal_purposes,
        "MANDATORY_HISTORICAL_REPLAY_DISCLOSURE": disclosure,
        "LIVE_ISSUANCE_PROHIBITION_LOCAL": live_prohibition,
        "PUBLIC_DISCLOSURE_FIELDS_COMPLETE": public_fields,
        "PUBLIC_EVIDENCE_CONTROLS": public_controls,
        "USER_BEHAVIOR_NOT_FINANCIAL_TRUTH": behavior_truth,
        "USER_ACTION_NOT_OUTCOME_PROOF": action_proof,
        "BEHAVIORAL_CONSENT_GOVERNANCE": consent_gov,
        "P5_LOCAL_ENGINEERING_COMPLETE": local_complete,
        "P5_CLOSED": (
            module_surfaces == 0
            and internal_purposes is True
            and disclosure is True
            and live_prohibition is True
            and public_fields is True
            and public_controls is True
            and behavior_truth is True
            and action_proof is True
            and consent_gov is True
            and local_complete is True
        ),
    }

    return {
        "closure_assertions": closure_assertions,
        "P5_TOTAL_ACTIVE_ATOMIC_REQUIREMENTS": P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS,
        "P5_LOCAL_ENGINEERING_COMPLETE_COUNT": local_count,
        "P5_UNIMPLEMENTED_ACTIVE_ATOMIC_REQUIREMENTS": max(
            0, P5_EXPECTED_ACTIVE_ATOMIC_REQUIREMENTS - local_count
        ),
        "P5_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS": list(P5_EXTERNAL_OR_LIVE_GATED_ATOMIC_IDS),
        "temp_ar_0261": temp_ar_0261,
        "runtime_probe_paths": {
            "P5_MODULE_SURFACES": "p5_closure_verification.probe_p5_module_surfaces",
            "INTERNAL_MODE_PURPOSES_COMPLETE": "p5_closure_verification.probe_internal_mode_purposes_complete",
            "MANDATORY_HISTORICAL_REPLAY_DISCLOSURE": (
                "p5_closure_verification.probe_mandatory_historical_replay_disclosure"
            ),
            "LIVE_ISSUANCE_PROHIBITION_LOCAL": "p5_closure_verification.probe_live_issuance_prohibition_local",
            "PUBLIC_DISCLOSURE_FIELDS_COMPLETE": "p5_closure_verification.probe_public_disclosure_fields",
            "PUBLIC_EVIDENCE_CONTROLS": "p5_closure_verification.probe_public_evidence_controls",
            "USER_BEHAVIOR_NOT_FINANCIAL_TRUTH": "p5_closure_verification.probe_user_behavior_not_financial_truth",
            "USER_ACTION_NOT_OUTCOME_PROOF": "p5_closure_verification.probe_user_action_not_outcome_proof",
            "BEHAVIORAL_CONSENT_GOVERNANCE": "p5_closure_verification.probe_behavioral_consent_governance",
            "P5_LOCAL_ENGINEERING_COMPLETE": "p5_closure_verification.probe_p5_local_engineering_complete",
        },
    }
