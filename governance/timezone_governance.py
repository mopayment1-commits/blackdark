"""Global timezone governance — IANA zones, UTC canonical storage (BGS-007)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo, available_timezones

_FALLBACK_TZ = "UTC"
_CANONICAL_AUTHORITY = "governance/timezone_governance.py"


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def ensure_utc_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def parse_canonical_timestamp(value: Any) -> datetime | None:
    """Parse canonical evidence timestamps; always returns UTC-aware or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return ensure_utc_aware(value)
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return ensure_utc_aware(parsed)


def resolve_user_timezone(tz_name: str | None) -> dict[str, Any]:
    """Resolve user timezone with governed fallback — single canonical authority."""
    requested = str(tz_name or "").strip()
    if requested and validate_iana_timezone(requested):
        return {
            "timezone": requested,
            "fallback_used": False,
            "fallback_reason": None,
            "authority": _CANONICAL_AUTHORITY,
        }
    return {
        "timezone": _FALLBACK_TZ,
        "fallback_used": True,
        "fallback_reason": "invalid_or_unknown_timezone" if requested else "timezone_not_provided",
        "requested_timezone": requested or None,
        "authority": _CANONICAL_AUTHORITY,
    }


def to_user_local(dt: datetime, tz_name: str) -> datetime:
    resolved = resolve_user_timezone(tz_name)
    zone = ZoneInfo(resolved["timezone"])
    return ensure_utc_aware(dt).astimezone(zone)


def format_user_facing_timestamp(
    value: Any,
    tz_name: str | None,
    *,
    lang: str | None = None,
) -> dict[str, Any]:
    """Presentation conversion — canonical UTC preserved; user-local is derived only."""
    canonical = parse_canonical_timestamp(value)
    if canonical is None:
        return {
            "canonical_utc": None,
            "user_local": None,
            "display": None,
            "timezone": resolve_user_timezone(tz_name),
            "naive": True,
            "lang": lang,
        }
    resolved = resolve_user_timezone(tz_name)
    local = to_user_local(canonical, resolved["timezone"])
    return {
        "canonical_utc": canonical.isoformat(),
        "user_local": local.isoformat(),
        "display": local.strftime("%Y-%m-%d %H:%M %Z"),
        "timezone": resolved,
        "naive": False,
        "canonical_mutated": False,
        "lang": lang,
    }


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
