"""Recurring local schedules — IANA zone + wall-clock rule (TZ-025)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from blackdark.timezone import safe_timezone, validate_iana_timezone


@dataclass
class RecurringSchedule:
    schedule_id: str
    iana_zone: str
    wall_clock_rule: str  # e.g. "0 9 * * 1-5" cron-style local wall clock
    label: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if not validate_iana_timezone(self.iana_zone) and self.iana_zone.upper() != "UTC":
            raise ValueError("invalid_iana_zone_for_schedule")
        if not self.wall_clock_rule.strip():
            raise ValueError("wall_clock_rule_required")


_SCHEDULES: dict[str, RecurringSchedule] = {}


def register_schedule(schedule: RecurringSchedule) -> RecurringSchedule:
    schedule.iana_zone = safe_timezone(schedule.iana_zone)
    schedule.validate()
    _SCHEDULES[schedule.schedule_id] = schedule
    return schedule


def get_schedule(schedule_id: str) -> RecurringSchedule | None:
    return _SCHEDULES.get(schedule_id)


def list_schedules() -> list[dict[str, Any]]:
    return [s.to_dict() for s in _SCHEDULES.values()]
