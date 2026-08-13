"""Persist Decision API v1 request audit without failing the customer response."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlsplit

from fastapi import Request

logger = logging.getLogger("BLACKDARK.DecisionAPIAudit")


def sanitize_audit_path(path: str) -> str:
    raw = (path or "/")[:512]
    split = urlsplit(raw)
    cleaned = split.path or "/"
    return cleaned.split("?")[0][:256]


async def persist_decision_api_audit(
    request: Request,
    *,
    status: int,
    error_code: str | None = None,
) -> None:
    try:
        principal = getattr(request.state, "decision_api_principal", None) or {}
        from database import insert_decision_api_audit

        await insert_decision_api_audit(
            key_public_id=principal.get("public_id"),
            org_id=principal.get("org_id"),
            method=str(request.method or "GET")[:16],
            path=sanitize_audit_path(request.url.path),
            status=int(status),
            request_id=str(getattr(request.state, "request_id", "") or "")[:64],
            error_code=(error_code or None) if status >= 400 else None,
        )
    except Exception:
        logger.debug("Decision API audit persist failed", exc_info=True)


def error_code_from_detail(detail: Any) -> str | None:
    if isinstance(detail, dict):
        return str(detail.get("error") or detail.get("code") or "")[:64] or None
    return None


async def persist_decision_api_ws_audit(
    *,
    principal: dict[str, Any] | None,
    status: int,
    error_code: str | None = None,
    request_id: str = "",
) -> None:
    try:
        row = principal or {}
        from database import insert_decision_api_audit

        await insert_decision_api_audit(
            key_public_id=row.get("public_id"),
            org_id=row.get("org_id"),
            method="WS",
            path="/api/v1/feed/ws",
            status=int(status),
            request_id=(request_id or "")[:64],
            error_code=error_code,
        )
    except Exception:
        logger.debug("Decision API WS audit persist failed", exc_info=True)
