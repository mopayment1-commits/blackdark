#!/usr/bin/env python3
"""Circuit breaker observability middleware — record request outcomes (#1051)."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.responses import JSONResponse, Response


def _service_from_path(path: str) -> str | None:
    if path.startswith("/api/oracle") or path.startswith("/oracle"):
        return "oracle_api"
    if path.startswith("/api/v1/data") or path.startswith("/api/data"):
        return "data_engine"
    if path.startswith("/api/auth"):
        return "auth_api"
    if path.startswith("/api/"):
        return "platform_api"
    return None


async def circuit_breaker_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Record latency/errors and return degraded response when circuit open."""
    from circuit_breaker_layer import check_circuit, record_service_request

    path = request.url.path or "/"
    service = _service_from_path(path)
    if service is None:
        return await call_next(request)

    gate = check_circuit(service)
    if not gate.get("allow"):
        return JSONResponse(
            {
                "status": "degraded",
                "message": gate.get("message", "Service Recovery in Progress"),
                "badge": gate.get("badge"),
                "fallback": gate.get("fallback"),
                "provenance": {
                    "flag": gate.get("provenance_flag"),
                    "source": "circuit_breaker_cache",
                },
                "circuit_breaker": True,
            },
            status_code=503,
            headers={"Retry-After": "30", "X-Service-Degraded": "1"},
        )

    started = time.perf_counter()
    try:
        response = await call_next(request)
        ok = response.status_code < 500
        latency_ms = (time.perf_counter() - started) * 1000
        record_service_request(service, success=ok, latency_ms=latency_ms)
        if gate.get("degraded"):
            response.headers["X-Service-Degraded"] = "half-open"
        return response
    except Exception:
        latency_ms = (time.perf_counter() - started) * 1000
        record_service_request(service, success=False, latency_ms=latency_ms)
        raise
