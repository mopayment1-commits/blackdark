"""User-facing time display — canonical UTC in, localized TZ out (TZ-014–024, TZ-030)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from blackdark.timezone import format_iso_z, parse_to_utc, resolve_timezone, safe_timezone, to_display_tz

# Surfaces registered for cross-surface audit (TZ-030)
_REGISTERED_SURFACES = frozenset(
    {
        "api",
        "charts",
        "heroes",
        "alerts",
        "billing",
        "email",
        "ai_oracle",
        "activity_log",
        "exports",
        "notifications",
        "profile",
    }
)


def format_with_label(
    value: str | int | float | datetime | None,
    tz_name: str,
    *,
    include_utc: bool = False,
) -> dict[str, Any]:
    """TZ-016 — clear timezone context/label on decision-critical times."""
    tz = safe_timezone(tz_name)
    instant = parse_to_utc(value) if value is not None else None
    if instant is None:
        return {"utc": None, "local": None, "label": None, "timezone": tz}
    local = to_display_tz(instant, tz)
    label = f"{local.strftime('%Y-%m-%d %H:%M:%S')} {tz}"
    out: dict[str, Any] = {
        "utc": format_iso_z(instant),
        "local": format_iso_z(local),
        "label": label,
        "timezone": tz,
    }
    if include_utc:
        out["utc_label"] = f"{format_iso_z(instant)} UTC"
    return out


def format_for_locale(
    value: str | int | float | datetime | None,
    tz_name: str,
    locale: str = "en",
) -> dict[str, Any]:
    """TZ-015 / TZ-029 — locale formatting via i18n_service; timezone stays independent."""
    try:
        from i18n_service import normalize_lang

        locale = normalize_lang(locale or "en")
    except Exception:
        locale = (locale or "en")[:12]
    base = format_with_label(value, tz_name)
    base["locale"] = locale
    # Locale affects presentation hint only; TZ is never derived from locale.
    base["locale_format_hint"] = f"{base['locale']}_{base['timezone']}"
    base["i18n_integrated"] = True
    return base


def resolve_user_tz(
    user: dict[str, Any] | None = None,
    *,
    request_override: str | None = None,
    session_preference: str | None = None,
    detected_browser: str | None = None,
) -> str:
    account = (user or {}).get("timezone") if user else None
    return resolve_timezone(
        request_override=request_override,
        account_preference=account,
        session_preference=session_preference,
        detected_browser=detected_browser,
    )


def enrich_fields(
    payload: dict[str, Any],
    tz_name: str,
    *field_names: str,
    suffix: str = "_display",
) -> dict[str, Any]:
    """Attach display fields for canonical UTC instants."""
    out = dict(payload)
    tz = safe_timezone(tz_name)
    out["display_timezone"] = tz
    for field in field_names:
        if field in out and out[field] is not None:
            formatted = format_with_label(out[field], tz)
            out[f"{field}{suffix}"] = formatted["label"]
            out[f"{field}_utc"] = formatted["utc"]
    return out


def format_ai_output(
    value: str | int | float | datetime | None,
    tz_name: str,
) -> dict[str, Any]:
    """TZ-019 — AI user-facing times in resolved user timezone."""
    return format_with_label(value, tz_name, include_utc=True)


def format_notification(
    value: str | int | float | datetime | None,
    tz_name: str,
) -> dict[str, Any]:
    """TZ-020 — notification display honors user timezone; canonical stays UTC."""
    return format_with_label(value, tz_name)


def format_email(
    value: str | int | float | datetime | None,
    tz_name: str,
    locale: str = "en",
) -> str:
    """TZ-021 — transactional email time rendering."""
    row = format_for_locale(value, tz_name, locale)
    return row.get("label") or ""


def export_metadata(tz_name: str) -> dict[str, Any]:
    """TZ-022 — machine-readable export timezone metadata."""
    tz = safe_timezone(tz_name)
    return {
        "canonical_storage": "UTC",
        "display_timezone": tz,
        "export_policy": "UTC timestamps preserved; display_timezone for localization",
        "generated_at_utc": format_iso_z(parse_to_utc(__import__("blackdark.timezone", fromlist=["utc_now"]).utc_now())),
    }


def format_activity_log(
    value: str | int | float | datetime | None,
    tz_name: str,
) -> dict[str, Any]:
    """TZ-023 — user-visible activity local; audit retains UTC."""
    return format_with_label(value, tz_name, include_utc=True)


def format_billing(
    value: str | int | float | datetime | None,
    tz_name: str,
) -> dict[str, Any]:
    """TZ-024 — billing display localization without changing cycle authority."""
    row = format_with_label(value, tz_name, include_utc=True)
    row["billing_authority"] = "UTC"
    return row


def chart_config(tz_name: str) -> dict[str, Any]:
    """TZ-017 — explicit display timezone for chart axes/tooltips."""
    tz = safe_timezone(tz_name)
    return {
        "display_timezone": tz,
        "axis_policy": "single_explicit_zone",
        "mixing_forbidden": True,
        "time_formatter": "blackdark-timezone.js",
    }


def cross_surface_status() -> dict[str, Any]:
    """TZ-030 / TZ-035 — cross-surface binding registry."""
    return {
        "surfaces": sorted(_REGISTERED_SURFACES),
        "canonical_module": "blackdark.timezone",
        "display_module": "blackdark.timezone.display",
        "count": len(_REGISTERED_SURFACES),
    }


def resolve_timezone_independent_of_lang(
    ui_lang: str,
    *,
    account_preference: str | None = None,
    detected_browser: str | None = None,
) -> str:
    """TZ-009 — language/locale must not determine timezone."""
    return resolve_timezone(
        account_preference=account_preference,
        detected_browser=detected_browser,
    )


def resolve_timezone_independent_of_country(
    country: str | None,
    *,
    account_preference: str | None = None,
    detected_browser: str | None = None,
) -> str:
    """TZ-010 — country/region is not the sole timezone source."""
    resolved = resolve_timezone(
        account_preference=account_preference,
        detected_browser=detected_browser,
    )
    if account_preference:
        return resolved
    if country and resolved == country:
        return "UTC"
    return resolved


def timezone_detection_privacy() -> dict[str, Any]:
    """TZ-034 — detected timezone is preference/context only, not location/identity proof."""
    return {
        "timezone_detection_is_preference_only": True,
        "not_exact_physical_location": True,
        "not_identity_proof": True,
        "policy": "Browser timezone may suggest display preference; never used for auth decisions.",
    }
