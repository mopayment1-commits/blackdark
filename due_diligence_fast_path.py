"""Fast-path responses for due-diligence evidence routes (no heavy /api middleware)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response


def maybe_fast_evidence_due_diligence_response(request: Request) -> Response | None:
    """Return a response without invoking the route stack, or None to continue."""
    path = request.url.path or ""
    method = request.method or "GET"
    if method != "GET":
        return None
    if path == "/api/due-diligence/evidence-pack/public-summary":
        from evidence_public_summary import get_cached_evidence_public_summary
        from starlette.responses import JSONResponse

        return JSONResponse(get_cached_evidence_public_summary())
    if path == "/api/due-diligence/evidence-pack":
        from anonymous_route_foundation import (
            enforce_anonymous_route_boundary,
            request_has_authentication_signal,
        )

        if not request_has_authentication_signal(request):
            return enforce_anonymous_route_boundary(request)
    return None
