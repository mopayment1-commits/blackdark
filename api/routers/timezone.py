"""Timezone API — canonical UTC + IANA preference resolution (TZ SSOT)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.deps import optional_user

router = APIRouter(tags=["timezone"])


class TimezoneResolveBody(BaseModel):
    request_override: str | None = None
    session_preference: str | None = None
    detected_browser: str | None = None


class TimezoneFormatBody(BaseModel):
    instant: str = Field(..., description="UTC ISO-8601 instant")
    timezone: str = Field(..., description="IANA display timezone")
    include_label: bool = True


@router.get("/api/timezone/status")
async def timezone_api_status() -> dict[str, Any]:
    from blackdark.timezone import timezone_status

    return timezone_status()


@router.post("/api/timezone/resolve")
async def timezone_resolve(
    body: TimezoneResolveBody,
    user: dict | None = Depends(optional_user),
) -> dict[str, Any]:
    from blackdark.timezone import resolve_timezone, validate_iana_timezone

    account_pref = user.get("timezone") if user else None
    resolved = resolve_timezone(
        request_override=body.request_override,
        account_preference=account_pref,
        session_preference=body.session_preference,
        detected_browser=body.detected_browser,
    )
    return {
        "timezone": resolved,
        "valid_iana": validate_iana_timezone(resolved) or resolved == "UTC",
        "account_timezone": account_pref,
    }


@router.post("/api/timezone/format")
async def timezone_format(body: TimezoneFormatBody) -> dict[str, Any]:
    from blackdark.timezone import format_iso_z, parse_to_utc, safe_timezone, to_display_tz

    instant = parse_to_utc(body.instant)
    if instant is None:
        raise HTTPException(status_code=400, detail="invalid_instant")
    tz = safe_timezone(body.timezone)
    local = to_display_tz(instant, tz)
    out: dict[str, Any] = {
        "utc": format_iso_z(instant),
        "local": format_iso_z(local),
        "timezone": tz,
    }
    if body.include_label:
        out["label"] = f"{local.strftime('%Y-%m-%d %H:%M:%S')} {tz}"
    return out


@router.get("/api/timezone/validate/{tz_name}")
async def timezone_validate(tz_name: str) -> dict[str, Any]:
    from blackdark.timezone import safe_timezone, validate_iana_timezone

    valid = validate_iana_timezone(tz_name) or tz_name.upper() == "UTC"
    if not valid:
        raise HTTPException(status_code=400, detail={"valid": False, "fallback": "UTC"})
    return {"valid": True, "timezone": safe_timezone(tz_name)}
