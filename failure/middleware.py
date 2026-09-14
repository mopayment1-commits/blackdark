"""Correlation middleware and response header propagation (ERR-004)."""

from __future__ import annotations

from starlette.requests import Request

from failure.correlation import (
    new_correlation_id,
    parse_incoming_correlation_id,
    set_correlation_id,
)


async def correlation_middleware(request: Request, call_next):
    incoming = parse_incoming_correlation_id(request.headers)
    cid = incoming or new_correlation_id()
    set_correlation_id(cid)
    request.state.correlation_id = cid
    response = await call_next(request)
    response.headers.setdefault("X-Correlation-ID", cid)
    return response
