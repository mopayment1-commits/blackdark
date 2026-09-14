"""Counterfactual replay lab (P4 / TEMP-AR-0241..0250)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

from blackdark.temporal.decision_path import execute_historical_decision_path
from blackdark.temporal.event_store import TemporalCanonicalEventStore
from blackdark.temporal.replay import ReplayRequest, ReplayResult, run_deterministic_mass_replay

COUNTERFACTUAL_LAB_CONTRACT_VERSION = "p4.counterfactual_lab.1.0"
COUNTERFACTUAL_EVALUATES_ROBUSTNESS = True


class CounterfactualQuestion(str, Enum):
    CONFIDENCE_THRESHOLD = "different_confidence_threshold"
    ABSTENTION_THRESHOLD = "alternative_abstention_threshold"
    SOURCE_REMOVED = "source_removed"
    SOURCE_DELAYED = "source_delayed"
    ALTERNATE_MODEL = "alternate_model_version"
    ALTERNATE_RULE = "alternate_rule_version"
    HIGHER_LATENCY = "higher_latency"
    DIFFERENT_COSTS = "different_costs"
    ALTERNATE_REGIME = "alternative_regime_assumptions"


@dataclass(frozen=True, slots=True)
class CounterfactualSpec:
    question: CounterfactualQuestion
    parameters: Mapping[str, Any]
    scenario_id: str

    def to_metadata(self) -> dict[str, Any]:
        return {
            "question": self.question.value,
            "parameters": dict(self.parameters),
            "scenario_id": self.scenario_id,
        }


@dataclass(frozen=True, slots=True)
class CounterfactualResult:
    spec: CounterfactualSpec
    replay: ReplayResult
    decision_path_fingerprint: str
    robustness_focus: bool = True

    def to_metadata(self) -> dict[str, Any]:
        return {
            "spec": self.spec.to_metadata(),
            "replay_id": self.replay.replay_id,
            "decision_path_fingerprint": self.decision_path_fingerprint,
            "robustness_focus": self.robustness_focus,
            "evidence_class": self.replay.evidence_class,
        }


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def run_counterfactual_replay(
    *,
    event_source: TemporalCanonicalEventStore,
    base_request: ReplayRequest,
    spec: CounterfactualSpec,
) -> CounterfactualResult:
    """Execute counterfactual replay reusing P1 deterministic replay engine."""
    params = dict(base_request.replay_parameters)
    params.update(spec.parameters)
    if spec.question == CounterfactualQuestion.SOURCE_REMOVED:
        events = [e for e in event_source.list_events() if e.provenance.source != params.get("removed_source")]
        store = TemporalCanonicalEventStore(events)
    elif spec.question == CounterfactualQuestion.SOURCE_DELAYED:
        store = event_source
        params["latency_penalty"] = params.get("latency_ms", 500)
    else:
        store = event_source

    request = ReplayRequest(
        event_source=store,
        start_time=base_request.start_time,
        end_time=base_request.end_time,
        replay_clock_or_schedule=base_request.replay_clock_or_schedule,
        strict_mode=base_request.strict_mode,
        replay_parameters=params,
        dataset_or_source_version_context=base_request.dataset_or_source_version_context,
    )
    replay = run_deterministic_mass_replay(request)
    decision = execute_historical_decision_path(
        event_source=store,
        mass_replay=replay,
        parameters=params,
        model_identity=str(params.get("model_version", "model-v1")),
    )
    return CounterfactualResult(
        spec=spec,
        replay=replay,
        decision_path_fingerprint=_fingerprint(decision.to_metadata()),
        robustness_focus=True,
    )


def build_counterfactual_suite(
    *,
    event_source: TemporalCanonicalEventStore,
    base_request: ReplayRequest,
) -> tuple[CounterfactualResult, ...]:
    specs = [
        CounterfactualSpec(
            question=CounterfactualQuestion.CONFIDENCE_THRESHOLD,
            parameters={"threshold": 0.7},
            scenario_id="cf-confidence",
        ),
        CounterfactualSpec(
            question=CounterfactualQuestion.ABSTENTION_THRESHOLD,
            parameters={"abstention_threshold": 0.6},
            scenario_id="cf-abstention",
        ),
        CounterfactualSpec(
            question=CounterfactualQuestion.ALTERNATE_MODEL,
            parameters={"model_version": "model-v2"},
            scenario_id="cf-model",
        ),
        CounterfactualSpec(
            question=CounterfactualQuestion.ALTERNATE_REGIME,
            parameters={"regime": "volatile"},
            scenario_id="cf-regime",
        ),
    ]
    return tuple(
        run_counterfactual_replay(
            event_source=event_source,
            base_request=base_request,
            spec=spec,
        )
        for spec in specs
    )
