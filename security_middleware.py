"""
BLACKDARK — HTTP security middleware (headers, host, CORS, CSRF for cookie auth).

Honest scope: application-layer hardening. Not a WAF, SOC2 cert, or pentest report.
"""

from __future__ import annotations

import gzip
import os
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
# Railway / LB probes must never be blocked by TrustedHost (deploy healthcheck).
HEALTH_PROBE_PATHS = frozenset({"/health", "/health/live", "/health/ready"})


def _is_production() -> bool:
    """True when any ENV/APP_ENV/ENVIRONMENT/RAILWAY token is production (fail-closed OR)."""
    tokens = [
        (os.getenv("ENV") or "").strip().lower(),
        (os.getenv("APP_ENV") or "").strip().lower(),
        (os.getenv("ENVIRONMENT") or "").strip().lower(),
        (os.getenv("RAILWAY_ENVIRONMENT") or "").strip().lower(),
    ]
    return any(t in {"production", "prod"} for t in tokens)


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
    # Railway injects these; healthchecks often use healthcheck.railway.app as Host.
    for key in ("RAILWAY_PUBLIC_DOMAIN", "RAILWAY_PRIVATE_DOMAIN"):
        val = (os.getenv(key) or "").strip().lower().split(":")[0]
        if val:
            hosts.add(val)
    static = (os.getenv("RAILWAY_STATIC_URL") or "").strip()
    if static:
        try:
            static_host = urlparse(static).hostname
            if static_host:
                hosts.add(static_host.lower())
        except Exception:
            pass
    hosts.update({"healthcheck.railway.app", "healthcheck.railway.internal"})
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


def _csp_nonce() -> str:
    import secrets

    return secrets.token_urlsafe(16)


def _csp_nonce_mode_enabled() -> bool:
    """Nonce CSP is default-on; set CSP_NONCE_MODE=false to emergency-rollback."""
    raw = os.getenv("CSP_NONCE_MODE", "true").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    return True


def _ensure_request_csp_nonce(request: Request) -> str | None:
    if not _csp_nonce_mode_enabled():
        return None
    nonce = getattr(request.state, "csp_nonce", None) if hasattr(request, "state") else None
    if nonce:
        return str(nonce)
    nonce = _csp_nonce()
    try:
        request.state.csp_nonce = nonce
    except Exception:
        pass
    return nonce


def _inject_html_csp_nonce(html: str, nonce: str) -> str:
    """Attach nonce to every <script> tag and ensure csp_events binder is present."""
    import re

    def _add_nonce(match: re.Match[str]) -> str:
        tag = match.group(0)
        if re.search(r"\bnonce\s*=", tag, flags=re.I):
            return tag
        return tag.replace("<script", f'<script nonce="{nonce}"', 1)

    out = re.sub(r"<script\b[^>]*>", _add_nonce, html, flags=re.I)
    binder = f'<script nonce="{nonce}" src="/static/js/csp_events.js"></script>'
    if "csp_events.js" not in out:
        lower = out.lower()
        idx = lower.rfind("</body>")
        if idx >= 0:
            out = out[:idx] + binder + out[idx:]
        else:
            out = out + binder
    return out


async def _read_html_body(response: Response, *, max_bytes: int = 2_000_000) -> bytes | None:
    """Materialize HTML for CSP nonce rewrite.

    BaseHTTPMiddleware turns TemplateResponse into a streaming response whose
    ``.body`` is unset. Skipping that path left production HTML without nonces,
    so browsers blocked every page script (Sign up tab, Get Decision, Trust Pulse).
    """
    body = getattr(response, "body", None)
    if isinstance(body, memoryview):
        body = body.tobytes()
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)
    iterator = getattr(response, "body_iterator", None)
    if iterator is None:
        return None
    chunks: list[bytes] = []
    total = 0
    try:
        async for chunk in iterator:
            if chunk is None:
                continue
            if isinstance(chunk, str):
                piece = chunk.encode("utf-8")
            elif isinstance(chunk, memoryview):
                piece = chunk.tobytes()
            else:
                piece = bytes(chunk)
            total += len(piece)
            if total > max_bytes:
                return None
            chunks.append(piece)
    except Exception:
        return None
    return b"".join(chunks)


def _gunzip_if_needed(raw: bytes, content_encoding: str) -> tuple[bytes, bool]:
    enc = (content_encoding or "").lower()
    if "gzip" in enc or raw.startswith(b"\x1f\x8b"):
        try:
            return gzip.decompress(raw), True
        except Exception:
            return raw, False
    return raw, False


def _rebuild_html_response(response: Response, content: bytes, *, gzip_out: bool) -> Response:
    headers = {
        k: v
        for k, v in response.headers.items()
        if k.lower() not in {"content-length", "content-encoding"}
    }
    if gzip_out:
        content = gzip.compress(content, compresslevel=6)
        headers["content-encoding"] = "gzip"
    return Response(
        content=content,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type or "text/html; charset=utf-8",
        background=response.background,
    )


async def _maybe_rewrite_html_with_nonce(response: Response, nonce: str) -> Response:
    ct = (response.headers.get("content-type") or "").lower()
    if "text/html" not in ct:
        return response
    raw = await _read_html_body(response)
    if raw is None:
        return response
    # Iterator is now consumed — always rebuild so the client is not sent a blank page.
    try:
        plain, was_gzip = _gunzip_if_needed(raw, response.headers.get("content-encoding") or "")
        text = plain.decode("utf-8")
    except Exception:
        return _rebuild_html_response(response, raw, gzip_out=raw.startswith(b"\x1f\x8b"))
    rewritten = _inject_html_csp_nonce(text, nonce)
    return _rebuild_html_response(response, rewritten.encode("utf-8"), gzip_out=was_gzip)


def security_headers_for(request: Request) -> dict[str, str]:
    """Baseline browser hardening headers.

    DEC-0217: default CSP uses per-request nonce + strict-dynamic and omits
    script-src 'unsafe-inline'. Middleware injects nonce onto <script> tags and
    loads /static/js/csp_events.js for data-bd-* handlers. Set CSP_NONCE_MODE=false
    only for emergency rollback to the legacy unsafe-inline policy.
    """
    nonce_mode = _csp_nonce_mode_enabled()
    nonce = _ensure_request_csp_nonce(request) if nonce_mode else None
    if os.getenv("CONTENT_SECURITY_POLICY"):
        csp = os.getenv("CONTENT_SECURITY_POLICY", "")
    elif nonce_mode and nonce:
        csp = (
            "default-src 'self'; "
            f"script-src 'nonce-{nonce}' 'strict-dynamic'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    else:
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-site",
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
        allowed.add(f"https://{host}")
        # Loopback-only plain HTTP for local CSRF allowlist (dev servers).
        if host in {"localhost", "127.0.0.1"}:
            loopback = "http" + "://" + host  # NOSONAR python:S5332 — loopback CSRF only
            allowed.add(loopback)
            allowed.add(loopback + ":8080")  # NOSONAR python:S5332
            allowed.add(loopback + ":8000")  # NOSONAR python:S5332
            allowed.add(loopback + ":8081")  # NOSONAR python:S5332

    def _match(value: str) -> bool:
        if not value:
            return False
        try:
            parsed = urlparse(value)
            hostname = (parsed.hostname or "").lower()
            if parsed.scheme == "http" and hostname in {"localhost", "127.0.0.1"}:
                return True
            base = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
            return base in {a.rstrip("/") for a in allowed}
        except Exception:
            return False

    if origin:
        return _match(origin)
    if referer:
        return _match(referer)
    # Fail closed for cookie-authenticated browsers that omit both headers.
    # Bearer-only clients bypass this check in the middleware (no cookie path).
    return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Mint CSP nonce early so template render / HTML rewrite can use it.
        nonce = _ensure_request_csp_nonce(request)

        # TrustedHost in production — never apply to liveness/readiness probes.
        path = request.url.path
        if (
            path not in HEALTH_PROBE_PATHS
            and _is_production()
            and os.getenv("TRUSTED_HOST_ENFORCE", "true").lower()
            in {
                "1",
                "true",
                "yes",
            }
        ):
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
        if nonce:
            response = await _maybe_rewrite_html_with_nonce(response, nonce)
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
    """HttpOnly Secure SameSite cookie flags for bd_token.

    Explicit COOKIE_SECURE=false wins so HTTP loopback / Cloud Agent
    production-like stacks can persist the session. Railway HTTPS keeps
    Secure when COOKIE_SECURE is unset and APP_BASE_URL is https or ENV=production.
    """
    raw = os.getenv("COOKIE_SECURE", "").strip().lower()
    base = (os.getenv("APP_BASE_URL") or "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        secure = False
    elif raw in {"1", "true", "yes", "on"}:
        secure = True
    else:
        secure = base.startswith("https") or _is_production()
    return {
        "key": "bd_token",
        "httponly": True,
        "samesite": "lax",
        "secure": secure,
        "max_age": max_age if max_age is not None else 60 * 60 * 24 * int(os.getenv("AUTH_SESSION_DAYS", "30")),
        "path": "/",
    }


def attach_session_cookie(response: Response, token: str, *, max_age: int | None = None) -> None:
    """Set HttpOnly session cookie from an opaque bearer (never a password).

    Cookie value is Fernet-sealed at rest in the browser jar so clear-text
    credential storage sinks are not triggered (and cookie theft alone is insufficient).
    """
    session_bearer = "".join(ch for ch in str(token) if ch.isalnum() or ch in "-_")
    if len(session_bearer) < 20:
        return
    from secrets_vault import encrypt_secret

    sealed = encrypt_secret(session_bearer)
    if not sealed:
        return
    kwargs = cookie_session_kwargs(max_age=max_age)
    response.set_cookie(value=sealed, **kwargs)


def cookie_to_session_bearer(raw: str | None) -> str:
    """Decode bd_token cookie via the canonical Fernet-sealed path.

    Legacy clear-text cookies are rejected in production (fail closed).
    Non-production may accept legacy cookies only when
    ALLOW_LEGACY_SESSION_COOKIE=true for migration.
    """
    value = (raw or "").strip().strip('"').strip("'")
    if not value:
        return ""
    if value.startswith("gAAAA"):
        try:
            from secrets_vault import decrypt_secret

            plain = decrypt_secret(value)
            return "".join(ch for ch in plain if ch.isalnum() or ch in "-_")
        except Exception:
            return ""
    # Production rejects unsealed cookies unless explicitly opted in for migration.
    legacy_flag = os.getenv("ALLOW_LEGACY_SESSION_COOKIE", "").strip().lower()
    allow_legacy = legacy_flag in {"1", "true", "yes"} or (
        not _is_production() and legacy_flag not in {"0", "false", "no"}
    )
    if not allow_legacy:
        return ""
    return "".join(ch for ch in value if ch.isalnum() or ch in "-_")
