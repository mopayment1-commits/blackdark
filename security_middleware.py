"""
BLACKDARK — HTTP security middleware (headers, host, CORS, CSRF for cookie auth).

Honest scope: application-layer hardening. Not a WAF, SOC2 cert, or pentest report.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


def _is_production() -> bool:
    env = (os.getenv("ENV") or os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower()
    return env in {"production", "prod"}


def _allowed_hosts() -> set[str]:
    raw = (os.getenv("ALLOWED_HOSTS") or "").strip()
    hosts: set[str] = set()
    if raw:
        hosts.update(h.strip().lower() for h in raw.split(",") if h.strip())
    base = (os.getenv("APP_BASE_URL") or "").strip()
    if base:
        try:
            netloc = urlparse(base).hostname
            if netloc:
                hosts.add(netloc.lower())
        except Exception:
            pass
    # Local / health always allowed
    hosts.update({"localhost", "127.0.0.1", "test", "testserver"})
    return hosts


def _cors_origins() -> list[str]:
    raw = (os.getenv("CORS_ALLOWED_ORIGINS") or "").strip()
    origins: list[str] = []
    if raw:
        origins.extend(o.strip().rstrip("/") for o in raw.split(",") if o.strip())
    base = (os.getenv("APP_BASE_URL") or "").strip().rstrip("/")
    if base and base not in origins:
        origins.append(base)
    return origins


def security_headers_for(request: Request) -> dict[str, str]:
    """Baseline browser hardening headers."""
    csp = os.getenv(
        "CONTENT_SECURITY_POLICY",
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https: wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'",
    )
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "X-XSS-Protection": "0",
        "Content-Security-Policy": csp,
    }
    if _is_production() or (request.url.scheme == "https"):
        headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return headers


def _request_origin_ok(request: Request) -> bool:
    """CSRF defense for cookie-authenticated mutating requests."""
    origin = (request.headers.get("origin") or "").strip()
    referer = (request.headers.get("referer") or "").strip()
    allowed = set(_cors_origins())
    # Always allow same-host relative
    host = (request.headers.get("host") or "").split(":")[0].lower()
    if host:
        allowed.add(f"http://{host}")
        allowed.add(f"https://{host}")
        if host in {"localhost", "127.0.0.1"}:
            allowed.add(f"http://{host}:8080")
            allowed.add(f"http://{host}:8000")

    def _match(value: str) -> bool:
        if not value:
            return False
        try:
            parsed = urlparse(value)
            base = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
            return base in {a.rstrip("/") for a in allowed}
        except Exception:
            return False

    if origin:
        return _match(origin)
    if referer:
        return _match(referer)
    # No Origin/Referer: allow Bearer-only clients (non-browser) — cookie-only blocked below
    return True


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # TrustedHost in production
        if _is_production() and os.getenv("TRUSTED_HOST_ENFORCE", "true").lower() in {
            "1",
            "true",
            "yes",
        }:
            host = (request.headers.get("host") or "").split(":")[0].lower()
            allowed = _allowed_hosts()
            # If only localhost defaults + no APP_BASE_URL, skip hard fail (misconfig)
            configured = bool((os.getenv("ALLOWED_HOSTS") or os.getenv("APP_BASE_URL") or "").strip())
            if configured and host and host not in allowed:
                return JSONResponse(
                    {"error": "invalid_host", "message": "Host header rejected."},
                    status_code=400,
                )

        # CSRF: cookie present + mutating → require Origin/Referer match
        if request.method not in SAFE_METHODS:
            cookie = request.cookies.get("bd_token")
            auth = request.headers.get("authorization") or ""
            if cookie and not auth.startswith("Bearer ") and not _request_origin_ok(request):
                return JSONResponse(
                    {
                        "error": "csrf_rejected",
                        "message": "Cross-site request blocked. Send a same-origin Origin or use Bearer token.",
                    },
                    status_code=403,
                )

        response = await call_next(request)
        for key, value in security_headers_for(request).items():
            response.headers.setdefault(key, value)
        response.headers.setdefault("X-Security-Hardening", "1")
        return response


def apply_cors(app) -> None:
    """Attach explicit CORS allowlist — never '*' with credentials."""
    try:
        from fastapi.middleware.cors import CORSMiddleware
    except Exception:
        return
    origins = _cors_origins()
    if not origins:
        # Dev default: local UI only
        origins = ["http://localhost:8080", "http://127.0.0.1:8080"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Admin-Key", "X-API-Key", "Accept"],
        max_age=600,
    )


def cookie_session_kwargs(*, max_age: int | None = None) -> dict:
    """HttpOnly Secure SameSite cookie flags for bd_token."""
    base = (os.getenv("APP_BASE_URL") or "").strip().lower()
    secure = base.startswith("https") or _is_production()
    return {
        "key": "bd_token",
        "httponly": True,
        "samesite": "lax",
        "secure": secure,
        "max_age": max_age if max_age is not None else 60 * 60 * 24 * int(os.getenv("AUTH_SESSION_DAYS", "30")),
        "path": "/",
    }
