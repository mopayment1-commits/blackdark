"""Correlation middleware and response header propagation (ERR-004)."""

from __future__ import annotations

import os

from starlette.requests import Request

from failure.correlation import (
    new_correlation_id,
    parse_incoming_correlation_id,
    require_correlation_id,
    set_correlation_id,
)

_MAINTENANCE_BYPASS_PREFIXES = (
    "/health/live",
    "/health/ready",
)


def maintenance_mode_enabled() -> bool:
    return os.getenv("BLACKDARK_MAINTENANCE_MODE", os.getenv("MAINTENANCE_MODE", "")).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _maintenance_bypass(path: str) -> bool:
    p = (path or "").rstrip("/") or "/"
    return any(p == prefix or p.startswith(prefix + "/") for prefix in _MAINTENANCE_BYPASS_PREFIXES)


async def correlation_middleware(request: Request, call_next):
    incoming = parse_incoming_correlation_id(request.headers)
    cid = incoming or new_correlation_id()
    set_correlation_id(cid)
    request.state.correlation_id = cid
    response = await call_next(request)
    response.headers.setdefault("X-Correlation-ID", cid)
    response.headers.setdefault("X-Request-ID", cid)
    return response


async def maintenance_middleware(request: Request, call_next):
    if not maintenance_mode_enabled() or _maintenance_bypass(request.url.path):
        return await call_next(request)
    from failure.problem import problem_response
    from failure.registry import build_problem_from_spec, get_error_spec

    spec = get_error_spec("BD-MAINT-001")
    assert spec is not None
    cid = require_correlation_id()
    problem = build_problem_from_spec(spec, correlation_id=cid)
    problem.failure_origin = "platform"
    lang = None
    try:
        from i18n_service import resolve_request_lang

        lang = resolve_request_lang(request)
    except Exception:
        pass
    return problem_response(problem, lang=lang)
