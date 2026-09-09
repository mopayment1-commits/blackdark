"""Global time API — TZ-013, TZ-004."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request

from api.deps import optional_user
from api.openapi_responses import COMMON_ERROR_RESPONSES
from timezone.iana import COMMON_IANA_TIMEZONES
from timezone.request_context import resolve_from_request
from timezone.resolver import time_context_payload
from timezone.server_discipline import server_clock_readiness
from timezone.surface_registry import surface_audit

router = APIRouter(prefix="/api/time", tags=["time"])


@router.get("/context", responses=COMMON_ERROR_RESPONSES)
async def time_context(request: Request, user: dict | None = Depends(optional_user)) -> dict[str, Any]:
    resolved = resolve_from_request(request, user=user)
    return {
        "time": time_context_payload(resolved),
        "timezone_options": list(COMMON_IANA_TIMEZONES),
        "surfaces": surface_audit(),
    }


@router.get("/server-readiness", responses=COMMON_ERROR_RESPONSES)
async def time_server_readiness() -> dict[str, Any]:
    return server_clock_readiness()
