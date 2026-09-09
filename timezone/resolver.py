"""Timezone precedence resolution — TZ-004, TZ-007, TZ-009, TZ-010, TZ-034."""

from __future__ import annotations

from dataclasses import dataclass

from timezone.iana import validate_iana_timezone


@dataclass(frozen=True)
class ResolvedTimezone:
    timezone: str
    source: str
    account_timezone: str | None = None
    session_timezone: str | None = None
    detected_timezone: str | None = None
    request_override: str | None = None
    mismatch: bool = False


def resolve_timezone(
    *,
    request_override: str | None = None,
    account_timezone: str | None = None,
    session_timezone: str | None = None,
    detected_timezone: str | None = None,
) -> ResolvedTimezone:
    account = validate_iana_timezone(account_timezone) if account_timezone else None
    session = validate_iana_timezone(session_timezone) if session_timezone else None
    detected = validate_iana_timezone(detected_timezone) if detected_timezone else None
    override = validate_iana_timezone(request_override) if request_override else None

    if override and override != "UTC":
        resolved = override
        source = "request_override"
    elif account and account != "UTC":
        resolved = account
        source = "account"
    elif session and session != "UTC":
        resolved = session
        source = "session"
    elif detected and detected != "UTC":
        resolved = detected
        source = "detected"
    else:
        resolved = "UTC"
        source = "utc_fallback"

    mismatch = bool(account and detected and account != detected)
    return ResolvedTimezone(
        timezone=resolved,
        source=source,
        account_timezone=account,
        session_timezone=session,
        detected_timezone=detected,
        request_override=override,
        mismatch=mismatch,
    )


def time_context_payload(resolved: ResolvedTimezone) -> dict[str, object]:
    return {
        "resolved_timezone": resolved.timezone,
        "source": resolved.source,
        "account_timezone": resolved.account_timezone or "UTC",
        "session_timezone": resolved.session_timezone,
        "detected_timezone": resolved.detected_timezone,
        "request_override": resolved.request_override,
        "travel_mismatch": resolved.mismatch,
        "privacy_note": "Timezone is a preference signal only — not location proof or authorization evidence.",
    }
