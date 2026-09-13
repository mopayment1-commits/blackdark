"""Global timezone governance — IANA zones, UTC canonical storage (BGS-007)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo, available_timezones


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def to_user_local(dt: datetime, tz_name: str) -> datetime:
    zone = ZoneInfo(tz_name)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(zone)


def validate_iana_timezone(tz_name: str) -> bool:
    return tz_name in available_timezones()


def timezone_status() -> dict[str, Any]:
    sample = "America/New_York"
    now = datetime.now(UTC)
    local = to_user_local(now, sample)
    return {
        "canonical_storage": "UTC",
        "iana_available": True,
        "sample_zone": sample,
        "sample_local": local.isoformat(),
        "dst_aware": local.dst() is not None,
        "supported_zones_count": len(available_timezones()),
    }
