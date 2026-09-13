"""Global timezone governance — delegates to blackdark.timezone canonical API (BGS-007)."""

from __future__ import annotations

from typing import Any

from blackdark.timezone import (
    format_iso_z,
    safe_timezone,
    to_display_tz,
    utc_now,
    utc_now_iso as canonical_utc_now_iso,
    validate_iana_timezone,
)


def utc_now_iso() -> str:
    return canonical_utc_now_iso()


def to_user_local(dt, tz_name: str):
    return to_display_tz(dt, tz_name)


def timezone_status() -> dict[str, Any]:
    from blackdark.timezone import timezone_status as _status

    return _status()
