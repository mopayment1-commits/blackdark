"""Recurring local wall-clock schedules — TZ-025."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time
from typing import Any

from timezone.canonical import ensure_aware_utc, utc_now
from timezone.dst import local_wall_to_utc
from timezone.iana import validate_iana_timezone


@dataclass(frozen=True)
class LocalSchedule:
    wall_time: str
    iana_timezone: str
    recurrence: str = "daily"

    def validate(self) -> None:
        validate_iana_timezone(self.iana_timezone)
        parts = self.wall_time.split(":")
        if len(parts) != 2:
            raise ValueError("wall_time must be HH:MM")
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid wall_time")


def schedule_to_payload(schedule: LocalSchedule) -> dict[str, Any]:
    schedule.validate()
    return {
        "wall_time": schedule.wall_time,
        "iana_timezone": schedule.iana_timezone,
        "recurrence": schedule.recurrence,
    }


def next_occurrence_utc(schedule: LocalSchedule, *, after: datetime | None = None) -> datetime:
    schedule.validate()
    anchor = ensure_aware_utc(after or utc_now())
    hour, minute = (int(x) for x in schedule.wall_time.split(":", 1))
    candidate = local_wall_to_utc(
        local_date=anchor,
        wall=time(hour, minute),
        tz_name=schedule.iana_timezone,
    )
    if candidate <= anchor:
        from datetime import timedelta

        candidate = local_wall_to_utc(
            local_date=anchor + timedelta(days=1),
            wall=time(hour, minute),
            tz_name=schedule.iana_timezone,
        )
    return candidate
