"""Per-key RPM / RPD quotas for Decision API v1."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request

from api.v1.contract import PLAN_LIMITS


def _retry_headers(window_sec: int) -> dict[str, str]:
    return {"Retry-After": str(window_sec)}


def apply_rate_limit_headers(request: Request, *, limit: int, remaining: int, window_sec: int = 60) -> None:
    request.state.decision_api_rl = {
        "limit": limit,
        "remaining": max(0, remaining),
        "reset": window_sec,
    }


async def enforce_key_quotas(request: Request, principal: dict[str, Any]) -> None:
    from database import fetch_decision_api_usage_today, increment_decision_api_usage
    from viral_capacity import check_rate_limit

    rpm = int(principal.get("rpm_limit") or PLAN_LIMITS["institutional"]["rpm"])
    rpd = int(principal.get("rpd_limit") or PLAN_LIMITS["institutional"]["rpd"])
    key_id = str(principal["public_id"])
    try:
        check_rate_limit(key_id, limit=rpm, window_sec=60, prefix="decision_api")
    except HTTPException as exc:
        apply_rate_limit_headers(request, limit=rpm, remaining=0)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "message": "Per-key rate limit exceeded. Retry after the window.",
                "retry_after_sec": 60,
                "limit": rpm,
                "window": "1m",
            },
            headers=_retry_headers(60),
        ) from exc

    used = await fetch_decision_api_usage_today(key_id)
    if used >= rpd:
        apply_rate_limit_headers(request, limit=rpd, remaining=0, window_sec=86400)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "message": f"Daily request quota reached ({rpd}/day) for this API key.",
                "retry_after_sec": 86400,
                "limit": rpd,
                "window": "1d",
            },
            headers=_retry_headers(86400),
        )
    await increment_decision_api_usage(key_id)
    remaining = max(0, rpm - 1)
    apply_rate_limit_headers(request, limit=rpm, remaining=remaining)
    request.state.decision_api_daily = {"limit": rpd, "used": used + 1, "date": datetime.now(UTC).date().isoformat()}
