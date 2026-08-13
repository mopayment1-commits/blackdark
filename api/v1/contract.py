"""Stable commercial contract constants for Decision API v1."""

from __future__ import annotations

from typing import Any

API_VERSION = "v1"
CONTRACT_NAME = "decision-api-v1"
SUNSET_LEGACY_B2B = "Fri, 13 Aug 2027 00:00:00 GMT"
SUCCESSOR_FEED = "/api/v1/feed"
DISCLAIMER = (
    "BLACKDARK Decision API — decision evidence only. Not financial advice. "
    "Not a regulated investment service. Licensed for internal decision support. "
    "Redistribution and model-training on exported corpus require a separate license."
)

CUSTOMER_SCOPES: frozenset[str] = frozenset(
    {
        "oracle:read",
        "accuracy:read",
        "feed:read",
        "feed:ws",
        "audit:read",
        "webhooks:write",
    }
)
DEFAULT_CUSTOMER_SCOPES: tuple[str, ...] = (
    "oracle:read",
    "accuracy:read",
    "feed:read",
    "feed:ws",
    "audit:read",
    "webhooks:write",
)

PLAN_LIMITS: dict[str, dict[str, int]] = {
    "sandbox": {"rpm": 30, "rpd": 500, "export_limit": 15},
    "institutional": {"rpm": 120, "rpd": 50_000, "export_limit": 250},
}

LEGACY_B2B_HEADERS: dict[str, str] = {
    "Deprecation": "true",
    "Sunset": SUNSET_LEGACY_B2B,
    "Link": f'<{SUCCESSOR_FEED}>; rel="successor-version"',
    "X-Blackdark-Successor": SUCCESSOR_FEED,
}

DENY_PATH_PREFIXES: tuple[str, ...] = (
    "/api/v1/admin",
    "/api/v1/execution",
    "/api/v1/vault",
    "/api/v1/metrics",
    "/api/v1/ml/train",
)


def error_envelope(
    *,
    status: int,
    code: str,
    message: str,
    request_id: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "error": code,
        "code": code,
        "message": message,
        "request_id": request_id,
        "api_version": API_VERSION,
        "status": status,
    }
    if extra:
        body.update(extra)
    return body


def http_exception_envelope(detail: Any, *, status: int, request_id: str) -> dict[str, Any]:
    if isinstance(detail, dict):
        code = str(detail.get("error") or detail.get("code") or "request_failed")
        message = str(detail.get("message") or detail.get("error") or "Request failed")
        extra = {
            k: v
            for k, v in detail.items()
            if k not in {"error", "code", "message", "status"}
        }
        return error_envelope(
            status=status,
            code=code,
            message=message,
            request_id=request_id,
            extra=extra or None,
        )
    return error_envelope(
        status=status,
        code="request_failed" if status >= 500 else "request_error",
        message=str(detail or "Request failed"),
        request_id=request_id,
    )
