"""DTS-036 — User-local delivery (timezone-resolved, not hardcoded global 08:00)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from governance.timezone_governance import to_user_local, validate_iana_timezone, utc_now_iso


DEFAULT_DELIVERY_HOUR = 8  # user-local, not UTC-global mandate


def resolve_user_local_delivery(
    payload: dict[str, Any],
    *,
    user_timezone: str | None = None,
    preferences: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Resolve delivery schedule using canonical timezone governance."""
    prefs = preferences or payload.get("delivery_preferences") or {}
    tz = user_timezone or prefs.get("timezone") or payload.get("user_timezone") or "UTC"
    if not validate_iana_timezone(tz):
        tz = "UTC"

    hour = int(prefs.get("delivery_hour_local") or prefs.get("hour") or DEFAULT_DELIVERY_HOUR)
    opt_in = bool(prefs.get("opt_in", prefs.get("enabled", False)))

    now_utc = datetime.now(UTC)
    local_now = to_user_local(now_utc, tz)
    next_local = local_now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if local_now.hour >= hour:
        from datetime import timedelta

        next_local = next_local + timedelta(days=1)

    return {
        "canonical_storage": "UTC",
        "user_timezone": tz,
        "delivery_hour_local": hour,
        "hardcoded_global_08_00": False,
        "opt_in": opt_in,
        "policy_defined": True,
        "next_delivery_utc": next_local.astimezone(UTC).isoformat(),
        "next_delivery_local": next_local.isoformat(),
        "resolved_at_utc": utc_now_iso(),
        "timezone_authority": "governance/timezone_governance.py",
        "methodology_version": "dts-p5-user-local-delivery-1.0",
    }
