"""IANA TZDB validation — TZ-002, TZ-032, TZ-033."""

from __future__ import annotations

import logging
from zoneinfo import ZoneInfo, available_timezones

logger = logging.getLogger("BLACKDARK.Timezone")

COMMON_IANA_TIMEZONES: tuple[str, ...] = (
    "UTC",
    "Africa/Cairo",
    "Africa/Johannesburg",
    "America/Chicago",
    "America/Los_Angeles",
    "America/New_York",
    "America/Sao_Paulo",
    "Asia/Dubai",
    "Asia/Kolkata",
    "Asia/Singapore",
    "Asia/Tokyo",
    "Australia/Sydney",
    "Europe/Berlin",
    "Europe/London",
    "Europe/Paris",
)

_FIXED_OFFSET_RE = __import__("re").compile(r"^(?:UTC|GMT)?[+-]\d{1,2}(?::?\d{2})?$", __import__("re").I)


def is_fixed_offset_not_iana(name: str | None) -> bool:
    return bool(name and _FIXED_OFFSET_RE.match(str(name).strip()))


def validate_iana_timezone(name: str | None, *, fallback: str = "UTC") -> str:
    candidate = str(name or fallback or "UTC").strip() or "UTC"
    if is_fixed_offset_not_iana(candidate):
        logger.warning("Rejected fixed-offset timezone preference | value=%s", candidate)
        return fallback
    try:
        ZoneInfo(candidate)
    except Exception:
        logger.warning("Invalid IANA timezone | value=%s", candidate)
        return fallback
    if candidate not in available_timezones() and candidate != "UTC":
        logger.warning("Unknown IANA timezone | value=%s", candidate)
        return fallback
    return candidate
