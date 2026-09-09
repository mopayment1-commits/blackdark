"""Server-side anonymous authorization boundary — AV §18."""

from __future__ import annotations

from typing import Any

from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from anonymous_visitor.allowlist import is_anonymous_allowed, is_anonymous_denied, match_allowlist_entry
from anonymous_visitor.protections import PublicProtectionError, check_public_protections, release_public_concurrency
from anonymous_visitor.states import ProductAuthState, resolve_product_state


def _client_id(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for") or ""
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    if request.client and request.client.host:
        return request.client.host[:64]
    return "anonymous"


async def _extract_user(request: Request) -> dict[str, Any] | None:
    auth = request.headers.get("authorization") or ""
    token = None
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
    if not token:
        bd_token = request.cookies.get("bd_token")
        if bd_token:
            from security_middleware import cookie_to_session_bearer

            token = cookie_to_session_bearer(bd_token)
    if not token:
        return None
    try:
        from auth_service import get_user_from_token

        return await get_user_from_token(token)
    except Exception:
        return None


async def resolve_request_auth_state(request: Request) -> ProductAuthState:
    return resolve_product_state(await _extract_user(request))


def _has_admin_key(request: Request) -> bool:
    import os

    expected = os.getenv("ADMIN_API_KEY", "").strip()
    if not expected:
        return False
    got = (request.headers.get("x-admin-key") or request.headers.get("X-Admin-Key") or "").strip()
    return bool(got) and got == expected


async def has_authenticated_session(request: Request) -> bool:
    if _has_admin_key(request):
        return True
    return (await resolve_request_auth_state(request)) != ProductAuthState.ANONYMOUS


def anonymous_auth_response(*, status_code: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(
        {
            "ok": False,
            "error": code,
            "detail": detail,
            "auth_state": ProductAuthState.ANONYMOUS.value,
            "server_side_enforcement": True,
        },
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def protection_error_response(err: PublicProtectionError) -> JSONResponse:
    headers = {"Cache-Control": "no-store", "Retry-After": str(int(err.retry_after_sec or 60))}
    return JSONResponse(
        {
            "ok": False,
            "error": err.code,
            "detail": "Public API protection triggered",
            "auth_state": ProductAuthState.ANONYMOUS.value,
            "degraded": True,
        },
        status_code=429,
        headers=headers,
    )


async def enforce_anonymous_boundary(request: Request, call_next) -> Response:
    path = request.url.path or ""
    method = request.method.upper()

    # Only enforce on API paths and explicitly denied prefixes.
    enforce = path.startswith("/api/") or is_anonymous_denied(path)
    if not enforce:
        return await call_next(request)

    if await has_authenticated_session(request):
        return await call_next(request)

    if is_anonymous_denied(path):
        return anonymous_auth_response(
            status_code=401,
            code="authentication_required",
            detail="Private route — account required",
        )

    entry = match_allowlist_entry(method, path)
    client_id = _client_id(request)
    if entry is not None:
        try:
            check_public_protections(method=method, path=path, client_id=client_id, entry=entry)
        except PublicProtectionError as err:
            return protection_error_response(err)
        try:
            response = await call_next(request)
        finally:
            release_public_concurrency(method=method, path=path, client_id=client_id)
        if entry.cache_policy and response.status_code < 400 and "Cache-Control" not in response.headers:
            response.headers["Cache-Control"] = entry.cache_policy
        response.headers["X-BD-Auth-State"] = ProductAuthState.ANONYMOUS.value
        response.headers["X-BD-Public-Route"] = "true"
        return response

    response = await call_next(request)
    response.headers["X-BD-Auth-State"] = ProductAuthState.ANONYMOUS.value
    return response
