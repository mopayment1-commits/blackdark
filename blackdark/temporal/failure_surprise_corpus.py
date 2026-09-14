"""Failure, Surprise & Abstention Corpus (P3 FAILURE_SURPRISE_ABSTENTION)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping

from blackdark.temporal.evidence_class import (
    TemporalEvidenceClass,
    assert_no_automatic_promotion,
    validate_evidence_class_assignment,
)
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.outcome_contract import OutcomeContract, OutcomeLabelStatus
from blackdark.temporal.outcome_quality import assess_outcome_quality

FAILURE_CORPUS_CONTRACT_VERSION = "p3.fsa.1.0"
FAILURE_SURPRISE_ABSTENTION_TOTAL = 18

CORPUS_AUTO_MODEL_MUTATION = 0
CORPUS_AUTO_MODEL_PROMOTION = 0
DUPLICATE_OUTCOME_FACTORY = 0
DUPLICATE_EVIDENCE_LEDGER = 0

FSB_ATOMIC_IDS: tuple[str, ...] = (
    "TEMP-AR-0167",
    "TEMP-AR-0168",
    "TEMP-AR-0169",
    "TEMP-AR-0170",
    "TEMP-AR-0171",
    "TEMP-AR-0172",
    "TEMP-AR-0173",
    "TEMP-AR-0174",
    "TEMP-AR-0175",
    "TEMP-AR-0176",
    "TEMP-AR-0177",
    "TEMP-AR-0178",
    "TEMP-AR-0179",
    "TEMP-AR-0180",
    "TEMP-AR-0181",
    "TEMP-AR-0182",
    "TEMP-AR-0183",
    "TEMP-AR-0453",
)


class CaptureCategory(str, Enum):
    FAILURE = "failure"
    SURPRISE = "surprise"
    ABSTENTION = "abstention"


class FailureCaseType(str, Enum):
    HIGH_CONFIDENCE_WRONG = "high_confidence_wrong_prediction"
    FAILURE_TO_ABSTAIN = "failure_to_abstain"
    UNNECESSARY_ABSTENTION = "unnecessary_abstention"
    MISSED_MAJOR_EVENT = "missed_major_event"
    MODEL_DISAGREEMENT = "model_disagreement"
    UNEXPECTED_REGIME_SHIFT = "unexpected_regime_shift"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    STALE_SOURCE = "stale_source"
    CONFLICTING_SOURCES = "conflicting_sources"
    MISSING_SOURCE = "missing_source"
    TAIL_EVENT = "tail_event"
    CALIBRATION_COLLAPSE = "calibration_collapse"
    PREDICTION_INSTABILITY = "prediction_instability"
    SOURCE_REVISION = "source_revision"
    MODEL_REGRESSION = "model_regression"


ATOMIC_CASE_TYPE: dict[str, FailureCaseType] = {
    "TEMP-AR-0168": FailureCaseType.HIGH_CONFIDENCE_WRONG,
    "TEMP-AR-0169": FailureCaseType.FAILURE_TO_ABSTAIN,
    "TEMP-AR-0170": FailureCaseType.UNNECESSARY_ABSTENTION,
    "TEMP-AR-0171": FailureCaseType.MISSED_MAJOR_EVENT,
    "TEMP-AR-0172": FailureCaseType.MODEL_DISAGREEMENT,
    "TEMP-AR-0173": FailureCaseType.UNEXPECTED_REGIME_SHIFT,
    "TEMP-AR-0174": FailureCaseType.CORRELATION_BREAKDOWN,
    "TEMP-AR-0175": FailureCaseType.STALE_SOURCE,
    "TEMP-AR-0176": FailureCaseType.CONFLICTING_SOURCES,
    "TEMP-AR-0177": FailureCaseType.MISSING_SOURCE,
    "TEMP-AR-0178": FailureCaseType.TAIL_EVENT,
    "TEMP-AR-0179": FailureCaseType.CALIBRATION_COLLAPSE,
    "TEMP-AR-0180": FailureCaseType.PREDICTION_INSTABILITY,
    "TEMP-AR-0181": FailureCaseType.SOURCE_REVISION,
    "TEMP-AR-0182": FailureCaseType.MODEL_REGRESSION,
}


@dataclass(frozen=True, slots=True)
class CaseTraceability:
    """TEMP-AR-0183 traceability chain."""

    case_id: str
    root_cause: str
    affected_capability: str
    model_rule_version: str
    remediation: str | None = None
    regression_test: str | None = None
    post_fix_replay: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "case": self.case_id,
            "root_cause": self.root_cause,
            "affected_capability": self.affected_capability,
            "model_rule_version": self.model_rule_version,
            "remediation": self.remediation,
            "regression_test": self.regression_test,
            "post_fix_replay": self.post_fix_replay,
        }


@dataclass(frozen=True, slots=True)
class FailureSurpriseCase:
    """One high-learning-value failure/surprise/abstention case."""

    case_id: str
    case_type: FailureCaseType
    capture_category: CaptureCategory
    shadow_receipt_id: str | None
    prediction_identity: str | None
    decision_identity: str | None
    outcome_id: str | None
    outcome_unresolved: bool
    root_cause: str
    affected_capability: str
    model_rule_version: str
    evidence_class: str
    recorded_at: datetime
    temporal_context: Mapping[str, Any]
    provenance_reference: str
    traceability: CaseTraceability
    lineage: tuple[str, ...] = ()
    triggers_model_mutation: bool = False
    triggers_model_promotion: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "case_type": self.case_type.value,
            "capture_category": self.capture_category.value,
            "shadow_receipt_id": self.shadow_receipt_id,
            "prediction_identity": self.prediction_identity,
            "decision_identity": self.decision_identity,
            "outcome_id": self.outcome_id,
            "outcome_unresolved": self.outcome_unresolved,
            "root_cause": self.root_cause,
            "affected_capability": self.affected_capability,
            "model_rule_version": self.model_rule_version,
            "evidence_class": self.evidence_class,
            "recorded_at": self.recorded_at.isoformat(),
            "temporal_context": dict(self.temporal_context),
            "provenance_reference": self.provenance_reference,
            "traceability": self.traceability.to_metadata(),
            "lineage": list(self.lineage),
            "triggers_model_mutation": self.triggers_model_mutation,
            "triggers_model_promotion": self.triggers_model_promotion,
        }


@dataclass(frozen=True, slots=True)
class CorpusGovernanceMetadata:
    """TEMP-AR-0453: strategic proprietary asset."""

    strategic_proprietary_asset: bool = True
    contract_version: str = FAILURE_CORPUS_CONTRACT_VERSION

    def to_metadata(self) -> dict[str, Any]:
        return {
            "strategic_proprietary_asset": self.strategic_proprietary_asset,
            "contract_version": self.contract_version,
        }


@dataclass
class FailureSurpriseCorpus:
    """TEMP-AR-0167: durable append-only failure/surprise/abstention corpus."""

    _cases: list[FailureSurpriseCase]
    _lineage_log: list[Mapping[str, Any]]
    governance: CorpusGovernanceMetadata

    def __init__(self) -> None:
        self._cases = []
        self._lineage_log = []
        self.governance = CorpusGovernanceMetadata()

    def list_cases(self) -> tuple[FailureSurpriseCase, ...]:
        return tuple(self._cases)

    def lineage_log(self) -> tuple[Mapping[str, Any], ...]:
        return tuple(self._lineage_log)

    def _append_lineage(self, event: Mapping[str, Any]) -> None:
        self._lineage_log.append(dict(event))

    def _build_traceability(
        self,
        *,
        case_id: str,
        root_cause: str,
        affected_capability: str,
        model_rule_version: str,
    ) -> CaseTraceability:
        return CaseTraceability(
            case_id=case_id,
            root_cause=root_cause,
            affected_capability=affected_capability,
            model_rule_version=model_rule_version,
            remediation=None,
            regression_test=None,
            post_fix_replay=None,
        )

    def _record(
        self,
        *,
        case_id: str,
        case_type: FailureCaseType,
        capture_category: CaptureCategory,
        shadow_receipt_id: str | None,
        prediction_identity: str | None,
        decision_identity: str | None,
        outcome_id: str | None,
        outcome_unresolved: bool,
        root_cause: str,
        affected_capability: str,
        model_rule_version: str,
        evidence_class: str,
        recorded_at: datetime,
        temporal_context: Mapping[str, Any],
        provenance_reference: str,
        lineage: tuple[str, ...] = (),
    ) -> FailureSurpriseCase:
        validate_evidence_class_assignment(evidence_class)
        case = FailureSurpriseCase(
            case_id=case_id,
            case_type=case_type,
            capture_category=capture_category,
            shadow_receipt_id=shadow_receipt_id,
            prediction_identity=prediction_identity,
            decision_identity=decision_identity,
            outcome_id=outcome_id,
            outcome_unresolved=outcome_unresolved,
            root_cause=root_cause,
            affected_capability=affected_capability,
            model_rule_version=model_rule_version,
            evidence_class=evidence_class,
            recorded_at=recorded_at,
            temporal_context=dict(temporal_context),
            provenance_reference=provenance_reference,
            traceability=self._build_traceability(
                case_id=case_id,
                root_cause=root_cause,
                affected_capability=affected_capability,
                model_rule_version=model_rule_version,
            ),
            lineage=lineage,
        )
        self._cases.append(case)
        self._append_lineage(
            {
                "action": "record_case",
                "case_id": case_id,
                "case_type": case_type.value,
                "recorded_at": recorded_at.isoformat(),
            }
        )
        return case

    def capture_high_confidence_wrong(
        self,
        *,
        case_id: str,
        prediction_identity: str,
        decision_identity: str,
        outcome: OutcomeContract,
        shadow_receipt_id: str | None,
        evidence_class: str,
        recorded_at: datetime,
        temporal_context: Mapping[str, Any],
        provenance_reference: str,
        confidence: float,
    ) -> FailureSurpriseCase | None:
        """TEMP-AR-0168."""
        if outcome.label_status == OutcomeLabelStatus.UNRESOLVED:
            return None
        if outcome.directional_correctness is not False or confidence < 0.8:
            return None
        return self._record(
            case_id=case_id,
            case_type=FailureCaseType.HIGH_CONFIDENCE_WRONG,
            capture_category=CaptureCategory.FAILURE,
            shadow_receipt_id=shadow_receipt_id,
            prediction_identity=prediction_identity,
            decision_identity=decision_identity,
            outcome_id=outcome.outcome_id,
            outcome_unresolved=False,
            root_cause="overconfident_incorrect_prediction",
            affected_capability="prediction",
            model_rule_version=prediction_identity,
            evidence_class=evidence_class,
            recorded_at=recorded_at,
            temporal_context=temporal_context,
            provenance_reference=provenance_reference,
            lineage=(prediction_identity, decision_identity, outcome.outcome_id),
        )

    def capture_failure_to_abstain(
        self,
        *,
        case_id: str,
        prediction_identity: str,
        decision_identity: str,
        outcome: OutcomeContract | None,
        shadow_receipt_id: str | None,
        evidence_class: str,
        recorded_at: datetime,
        temporal_context: Mapping[str, Any],
        provenance_reference: str,
        abstained: bool,
        should_have_abstained: bool,
    ) -> FailureSurpriseCase | None:
        """TEMP-AR-0169."""
        if abstained or not should_have_abstained:
            return None
        if outcome is not None and outcome.label_status == OutcomeLabelStatus.UNRESOLVED:
            return None
        return self._record(
            case_id=case_id,
            case_type=FailureCaseType.FAILURE_TO_ABSTAIN,
            capture_category=CaptureCategory.ABSTENTION,
            shadow_receipt_id=shadow_receipt_id,
            prediction_identity=prediction_identity,
            decision_identity=decision_identity,
            outcome_id=outcome.outcome_id if outcome else None,
            outcome_unresolved=outcome is None or outcome.label_status == OutcomeLabelStatus.UNRESOLVED,
            root_cause="should_have_abstained",
            affected_capability="abstention",
            model_rule_version=prediction_identity,
            evidence_class=evidence_class,
            recorded_at=recorded_at,
            temporal_context=temporal_context,
            provenance_reference=provenance_reference,
            lineage=(prediction_identity, decision_identity),
        )

    def capture_unnecessary_abstention(
        self,
        *,
        case_id: str,
        prediction_identity: str,
        decision_identity: str,
        outcome: OutcomeContract | None,
        shadow_receipt_id: str | None,
        evidence_class: str,
        recorded_at: datetime,
        temporal_context: Mapping[str, Any],
        provenance_reference: str,
        abstained: bool,
        should_have_abstained: bool,
    ) -> FailureSurpriseCase | None:
        """TEMP-AR-0170."""
        if not abstained or should_have_abstained:
            return None
        if outcome is not None and outcome.label_status == OutcomeLabelStatus.UNRESOLVED:
            return None
        return self._record(
            case_id=case_id,
            case_type=FailureCaseType.UNNECESSARY_ABSTENTION,
            capture_category=CaptureCategory.ABSTENTION,
            shadow_receipt_id=shadow_receipt_id,
            prediction_identity=prediction_identity,
            decision_identity=decision_identity,
            outcome_id=outcome.outcome_id if outcome else None,
            outcome_unresolved=False,
            root_cause="unnecessary_abstention",
            affected_capability="abstention",
            model_rule_version=prediction_identity,
            evidence_class=evidence_class,
            recorded_at=recorded_at,
            temporal_context=temporal_context,
            provenance_reference=provenance_reference,
            lineage=(prediction_identity, decision_identity),
        )

    def capture_signal_case(
        self,
        *,
        atomic_id: str,
        case_id: str,
        prediction_identity: str,
        decision_identity: str,
        outcome: OutcomeContract | None,
        shadow_receipt_id: str | None,
        evidence_class: str,
        recorded_at: datetime,
        temporal_context: Mapping[str, Any],
        provenance_reference: str,
        signal_active: bool,
        root_cause: str,
        affected_capability: str,
        capture_category: CaptureCategory = CaptureCategory.SURPRISE,
    ) -> FailureSurpriseCase | None:
        """TEMP-AR-0171..0182 signal-driven captures."""
        if not signal_active:
            return None
        if outcome is not None and outcome.label_status == OutcomeLabelStatus.UNRESOLVED:
            return None
        case_type = ATOMIC_CASE_TYPE[atomic_id]
        return self._record(
            case_id=case_id,
            case_type=case_type,
            capture_category=capture_category,
            shadow_receipt_id=shadow_receipt_id,
            prediction_identity=prediction_identity,
            decision_identity=decision_identity,
            outcome_id=outcome.outcome_id if outcome else None,
            outcome_unresolved=outcome is None,
            root_cause=root_cause,
            affected_capability=affected_capability,
            model_rule_version=prediction_identity,
            evidence_class=evidence_class,
            recorded_at=recorded_at,
            temporal_context=temporal_context,
            provenance_reference=provenance_reference,
            lineage=(prediction_identity, decision_identity, case_id),
        )

    def capture_from_evaluation(
        self,
        *,
        case_id: str,
        prediction_identity: str,
        decision_identity: str,
        outcome: OutcomeContract | None,
        shadow_receipt_id: str | None,
        evidence_class: str,
        recorded_at: datetime,
        temporal_context: Mapping[str, Any],
        provenance_reference: str,
        signals: Mapping[str, bool],
        confidence: float,
        abstained: bool,
        should_have_abstained: bool,
    ) -> tuple[FailureSurpriseCase, ...]:
        """Route evaluation context to all applicable corpus captures."""
        captured: list[FailureSurpriseCase] = []

        if outcome is not None:
            case = self.capture_high_confidence_wrong(
                case_id=f"{case_id}:0168",
                prediction_identity=prediction_identity,
                decision_identity=decision_identity,
                outcome=outcome,
                shadow_receipt_id=shadow_receipt_id,
                evidence_class=evidence_class,
                recorded_at=recorded_at,
                temporal_context=temporal_context,
                provenance_reference=provenance_reference,
                confidence=confidence,
            )
            if case:
                captured.append(case)

        case = self.capture_failure_to_abstain(
            case_id=f"{case_id}:0169",
            prediction_identity=prediction_identity,
            decision_identity=decision_identity,
            outcome=outcome,
            shadow_receipt_id=shadow_receipt_id,
            evidence_class=evidence_class,
            recorded_at=recorded_at,
            temporal_context=temporal_context,
            provenance_reference=provenance_reference,
            abstained=abstained,
            should_have_abstained=should_have_abstained,
        )
        if case:
            captured.append(case)

        case = self.capture_unnecessary_abstention(
            case_id=f"{case_id}:0170",
            prediction_identity=prediction_identity,
            decision_identity=decision_identity,
            outcome=outcome,
            shadow_receipt_id=shadow_receipt_id,
            evidence_class=evidence_class,
            recorded_at=recorded_at,
            temporal_context=temporal_context,
            provenance_reference=provenance_reference,
            abstained=abstained,
            should_have_abstained=should_have_abstained,
        )
        if case:
            captured.append(case)

        signal_map = {
            "TEMP-AR-0171": ("missed_major_event", "event_detection", CaptureCategory.FAILURE),
            "TEMP-AR-0172": ("model_disagreement", "ensemble", CaptureCategory.SURPRISE),
            "TEMP-AR-0173": ("unexpected_regime_shift", "regime", CaptureCategory.SURPRISE),
            "TEMP-AR-0174": ("correlation_breakdown", "correlation", CaptureCategory.SURPRISE),
            "TEMP-AR-0175": ("stale_source", "source_quality", CaptureCategory.FAILURE),
            "TEMP-AR-0176": ("conflicting_sources", "source_quality", CaptureCategory.FAILURE),
            "TEMP-AR-0177": ("missing_source", "source_quality", CaptureCategory.FAILURE),
            "TEMP-AR-0178": ("tail_event", "risk", CaptureCategory.SURPRISE),
            "TEMP-AR-0179": ("calibration_collapse", "calibration", CaptureCategory.FAILURE),
            "TEMP-AR-0180": ("prediction_instability", "prediction", CaptureCategory.SURPRISE),
            "TEMP-AR-0181": ("source_revision", "provenance", CaptureCategory.SURPRISE),
            "TEMP-AR-0182": ("model_regression", "model_quality", CaptureCategory.FAILURE),
        }
        for atomic_id, (signal_key, capability, category) in signal_map.items():
            case = self.capture_signal_case(
                atomic_id=atomic_id,
                case_id=f"{case_id}:{atomic_id[-4:]}",
                prediction_identity=prediction_identity,
                decision_identity=decision_identity,
                outcome=outcome,
                shadow_receipt_id=shadow_receipt_id,
                evidence_class=evidence_class,
                recorded_at=recorded_at,
                temporal_context=temporal_context,
                provenance_reference=provenance_reference,
                signal_active=bool(signals.get(signal_key)),
                root_cause=signal_key,
                affected_capability=capability,
                capture_category=category,
            )
            if case:
                captured.append(case)

        return tuple(captured)

    def record_in_evidence_ledger(
        self,
        case: FailureSurpriseCase,
        *,
        ledger: EvidenceProvenanceLedger,
        outcome: OutcomeContract | None = None,
    ) -> str:
        """Link corpus case into P2 Evidence Provenance Ledger without duplicate authority."""
        quality = assess_outcome_quality(outcome) if outcome else None
        record = ledger.record_evidence(
            evidence_class=case.evidence_class,
            producer="failure_surprise_abstention_corpus",
            source_provenance={"provenance_reference": case.provenance_reference},
            temporal_context=dict(case.temporal_context),
            versions={"model_rule_version": case.model_rule_version},
            lineage=case.lineage,
            quality_state=quality.to_metadata() if quality else {},
            limitations=(),
            methodology="failure_surprise_abstention_capture",
            timestamps={"recorded_at": case.recorded_at.isoformat()},
            evaluator_identity=None,
            payload=case.to_metadata(),
        )
        self._append_lineage(
            {
                "action": "evidence_ledger_link",
                "case_id": case.case_id,
                "evidence_id": record.evidence_id,
            }
        )
        return record.evidence_id

    def attempt_evidence_promotion(self, case: FailureSurpriseCase, to_class: str) -> None:
        """Corpus cannot auto-promote evidence classes."""
        assert_no_automatic_promotion(case.evidence_class, to_class)
        raise ValueError(f"corpus evidence promotion forbidden: {case.evidence_class} -> {to_class}")

    def attempt_model_mutation(self, case: FailureSurpriseCase) -> None:
        """Corpus cannot auto-mutate models."""
        if case.triggers_model_mutation:
            raise ValueError("corpus auto model mutation forbidden")
        raise ValueError("corpus auto model mutation forbidden")

    def attempt_model_promotion(self, case: FailureSurpriseCase) -> None:
        """Corpus cannot auto-promote models."""
        if case.triggers_model_promotion:
            raise ValueError("corpus auto model promotion forbidden")
        raise ValueError("corpus auto model promotion forbidden")

    # Backward-compatible helper used by p3_pipeline
    def classify_from_shadow_outcome(
        self,
        *,
        case_id: str,
        shadow_receipt_id: str,
        outcome_id: str | None,
        prediction_confidence: float,
        prediction_correct: bool | None,
        abstained: bool,
        should_have_abstained: bool,
        evidence_class: str,
        recorded_at: datetime,
        model_version: str,
        outcome: OutcomeContract | None = None,
        temporal_context: Mapping[str, Any] | None = None,
        provenance_reference: str = "shadow_pipeline",
    ) -> FailureSurpriseCase | None:
        if outcome is not None and outcome.label_status == OutcomeLabelStatus.UNRESOLVED:
            return None
        cases = self.capture_from_evaluation(
            case_id=case_id,
            prediction_identity=model_version,
            decision_identity=f"decision:{shadow_receipt_id}",
            outcome=outcome,
            shadow_receipt_id=shadow_receipt_id,
            evidence_class=evidence_class,
            recorded_at=recorded_at,
            temporal_context=temporal_context or {},
            provenance_reference=provenance_reference,
            signals={},
            confidence=prediction_confidence,
            abstained=abstained,
            should_have_abstained=should_have_abstained,
        )
        for case in cases:
            if case.case_type in (
                FailureCaseType.HIGH_CONFIDENCE_WRONG,
                FailureCaseType.FAILURE_TO_ABSTAIN,
                FailureCaseType.UNNECESSARY_ABSTENTION,
            ):
                return case
        return cases[0] if cases else None
