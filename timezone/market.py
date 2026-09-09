"""Market/source timestamp integrity — TZ-018."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from timezone.canonical import ensure_aware_utc, format_api_timestamp, parse_iso
from timezone.format import format_chart_display_time


def preserve_market_event(raw: dict[str, Any]) -> dict[str, Any]:
    event_time = raw.get("event_time") or raw.get("timestamp") or raw.get("ts")
    canonical = format_api_timestamp(parse_iso(str(event_time))) if event_time else None
    return {
        **raw,
        "source_timestamp": raw.get("source_timestamp") or event_time,
        "canonical_utc": canonical,
        "source_provenance": raw.get("source") or raw.get("exchange") or raw.get("provider"),
    }


def localize_market_event_for_display(
    raw: dict[str, Any],
    *,
    lang: str | None,
    tz_name: str | None,
) -> dict[str, Any]:
    preserved = preserve_market_event(raw)
    canonical = preserved.get("canonical_utc")
    if not canonical:
        return preserved
    preserved["display_time"] = format_chart_display_time(canonical, lang=lang, tz_name=tz_name)
    preserved["display_timezone"] = tz_name or "UTC"
    return preserved
