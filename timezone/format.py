"""Timezone format helpers for data governance timestamps (DIG-032)."""

from __future__ import annotations

from typing import Any


def format_utc_instant(value: Any) -> str:
    try:
        from blackdark.timezone import format_iso_z, parse_to_utc

        dt = parse_to_utc(value)
        if dt is None:
            raise ValueError("invalid_instant")
        return format_iso_z(dt)
    except Exception:
        from datetime import UTC, datetime

        return datetime.now(UTC).isoformat().replace("+00:00", "Z")
