"""RFC 9457 Problem Details for HTTP APIs (ERR-003, ERR-004)."""

from __future__ import annotations

import uuid
from typing import Any


def problem_response(
    *,
    status: int,
    title: str,
    detail: str | None = None,
    type_uri: str = "about:blank",
    instance: str | None = None,
    correlation_id: str | None = None,
    extensions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cid = correlation_id or f"bd-{uuid.uuid4().hex[:16]}"
    body: dict[str, Any] = {
        "type": type_uri,
        "title": title,
        "status": status,
        "correlation_id": cid,
    }
    if detail:
        body["detail"] = detail
    if instance:
        body["instance"] = instance
    if extensions:
        body.update(extensions)
    return body


def is_problem_detail(payload: dict[str, Any]) -> bool:
    return isinstance(payload, dict) and "title" in payload and "status" in payload
