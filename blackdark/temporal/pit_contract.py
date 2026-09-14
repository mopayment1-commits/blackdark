"""PIT mandatory metadata contract enforcement (TEMP-PR-0010 / TEMP-AR-0016..0025)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from blackdark.temporal.event_contract import CanonicalTemporalEvent, ProvenanceMetadata
from blackdark.temporal.reconstruction import TemporalRecord
from blackdark.temporal.truth import TemporalObservation, TemporalSemanticField, TemporalTimestamp


MANDATORY_PROVENANCE_FIELDS = (
    "source",
    "source_version",
    "dataset_version",
    "rights_or_provenance",
)

MANDATORY_TEMPORAL_FIELDS = tuple(field.value for field in TemporalSemanticField)


class PitContractViolation(ValueError):
    """Fail-closed violation of mandatory PIT/provenance contract."""

    def __init__(self, code: str, message: str, *, missing_fields: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.code = code
        self.missing_fields = missing_fields


@dataclass(frozen=True, slots=True)
class PitContractValidationResult:
    valid: bool
    missing_temporal_fields: tuple[str, ...]
    missing_provenance_fields: tuple[str, ...]
    unknown_temporal_fields: tuple[str, ...]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "missing_temporal_fields": list(self.missing_temporal_fields),
            "missing_provenance_fields": list(self.missing_provenance_fields),
            "unknown_temporal_fields": list(self.unknown_temporal_fields),
        }


def _missing_temporal_fields(observation: TemporalObservation) -> tuple[str, ...]:
    missing: list[str] = []
    for field in TemporalSemanticField:
        ts = getattr(observation, field.value)
        if not isinstance(ts, TemporalTimestamp) or not ts.is_known():
            missing.append(field.value)
    return tuple(missing)


def _missing_provenance_fields(provenance: ProvenanceMetadata) -> tuple[str, ...]:
    missing: list[str] = []
    for name in MANDATORY_PROVENANCE_FIELDS:
        if not provenance.field_known(name):
            missing.append(name)
    return tuple(missing)


def validate_pit_contract(
    *,
    observation: TemporalObservation,
    provenance: ProvenanceMetadata,
    strict: bool = True,
) -> PitContractValidationResult:
    missing_temporal = _missing_temporal_fields(observation)
    missing_provenance = _missing_provenance_fields(provenance)
    valid = not missing_temporal and not missing_provenance
    result = PitContractValidationResult(
        valid=valid,
        missing_temporal_fields=missing_temporal,
        missing_provenance_fields=missing_provenance,
        unknown_temporal_fields=(),
    )
    if strict and not valid:
        missing = tuple(list(missing_temporal) + list(missing_provenance))
        raise PitContractViolation(
            "PIT_CONTRACT_INCOMPLETE",
            f"Mandatory PIT/provenance contract incomplete: {', '.join(missing)}",
            missing_fields=missing,
        )
    return result


def validate_canonical_event_contract(event: CanonicalTemporalEvent, *, strict: bool = True) -> PitContractValidationResult:
    return validate_pit_contract(
        observation=event.observation,
        provenance=event.provenance,
        strict=strict,
    )


def validate_temporal_record_contract(record: TemporalRecord, *, provenance: ProvenanceMetadata, strict: bool = True) -> PitContractValidationResult:
    return validate_pit_contract(
        observation=record.observation,
        provenance=provenance,
        strict=strict,
    )


def validate_ingestion_payload(
    payload: Mapping[str, Any],
    *,
    strict: bool = True,
) -> PitContractValidationResult:
    """Validate raw ingestion dict before normalization."""
    observation_raw = payload.get("observation") or {}
    provenance_raw = payload.get("provenance") or {}
    missing_temporal = [f for f in MANDATORY_TEMPORAL_FIELDS if not observation_raw.get(f)]
    missing_provenance = [f for f in MANDATORY_PROVENANCE_FIELDS if not provenance_raw.get(f)]
    valid = not missing_temporal and not missing_provenance
    result = PitContractValidationResult(
        valid=valid,
        missing_temporal_fields=tuple(missing_temporal),
        missing_provenance_fields=tuple(missing_provenance),
        unknown_temporal_fields=(),
    )
    if strict and not valid:
        missing = tuple(missing_temporal + missing_provenance)
        raise PitContractViolation(
            "INGESTION_PIT_CONTRACT_INCOMPLETE",
            f"Ingestion payload missing mandatory fields: {', '.join(missing)}",
            missing_fields=missing,
        )
    return result
