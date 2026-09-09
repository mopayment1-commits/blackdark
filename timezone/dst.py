"""DST gap/fold handling — TZ-008, TZ-026."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

from timezone.iana import validate_iana_timezone

# Deterministic policy:
# - nonexistent local times (spring-forward gap): use the next valid instant (fold forward)
# - ambiguous local times (fall-back duplicate hour): choose the first (earlier) occurrence


def local_wall_to_utc(
    *,
    local_date: datetime,
    wall: time,
    tz_name: str,
) -> datetime:
    zone = ZoneInfo(validate_iana_timezone(tz_name))
    naive = datetime.combine(local_date.date(), wall)
    try:
        return naive.replace(tzinfo=zone).astimezone(UTC)
    except Exception:
        # Gap: advance minute-by-minute up to 180 minutes to find a valid mapping.
        cursor = naive
        for _ in range(180):
            try:
                return cursor.replace(tzinfo=zone).astimezone(UTC)
            except Exception:
                cursor += timedelta(minutes=1)
        raise ValueError(f"Unable to map local wall time in {tz_name}")


def resolve_ambiguous_local(
    *,
    local_dt: datetime,
    tz_name: str,
    prefer: str = "earlier",
) -> datetime:
    zone = ZoneInfo(validate_iana_timezone(tz_name))
    if local_dt.tzinfo is None:
        folded = local_dt.replace(tzinfo=zone, fold=(0 if prefer == "earlier" else 1))
        return folded.astimezone(UTC)
    return local_dt.astimezone(UTC)
