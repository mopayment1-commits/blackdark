"""Focused P4 Champion/Challenger evaluation tests — TEMP-AR-0230..0232."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from blackdark.temporal.champion_challenger import (
    CHALLENGER_AUTO_PROMOTION,
    CHALLENGER_EVIDENCE_CLASS_COLLAPSE,
    CHAMPION_AUTO_REPLACEMENT,
    CHAMPION_CHALLENGER_EVALUATION_DETERMINISTIC,
    INSUFFICIENT_EVIDENCE_FORCES_WINNER,
    PRODUCTION_MODEL_MUTATION,
    UNPROVEN_CHAMPION_CHALLENGER_COMPARISON_FAILS_CLOSED,
    ChampionChallengerComparisonContext,
    ChampionChallengerEvaluator,
    ComparisonStatus,
    PromotionRecommendation,
    champion_challenger_preserves_evidence_lineage,
    promotion_pipeline_stages,
)
from blackdark.temporal.evidence_class import TemporalEvidenceClass
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.forward_shadow import ForwardShadowLedger
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY, OutcomeContract, OutcomeLabelStatus
from blackdark.temporal.p4_champion_challenger_registry import P4_CHAMPION_CHALLENGER_ATOMIC_REQUIREMENT_IDS
from blackdark.temporal.replay_coverage import ReplayScenarioSpec, run_multi_scenario_replay
from tests.test_temporal_p1_3_remaining_replay_coverage import (
    T_END,
    T_MID,
    T_SCHEDULE_LATE,
    _base_store,
    _scenario,
)

T_ISSUED = datetime(2024, 9, 1, 10, 0, 0, tzinfo=UTC)
T_EVAL_END = datetime(2024, 9, 1, 14, 0, 0, tzinfo=UTC)
PROV = "prov-ref-1"

_PROVEN_KEYS = frozenset(
    {
        "replay_window",
        "input_identity_set",
        "source_dataset_versions",
        "parameter_set",
        "evidence_class",
        "temporal_semantics",
        "scenario_identity",
    }
)


def _outcome(**kwargs) -> OutcomeContract:
    defaults = {
        "outcome_id": "outcome-1",
        "subject_identity": "asset-a",
        "prediction_identity": "model-v1",
        "decision_identity": "asset-a:act",
        "target_definition": "directional",
        "evaluation_horizon": "1h",
        "outcome_timestamp": T_ISSUED,
        "realized_result": 100.0,
        "benchmark_result": 99.0,
        "confidence": 0.9,
        "calibration_error": 0.1,
        "directional_correctness": True,
        "magnitude_error": 0.1,
        "regret": 0.0,
        "favorable_excursion": 1.0,
        "adverse_excursion": 0.0,
        "drawdown": None,
        "false_positive_cost": None,
        "false_negative_cost": None,
        "abstention_quality": "evaluated",
        "market_regime": "bull",
        "evaluator_version": OUTCOME_EVALUATOR_IDENTITY,
        "label_status": OutcomeLabelStatus.VERIFIED,
    }
    defaults.update(kwargs)
    return OutcomeContract(**defaults)


def _context(**kwargs) -> ChampionChallengerComparisonContext:
    defaults = {
        "champion_identity": "champion-model-v1",
        "challenger_identity": "challenger-model-v2",
        "model_or_engine_versions": {"champion": "model-v1", "challenger": "model-v2"},
        "evaluation_window": {"start": T_ISSUED.isoformat(), "end": T_EVAL_END.isoformat()},
        "input_identity_context": {"dataset_version": "ds-1"},
        "dataset_or_source_versions": {"dataset_version": "ds-1"},
        "parameters": {"threshold": 0.5},
        "champion_evidence_class": TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        "challenger_evidence_class": TemporalEvidenceClass.HISTORICAL_REPLAY.value,
    }
    defaults.update(kwargs)
    return ChampionChallengerComparisonContext(**defaults)


def _replay_pair():
    store = _base_store()
    baseline = run_multi_scenario_replay(
        store, [_scenario("shared-scenario", model_version="model-v1", threshold=0.5)]
    ).scenarios[0]
    challenger = run_multi_scenario_replay(
        store, [_scenario("shared-scenario", model_version="model-v2", threshold=0.5)]
    ).scenarios[0]
    return baseline.result, challenger.result


def _evidence(ledger: EvidenceProvenanceLedger, evidence_class: str):
    return ledger.record_evidence(
        evidence_class=evidence_class,
        producer="test",
        source_provenance={"provenance_reference": PROV},
        temporal_context={},
        versions={"model_version": "model-v1"},
        lineage=("line-1",),
        quality_state={"outcome_quality": "direct_observed", "label_confidence": 0.95},
        limitations=(),
        methodology="test",
        timestamps={"recorded_at": T_ISSUED.isoformat()},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )


def test_selected_atomic_requirement_ids() -> None:
    assert P4_CHAMPION_CHALLENGER_ATOMIC_REQUIREMENT_IDS == (
        "TEMP-AR-0230",
        "TEMP-AR-0231",
        "TEMP-AR-0232",
    )
    assert promotion_pipeline_stages()[0] == "outcome"
    assert promotion_pipeline_stages()[-1] == "champion"


def test_comparable_inputs_evaluate_deterministically() -> None:
    evaluator = ChampionChallengerEvaluator(current_champion_identity="champion-model-v1")
    baseline, challenger = _replay_pair()
    kwargs = {
        "context": _context(),
        "outcome": _outcome(),
        "baseline_replay_result": baseline,
        "challenger_replay_result": challenger,
        "proven_replay_context_keys": _PROVEN_KEYS,
    }
    first = evaluator.evaluate(**kwargs)
    second = evaluator.evaluate(**kwargs)
    assert first.to_metadata() == second.to_metadata()
    assert CHAMPION_CHALLENGER_EVALUATION_DETERMINISTIC is True


def test_mismatched_context_fails_closed() -> None:
    evaluator = ChampionChallengerEvaluator()
    store = _base_store()
    baseline = run_multi_scenario_replay(store, [_scenario("baseline")]).scenarios[0]
    challenger_spec = _scenario("challenger")
    challenger_spec = ReplayScenarioSpec(
        scenario_id=challenger_spec.scenario_id,
        parameters=challenger_spec.parameters,
        time_window={
            "start": T_MID.isoformat(),
            "end": T_END.isoformat(),
            "schedule": [T_SCHEDULE_LATE.isoformat()],
        },
        input_identity_context={"dataset_version": "ds-9"},
        assets=challenger_spec.assets,
        venues=challenger_spec.venues,
        time_horizons=challenger_spec.time_horizons,
        historical_periods=challenger_spec.historical_periods,
        regimes=challenger_spec.regimes,
        model_versions=challenger_spec.model_versions,
        thresholds=challenger_spec.thresholds,
        source_availability=challenger_spec.source_availability,
    )
    challenger = run_multi_scenario_replay(store, [challenger_spec]).scenarios[0]
    result = evaluator.evaluate(
        _context(),
        baseline_replay_result=baseline.result,
        challenger_replay_result=challenger.result,
    )
    assert UNPROVEN_CHAMPION_CHALLENGER_COMPARISON_FAILS_CLOSED is True
    assert result.comparison_status == ComparisonStatus.REJECTED.value
    assert "CONTEXT_MISMATCH" in result.reason_codes


def test_insufficient_evidence_does_not_force_winner() -> None:
    evaluator = ChampionChallengerEvaluator()
    result = evaluator.evaluate(_context())
    assert INSUFFICIENT_EVIDENCE_FORCES_WINNER is False
    assert result.comparison_status == ComparisonStatus.INCONCLUSIVE.value
    assert "winner" not in result.comparison_metrics
    assert result.promotion_recommendation == PromotionRecommendation.NONE.value


def test_historical_replay_remains_historical_replay() -> None:
    evaluator = ChampionChallengerEvaluator()
    baseline, challenger = _replay_pair()
    result = evaluator.evaluate(
        _context(),
        baseline_replay_result=baseline,
        challenger_replay_result=challenger,
        proven_replay_context_keys=_PROVEN_KEYS,
        outcome=_outcome(),
    )
    assert result.champion_evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value
    assert result.challenger_evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value
    assert result.replay_comparison is not None
    assert result.replay_comparison["evidence_class"] == TemporalEvidenceClass.HISTORICAL_REPLAY.value
    assert CHALLENGER_EVIDENCE_CLASS_COLLAPSE == 0


def test_forward_shadow_remains_forward_shadow() -> None:
    ledger = ForwardShadowLedger()
    receipt = ledger.create_pre_outcome_receipt(
        subject_identity="asset-a",
        input_identity="input-1",
        decision_or_prediction_identity="pred-1",
        model_version="model-v2",
        rule_config_version="rule-v1",
        dataset_version="ds-1",
        code_version="code-v1",
        input_snapshot_hash="hash",
        prediction={"direction": "up"},
        confidence=0.8,
        abstention_state="act",
        issued_at=T_ISSUED,
        temporal_context={},
        source_or_dataset_context={},
    )
    evaluator = ChampionChallengerEvaluator()
    baseline, challenger = _replay_pair()
    result = evaluator.evaluate(
        _context(
            challenger_evidence_class=TemporalEvidenceClass.FORWARD_SHADOW.value,
        ),
        baseline_replay_result=baseline,
        challenger_replay_result=challenger,
        proven_replay_context_keys=_PROVEN_KEYS,
        forward_shadow_receipt=receipt,
        outcome=_outcome(),
        stability_review_passed=True,
    )
    assert result.challenger_evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value
    assert receipt.evidence_class == TemporalEvidenceClass.FORWARD_SHADOW.value


def test_evaluation_does_not_auto_promote_challenger() -> None:
    evaluator = ChampionChallengerEvaluator(current_champion_identity="champion-model-v1")
    baseline, challenger = _replay_pair()
    result = evaluator.evaluate(
        _context(),
        baseline_replay_result=baseline,
        challenger_replay_result=challenger,
        proven_replay_context_keys=_PROVEN_KEYS,
        outcome=_outcome(),
        stability_review_passed=True,
    )
    assert CHALLENGER_AUTO_PROMOTION == 0
    assert evaluator.current_champion_identity == "champion-model-v1"
    with pytest.raises(ValueError, match="challenger_auto_promotion"):
        evaluator.attempt_auto_promote_challenger(result)


def test_evaluation_does_not_replace_champion() -> None:
    evaluator = ChampionChallengerEvaluator(current_champion_identity="champion-model-v1")
    result = evaluator.evaluate(_context())
    assert CHAMPION_AUTO_REPLACEMENT == 0
    with pytest.raises(ValueError, match="champion_auto_replacement"):
        evaluator.attempt_replace_champion(result)


def test_evaluation_does_not_mutate_production_model() -> None:
    evaluator = ChampionChallengerEvaluator()
    result = evaluator.evaluate(_context())
    assert PRODUCTION_MODEL_MUTATION == 0
    with pytest.raises(ValueError, match="production_model_mutation"):
        evaluator.attempt_production_model_mutation(result)


def test_outcome_quality_and_provenance_preserved() -> None:
    evaluator = ChampionChallengerEvaluator()
    ledger = EvidenceProvenanceLedger()
    champion_record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    challenger_record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    baseline, challenger = _replay_pair()
    result = evaluator.evaluate(
        _context(),
        outcome=_outcome(),
        champion_evidence=champion_record,
        challenger_evidence=challenger_record,
        baseline_replay_result=baseline,
        challenger_replay_result=challenger,
        proven_replay_context_keys=_PROVEN_KEYS,
    )
    assert result.outcome_quality is not None
    assert result.outcome_quality["equivalent_to_direct_truth"] is True
    assert champion_record.evidence_class in result.evidence_lineage or "line-1" in result.evidence_lineage


def test_historical_replay_superiority_not_production_superiority() -> None:
    evaluator = ChampionChallengerEvaluator()
    baseline, challenger = _replay_pair()
    result = evaluator.evaluate(
        _context(),
        baseline_replay_result=baseline,
        challenger_replay_result=challenger,
        proven_replay_context_keys=_PROVEN_KEYS,
        outcome=_outcome(),
    )
    if result.comparison_metrics.get("fingerprints_match") is False:
        assert result.comparison_status == ComparisonStatus.INCONCLUSIVE.value
        assert "HISTORICAL_REPLAY_NOT_PRODUCTION_SUPERIORITY" in result.reason_codes
        assert result.promotion_recommendation != PromotionRecommendation.REVIEW_REQUIRED.value


def test_p2_evidence_lineage_remains_intact() -> None:
    evaluator = ChampionChallengerEvaluator()
    ledger = EvidenceProvenanceLedger()
    champion_record = _evidence(ledger, TemporalEvidenceClass.HISTORICAL_REPLAY.value)
    before = tuple(r.to_metadata() for r in ledger.list_records())
    baseline, challenger = _replay_pair()
    evaluator.evaluate(
        _context(),
        champion_evidence=champion_record,
        baseline_replay_result=baseline,
        challenger_replay_result=challenger,
        proven_replay_context_keys=_PROVEN_KEYS,
        outcome=_outcome(),
    )
    assert champion_challenger_preserves_evidence_lineage(ledger, before_snapshot=before)
