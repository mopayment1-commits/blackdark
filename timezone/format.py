"""User-facing datetime formatting — TZ-014, TZ-015, TZ-016, TZ-029."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from timezone.canonical import ensure_aware_utc, format_api_timestamp, parse_iso
from timezone.iana import validate_iana_timezone


def to_user_local(dt: datetime | str, tz_name: str) -> datetime:
    instant = parse_iso(dt) if not isinstance(dt, datetime) else ensure_aware_utc(dt)
    zone = ZoneInfo(validate_iana_timezone(tz_name))
    return instant.astimezone(zone)


def _locale_pattern(lang: str) -> str:
    code = (lang or "en").lower()
    if code in {"ja", "ko", "zh-cn", "zh-tw"}:
        return "%Y/%m/%d %H:%M"
    if code in {"de", "fr", "es", "it", "pt-pt", "pt-br", "nl", "pl", "cs", "ro", "hu", "sv", "ru", "uk"}:
        return "%d.%m.%Y %H:%M"
    return "%Y-%m-%d %H:%M"


def format_user_datetime(
    dt: datetime | str,
    *,
    lang: str | None = None,
    tz_name: str | None = None,
) -> str:
    local = to_user_local(dt, validate_iana_timezone(tz_name))
    return local.strftime(_locale_pattern(lang or "en"))


def format_with_timezone_context(
    dt: datetime | str,
    *,
    lang: str | None = None,
    tz_name: str | None = None,
) -> str:
    zone = validate_iana_timezone(tz_name)
    local = to_user_local(dt, zone)
    return f"{format_user_datetime(local, lang=lang, tz_name=zone)} {zone}"


def format_ai_output_time(
    dt: datetime | str,
    *,
    lang: str | None,
    tz_name: str | None,
) -> str:
    return format_with_timezone_context(dt, lang=lang, tz_name=tz_name)


def format_notification_time(dt: datetime | str, *, lang: str | None, tz_name: str | None) -> str:
    return format_with_timezone_context(dt, lang=lang, tz_name=tz_name)


def format_email_time(dt: datetime | str, *, lang: str | None, tz_name: str | None) -> str:
    return format_with_timezone_context(dt, lang=lang, tz_name=tz_name)


def format_billing_display_time(dt: datetime | str, *, lang: str | None, tz_name: str | None) -> str:
    return format_with_timezone_context(dt, lang=lang, tz_name=tz_name)


def format_activity_log_user_view(dt: datetime | str, *, lang: str | None, tz_name: str | None) -> str:
    return format_with_timezone_context(dt, lang=lang, tz_name=tz_name)


def format_chart_display_time(
    dt: datetime | str,
    *,
    lang: str | None,
    tz_name: str | None,
) -> str:
    return format_with_timezone_context(dt, lang=lang, tz_name=tz_name)


def export_timestamp_fields(dt: datetime | str, *, tz_name: str | None) -> dict[str, str]:
    instant = parse_iso(dt) if not isinstance(dt, datetime) else ensure_aware_utc(dt)
    zone = validate_iana_timezone(tz_name)
    return {
        "canonical_utc": format_api_timestamp(instant),
        "display_timezone": zone,
        "display_local": format_user_datetime(instant, tz_name=zone),
    }
