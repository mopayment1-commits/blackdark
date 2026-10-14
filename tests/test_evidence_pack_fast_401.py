"""Unauthenticated evidence-pack must 401 without hitting the route handler."""

from __future__ import annotations

import time

from starlette.requests import Request


def _anonymous_evidence_pack_request() -> Request:
    scope = {
        "type": "http",
        "asgi": {"spec_version": "2.3", "version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "https",
        "path": "/api/due-diligence/evidence-pack",
        "raw_path": b"/api/due-diligence/evidence-pack",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "server": ("testserver", 443),
    }
    return Request(scope)


def test_evidence_pack_fast_path_returns_401_quickly():
    from due_diligence_fast_path import maybe_fast_evidence_due_diligence_response

    request = _anonymous_evidence_pack_request()
    t0 = time.perf_counter()
    response = maybe_fast_evidence_due_diligence_response(request)
    elapsed = time.perf_counter() - t0

    assert response is not None
    assert response.status_code == 401
    assert elapsed < 1.0
