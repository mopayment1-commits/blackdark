"""Canonical evidence taxonomy reconciliation — CAP646 + TEAS."""

from __future__ import annotations

import pytest

from blackdark.evidence_taxonomy import (
    EVIDENCE_TAXONOMY_VERSION,
    TemporalEvidenceClass,
    assert_cap646_promotion_allowed,
    assert_governed_cross_domain_promotion,
    assert_no_automatic_temporal_promotion,
    can_promote_cap646_evidence_class,
    can_promote_temporal_evidence_class,
    map_cap646_to_temporal,
    map_temporal_to_cap646,
    taxonomy_registry,
    validate_cap646_evidence_class,
    validate_temporal_evidence_class,
)
from blackdark.temporal.evidence_class import (
    TemporalEvidenceClass as FacadeTemporalEvidenceClass,
    assert_no_automatic_promotion,
    can_promote_evidence_class,
    from_cap646_evidence_class,
    to_cap646_evidence_class,
)
from cap646.evidence_class import (
    assert_promotion_allowed,
    from_temporal_evidence_class,
    infer_evidence_class,
    to_temporal_evidence_class,
)


def test_canonical_owner_registry_versioned() -> None:
    registry = taxonomy_registry()
    assert registry["version"] == EVIDENCE_TAXONOMY_VERSION
    assert registry["canonical_owner"] == "blackdark/evidence_taxonomy.py"
    assert len(registry["cap646_classes"]) == 4
    assert len(registry["temporal_classes"]) == 6


def test_cap646_to_temporal_mapping_deterministic() -> None:
    assert map_cap646_to_temporal("BACKTESTED") == TemporalEvidenceClass.HISTORICAL_BACKTEST.value
    assert (
        map_cap646_to_temporal("BACKTESTED", replay_hint=True)
        == TemporalEvidenceClass.HISTORICAL_REPLAY.value
    )
    assert map_cap646_to_temporal("SHADOW_LIVE_FORWARD") == TemporalEvidenceClass.FORWARD_SHADOW.value


def test_temporal_to_cap646_projection_lossy() -> None:
    assert map_temporal_to_cap646(TemporalEvidenceClass.HISTORICAL_REPLAY.value) == "BACKTESTED"
    assert map_temporal_to_cap646(TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value) == "PRODUCTION_VERIFIED"


def test_fail_closed_unknown_classes() -> None:
    with pytest.raises(ValueError, match="unknown cap646"):
        validate_cap646_evidence_class("NOT_A_CLASS")
    with pytest.raises(ValueError, match="unknown temporal"):
        validate_temporal_evidence_class("NOT_A_CLASS")


def test_cap646_promotion_rules_preserved() -> None:
    assert_promotion_allowed("SHADOW_LIVE_FORWARD", "PRODUCTION_VERIFIED")
    with pytest.raises(ValueError, match="evidence_promotion_denied"):
        assert_promotion_allowed("BACKTESTED", "PRODUCTION_VERIFIED")
    assert not can_promote_cap646_evidence_class("SIMULATED", "SHADOW_LIVE_FORWARD")


def test_temporal_promotion_rules_preserved() -> None:
    with pytest.raises(ValueError, match="automatic evidence class promotion forbidden"):
        assert_no_automatic_promotion(
            TemporalEvidenceClass.HISTORICAL_REPLAY.value,
            TemporalEvidenceClass.FORWARD_SHADOW.value,
        )
    with pytest.raises(ValueError, match="automatic evidence class promotion forbidden"):
        assert_no_automatic_temporal_promotion(
            TemporalEvidenceClass.FORWARD_SHADOW.value,
            TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
        )
    assert not can_promote_evidence_class("HISTORICAL_REPLAY", "FORWARD_SHADOW")
    assert can_promote_evidence_class("HISTORICAL_REPLAY", "HISTORICAL_REPLAY")


def test_cross_domain_promotion_requires_governing_gate() -> None:
    with pytest.raises(ValueError, match="cross_domain_evidence_promotion_denied"):
        assert_governed_cross_domain_promotion(
            "cap646",
            "BACKTESTED",
            "temporal",
            TemporalEvidenceClass.FORWARD_SHADOW.value,
            governing_gate=None,
        )
    assert_governed_cross_domain_promotion(
        "cap646",
        "BACKTESTED",
        "temporal",
        TemporalEvidenceClass.HISTORICAL_BACKTEST.value,
        governing_gate="TEMPORAL_EVIDENCE_LEDGER_ADMISSION",
    )


def test_facade_delegates_to_canonical_adapter() -> None:
    assert to_temporal_evidence_class("BACKTESTED", source="market_replay_v1") == "HISTORICAL_REPLAY"
    assert from_temporal_evidence_class(TemporalEvidenceClass.FORWARD_SHADOW.value) == "SHADOW_LIVE_FORWARD"
    assert from_cap646_evidence_class("SIMULATED") == "SIMULATED"
    assert to_cap646_evidence_class(TemporalEvidenceClass.VERIFIED_PRODUCTION.value) == "PRODUCTION_VERIFIED"
    assert FacadeTemporalEvidenceClass.HISTORICAL_REPLAY.value == "HISTORICAL_REPLAY"


def test_cap646_infer_behavior_unchanged() -> None:
    assert infer_evidence_class(source="market_replay_v1") == "BACKTESTED"
    assert infer_evidence_class(source="paper") == "SIMULATED"
    assert infer_evidence_class(env_production=True) == "PRODUCTION_VERIFIED"
