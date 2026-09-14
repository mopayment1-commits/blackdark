"""Historical decision-path replay stages (P1.3) — no new decision authority."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from blackdark.temporal.event_store import TemporalCanonicalEventStore
from blackdark.temporal.replay import REPLAY_EVIDENCE_CLASS, ReplayResult, ReplayStepOutput

DECISION_PATH_CONTRACT_VERSION = "p1.3.0"
DECISION_PATH_STAGES: tuple[str, ...] = (
    "observation",
    "feature_state",
    "signal",
    "prediction",
    "decision",
    "confidence",
    "abstain_act",
    "outcome",
)


@dataclass(frozen=True, slots=True)
class DecisionPathStepResult:
    """One simulated-time decision-path replay step."""

    simulated_time: datetime
    stages: Mapping[str, Any]
    evidence_class: str = REPLAY_EVIDENCE_CLASS

    def to_metadata(self) -> dict[str, Any]:
        return {
            "simulated_time": self.simulated_time.isoformat(),
            "stages": dict(self.stages),
            "evidence_class": self.evidence_class,
        }


@dataclass(frozen=True, slots=True)
class DecisionPathReplayResult:
    """Full historical decision-path replay over a mass replay result."""

    model_identity: str | None
    parameters: Mapping[str, Any]
    steps: tuple[DecisionPathStepResult, ...]
    evidence_class: str
    creates_new_decision_authority: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "contract_version": DECISION_PATH_CONTRACT_VERSION,
            "model_identity": self.model_identity,
            "parameters": dict(self.parameters),
            "steps": [step.to_metadata() for step in self.steps],
            "evidence_class": self.evidence_class,
            "creates_new_decision_authority": self.creates_new_decision_authority,
        }


def _threshold(parameters: Mapping[str, Any]) -> float:
    raw = parameters.get("threshold")
    if raw is None:
        return 0.5
    return float(raw)


def _build_step_stages(
    *,
    step: ReplayStepOutput,
    event_source: TemporalCanonicalEventStore,
    parameters: Mapping[str, Any],
    model_identity: str | None,
) -> dict[str, Any]:
    admitted_events = [
        event_source.get_event(event_id)
        for event_id in step.admitted_event_ids
        if event_source.get_event(event_id) is not None
    ]
    observation = {
        "admitted_event_ids": list(step.admitted_event_ids),
        "state_by_entity": dict(step.state_by_entity),
        "reconstruction": dict(step.reconstruction),
    }
    feature_state = {
        entity: {
            "entity_key": event.entity_key,
            "event_type": event.event_type,
            "payload": dict(event.payload),
            "source": event.provenance.source,
        }
        for event in admitted_events
        if event is not None
        for entity in [event.entity_key]
    }
    signals = {
        entity: {
            "direction": "bullish" if float(str(features.get("payload", {}).get("price", "0")).replace("n/a", "0") or 0) >= 100 else "neutral"
        }
        for entity, features in feature_state.items()
    }
    predictions = {
        entity: {
            "model_identity": model_identity,
            "score": 0.6 if signals[entity]["direction"] == "bullish" else 0.4,
        }
        for entity in signals
    }
    threshold = _threshold(parameters)
    decisions = {
        entity: {
            "action": "act" if predictions[entity]["score"] >= threshold else "abstain",
            "threshold": threshold,
        }
        for entity in predictions
    }
    confidence = {
        entity: {"confidence": predictions[entity]["score"]} for entity in predictions
    }
    abstain_act = {entity: {"result": decisions[entity]["action"]} for entity in decisions}
    outcome = {
        "status": "deferred_outcome_factory_not_in_p1_3",
        "evidence_class": REPLAY_EVIDENCE_CLASS,
        "note": "Outcome Factory is outside P1.3 scope; no production outcome authority created",
    }
    return {
        "observation": observation,
        "feature_state": feature_state,
        "signal": signals,
        "prediction": predictions,
        "decision": decisions,
        "confidence": confidence,
        "abstain_act": abstain_act,
        "outcome": outcome,
    }


def execute_historical_decision_path(
    *,
    event_source: TemporalCanonicalEventStore,
    mass_replay: ReplayResult,
    parameters: Mapping[str, Any] | None = None,
    model_identity: str | None = None,
) -> DecisionPathReplayResult:
    """
    Reproduce the canonical decision-path stages from admitted historical replay state.

    Does not create a new decision authority or invoke Outcome Factory.
    """
    params = dict(parameters or {})
    steps: list[DecisionPathStepResult] = []
    for step in mass_replay.replay_outputs:
        stages = _build_step_stages(
            step=step,
            event_source=event_source,
            parameters=params,
            model_identity=model_identity,
        )
        steps.append(
            DecisionPathStepResult(
                simulated_time=step.simulated_time,
                stages=stages,
            )
        )
    return DecisionPathReplayResult(
        model_identity=model_identity,
        parameters=params,
        steps=tuple(steps),
        evidence_class=REPLAY_EVIDENCE_CLASS,
        creates_new_decision_authority=False,
    )
