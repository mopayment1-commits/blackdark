"""
Launch-57 canonical infrastructure temporal owner for B14 (SPEC §23–§27).

API serialization, database storage semantics, clock discipline, DST/scheduling.
Delegates primitives to launch57.temporal_common — no competing truth path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from enum import Enum
from time import monotonic
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from launch57.temporal_common import (
    DEFAULT_HOST_CLOCK_SKEW_SEC,
    DstGapFoldPolicy,
    MonotonicTimer,
    TimestampUnit,
    infer_timestamp_unit,
    parse_rfc3339,
    require_aware,
    to_rfc3339,
    utc_now,
)

METHODOLOGY_VERSION = "launch57-infrastructure-temporal-common-1.0"
API_TIMESTAMP_FIELDS: frozenset[str] = frozenset(
    {
        "event_time",
        "source_time",
        "observed_time",
        "ingested_at",
        "processed_at",
        "available_at",
        "decision_time",
        "outcome_time",
        "updated_at",
        "timestamp",
        "issued_at",
        "last_update_time",
        "canonical_open_time",
    }
)
LOCAL_TIMESTAMP_RE = __import__("re").compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$"
)


class ClockContext(str, Enum):
    OPPORTUNITY_FRESHNESS = "opportunity_freshness"
    AUTH_TOKEN = "auth_token"
    AUDIT_DISPLAY = "audit_display"
    DEFAULT = "default"


DEFAULT_SKEW_BUDGET_SEC: dict[ClockContext, float] = {
    ClockContext.OPPORTUNITY_FRESHNESS: 5.0,
    ClockContext.AUTH_TOKEN: 60.0,
    ClockContext.AUDIT_DISPLAY: 30.0,
    ClockContext.DEFAULT: DEFAULT_HOST_CLOCK_SKEW_SEC,
}


class LocalCivilState(str, Enum):
    VALID = "valid"
    NONEXISTENT = "nonexistent"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class ApiTimestampContract:
    epoch: int | float
    unit: TimestampUnit
    signedness: str = "signed"
    precision: str = "as_provided"
    leap_second_policy: str = "normalize_to_59"


@dataclass(frozen=True)
class ApiSerializationResult:
    ok: bool
    serialized: str | None = None
    error: str | None = None
    contract: ApiTimestampContract | None = None


@dataclass(frozen=True)
class DbInstantRecord:
    instant_utc: str
    storage_type: str = "timestamptz"
    comparison_semantics: str = "utc_normalized"


@dataclass(frozen=True)
class DbCivilTimeIntent:
    local_wall_time: str
    iana_zone: str
    recurrence_rule: str | None = None
    dst_policy: str = DstGapFoldPolicy.REJECT.value
    migration_assumed_zone: str | None = None


@dataclass(frozen=True)
class ClockHealthSnapshot:
    synchronized: bool
    estimated_offset_sec: float
    last_synchronization: str | None
    clock_step_detected: bool
    drift_alert_threshold_sec: float
    skew_budget_sec: float
    context: str
    within_budget: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "synchronized": self.synchronized,
            "estimated_offset_sec": self.estimated_offset_sec,
            "last_synchronization": self.last_synchronization,
            "clock_step_detected": self.clock_step_detected,
            "drift_alert_threshold_sec": self.drift_alert_threshold_sec,
            "skew_budget_sec": self.skew_budget_sec,
            "context": self.context,
            "within_budget": self.within_budget,
        }


@dataclass(frozen=True)
class ScheduleIntent:
    local_wall_time: str
    iana_zone: str
    recurrence_rule: str | None = None
    dst_policy: DstGapFoldPolicy = DstGapFoldPolicy.REJECT


@dataclass(frozen=True)
class ResolvedLocalCivilTime:
    ok: bool
    instant_utc: str | None = None
    state: LocalCivilState | None = None
    policy_applied: str | None = None
    error: str | None = None
    dst_adjustment_explanation: str | None = None


@dataclass(frozen=True)
class InfrastructureTemporalContext:
    api_serialization_policy: str
    db_storage_policy: str
    clock_discipline_policy: str
    dst_policy: str
    scheduling_policy: str
    violations: tuple[str, ...] = field(default_factory=tuple)
    infrastructure_temporally_consistent: bool = True
    expired_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "api_serialization_policy": self.api_serialization_policy,
            "db_storage_policy": self.db_storage_policy,
            "clock_discipline_policy": self.clock_discipline_policy,
            "dst_policy": self.dst_policy,
            "scheduling_policy": self.scheduling_policy,
            "violations": list(self.violations),
            "infrastructure_temporally_consistent": self.infrastructure_temporally_consistent,
            "expired_reason": self.expired_reason,
            "methodology_version": METHODOLOGY_VERSION,
        }


def serialize_api_instant(dt: datetime, *, timespec: str = "milliseconds") -> str:
    """SPEC §23/§23A — canonical API instants use RFC3339 UTC Z."""
    return to_rfc3339(require_aware(dt, field_name="api_instant"), timespec=timespec)


def validate_api_timestamp_string(value: str) -> ApiSerializationResult:
    """Reject ambiguous local timestamp strings without timezone context."""
    raw = str(value or "").strip()
    if not raw:
        return ApiSerializationResult(False, error="empty_timestamp")
    if LOCAL_TIMESTAMP_RE.match(raw):
        return ApiSerializationResult(False, error="ambiguous_local_timestamp_without_timezone")
    try:
        parsed = parse_rfc3339(raw)
    except ValueError as exc:
        return ApiSerializationResult(False, error=str(exc))
    return ApiSerializationResult(True, serialized=serialize_api_instant(parsed))


def serialize_epoch_timestamp(value: int | float, *, unit: TimestampUnit) -> ApiSerializationResult:
    """SPEC §23A — epoch timestamps require explicit unit contract."""
    contract = ApiTimestampContract(epoch=value, unit=unit)
    from launch57.temporal_common import epoch_to_utc

    instant = epoch_to_utc(value, unit=unit)
    return ApiSerializationResult(True, serialized=serialize_api_instant(instant), contract=contract)


def infer_and_serialize_epoch(value: int | float) -> ApiSerializationResult:
    unit = infer_timestamp_unit(value)
    return serialize_epoch_timestamp(value, unit=unit)


def prepare_db_instant_record(dt: datetime) -> DbInstantRecord:
    """SPEC §24/§24A — timezone-aware absolute instant storage."""
    aware = require_aware(dt, field_name="db_instant")
    return DbInstantRecord(instant_utc=serialize_api_instant(aware))


def prepare_db_civil_intent(
    *,
    local_wall_time: str,
    iana_zone: str,
    recurrence_rule: str | None = None,
    dst_policy: DstGapFoldPolicy = DstGapFoldPolicy.REJECT,
    migration_assumed_zone: str | None = None,
) -> DbCivilTimeIntent:
    """SPEC §24A — civil-time intent stored separately from absolute instants."""
    return DbCivilTimeIntent(
        local_wall_time=local_wall_time,
        iana_zone=iana_zone,
        recurrence_rule=recurrence_rule,
        dst_policy=dst_policy.value,
        migration_assumed_zone=migration_assumed_zone,
    )


def classify_naive_timestamp(
    naive_dt: datetime,
    *,
    assumed_zone: str,
    document_only: bool = True,
) -> dict[str, Any]:
    """SPEC §24 — legacy naive timestamps: classify and document; no silent reinterpret."""
    if naive_dt.tzinfo is not None:
        raise ValueError("not_naive_timestamp")
    return {
        "classification": "legacy_naive",
        "assumed_original_zone": assumed_zone,
        "documented_only": document_only,
        "silent_reinterpret_forbidden": True,
        "naive_value": naive_dt.isoformat(),
    }


def wall_clock_now() -> datetime:
    """SPEC §25A — wall clock for externally meaningful instants."""
    return utc_now()


def monotonic_elapsed_sec(start_monotonic: float) -> float:
    """SPEC §25A — monotonic clock for in-process elapsed durations."""
    return monotonic() - start_monotonic


def measure_elapsed(timer: MonotonicTimer) -> float:
    return timer.elapsed_sec()


def build_clock_health_snapshot(
    *,
    estimated_offset_sec: float,
    context: ClockContext = ClockContext.DEFAULT,
    synchronized: bool = True,
    last_synchronization: datetime | None = None,
    clock_step_detected: bool = False,
) -> ClockHealthSnapshot:
    """SPEC §25/§25B — measurable clock-health controls with context-specific skew budget."""
    budget = DEFAULT_SKEW_BUDGET_SEC[context]
    within = abs(estimated_offset_sec) <= budget
    return ClockHealthSnapshot(
        synchronized=synchronized,
        estimated_offset_sec=estimated_offset_sec,
        last_synchronization=serialize_api_instant(last_synchronization) if last_synchronization else None,
        clock_step_detected=clock_step_detected,
        drift_alert_threshold_sec=budget,
        skew_budget_sec=budget,
        context=context.value,
        within_budget=within,
    )


def check_clock_skew_budget(
    estimated_offset_sec: float,
    *,
    context: ClockContext = ClockContext.DEFAULT,
) -> tuple[bool, ClockHealthSnapshot]:
    snapshot = build_clock_health_snapshot(estimated_offset_sec=estimated_offset_sec, context=context)
    return snapshot.within_budget, snapshot


def classify_local_civil_state(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    *,
    zone_id: str,
    second: int = 0,
) -> LocalCivilState:
    """SPEC §26/§26A — detect DST gap/fold without silent invention."""
    try:
        zone = ZoneInfo(zone_id)
    except ZoneInfoNotFoundError:
        return LocalCivilState.VALID
    naive = datetime(year, month, day, hour, minute, second)
    day_start_utc = datetime(year, month, day, 0, 0, tzinfo=timezone.utc) - timedelta(hours=12)
    matches: list[datetime] = []
    for i in range(72 * 60):
        utc = day_start_utc + timedelta(minutes=i)
        local = utc.astimezone(zone).replace(tzinfo=None)
        if local == naive:
            matches.append(utc)
    if not matches:
        return LocalCivilState.NONEXISTENT
    if len(matches) > 1:
        return LocalCivilState.AMBIGUOUS
    return LocalCivilState.VALID


def resolve_local_civil_time(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    *,
    zone_id: str,
    second: int = 0,
    policy: DstGapFoldPolicy = DstGapFoldPolicy.REJECT,
) -> ResolvedLocalCivilTime:
    """SPEC §26A — deterministic DST gap/fold policy."""
    state = classify_local_civil_state(year, month, day, hour, minute, zone_id=zone_id, second=second)
    zone = ZoneInfo(zone_id)
    naive = datetime(year, month, day, hour, minute, second)

    if state == LocalCivilState.VALID:
        instant = naive.replace(fold=0, tzinfo=zone)
        return ResolvedLocalCivilTime(
            ok=True,
            instant_utc=serialize_api_instant(instant),
            state=state,
            policy_applied="valid",
        )

    if policy == DstGapFoldPolicy.REJECT:
        return ResolvedLocalCivilTime(
            ok=False,
            state=state,
            policy_applied=policy.value,
            error="dst_gap_or_ambiguous_local_time",
            dst_adjustment_explanation=f"local civil time rejected ({state.value})",
        )

    if state == LocalCivilState.AMBIGUOUS:
        if policy == DstGapFoldPolicy.FIRST_OCCURRENCE:
            fold = 0
        elif policy == DstGapFoldPolicy.SECOND_OCCURRENCE:
            fold = 1
        else:
            fold = 0
        instant = datetime(year, month, day, hour, minute, second, fold=fold, tzinfo=zone)
        return ResolvedLocalCivilTime(
            ok=True,
            instant_utc=serialize_api_instant(instant),
            state=state,
            policy_applied=policy.value,
            dst_adjustment_explanation="ambiguous local time resolved with explicit fold policy",
        )

    if policy == DstGapFoldPolicy.SHIFT_NEXT_VALID:
        candidate = naive
        for _ in range(180):
            cf0 = datetime(
                candidate.year,
                candidate.month,
                candidate.day,
                candidate.hour,
                candidate.minute,
                candidate.second,
                fold=0,
                tzinfo=zone,
            )
            cf1 = datetime(
                candidate.year,
                candidate.month,
                candidate.day,
                candidate.hour,
                candidate.minute,
                candidate.second,
                fold=1,
                tzinfo=zone,
            )
            back = cf0.astimezone(zone).replace(tzinfo=None)
            if cf0.utcoffset() == cf1.utcoffset() and back == candidate:
                return ResolvedLocalCivilTime(
                    ok=True,
                    instant_utc=serialize_api_instant(cf0),
                    state=state,
                    policy_applied=policy.value,
                    dst_adjustment_explanation="nonexistent local time shifted to next valid occurrence",
                )
            candidate += timedelta(minutes=1)
        return ResolvedLocalCivilTime(
            ok=False,
            state=state,
            policy_applied=policy.value,
            error="no_valid_local_time",
        )

    return ResolvedLocalCivilTime(
        ok=False,
        state=state,
        policy_applied=policy.value,
        error="unsupported_dst_policy_for_gap",
    )


def store_schedule_intent(intent: ScheduleIntent) -> dict[str, Any]:
    """SPEC §27/§27A — persist civil-time recurrence intent, not fixed offset."""
    return {
        "local_wall_time": intent.local_wall_time,
        "iana_zone": intent.iana_zone,
        "recurrence_rule": intent.recurrence_rule,
        "dst_policy": intent.dst_policy.value,
        "storage_model": "civil_time_recurrence_not_fixed_offset",
    }


def derive_next_utc_occurrence(
    intent: ScheduleIntent,
    *,
    after_utc: datetime | None = None,
    parts: tuple[int, int, int, int, int] | None = None,
) -> ResolvedLocalCivilTime:
    """Derive UTC execution instant from stored civil-time intent."""
    anchor = after_utc or wall_clock_now()
    if parts is None:
        hour, minute = 9, 0
        local_parts = intent.local_wall_time.split(":")
        if len(local_parts) >= 2:
            hour, minute = int(local_parts[0]), int(local_parts[1])
        parts = (anchor.year, anchor.month, anchor.day, hour, minute)
    year, month, day, hour, minute = parts
    resolved = resolve_local_civil_time(
        year,
        month,
        day,
        hour,
        minute,
        zone_id=intent.iana_zone,
        policy=intent.dst_policy,
    )
    if not resolved.ok:
        return resolved
    if resolved.instant_utc and parse_rfc3339(resolved.instant_utc) <= require_aware(anchor, field_name="after_utc"):
        next_day = datetime(year, month, day, tzinfo=UTC) + timedelta(days=1)
        return derive_next_utc_occurrence(
            intent,
            after_utc=anchor,
            parts=(next_day.year, next_day.month, next_day.day, hour, minute),
        )
    return resolved


def normalize_response_api_timestamps(body: Mapping[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Walk response payload and enforce API serialization policy on known timestamp fields."""
    violations: list[str] = []
    out = dict(body)

    temporal = dict(out.get("temporal") or {})
    for key, value in list(temporal.items()):
        if key in API_TIMESTAMP_FIELDS and value is not None and not isinstance(value, (int, float)):
            result = validate_api_timestamp_string(str(value))
            if not result.ok:
                violations.append(f"temporal.{key}:{result.error}")
            elif result.serialized:
                temporal[key] = result.serialized
    if temporal:
        out["temporal"] = temporal

    for key in API_TIMESTAMP_FIELDS:
        if key in out and out[key] is not None and not isinstance(out[key], (int, float)):
            result = validate_api_timestamp_string(str(out[key]))
            if not result.ok:
                violations.append(f"{key}:{result.error}")
            elif result.serialized:
                out[key] = result.serialized

    return out, violations


def build_infrastructure_temporal_context(
    body: Mapping[str, Any],
    *,
    estimated_clock_offset_sec: float = 0.0,
    clock_context: ClockContext = ClockContext.DEFAULT,
    dst_policy: DstGapFoldPolicy = DstGapFoldPolicy.REJECT,
) -> InfrastructureTemporalContext:
    """Evaluate cross-cutting infrastructure temporal consistency for an API body."""
    _, violations = normalize_response_api_timestamps(body)
    within_budget, _ = check_clock_skew_budget(estimated_clock_offset_sec, context=clock_context)
    if not within_budget:
        violations.append(f"clock_skew_exceeds_budget:{clock_context.value}")

    expired_reason = None
    if violations:
        expired_reason = "infrastructure_temporal_violation"

    return InfrastructureTemporalContext(
        api_serialization_policy="rfc3339_utc_z_preferred",
        db_storage_policy="instant_and_civil_intent_separate",
        clock_discipline_policy="wall_for_instants_monotonic_for_elapsed",
        dst_policy=dst_policy.value,
        scheduling_policy="civil_time_recurrence_with_iana_zone",
        violations=tuple(violations),
        infrastructure_temporally_consistent=expired_reason is None,
        expired_reason=expired_reason,
    )


def attach_infrastructure_temporal_envelope(
    body: dict[str, Any],
    context: InfrastructureTemporalContext,
    *,
    clock_health: ClockHealthSnapshot | None = None,
) -> dict[str, Any]:
    normalized, _ = normalize_response_api_timestamps(body)
    out = dict(normalized)
    out["infrastructure_temporal"] = context.as_dict()
    out["infrastructure_temporally_consistent"] = context.infrastructure_temporally_consistent
    if clock_health is not None:
        out["clock_health"] = clock_health.as_dict()
    return out


def is_api_bearing_body(body: Mapping[str, Any]) -> bool:
    if body.get("temporal") is not None:
        return True
    if any(key in body for key in API_TIMESTAMP_FIELDS):
        return True
    return body.get("launch57_isolation_boundary") is True
