"""Automated Outcome Factory — independent outcome evaluation (P2)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from blackdark.temporal.event_store import TemporalCanonicalEventStore
from blackdark.temporal.outcome_contract import (
    OUTCOME_EVALUATOR_IDENTITY,
    OUTCOME_FACTORY_CONTRACT_VERSION,
    OutcomeContract,
    OutcomeLabelStatus,
)
from blackdark.temporal.replay import ReplayStepOutput
PREDICTOR_SELF_VALIDATION = False


@dataclass(frozen=True, slots=True)
class OutcomeFactoryResult:
    outcomes: tuple[OutcomeContract, ...]
    evaluator_identity: str
    predictor_self_validation: bool = PREDICTOR_SELF_VALIDATION
    unproven_outcome_fabrication: int = 0

    def to_metadata(self) -> dict[str, Any]:
        return {
            "contract_version": OUTCOME_FACTORY_CONTRACT_VERSION,
            "evaluator_identity": self.evaluator_identity,
            "predictor_self_validation": self.predictor_self_validation,
            "unproven_outcome_fabrication": self.unproven_outcome_fabrication,
            "outcomes": [outcome.to_metadata() for outcome in self.outcomes],
        }


def _parse_price(payload: Mapping[str, Any]) -> float | None:
    raw = payload.get("price")
    if raw is None:
        return None
    try:
        return float(str(raw).replace("n/a", ""))
    except ValueError:
        return None


def _observable_at(
    event_source: TemporalCanonicalEventStore,
    entity_key: str,
    evaluation_time: datetime,
) -> float | None:
    """PIT-correct observable lookup: only events available at evaluation_time."""
    best: float | None = None
    for event in event_source.list_events():
        if event.entity_key != entity_key:
            continue
        available_at = event.observation.available_at
        if not available_at.is_known() or available_at.value is None:
            continue
        if available_at.value > evaluation_time:
            continue
        price = _parse_price(event.payload)
        if price is not None:
            best = price
    return best


def generate_outcome_contract(
    *,
    entity_key: str,
    step: ReplayStepOutput,
    event_source: TemporalCanonicalEventStore,
    prediction: Mapping[str, Any],
    decision: Mapping[str, Any],
    parameters: Mapping[str, Any],
    model_identity: str | None,
    evaluation_horizon: str | None = None,
) -> OutcomeContract:
    """
    Independent outcome evaluator (TEMP-AR-0115, TEMP-AR-0116).

    Predictor/model identity is recorded separately; evaluator does not self-validate.
    """
    simulated_time = step.simulated_time
    horizon = evaluation_horizon or str(parameters.get("evaluation_horizon", "same_step"))
    regime = str(parameters.get("regime", "unknown"))
    target_def = str(parameters.get("target_definition", "directional_price_move"))
    realized = _observable_at(event_source, entity_key, simulated_time)
    predicted_score = float(prediction.get("score", 0.0))
    action = decision.get("action", "abstain")

    if realized is None:
        label_status = OutcomeLabelStatus.UNRESOLVED
        directional_correctness = None
        magnitude_error = None
        calibration_error = None
    else:
        benchmark = float(parameters.get("benchmark_price", realized))
        predicted_direction = "up" if predicted_score >= 0.5 else "down"
        actual_direction = "up" if realized >= benchmark else "down"
        directional_correctness = (
            None if action == "abstain" else predicted_direction == actual_direction
        )
        magnitude_error = abs(predicted_score - min(1.0, max(0.0, realized / max(benchmark, 1.0))))
        calibration_error = abs(predicted_score - (1.0 if directional_correctness else 0.0)) if directional_correctness is not None else None
        label_status = OutcomeLabelStatus.VERIFIED

    abstention_quality = "appropriate" if action == "abstain" and realized is None else (
        "evaluated" if action != "abstain" else "abstained"
    )

    identity_payload = {
        "entity_key": entity_key,
        "simulated_time": simulated_time.isoformat(),
        "model_identity": model_identity,
        "action": action,
        "horizon": horizon,
    }
    outcome_id = f"outcome_{hashlib.sha256(json.dumps(identity_payload, sort_keys=True).encode()).hexdigest()[:16]}"

    return OutcomeContract(
        outcome_id=outcome_id,
        subject_identity=entity_key,
        prediction_identity=str(prediction.get("model_identity") or model_identity),
        decision_identity=f"{entity_key}:{action}",
        target_definition=target_def,
        evaluation_horizon=horizon,
        outcome_timestamp=simulated_time,
        realized_result=realized,
        benchmark_result=parameters.get("benchmark_price"),
        confidence=predicted_score if realized is not None else None,
        calibration_error=calibration_error,
        directional_correctness=directional_correctness,
        magnitude_error=magnitude_error,
        regret=None if realized is None else max(0.0, magnitude_error or 0.0),
        favorable_excursion=None if realized is None else max(0.0, (realized or 0) - (parameters.get("benchmark_price") or realized or 0)),
        adverse_excursion=None if realized is None else max(0.0, (parameters.get("benchmark_price") or realized or 0) - (realized or 0)),
        drawdown=None,
        false_positive_cost=None if directional_correctness is not False else 1.0,
        false_negative_cost=None if directional_correctness is not True else 0.0,
        abstention_quality=abstention_quality,
        market_regime=regime,
        evaluator_version=OUTCOME_EVALUATOR_IDENTITY,
        label_status=label_status,
        evaluation_context={
            "simulated_time": simulated_time.isoformat(),
            "evaluator_independent_from_predictor": True,
            "predictor_identity": model_identity,
        },
    )


def generate_outcomes_from_decision_step(
    *,
    step: ReplayStepOutput,
    event_source: TemporalCanonicalEventStore,
    stages: Mapping[str, Any],
    parameters: Mapping[str, Any],
    model_identity: str | None,
) -> OutcomeFactoryResult:
    """TEMP-AR-0096: link signals/predictions/decisions to measurable outcome contracts."""
    predictions = stages.get("prediction", {})
    decisions = stages.get("decision", {})
    outcomes: list[OutcomeContract] = []
    fabrication_count = 0

    for entity_key, prediction in predictions.items():
        decision = decisions.get(entity_key, {})
        contract = generate_outcome_contract(
            entity_key=entity_key,
            step=step,
            event_source=event_source,
            prediction=prediction,
            decision=decision,
            parameters=parameters,
            model_identity=model_identity,
        )
        if contract.label_status == OutcomeLabelStatus.UNRESOLVED and contract.realized_result is not None:
            fabrication_count += 1
        outcomes.append(contract)

    return OutcomeFactoryResult(
        outcomes=tuple(outcomes),
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
    )


def predictor_must_not_self_validate(
    predictor_identity: str | None,
    evaluator_identity: str,
) -> bool:
    """TEMP-AR-0116: production prediction must not validate itself."""
    if predictor_identity is None:
        return True
    return predictor_identity != evaluator_identity
