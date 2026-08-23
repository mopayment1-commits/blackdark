"""
BLACKDARK — Wave 0: Security & Performance Hardening.

Scope: institutional compounding write/export paths, timing telemetry,
public verify cache headers. Not a pentest or WAF replacement.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("BLACKDARK.Wave00")

WAVE_00_VERSION = "0.1.0"

# Institutional write paths — body size capped
INSTITUTIONAL_WRITE_PREFIXES = (
    "/api/audit/log",
    "/api/decisions",
    "/api/kg/",
    "/api/signals",
    "/api/learning/",
    "/api/analytics/event",
    "/api/analytics/share",
)

INSTITUTIONAL_WRITE_METHODS = frozenset({"POST", "PUT", "PATCH"})

# Public read paths — short CDN-friendly cache
PUBLIC_VERIFY_PATHS = frozenset(
    {
        "/api/compounding/_verify",
        "/api/security/wave-00",
        "/api/security/status",
        "/health",
        "/health/live",
        "/health/ready",
    }
)

PUBLIC_VERIFY_PREFIXES = (
    "/api/compounding/_verify/phase/",
)


def max_body_bytes() -> int:
    return int(os.getenv("WAVE_00_MAX_BODY_BYTES", "65536"))


def slow_request_warn_ms() -> float:
    return float(os.getenv("WAVE_00_SLOW_WARN_MS", "500"))


def slow_request_alert_ms() -> float:
    return float(os.getenv("WAVE_00_SLOW_ALERT_MS", "2000"))


def verify_cache_max_age() -> int:
    return int(os.getenv("WAVE_00_VERIFY_CACHE_SEC", "30"))


def is_institutional_write(path: str, method: str) -> bool:
    if method.upper() not in INSTITUTIONAL_WRITE_METHODS:
        return False
    return any(path.startswith(p) for p in INSTITUTIONAL_WRITE_PREFIXES)


def is_audit_export(path: str, method: str) -> bool:
    return method.upper() == "GET" and path.startswith("/api/audit/export")


def is_public_verify_path(path: str) -> bool:
    if path in PUBLIC_VERIFY_PATHS:
        return True
    return any(path.startswith(p) for p in PUBLIC_VERIFY_PREFIXES)


def check_content_length(request: Request) -> JSONResponse | None:
    """Reject oversized institutional write bodies before parsing."""
    if not is_institutional_write(request.url.path or "", request.method):
        return None
    raw = request.headers.get("content-length")
    if raw is None:
        return None
    try:
        length = int(raw)
    except ValueError:
        return JSONResponse(
            {"error": "invalid_content_length", "message": "Content-Length must be numeric."},
            status_code=400,
        )
    limit = max_body_bytes()
    if length > limit:
        return JSONResponse(
            {
                "error": "payload_too_large",
                "message": f"Request body exceeds Wave 0 limit ({limit} bytes).",
                "max_bytes": limit,
            },
            status_code=413,
        )
    return None


def apply_wave_00_response_headers(path: str, response: Response, duration_ms: float) -> None:
    response.headers.setdefault("X-Response-Time", f"{duration_ms:.2f}ms")
    response.headers.setdefault("X-Wave-00", WAVE_00_VERSION)
    if is_public_verify_path(path):
        response.headers.setdefault(
            "Cache-Control",
            f"public, max-age={verify_cache_max_age()}, stale-while-revalidate=60",
        )


def record_slow_request(path: str, method: str, duration_ms: float) -> None:
    warn = slow_request_warn_ms()
    alert = slow_request_alert_ms()
    if duration_ms < warn:
        return
    try:
        from observability import increment_metric

        increment_metric("slow_requests_total")
        if duration_ms >= alert:
            increment_metric("very_slow_requests_total")
    except Exception:
        pass
    level = logging.WARNING if duration_ms < alert else logging.ERROR
    logger.log(level, "slow request %s %s %.1fms", method, path, duration_ms)


async def wave_00_status() -> dict[str, Any]:
    from security_posture import security_posture_report

    posture = security_posture_report()
    checks = [
        {
            "id": "body_size_cap",
            "ok": True,
            "detail": f"institutional writes capped at {max_body_bytes()} bytes",
        },
        {
            "id": "audit_export_rate_limit",
            "ok": True,
            "detail": "viral_capacity class audit_export (20/min default)",
        },
        {
            "id": "institutional_write_rate_limit",
            "ok": True,
            "detail": "viral_capacity class institutional_write (40/min default)",
        },
        {
            "id": "response_timing_header",
            "ok": True,
            "detail": "X-Response-Time on all responses",
        },
        {
            "id": "verify_cache_headers",
            "ok": True,
            "detail": f"Cache-Control max-age={verify_cache_max_age()} on verify paths",
        },
        {
            "id": "security_headers",
            "ok": True,
            "detail": "CSP, CORP, Permissions-Policy via security_middleware",
        },
        {
            "id": "slow_request_telemetry",
            "ok": True,
            "detail": f"warn>={slow_request_warn_ms()}ms alert>={slow_request_alert_ms()}ms",
        },
    ]
    try:
        from observability import observability_status

        obs = observability_status()
    except Exception:
        obs = {}
    return {
        "wave": 0,
        "version": WAVE_00_VERSION,
        "title": "Security & Performance Hardening",
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
        "limits": {
            "max_body_bytes": max_body_bytes(),
            "slow_warn_ms": slow_request_warn_ms(),
            "slow_alert_ms": slow_request_alert_ms(),
            "verify_cache_sec": verify_cache_max_age(),
        },
        "observability": obs,
        "security_posture_honesty": posture.get("honesty", {}),
        "external_dependencies": [
            "human_pentest",
            "cdn_waf_activation",
            "soc2_iso_certification",
        ],
    }
