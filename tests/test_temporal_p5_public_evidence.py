"""P5 Public Evidence tests — TEMP-AR-0262..0280."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from blackdark.temporal.dependence_aware_sampling import DependenceAwareSampler, dependence_cluster_key
from blackdark.temporal.evidence_class import TemporalEvidenceClass, assert_no_automatic_promotion
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger
from blackdark.temporal.outcome_contract import OUTCOME_EVALUATOR_IDENTITY
from blackdark.temporal.public_evidence import (
    PUBLIC_LEDGER_MATURITY_REQUIRED,
    assert_public_claim_maturity,
    build_public_disclosure_from_ledger,
    public_surface_cannot_reclassify,
    validate_public_evidence_controls,
)

T_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _ledger_with_record(*, evidence_class: str = TemporalEvidenceClass.HISTORICAL_REPLAY.value) -> EvidenceProvenanceLedger:
    ledger = EvidenceProvenanceLedger()
    ledger.record_evidence(
        evidence_class=evidence_class,
        producer="test",
        source_provenance={"provenance_reference": "prov-1"},
        temporal_context={"available_at": T_NOW.isoformat()},
        versions={"model_version": "m1"},
        lineage=("line-1",),
        quality_state={"label_confidence": 0.85},
        limitations=("synthetic excluded",),
        methodology="walk-forward historical replay",
        timestamps={"recorded_at": T_NOW.isoformat()},
        evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
        payload={},
    )
    return ledger


def test_temp_ar_0262_public_ledger_maturity_required() -> None:
    assert PUBLIC_LEDGER_MATURITY_REQUIRED is True
    with pytest.raises(ValueError, match="not_mature"):
        assert_public_claim_maturity(maturity_sufficient=False, evidence_mature=True)


def test_temp_ar_0263_evidence_class_disclosed() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-1",
        ledger=_ledger_with_record(),
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.evidence_class == TemporalEvidenceClass.HISTORICAL_REPLAY.value


def test_temp_ar_0264_date_range_disclosed() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-2",
        ledger=_ledger_with_record(),
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.date_range_start is not None


def test_temp_ar_0265_sample_size_disclosed() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-3",
        ledger=_ledger_with_record(),
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.sample_size >= 1


def test_temp_ar_0266_effective_independent_count() -> None:
    sampler = DependenceAwareSampler()
    dims = {"temporal_overlap": True}
    cluster = dependence_cluster_key(event_family="fam-1", dimensions=dims)
    for i in range(3):
        sampler.record_instance(
            case_id=f"c-{i}",
            event_family="fam-1",
            dependence_cluster=cluster,
            dimensions=dims,
            overlap_factor=2.0,
        )
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-4",
        ledger=_ledger_with_record(),
        sampler=sampler,
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.effective_independent_count < disclosure.sample_size or disclosure.sample_size == 1


def test_temp_ar_0267_regime_distribution() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-5",
        ledger=_ledger_with_record(),
        regime_distribution={"bull": 0.6, "bear": 0.4},
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.regime_distribution["bull"] == 0.6


def test_temp_ar_0268_asset_universe() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-6",
        ledger=_ledger_with_record(),
        asset_universe=("BTC", "ETH"),
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert "BTC" in disclosure.asset_universe


def test_temp_ar_0269_evaluation_horizon() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-7",
        ledger=_ledger_with_record(),
        evaluation_horizon="24h",
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.evaluation_horizon == "24h"


def test_temp_ar_0270_model_version() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-8",
        ledger=_ledger_with_record(),
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.model_version == "m1"


def test_temp_ar_0271_abstentions() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-9",
        ledger=_ledger_with_record(),
        abstention_count=5,
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.abstention_count == 5


def test_temp_ar_0272_methodology() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-10",
        ledger=_ledger_with_record(),
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.methodology


def test_temp_ar_0273_uncertainty() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-11",
        ledger=_ledger_with_record(),
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.uncertainty_statement


def test_temp_ar_0274_exclusions() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-12",
        ledger=_ledger_with_record(),
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.exclusions


def test_temp_ar_0275_limitations() -> None:
    disclosure = build_public_disclosure_from_ledger(
        claim_id="claim-13",
        ledger=_ledger_with_record(),
        maturity_sufficient=True,
        freshness_timestamp=T_NOW,
    )
    assert disclosure.limitations


def test_temp_ar_0276_cherry_picking_control() -> None:
    ledger = _ledger_with_record()
    controls = validate_public_evidence_controls(
        records=ledger.list_records(),
        claimed_date_start=T_NOW,
        claimed_date_end=T_NOW,
    )
    assert controls.cherry_picking_blocked is True


def test_temp_ar_0277_survivorship_bias_disclosed() -> None:
    controls = validate_public_evidence_controls(
        records=_ledger_with_record().list_records(),
        claimed_date_start=T_NOW,
        claimed_date_end=T_NOW,
    )
    assert controls.survivorship_bias_disclosed is True


def test_temp_ar_0278_retroactive_deletion_blocked() -> None:
    controls = validate_public_evidence_controls(
        records=_ledger_with_record().list_records(),
        claimed_date_start=T_NOW,
        claimed_date_end=T_NOW,
        deleted_evidence_ids=("ev-deleted",),
    )
    assert controls.retroactive_deletion_blocked is False


def test_temp_ar_0279_selective_date_window_blocked() -> None:
    controls = validate_public_evidence_controls(
        records=_ledger_with_record().list_records(),
        claimed_date_start=T_NOW.replace(year=2027),
        claimed_date_end=T_NOW,
    )
    assert controls.selective_date_window_blocked is False


def test_temp_ar_0280_mixed_evidence_classes_blocked() -> None:
    ledger = EvidenceProvenanceLedger()
    for cls in (
        TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        TemporalEvidenceClass.SIMULATED.value,
    ):
        ledger.record_evidence(
            evidence_class=cls,
            producer="test",
            source_provenance={},
            temporal_context={},
            versions={},
            lineage=(),
            quality_state={},
            limitations=(),
            methodology="test",
            timestamps={"recorded_at": T_NOW.isoformat()},
            evaluator_identity=OUTCOME_EVALUATOR_IDENTITY,
            payload={},
        )
    with pytest.raises(ValueError, match="mixed evidence classes"):
        build_public_disclosure_from_ledger(
            claim_id="mixed",
            ledger=ledger,
            maturity_sufficient=True,
            freshness_timestamp=T_NOW,
        )


def test_public_surface_cannot_reclassify() -> None:
    with pytest.raises(ValueError):
        public_surface_cannot_reclassify(
            TemporalEvidenceClass.HISTORICAL_REPLAY.value,
            TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
        )
    assert_no_automatic_promotion(
        TemporalEvidenceClass.HISTORICAL_REPLAY.value,
        TemporalEvidenceClass.HISTORICAL_REPLAY.value,
    )
