"""
Launch-57 canonical temporal primitives — isolated boundary owner.

Cross-cutting temporal consistency baseline (not a user capability).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, tzinfo
from enum import Enum
from time import monotonic
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError, available_timezones

RFC3339_Z_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(Z|[+-]\d{2}:\d{2})$"
)
LEAP_SECOND_MARK = re.compile(r"^(\d{4}-\d{2}-\d{2})T23:59:60")

DEFAULT_PROVIDER_FUTURE_SKEW_SEC = 120.0
DEFAULT_PROVIDER_PAST_SKEW_SEC = 86400.0 * 365 * 5
DEFAULT_HOST_CLOCK_SKEW_SEC = 30.0

TZDB_PACKAGE = "zoneinfo"


class AvailabilityState(str, Enum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"


class DstGapFoldPolicy(str, Enum):
    REJECT = "reject"
    SHIFT_NEXT_VALID = "shift_next_valid"
    FIRST_OCCURRENCE = "first_occurrence"
    SECOND_OCCURRENCE = "second_occurrence"


class LeapSecondPolicy(str, Enum):
    PRESERVE_RAW = "preserve_raw"
    NORMALIZE_TO_59 = "normalize_to_59"


class TimestampUnit(str, Enum):
    SECONDS = "s"
    MILLISECONDS = "ms"
    MICROSECONDS = "us"
    NANOSECONDS = "ns"


@dataclass(frozen=True)
class ProviderTimestampValidation:
    ok: bool
    canonical: datetime | None
    raw: Any
    unit: TimestampUnit | None
    error: str | None = None
    future_skew_sec: float | None = None
    past_skew_sec: float | None = None
    leap_second_normalized: bool = False


@dataclass(frozen=True)
class TemporalEnvelope:
    event_time: str | None = None
    source_time: str | None = None
    observed_time: str | None = None
    ingested_at: str | None = None
    processed_at: str | None = None
    available_at: str | None = None
    availability_state: AvailabilityState = AvailabilityState.UNKNOWN
    decision_time: str | None = None
    updated_at: str | None = None
    timestamp_unit: str | None = None
    timestamp_precision: str | None = None
    ordering_tie_break: str | None = None
    tzdb_version: str = TZDB_PACKAGE

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_time": self.event_time,
            "source_time": self.source_time,
            "observed_time": self.observed_time,
            "ingested_at": self.ingested_at,
            "processed_at": self.processed_at,
            "available_at": self.available_at,
            "availability_state": self.availability_state.value,
            "decision_time": self.decision_time,
            "updated_at": self.updated_at,
            "timestamp_unit": self.timestamp_unit,
            "timestamp_precision": self.timestamp_precision,
            "ordering_tie_break": self.ordering_tie_break,
            "tzdb_version": self.tzdb_version,
        }


def utc_now() -> datetime:
    return datetime.now(UTC)


def require_aware(dt: datetime, *, field_name: str = "timestamp") -> datetime:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(f"naive_datetime_rejected:{field_name}")
    return dt.astimezone(UTC)


def to_rfc3339(dt: datetime, *, timespec: str = "milliseconds") -> str:
    aware = require_aware(dt, field_name="serialize")
    text = aware.isoformat(timespec=timespec)
    if text.endswith("+00:00"):
        return text[:-6] + "Z"
    return text


def parse_rfc3339(value: str) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("empty_timestamp")
    if LEAP_SECOND_MARK.match(raw):
        raw = raw.replace("T23:59:60", "T23:59:59", 1)
    normalized = raw.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    return require_aware(dt, field_name="parse_rfc3339")


def infer_timestamp_unit(value: int | float) -> TimestampUnit:
    iv = int(value)
    if iv > 10_000_000_000_000_000:
        return TimestampUnit.NANOSECONDS
    if iv > 10_000_000_000_000:
        return TimestampUnit.MICROSECONDS
    if iv > 10_000_000_000:
        return TimestampUnit.MILLISECONDS
    return TimestampUnit.SECONDS


def epoch_to_utc(value: int | float, *, unit: TimestampUnit) -> datetime:
    if unit == TimestampUnit.MILLISECONDS:
        return datetime.fromtimestamp(value / 1000.0, tz=UTC)
    if unit == TimestampUnit.MICROSECONDS:
        return datetime.fromtimestamp(value / 1_000_000.0, tz=UTC)
    if unit == TimestampUnit.NANOSECONDS:
        return datetime.fromtimestamp(value / 1_000_000_000.0, tz=UTC)
    return datetime.fromtimestamp(float(value), tz=UTC)


def validate_provider_timestamp(
    raw: Any,
    *,
    unit: TimestampUnit | None = None,
    now: datetime | None = None,
    future_skew_sec: float = DEFAULT_PROVIDER_FUTURE_SKEW_SEC,
    past_skew_sec: float = DEFAULT_PROVIDER_PAST_SKEW_SEC,
    leap_policy: LeapSecondPolicy = LeapSecondPolicy.NORMALIZE_TO_59,
) -> ProviderTimestampValidation:
    if raw is None or raw == "":
        return ProviderTimestampValidation(False, None, raw, None, error="missing_timestamp")

    leap_normalized = False
    try:
        if isinstance(raw, datetime):
            canonical = require_aware(raw, field_name="provider")
            inferred_unit = None
        elif isinstance(raw, (int, float)):
            inferred_unit = unit or infer_timestamp_unit(raw)
            canonical = epoch_to_utc(raw, unit=inferred_unit)
        else:
            text = str(raw).strip()
            if LEAP_SECOND_MARK.match(text) and leap_policy == LeapSecondPolicy.NORMALIZE_TO_59:
                leap_normalized = True
            canonical = parse_rfc3339(text)
            inferred_unit = None
    except ValueError as exc:
        return ProviderTimestampValidation(False, None, raw, unit, error=str(exc))

    anchor = now or utc_now()
    delta = (canonical - anchor).total_seconds()
    if delta > future_skew_sec:
        return ProviderTimestampValidation(
            False,
            canonical,
            raw,
            unit or inferred_unit,
            error="future_timestamp",
            future_skew_sec=delta,
        )
    if delta < -past_skew_sec:
        return ProviderTimestampValidation(
            False,
            canonical,
            raw,
            unit or inferred_unit,
            error="excessive_past_timestamp",
            past_skew_sec=abs(delta),
        )
    return ProviderTimestampValidation(True, canonical, raw, unit or inferred_unit, leap_second_normalized=leap_normalized)


def resolve_available_at(
    *,
    source_time: datetime | None,
    observed_time: datetime | None,
    ingested_at: datetime | None,
    processed_at: datetime | None = None,
) -> tuple[str | None, AvailabilityState]:
    """Never fabricate availability from event/source time alone."""
    candidates: list[datetime] = []
    for dt in (observed_time, ingested_at, processed_at):
        if dt is not None:
            candidates.append(require_aware(dt, field_name="available_at_candidate"))
    if not candidates:
        return None, AvailabilityState.UNKNOWN
    earliest = min(candidates)
    if source_time is not None:
        st = require_aware(source_time, field_name="source_time")
        if earliest < st:
            return None, AvailabilityState.UNKNOWN
    return to_rfc3339(earliest), AvailabilityState.KNOWN


def deterministic_order_key(
    canonical_time: datetime | None,
    *,
    source_sequence: int | None = None,
    ingestion_sequence: int | None = None,
    immutable_event_id: str | None = None,
) -> tuple[Any, ...]:
    ts = to_rfc3339(canonical_time) if canonical_time is not None else ""
    return (
        ts,
        source_sequence if source_sequence is not None else -1,
        ingestion_sequence if ingestion_sequence is not None else -1,
        immutable_event_id or "",
    )


def sort_by_temporal_key(rows: Sequence[Mapping[str, Any]], *, time_field: str) -> list[dict[str, Any]]:
    def _key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        raw = row.get(time_field)
        dt = None
        if raw is not None:
            if isinstance(raw, (int, float)):
                unit = infer_timestamp_unit(raw)
                dt = epoch_to_utc(raw, unit=unit)
            else:
                dt = parse_rfc3339(str(raw))
        return deterministic_order_key(
            dt,
            source_sequence=row.get("source_sequence"),
            ingestion_sequence=row.get("ingestion_sequence"),
            immutable_event_id=str(row.get("immutable_event_id") or ""),
        )

    return [dict(r) for r in sorted(rows, key=_key)]


def resolve_user_timezone(
    *,
    request_override: str | None = None,
    account_preference: str | None = None,
    session_preference: str | None = None,
    browser_detected: str | None = None,
) -> tuple[str, str]:
    for candidate, source in (
        (request_override, "request_override"),
        (account_preference, "account_preference"),
        (session_preference, "session_preference"),
        (browser_detected, "browser_detected"),
    ):
        zone = _normalize_zone_id(candidate)
        if zone:
            return zone, source
    return "UTC", "utc_fallback"


def _normalize_zone_id(value: str | None) -> str | None:
    if not value:
        return None
    zone = str(value).strip()
    if not zone or zone.upper() == "UTC":
        return "UTC"
    if zone in available_timezones():
        return zone
    return None


def local_render_instant(canonical_utc: datetime, zone_id: str) -> str:
    """Render canonical UTC instant for display in zone_id without mutating storage form."""
    aware = require_aware(canonical_utc, field_name="local_render")
    try:
        zone: tzinfo = ZoneInfo(zone_id) if zone_id != "UTC" else UTC
    except ZoneInfoNotFoundError:
        zone = UTC
    local_dt = aware.astimezone(zone)
    text = local_dt.isoformat(timespec="milliseconds")
    if text.endswith("+00:00"):
        return text[:-6] + "Z"
    return text


def point_in_time_eligible(available_at: str | None, decision_time: str) -> bool:
    if not available_at:
        return False
    return parse_rfc3339(available_at) <= parse_rfc3339(decision_time)


class MonotonicTimer:
    def __init__(self) -> None:
        self._start = monotonic()

    def elapsed_sec(self) -> float:
        return monotonic() - self._start


def attach_temporal_envelope(payload: dict[str, Any], envelope: TemporalEnvelope) -> dict[str, Any]:
    out = dict(payload)
    out["temporal"] = envelope.as_dict()
    return out


def build_market_temporal_envelope(
    *,
    source_raw: Any = None,
    source_unit: TimestampUnit | None = None,
    observed_at: datetime | None = None,
    ingested_at: datetime | None = None,
    processed_at: datetime | None = None,
    source_sequence: int | None = None,
    ingestion_sequence: int | None = None,
    immutable_event_id: str | None = None,
) -> TemporalEnvelope:
    observed = observed_at or utc_now()
    ingested = ingested_at or observed
    processed = processed_at or ingested
    validation = validate_provider_timestamp(source_raw, unit=source_unit) if source_raw is not None else None
    source_dt = validation.canonical if validation and validation.ok else None
    event_dt = source_dt
    available_at, availability_state = resolve_available_at(
        source_time=source_dt,
        observed_time=observed,
        ingested_at=ingested,
        processed_at=processed,
    )
    unit = validation.unit.value if validation and validation.unit else None
    precision = "milliseconds" if unit in {TimestampUnit.MILLISECONDS.value, None} else unit
    tie = None
    if event_dt is not None:
        tie = str(
            deterministic_order_key(
                event_dt,
                source_sequence=source_sequence,
                ingestion_sequence=ingestion_sequence,
                immutable_event_id=immutable_event_id,
            )
        )
    return TemporalEnvelope(
        event_time=to_rfc3339(event_dt) if event_dt else None,
        source_time=to_rfc3339(source_dt) if source_dt else None,
        observed_time=to_rfc3339(observed),
        ingested_at=to_rfc3339(ingested),
        processed_at=to_rfc3339(processed),
        available_at=available_at,
        availability_state=availability_state,
        updated_at=to_rfc3339(processed),
        timestamp_unit=unit,
        timestamp_precision=precision,
        ordering_tie_break=tie,
    )


def classify_temporal_paths(batch_id: str, launch_numbers: Iterable[int]) -> dict[str, Any]:
    return {
        "batch_id": batch_id,
        "launch_numbers": list(launch_numbers),
        "temporal_owner": "launch57.temporal_common",
        "isolation_boundary": "launch57/*",
    }
