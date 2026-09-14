"""P1.3 remaining replay coverage: multi-scenario replay and cross-run comparability.

Reuses P1.2 deterministic mass replay and P1.3 decision-path replay without
introducing a second replay engine or temporal guard.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from blackdark.temporal.decision_path import (
    DECISION_PATH_STAGES,
    DecisionPathReplayResult,
    execute_historical_decision_path,
)
from blackdark.temporal.event_store import TemporalCanonicalEventStore
from blackdark.temporal.replay import (
    REPLAY_EVIDENCE_CLASS,
    ReplayRequest,
    ReplayResult,
    run_deterministic_mass_replay,
)

HISTORICAL_REPLAY = REPLAY_EVIDENCE_CLASS
REPLAY_COMPARISON_CAUSES_MODEL_PROMOTION = False

# TEMP-AR-0058 through TEMP-AR-0065 scenario dimensions
SCENARIO_DIMENSIONS = (
    "assets",
    "venues",
    "time_horizons",
    "historical_periods",
    "regimes",
    "model_versions",
    "thresholds",
    "source_availability",
)


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def compute_decision_path_fingerprint(result: DecisionPathReplayResult) -> str:
    return hashlib.sha256(_canonical_json(result.to_metadata()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReplayScenarioSpec:
    """Explicit multi-scenario replay contract (TEMP-AR-0058..0065)."""

    scenario_id: str
    parameters: Mapping[str, Any]
    time_window: Mapping[str, Any]
    input_identity_context: Mapping[str, Any]
    assets: tuple[str, ...] = ()
    venues: tuple[str, ...] = ()
    time_horizons: tuple[str, ...] = ()
    historical_periods: tuple[str, ...] = ()
    regimes: tuple[str, ...] = ()
    model_versions: tuple[str, ...] = ()
    thresholds: Mapping[str, Any] = field(default_factory=dict)
    source_availability: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReplayScenarioResult:
    scenario_id: str
    parameters: Mapping[str, Any]
    time_window: Mapping[str, Any]
    input_identity_context: Mapping[str, Any]
    result: Mapping[str, Any]
    rejections: tuple[str, ...]
    determinism_fingerprint: str
    evidence_class: str = HISTORICAL_REPLAY


@dataclass(frozen=True)
class MultiScenarioReplayResult:
    scenarios: tuple[ReplayScenarioResult, ...]
    cross_scenario_state_contamination: int = 0
    evidence_class: str = HISTORICAL_REPLAY


@dataclass(frozen=True)
class ReplayComparisonResult:
    comparable: bool
    reason_codes: tuple[str, ...]
    baseline_run_id: str
    challenger_run_id: str
    context_differences: tuple[str, ...]
    shared_context: Mapping[str, Any]
    comparison_outputs: Mapping[str, Any]
    evidence_class: str = HISTORICAL_REPLAY
    causes_model_promotion: bool = REPLAY_COMPARISON_CAUSES_MODEL_PROMOTION


def _build_replay_request(
    event_source: TemporalCanonicalEventStore,
    scenario: ReplayScenarioSpec,
) -> ReplayRequest:
    schedule = scenario.time_window.get("schedule")
    if schedule is None:
        schedule = [scenario.time_window.get("simulated_now", scenario.time_window["end"])]

    replay_params = dict(scenario.parameters)
    replay_params["scenario_id"] = scenario.scenario_id
    if scenario.assets:
        replay_params["assets"] = list(scenario.assets)
    if scenario.venues:
        replay_params["venues"] = list(scenario.venues)
    if scenario.time_horizons:
        replay_params["time_horizons"] = list(scenario.time_horizons)
    if scenario.historical_periods:
        replay_params["historical_periods"] = list(scenario.historical_periods)
    if scenario.regimes:
        replay_params["regimes"] = list(scenario.regimes)
    if scenario.thresholds:
        replay_params["thresholds"] = dict(scenario.thresholds)
        if "threshold" not in replay_params and "default" in scenario.thresholds:
            replay_params["threshold"] = scenario.thresholds["default"]
    if scenario.source_availability:
        replay_params["source_availability"] = dict(scenario.source_availability)

    version_context = dict(scenario.input_identity_context)
    version_context.update(scenario.source_availability)

    return ReplayRequest(
        event_source=event_source,
        start_time=scenario.time_window["start"],
        end_time=scenario.time_window["end"],
        replay_clock_or_schedule=schedule,
        strict_mode=bool(scenario.parameters.get("strict_mode", True)),
        replay_parameters=replay_params,
        dataset_or_source_version_context=version_context,
        chunk_size=scenario.parameters.get("chunk_size"),
    )


def _collect_rejections(
    mass_result: ReplayResult,
    decision_result: DecisionPathReplayResult,
) -> tuple[str, ...]:
    mass_rejections = {
        rejection.event_id or rejection.reason_code for rejection in mass_result.rejections
    }
    if not mass_result.success:
        mass_rejections.update(mass_result.failure_reasons)
    return tuple(sorted(mass_rejections))


def _scenario_fingerprint_payload(
    scenario: ReplayScenarioSpec,
    mass_result: ReplayResult,
    decision_result: DecisionPathReplayResult,
) -> Mapping[str, Any]:
    return {
        "scenario_id": scenario.scenario_id,
        "parameters": dict(scenario.parameters),
        "time_window": dict(scenario.time_window),
        "input_identity_context": dict(scenario.input_identity_context),
        "assets": list(scenario.assets),
        "venues": list(scenario.venues),
        "time_horizons": list(scenario.time_horizons),
        "historical_periods": list(scenario.historical_periods),
        "regimes": list(scenario.regimes),
        "model_versions": list(scenario.model_versions),
        "thresholds": dict(scenario.thresholds),
        "source_availability": dict(scenario.source_availability),
        "mass_replay_fingerprint": mass_result.determinism_fingerprint,
        "decision_path_fingerprint": compute_decision_path_fingerprint(decision_result),
        "mass_replay_metadata": mass_result.to_metadata(),
        "decision_path_metadata": decision_result.to_metadata(),
    }


def compute_scenario_determinism_fingerprint(
    scenario: ReplayScenarioSpec,
    mass_result: ReplayResult,
    decision_result: DecisionPathReplayResult,
) -> str:
    payload = _scenario_fingerprint_payload(scenario, mass_result, decision_result)
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def run_full_decision_path_replay(
    event_source: TemporalCanonicalEventStore,
    mass_request: ReplayRequest,
    *,
    parameters: Mapping[str, Any] | None = None,
    model_identity: str | None = None,
) -> DecisionPathReplayResult:
    """TEMP-AR-0057: full historical decision-path replay through existing path."""
    mass_result = run_deterministic_mass_replay(mass_request)
    return execute_historical_decision_path(
        event_source=event_source,
        mass_replay=mass_result,
        parameters=parameters or mass_request.replay_parameters,
        model_identity=model_identity,
    )


def _execute_isolated_scenario(
    event_source: TemporalCanonicalEventStore,
    scenario: ReplayScenarioSpec,
) -> ReplayScenarioResult:
    """Run one scenario in isolation without mutating shared replay state."""
    mass_request = _build_replay_request(event_source, scenario)
    mass_result = run_deterministic_mass_replay(mass_request)
    model_identity = (
        scenario.model_versions[0] if scenario.model_versions else None
    )
    decision_result = execute_historical_decision_path(
        event_source=event_source,
        mass_replay=mass_result,
        parameters=dict(scenario.parameters),
        model_identity=model_identity,
    )

    rejections = _collect_rejections(mass_result, decision_result)
    fingerprint = compute_scenario_determinism_fingerprint(
        scenario, mass_result, decision_result
    )

    result_payload = {
        "mass_replay": mass_result.to_metadata(),
        "decision_path": decision_result.to_metadata(),
        "scenario_dimensions": {
            dim: (
                list(getattr(scenario, dim))
                if dim not in ("thresholds", "source_availability")
                else dict(getattr(scenario, dim))
            )
            for dim in SCENARIO_DIMENSIONS
        },
    }

    return ReplayScenarioResult(
        scenario_id=scenario.scenario_id,
        parameters=dict(scenario.parameters),
        time_window=dict(scenario.time_window),
        input_identity_context=dict(scenario.input_identity_context),
        result=result_payload,
        rejections=rejections,
        determinism_fingerprint=fingerprint,
    )


def run_multi_scenario_replay(
    event_source: TemporalCanonicalEventStore,
    scenarios: Sequence[ReplayScenarioSpec],
) -> MultiScenarioReplayResult:
    """TEMP-AR-0058..0065: isolated multi-scenario replay without cross-contamination."""
    results: list[ReplayScenarioResult] = []
    contamination = 0

    for scenario in scenarios:
        result = _execute_isolated_scenario(event_source, scenario)
        for prior in results:
            if (
                prior.scenario_id != result.scenario_id
                and prior.determinism_fingerprint == result.determinism_fingerprint
                and prior.parameters != result.parameters
            ):
                contamination += 1
        results.append(result)

    return MultiScenarioReplayResult(
        scenarios=tuple(results),
        cross_scenario_state_contamination=contamination,
    )


def _comparison_context_from_result(result: Mapping[str, Any]) -> Mapping[str, Any]:
    mass = result.get("mass_replay", {})
    decision = result.get("decision_path", {})
    manifest = mass.get("replay_manifest", {})
    first_step = (decision.get("steps") or [{}])[0] if decision.get("steps") else {}
    stages = first_step.get("stages", {}) if isinstance(first_step, dict) else {}
    predictions = stages.get("prediction", {}) if isinstance(stages, dict) else {}
    model_identity = None
    if isinstance(predictions, dict) and predictions:
        first_prediction = next(iter(predictions.values()), {})
        if isinstance(first_prediction, dict):
            model_identity = first_prediction.get("model_identity")

    return {
        "replay_window": {
            "start": manifest.get("start_time"),
            "end": manifest.get("end_time"),
        },
        "input_identity_set": manifest.get("input_event_identity_set"),
        "source_dataset_versions": {
            "source_versions": manifest.get("source_versions"),
            "dataset_versions": manifest.get("dataset_versions"),
        },
        "model_engine_identity": model_identity or decision.get("model_identity"),
        "parameter_set": manifest.get("replay_parameters"),
        "evidence_class": mass.get("evidence_class", HISTORICAL_REPLAY),
        "temporal_semantics": manifest.get("simulated_time_sequence"),
        "scenario_identity": result.get("scenario_dimensions"),
        "determinism_fingerprint": mass.get("determinism_fingerprint"),
    }


def _normalize_parameter_set(parameters: Any) -> Any:
    if not isinstance(parameters, dict):
        return parameters
    return {key: value for key, value in parameters.items() if key != "scenario_id"}


def _normalize_scenario_identity(scenario_identity: Any) -> Any:
    if not isinstance(scenario_identity, dict):
        return scenario_identity
    normalized = dict(scenario_identity)
    normalized.pop("model_versions", None)
    return normalized


def compare_replay_runs(
    baseline: Mapping[str, Any],
    challenger: Mapping[str, Any],
    *,
    baseline_run_id: str,
    challenger_run_id: str,
    proven_context_keys: frozenset[str] | None = None,
    variable_context_keys: frozenset[str] | None = None,
) -> ReplayComparisonResult:
    """TEMP-AR-0071: cross-model / cross-run comparability with fail-closed semantics."""
    required_keys = frozenset(
        {
            "replay_window",
            "input_identity_set",
            "source_dataset_versions",
            "model_engine_identity",
            "parameter_set",
            "evidence_class",
            "temporal_semantics",
            "scenario_identity",
        }
    )
    proven = proven_context_keys if proven_context_keys is not None else required_keys
    variable = variable_context_keys or frozenset({"model_engine_identity"})

    baseline_ctx = _comparison_context_from_result(baseline)
    challenger_ctx = _comparison_context_from_result(challenger)

    context_differences: list[str] = []
    shared_context: dict[str, Any] = {}
    reason_codes: list[str] = []

    for key in sorted(required_keys):
        b_val = baseline_ctx.get(key)
        c_val = challenger_ctx.get(key)
        if key == "parameter_set":
            b_val = _normalize_parameter_set(b_val)
            c_val = _normalize_parameter_set(c_val)
        if key == "scenario_identity":
            b_val = _normalize_scenario_identity(b_val)
            c_val = _normalize_scenario_identity(c_val)
        if b_val is None or c_val is None:
            context_differences.append(f"missing_context:{key}")
            reason_codes.append("UNPROVEN_CONTEXT")
            continue
        if b_val != c_val:
            if key in variable:
                context_differences.append(f"variable:{key}")
            else:
                context_differences.append(f"divergent:{key}")
                reason_codes.append("CONTEXT_MISMATCH")
        elif key in proven:
            shared_context[key] = b_val

    if baseline_ctx.get("evidence_class") != HISTORICAL_REPLAY:
        reason_codes.append("BASELINE_NOT_HISTORICAL_REPLAY")
    if challenger_ctx.get("evidence_class") != HISTORICAL_REPLAY:
        reason_codes.append("CHALLENGER_NOT_HISTORICAL_REPLAY")

    unproven = [k for k in required_keys if k not in proven and k not in variable]
    if unproven:
        reason_codes.append("UNPROVEN_COMPARISON_CONTEXT")
        for key in unproven:
            context_differences.append(f"unproven:{key}")

    comparable = len(reason_codes) == 0

    comparison_outputs: dict[str, Any] = {}
    if comparable:
        comparison_outputs = {
            "baseline_fingerprint": baseline_ctx.get("determinism_fingerprint"),
            "challenger_fingerprint": challenger_ctx.get("determinism_fingerprint"),
            "fingerprints_match": (
                baseline_ctx.get("determinism_fingerprint")
                == challenger_ctx.get("determinism_fingerprint")
            ),
            "baseline_model_identity": baseline_ctx.get("model_engine_identity"),
            "challenger_model_identity": challenger_ctx.get("model_engine_identity"),
            "baseline_admitted_count": baseline.get("mass_replay", {}).get(
                "admitted_event_count", 0
            ),
            "challenger_admitted_count": challenger.get("mass_replay", {}).get(
                "admitted_event_count", 0
            ),
            "decision_path_stage_count": len(DECISION_PATH_STAGES),
        }

    return ReplayComparisonResult(
        comparable=comparable,
        reason_codes=tuple(sorted(set(reason_codes))),
        baseline_run_id=baseline_run_id,
        challenger_run_id=challenger_run_id,
        context_differences=tuple(context_differences),
        shared_context=shared_context,
        comparison_outputs=comparison_outputs,
    )
