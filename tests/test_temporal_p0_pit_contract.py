"""TEAS-REQ-010 PIT mandatory metadata contract tests."""

from __future__ import annotations

import pytest

from blackdark.temporal.event_contract import ProvenanceMetadata
from blackdark.temporal.pit_contract import PitContractViolation, validate_ingestion_payload, validate_pit_contract
from blackdark.temporal.truth import TemporalObservation, TemporalSemanticField, TemporalTimestamp


def _full_observation() -> TemporalObservation:
    def direct(field: TemporalSemanticField, value: str) -> TemporalTimestamp:
        return TemporalTimestamp.direct(field, value)

    return TemporalObservation.create(
        event_time=direct(TemporalSemanticField.EVENT_TIME, "2026-01-01T00:00:00Z"),
        observed_time=direct(TemporalSemanticField.OBSERVED_TIME, "2026-01-01T00:00:01Z"),
        available_at=direct(TemporalSemanticField.AVAILABLE_AT, "2026-01-01T00:00:02Z"),
        ingested_at=direct(TemporalSemanticField.INGESTED_AT, "2026-01-01T00:00:03Z"),
        effective_at=direct(TemporalSemanticField.EFFECTIVE_AT, "2026-01-01T00:00:00Z"),
        revised_at=direct(TemporalSemanticField.REVISED_AT, "2026-01-01T00:00:03Z"),
    )


def _full_provenance() -> ProvenanceMetadata:
    return ProvenanceMetadata(
        source="binance",
        source_version="v1",
        dataset_version="ds-1",
        rights_or_provenance={"permitted_purpose": "historical_evaluation"},
    )


def test_validate_pit_contract_accepts_complete_metadata() -> None:
    result = validate_pit_contract(
        observation=_full_observation(),
        provenance=_full_provenance(),
        strict=True,
    )
    assert result.valid is True


def test_validate_pit_contract_rejects_missing_source() -> None:
    provenance = ProvenanceMetadata(
        source=None,
        source_version="v1",
        dataset_version="ds-1",
        rights_or_provenance={"permitted_purpose": "historical_evaluation"},
    )
    with pytest.raises(PitContractViolation) as exc:
        validate_pit_contract(observation=_full_observation(), provenance=provenance, strict=True)
    assert "source" in exc.value.missing_fields


def test_validate_pit_contract_rejects_missing_dataset_version() -> None:
    provenance = ProvenanceMetadata(
        source="binance",
        source_version="v1",
        dataset_version=None,
        rights_or_provenance={"permitted_purpose": "historical_evaluation"},
    )
    with pytest.raises(PitContractViolation) as exc:
        validate_pit_contract(observation=_full_observation(), provenance=provenance, strict=True)
    assert "dataset_version" in exc.value.missing_fields


def test_validate_pit_contract_rejects_missing_rights() -> None:
    provenance = ProvenanceMetadata(
        source="binance",
        source_version="v1",
        dataset_version="ds-1",
        rights_or_provenance=None,
    )
    with pytest.raises(PitContractViolation) as exc:
        validate_pit_contract(observation=_full_observation(), provenance=provenance, strict=True)
    assert "rights_or_provenance" in exc.value.missing_fields


def test_validate_ingestion_payload_rejects_incomplete_observation() -> None:
    payload = {
        "entity_key": "BTCUSDT",
        "event_type": "market_tick",
        "observation": {"event_time": "2026-01-01T00:00:00Z"},
        "provenance": {
            "source": "binance",
            "source_version": "v1",
            "dataset_version": "ds-1",
            "rights_or_provenance": {"permitted_purpose": "historical_evaluation"},
        },
    }
    with pytest.raises(PitContractViolation):
        validate_ingestion_payload(payload, strict=True)
