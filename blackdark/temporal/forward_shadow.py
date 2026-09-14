"""Forward Shadow canonical path — immutable pre-outcome receipts (P3)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence

from blackdark.temporal.evidence_class import (
    TemporalEvidenceClass,
    assert_no_automatic_promotion,
    validate_evidence_class_assignment,
)
from blackdark.temporal.outcome_contract import OutcomeContract, OutcomeLabelStatus

FORWARD_SHADOW_CONTRACT_VERSION = "p3.0.0"
POST_OUTCOME_SHADOW_RECEIPT_CREATION = 0
FORWARD_EVIDENCE_BACKFILL_MASQUERADE = 0
REPLAY_TO_SHADOW_PROMOTION = 0
SHADOW_TO_PRODUCTION_PROMOTION = 0
SHADOW_TO_INDEPENDENT_PROMOTION = 0

POST_OUTCOME_REJECTION_USES_CANONICAL_TRUTH = True
CALLER_FLAG_CAN_BYPASS_POST_OUTCOME_GUARD = False
DUPLICATE_OUTCOME_AUTHORITY = 0
TEMPORAL_TIMESTAMP_FABRICATION = 0
SHADOW_EVIDENCE_CLASS_PRESERVED = True
POST_OUTCOME_REJECTION_AUTHORITY = "p2_outcome_contract+p0_pit_outcome_timestamp"
POST_OUTCOME_REJECTION_RUNTIME_PATH = (
    "forward_shadow.evaluate_post_outcome_receipt_admission"
)

_UNRESOLVED_OUTCOME_STATUSES = frozenset(
    {
        OutcomeLabelStatus.UNRESOLVED,
        OutcomeLabelStatus.UNAVAILABLE,
    }
)


@dataclass(frozen=True, slots=True)
class PostOutcomeReceiptAdmissionDecision:
    """Admission decision for pre-outcome shadow receipt creation."""

    admitted: bool
    rejection_reason: str | None
    authority: str
    runtime_path: str
    canonical_outcome_known_at_receipt_time: bool
    outcome_timestamp: datetime | None
    label_status: str | None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "rejection_reason": self.rejection_reason,
            "authority": self.authority,
            "runtime_path": self.runtime_path,
            "canonical_outcome_known_at_receipt_time": self.canonical_outcome_known_at_receipt_time,
            "outcome_timestamp": (
                self.outcome_timestamp.isoformat() if self.outcome_timestamp else None
            ),
            "label_status": self.label_status,
        }


def evaluate_post_outcome_receipt_admission(
    *,
    issued_at: datetime,
    subject_identity: str,
    canonical_outcome: OutcomeContract | None,
) -> PostOutcomeReceiptAdmissionDecision:
    """
    Reject pre-outcome receipt when P2 canonical outcome is already observable
    at issued_at per P0 PIT semantics (outcome_timestamp <= issued_at).

    Caller-supplied flags and metadata are intentionally ignored.
    """
    if canonical_outcome is None:
        return PostOutcomeReceiptAdmissionDecision(
            admitted=True,
            rejection_reason=None,
            authority=POST_OUTCOME_REJECTION_AUTHORITY,
            runtime_path=POST_OUTCOME_REJECTION_RUNTIME_PATH,
            canonical_outcome_known_at_receipt_time=False,
            outcome_timestamp=None,
            label_status=None,
        )

    if canonical_outcome.subject_identity != subject_identity:
        return PostOutcomeReceiptAdmissionDecision(
            admitted=True,
            rejection_reason=None,
            authority=POST_OUTCOME_REJECTION_AUTHORITY,
            runtime_path=POST_OUTCOME_REJECTION_RUNTIME_PATH,
            canonical_outcome_known_at_receipt_time=False,
            outcome_timestamp=canonical_outcome.outcome_timestamp,
            label_status=canonical_outcome.label_status.value,
        )

    if canonical_outcome.label_status in _UNRESOLVED_OUTCOME_STATUSES:
        return PostOutcomeReceiptAdmissionDecision(
            admitted=True,
            rejection_reason=None,
            authority=POST_OUTCOME_REJECTION_AUTHORITY,
            runtime_path=POST_OUTCOME_REJECTION_RUNTIME_PATH,
            canonical_outcome_known_at_receipt_time=False,
            outcome_timestamp=canonical_outcome.outcome_timestamp,
            label_status=canonical_outcome.label_status.value,
        )

    outcome_ts = canonical_outcome.outcome_timestamp
    if outcome_ts is None or outcome_ts > issued_at:
        return PostOutcomeReceiptAdmissionDecision(
            admitted=True,
            rejection_reason=None,
            authority=POST_OUTCOME_REJECTION_AUTHORITY,
            runtime_path=POST_OUTCOME_REJECTION_RUNTIME_PATH,
            canonical_outcome_known_at_receipt_time=False,
            outcome_timestamp=outcome_ts,
            label_status=canonical_outcome.label_status.value,
        )

    return PostOutcomeReceiptAdmissionDecision(
        admitted=False,
        rejection_reason="post_outcome_shadow_receipt_creation_forbidden",
        authority=POST_OUTCOME_REJECTION_AUTHORITY,
        runtime_path=POST_OUTCOME_REJECTION_RUNTIME_PATH,
        canonical_outcome_known_at_receipt_time=True,
        outcome_timestamp=outcome_ts,
        label_status=canonical_outcome.label_status.value,
    )


@dataclass(frozen=True, slots=True)
class ShadowReceiptAmendment:
    """TEMP-AR-0137: append-only correction with provenance."""

    amendment_id: str
    original_receipt_id: str
    reason: str
    provenance: Mapping[str, Any]
    created_at: datetime
    payload: Mapping[str, Any]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "amendment_id": self.amendment_id,
            "original_receipt_id": self.original_receipt_id,
            "reason": self.reason,
            "provenance": dict(self.provenance),
            "created_at": self.created_at.isoformat(),
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class ForwardShadowReceipt:
    """Immutable pre-outcome forward shadow receipt (TEMP-AR-0124..0135)."""

    shadow_receipt_id: str
    created_at_or_receipt_time: datetime
    subject_identity: str
    input_identity: str
    decision_or_prediction_identity: str
    model_or_engine_version: str
    parameters: Mapping[str, Any]
    temporal_context: Mapping[str, Any]
    source_or_dataset_context: Mapping[str, Any]
    pre_outcome_payload: Mapping[str, Any]
    evidence_class: str
    provenance_reference: str
    status: str
    prediction_id: str
    issued_at: datetime
    model_version: str
    rule_config_version: str
    dataset_version: str
    code_version: str
    input_snapshot_hash: str
    prediction: Any
    confidence: float | None
    abstention_state: str
    outcome_known_at: datetime | None = None
    linked_outcome_id: str | None = None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "shadow_receipt_id": self.shadow_receipt_id,
            "created_at_or_receipt_time": self.created_at_or_receipt_time.isoformat(),
            "subject_identity": self.subject_identity,
            "input_identity": self.input_identity,
            "decision_or_prediction_identity": self.decision_or_prediction_identity,
            "model_or_engine_version": self.model_or_engine_version,
            "parameters": dict(self.parameters),
            "temporal_context": dict(self.temporal_context),
            "source_or_dataset_context": dict(self.source_or_dataset_context),
            "pre_outcome_payload": dict(self.pre_outcome_payload),
            "evidence_class": self.evidence_class,
            "provenance_reference": self.provenance_reference,
            "status": self.status,
            "prediction_id": self.prediction_id,
            "issued_at": self.issued_at.isoformat(),
            "model_version": self.model_version,
            "rule_config_version": self.rule_config_version,
            "dataset_version": self.dataset_version,
            "code_version": self.code_version,
            "input_snapshot_hash": self.input_snapshot_hash,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "abstention_state": self.abstention_state,
            "outcome_known_at": self.outcome_known_at.isoformat() if self.outcome_known_at else None,
            "linked_outcome_id": self.linked_outcome_id,
        }


@dataclass
class ForwardShadowLedger:
    """Append-only forward shadow receipt store."""

    _receipts: list[ForwardShadowReceipt]
    _amendments: list[ShadowReceiptAmendment]

    def __init__(self) -> None:
        self._receipts = []
        self._amendments = []

    def list_receipts(self) -> tuple[ForwardShadowReceipt, ...]:
        return tuple(self._receipts)

    def get_receipt(self, shadow_receipt_id: str) -> ForwardShadowReceipt | None:
        for receipt in reversed(self._receipts):
            if receipt.shadow_receipt_id == shadow_receipt_id:
                return receipt
        return None

    def create_pre_outcome_receipt(
        self,
        *,
        subject_identity: str,
        input_identity: str,
        decision_or_prediction_identity: str,
        model_version: str,
        rule_config_version: str,
        dataset_version: str,
        code_version: str,
        input_snapshot_hash: str,
        prediction: Any,
        confidence: float | None,
        abstention_state: str,
        issued_at: datetime,
        temporal_context: Mapping[str, Any],
        source_or_dataset_context: Mapping[str, Any],
        parameters: Mapping[str, Any] | None = None,
        canonical_outcome: OutcomeContract | None = None,
    ) -> ForwardShadowReceipt:
        """TEMP-AR-0124: receipt must exist before outcome is canonically known."""
        admission = evaluate_post_outcome_receipt_admission(
            issued_at=issued_at,
            subject_identity=subject_identity,
            canonical_outcome=canonical_outcome,
        )
        if not admission.admitted:
            raise ValueError(admission.rejection_reason)

        evidence_class = TemporalEvidenceClass.FORWARD_SHADOW.value
        validate_evidence_class_assignment(evidence_class)

        identity_payload = {
            "subject": subject_identity,
            "input": input_identity,
            "issued_at": issued_at.isoformat(),
            "prediction": prediction,
        }
        receipt_id = hashlib.sha256(
            json.dumps(identity_payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        prediction_id = f"pred_{receipt_id}"

        receipt = ForwardShadowReceipt(
            shadow_receipt_id=f"shadow_{receipt_id}",
            created_at_or_receipt_time=issued_at,
            subject_identity=subject_identity,
            input_identity=input_identity,
            decision_or_prediction_identity=decision_or_prediction_identity,
            model_or_engine_version=model_version,
            parameters=dict(parameters or {}),
            temporal_context=dict(temporal_context),
            source_or_dataset_context=dict(source_or_dataset_context),
            pre_outcome_payload={
                "prediction": prediction,
                "confidence": confidence,
                "abstention_state": abstention_state,
            },
            evidence_class=evidence_class,
            provenance_reference=f"provenance_{receipt_id}",
            status="pre_outcome",
            prediction_id=prediction_id,
            issued_at=issued_at,
            model_version=model_version,
            rule_config_version=rule_config_version,
            dataset_version=dataset_version,
            code_version=code_version,
            input_snapshot_hash=input_snapshot_hash,
            prediction=prediction,
            confidence=confidence,
            abstention_state=abstention_state,
        )
        self._receipts.append(receipt)
        return receipt

    def mark_outcome_known(
        self,
        shadow_receipt_id: str,
        *,
        outcome_known_at: datetime,
        linked_outcome_id: str | None = None,
    ) -> ForwardShadowReceipt:
        """Link outcome without overwriting original receipt (TEMP-AR-0136)."""
        existing = self.get_receipt(shadow_receipt_id)
        if existing is None:
            raise ValueError(f"receipt not found: {shadow_receipt_id}")
        updated = ForwardShadowReceipt(
            shadow_receipt_id=existing.shadow_receipt_id,
            created_at_or_receipt_time=existing.created_at_or_receipt_time,
            subject_identity=existing.subject_identity,
            input_identity=existing.input_identity,
            decision_or_prediction_identity=existing.decision_or_prediction_identity,
            model_or_engine_version=existing.model_or_engine_version,
            parameters=existing.parameters,
            temporal_context=existing.temporal_context,
            source_or_dataset_context=existing.source_or_dataset_context,
            pre_outcome_payload=existing.pre_outcome_payload,
            evidence_class=existing.evidence_class,
            provenance_reference=existing.provenance_reference,
            status="outcome_linked",
            prediction_id=existing.prediction_id,
            issued_at=existing.issued_at,
            model_version=existing.model_version,
            rule_config_version=existing.rule_config_version,
            dataset_version=existing.dataset_version,
            code_version=existing.code_version,
            input_snapshot_hash=existing.input_snapshot_hash,
            prediction=existing.prediction,
            confidence=existing.confidence,
            abstention_state=existing.abstention_state,
            outcome_known_at=existing.outcome_known_at or outcome_known_at,
            linked_outcome_id=linked_outcome_id or existing.linked_outcome_id,
        )
        self._receipts.append(updated)
        return updated

    def append_amendment(
        self,
        shadow_receipt_id: str,
        *,
        reason: str,
        provenance: Mapping[str, Any],
        created_at: datetime,
        payload: Mapping[str, Any],
    ) -> ShadowReceiptAmendment:
        """TEMP-AR-0137: corrections via append-only amendments."""
        existing = self.get_receipt(shadow_receipt_id)
        if existing is None:
            raise ValueError(f"receipt not found: {shadow_receipt_id}")
        amendment = ShadowReceiptAmendment(
            amendment_id=f"amend_{hashlib.sha256(reason.encode()).hexdigest()[:12]}",
            original_receipt_id=shadow_receipt_id,
            reason=reason,
            provenance=dict(provenance),
            created_at=created_at,
            payload=dict(payload),
        )
        self._amendments.append(amendment)
        return amendment

    def attempt_promotion(self, shadow_receipt_id: str, to_class: str) -> None:
        """Fail closed on shadow → production/independent promotion."""
        existing = self.get_receipt(shadow_receipt_id)
        if existing is None:
            raise ValueError(f"receipt not found: {shadow_receipt_id}")
        assert_no_automatic_promotion(existing.evidence_class, to_class)
        if to_class in (
            TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
            TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value,
            TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        ):
            raise ValueError(f"shadow promotion forbidden: {existing.evidence_class} -> {to_class}")

    def list_amendments(self) -> tuple[ShadowReceiptAmendment, ...]:
        return tuple(self._amendments)
