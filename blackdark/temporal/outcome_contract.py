"""Outcome Contract types for the Automated Outcome Factory (P2)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping


class OutcomeLabelStatus(str, Enum):
    VERIFIED = "verified"
    PROVISIONAL = "provisional"
    INCOMPLETE = "incomplete"
    CONFLICTED = "conflicted"
    UNAVAILABLE = "unavailable"
    UNRESOLVED = "unresolved"
    LOW_CONFIDENCE = "low_confidence"


OUTCOME_FACTORY_CONTRACT_VERSION = "p2.0.0"
OUTCOME_EVALUATOR_IDENTITY = "independent_outcome_evaluator_v1"


@dataclass(frozen=True, slots=True)
class OutcomeContract:
    """Measurable outcome contract linkable to signal/prediction/decision (TEMP-AR-0096..0114)."""

    outcome_id: str
    subject_identity: str
    prediction_identity: str | None
    decision_identity: str | None
    target_definition: str | None
    evaluation_horizon: str | None
    outcome_timestamp: datetime | None
    realized_result: Any | None
    benchmark_result: Any | None
    confidence: float | None
    calibration_error: float | None
    directional_correctness: bool | None
    magnitude_error: float | None
    regret: float | None
    favorable_excursion: float | None
    adverse_excursion: float | None
    drawdown: float | None
    false_positive_cost: float | None
    false_negative_cost: float | None
    abstention_quality: str | None
    market_regime: str | None
    evaluator_version: str
    label_status: OutcomeLabelStatus
    evaluation_context: Mapping[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "contract_version": OUTCOME_FACTORY_CONTRACT_VERSION,
            "outcome_id": self.outcome_id,
            "subject_identity": self.subject_identity,
            "prediction_identity": self.prediction_identity,
            "decision_identity": self.decision_identity,
            "target_definition": self.target_definition,
            "evaluation_horizon": self.evaluation_horizon,
            "outcome_timestamp": (
                self.outcome_timestamp.isoformat() if self.outcome_timestamp else None
            ),
            "realized_result": self.realized_result,
            "benchmark_result": self.benchmark_result,
            "confidence": self.confidence,
            "calibration_error": self.calibration_error,
            "directional_correctness": self.directional_correctness,
            "magnitude_error": self.magnitude_error,
            "regret": self.regret,
            "favorable_excursion": self.favorable_excursion,
            "adverse_excursion": self.adverse_excursion,
            "drawdown": self.drawdown,
            "false_positive_cost": self.false_positive_cost,
            "false_negative_cost": self.false_negative_cost,
            "abstention_quality": self.abstention_quality,
            "market_regime": self.market_regime,
            "evaluator_version": self.evaluator_version,
            "label_status": self.label_status.value,
            "evaluation_context": dict(self.evaluation_context),
        }
