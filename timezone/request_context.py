"""Request/cookie timezone extraction — TZ-003, TZ-004."""

from __future__ import annotations

from typing import Any

SESSION_TZ_COOKIE = "bd_session_tz"
DETECTED_TZ_COOKIE = "bd_detected_tz"
REQUEST_TZ_HEADER = "x-timezone"


def _cookie(request: Any, name: str) -> str | None:
    if request is None:
        return None
    try:
        value = request.cookies.get(name)
    except Exception:
        return None
    return str(value).strip() if value else None


def request_override_timezone(request: Any | None) -> str | None:
    if request is None:
        return None
    try:
        header = request.headers.get(REQUEST_TZ_HEADER) or request.headers.get("X-Timezone")
    except Exception:
        header = None
    return str(header).strip() if header else None


def session_timezone_from_request(request: Any | None) -> str | None:
    return _cookie(request, SESSION_TZ_COOKIE)


def detected_timezone_from_request(request: Any | None) -> str | None:
    return _cookie(request, DETECTED_TZ_COOKIE)


def resolve_from_request(
    request: Any | None,
    *,
    user: dict[str, Any] | None = None,
) -> "ResolvedTimezone":
    from timezone.resolver import resolve_timezone

    account = (user or {}).get("timezone")
    return resolve_timezone(
        request_override=request_override_timezone(request),
        account_timezone=account,
        session_timezone=session_timezone_from_request(request),
        detected_timezone=detected_timezone_from_request(request),
    )


from timezone.resolver import ResolvedTimezone  # noqa: E402
