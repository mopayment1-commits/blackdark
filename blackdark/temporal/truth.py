"""Canonical Temporal truth contract — timestamp semantics and provenance (P0.1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Mapping


class TemporalSemanticField(str, Enum):
    """Non-interchangeable Temporal timestamp fields."""

    EVENT_TIME = "event_time"
    OBSERVED_TIME = "observed_time"
    AVAILABLE_AT = "available_at"
    INGESTED_AT = "ingested_at"
    EFFECTIVE_AT = "effective_at"
    REVISED_AT = "revised_at"


class TimestampProvenanceKind(str, Enum):
    """How a Temporal timestamp value was established."""

    DIRECT = "DIRECT"
    DERIVED = "DERIVED"
    UNKNOWN = "UNKNOWN"


# Registry / legacy row keys that alias available_at semantics (not interchangeable fields).
AVAILABLE_AT_FIELD_ALIASES: frozenset[str] = frozenset({"available_at", "available_time"})


def parse_temporal_instant(value: datetime | str) -> datetime:
    """Parse a deterministic Temporal instant; naive values are treated as UTC."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class TemporalTimestamp:
    """One Temporal timestamp with explicit semantics and provenance."""

    field: TemporalSemanticField
    provenance: TimestampProvenanceKind
    value: datetime | None = None
    derivation_basis: str | None = None

    def __post_init__(self) -> None:
        if self.provenance == TimestampProvenanceKind.UNKNOWN:
            if self.value is not None:
                raise ValueError("UNKNOWN Temporal timestamps must not carry a value")
            if self.derivation_basis is not None:
                raise ValueError("UNKNOWN Temporal timestamps must not carry derivation_basis")
        if self.provenance == TimestampProvenanceKind.DIRECT:
            if self.value is None:
                raise ValueError("DIRECT Temporal timestamps require a value")
            if self.derivation_basis is not None:
                raise ValueError("DIRECT Temporal timestamps must not carry derivation_basis")
        if self.provenance == TimestampProvenanceKind.DERIVED:
            if self.value is None:
                raise ValueError("DERIVED Temporal timestamps require a value")
            if not self.derivation_basis:
                raise ValueError("DERIVED Temporal timestamps require derivation_basis")

    @classmethod
    def direct(cls, field: TemporalSemanticField, value: datetime | str) -> TemporalTimestamp:
        return cls(
            field=field,
            provenance=TimestampProvenanceKind.DIRECT,
            value=parse_temporal_instant(value),
        )

    @classmethod
    def derived(
        cls,
        field: TemporalSemanticField,
        value: datetime | str,
        *,
        derivation_basis: str,
    ) -> TemporalTimestamp:
        return cls(
            field=field,
            provenance=TimestampProvenanceKind.DERIVED,
            value=parse_temporal_instant(value),
            derivation_basis=derivation_basis,
        )

    @classmethod
    def unknown(cls, field: TemporalSemanticField) -> TemporalTimestamp:
        return cls(field=field, provenance=TimestampProvenanceKind.UNKNOWN)

    def is_known(self) -> bool:
        """True when a concrete instant is established (DIRECT or DERIVED)."""
        return self.provenance != TimestampProvenanceKind.UNKNOWN and self.value is not None

    def to_metadata(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "field": self.field.value,
            "provenance": self.provenance.value,
            "known": self.is_known(),
        }
        if self.value is not None:
            payload["value"] = self.value.isoformat()
        if self.derivation_basis is not None:
            payload["derivation_basis"] = self.derivation_basis
        return payload


@dataclass(frozen=True, slots=True)
class TemporalObservation:
    """Datum-level Temporal truth bundle preserving non-interchangeable fields."""

    event_time: TemporalTimestamp
    observed_time: TemporalTimestamp
    available_at: TemporalTimestamp
    ingested_at: TemporalTimestamp
    effective_at: TemporalTimestamp
    revised_at: TemporalTimestamp

    @classmethod
    def create(
        cls,
        *,
        event_time: TemporalTimestamp,
        observed_time: TemporalTimestamp,
        available_at: TemporalTimestamp,
        ingested_at: TemporalTimestamp,
        effective_at: TemporalTimestamp,
        revised_at: TemporalTimestamp,
    ) -> TemporalObservation:
        _assert_field_match(event_time, TemporalSemanticField.EVENT_TIME)
        _assert_field_match(observed_time, TemporalSemanticField.OBSERVED_TIME)
        _assert_field_match(available_at, TemporalSemanticField.AVAILABLE_AT)
        _assert_field_match(ingested_at, TemporalSemanticField.INGESTED_AT)
        _assert_field_match(effective_at, TemporalSemanticField.EFFECTIVE_AT)
        _assert_field_match(revised_at, TemporalSemanticField.REVISED_AT)
        return cls(
            event_time=event_time,
            observed_time=observed_time,
            available_at=available_at,
            ingested_at=ingested_at,
            effective_at=effective_at,
            revised_at=revised_at,
        )

    @classmethod
    def from_explicit_fields(
        cls,
        fields: Mapping[TemporalSemanticField, TemporalTimestamp],
    ) -> TemporalObservation:
        missing = {f for f in TemporalSemanticField} - set(fields)
        if missing:
            raise ValueError(f"TemporalObservation requires all semantic fields; missing: {sorted(m.value for m in missing)}")
        return cls.create(
            event_time=fields[TemporalSemanticField.EVENT_TIME],
            observed_time=fields[TemporalSemanticField.OBSERVED_TIME],
            available_at=fields[TemporalSemanticField.AVAILABLE_AT],
            ingested_at=fields[TemporalSemanticField.INGESTED_AT],
            effective_at=fields[TemporalSemanticField.EFFECTIVE_AT],
            revised_at=fields[TemporalSemanticField.REVISED_AT],
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "event_time": self.event_time.to_metadata(),
            "observed_time": self.observed_time.to_metadata(),
            "available_at": self.available_at.to_metadata(),
            "ingested_at": self.ingested_at.to_metadata(),
            "effective_at": self.effective_at.to_metadata(),
            "revised_at": self.revised_at.to_metadata(),
        }


def _assert_field_match(timestamp: TemporalTimestamp, expected: TemporalSemanticField) -> None:
    if timestamp.field != expected:
        raise ValueError(f"Temporal field mismatch: expected {expected.value}, got {timestamp.field.value}")
