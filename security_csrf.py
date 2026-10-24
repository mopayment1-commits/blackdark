"""Double-submit CSRF token (cookie + header/form field)."""

from __future__ import annotations

import hmac
import os
import secrets
from hashlib import sha256

from starlette.requests import Request
from starlette.responses import Response

_COOKIE = "bd_csrf"
_HEADER = "x-csrf-token"
_FORM_FIELD = "_csrf"


def _csrf_secret() -> str:
    from security_auth import _session_token_pepper

    return _session_token_pepper()


def mint_csrf_token() -> str:
    raw = secrets.token_urlsafe(32)
    sig = hmac.new(_csrf_secret().encode(), raw.encode(), sha256).hexdigest()[:16]
    return f"{raw}.{sig}"


def validate_csrf_token(token: str | None) -> bool:
    value = (token or "").strip()
    if "." not in value:
        return False
    raw, sig = value.rsplit(".", 1)
    if len(raw) < 16 or len(sig) != 16:
        return False
    expected = hmac.new(_csrf_secret().encode(), raw.encode(), sha256).hexdigest()[:16]
    return hmac.compare_digest(expected, sig)


def csrf_token_for_request(request: Request) -> str:
    """Synchronizer token for this request (stored on ``request.state`` for HTML meta)."""
    cached = getattr(request.state, "bd_csrf_token", None)
    if isinstance(cached, str) and validate_csrf_token(cached):
        return cached
    existing = request.cookies.get(_COOKIE)
    if existing and validate_csrf_token(existing):
        request.state.bd_csrf_token = existing
        return existing
    token = mint_csrf_token()
    request.state.bd_csrf_token = token
    return token


def attach_csrf_cookie(response: Response, request: Request) -> None:
    token = csrf_token_for_request(request)
    secure = os.getenv("COOKIE_SECURE", "").lower() in {"1", "true", "yes"} or (
        (os.getenv("APP_BASE_URL") or "").startswith("https")
    )
    response.set_cookie(
        key=_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
        max_age=60 * 60 * 12,
    )


def csrf_token_from_request(request: Request) -> str | None:
    header = (request.headers.get(_HEADER) or request.headers.get("X-CSRF-Token") or "").strip()
    if header:
        return header
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        try:
            # Starlette may not have parsed form yet — middleware runs early; header preferred.
            pass
        except Exception:
            pass
    return None


def csrf_required_for_request(request: Request) -> bool:
    if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        return False
    path = request.url.path or ""
    if path.startswith("/static") or path in {"/health", "/health/live", "/health/ready"}:
        return False
    if request.cookies.get("bd_token"):
        return True
    if path in {"/api/auth/login", "/api/auth/register"}:
        return True
    return path in {"/login", "/register", "/join-waitlist", "/admin"}
