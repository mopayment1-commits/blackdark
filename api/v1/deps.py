"""FastAPI dependencies for Decision API v1."""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from api.v1.audit import error_code_from_detail, persist_decision_api_audit
from api.v1.contract import API_VERSION, CONTRACT_NAME, http_exception_envelope
from api.v1.keys import authenticate_decision_api_key, principal_has_scope
from api.v1.quota import enforce_key_quotas


def request_id_of(request: Request) -> str:
    existing = getattr(request.state, "request_id", None)
    if existing:
        return str(existing)
    incoming = (request.headers.get("x-request-id") or "").strip()
    rid = incoming[:64] if incoming else uuid.uuid4().hex
    request.state.request_id = rid
    return rid


def _auth_error(request: Request, message: str = "Valid Decision API key required") -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"error": "unauthorized", "message": message},
        headers={"WWW-Authenticate": 'Bearer realm="decision-api-v1"'},
    )


async def require_decision_api_key(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> dict[str, Any]:
    presented = (x_api_key or authorization or "").strip()
    if not presented:
        raise _auth_error(request)
    try:
        principal = await authenticate_decision_api_key(presented)
    except PermissionError:
        raise _auth_error(request, "Invalid or revoked API key") from None
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "misconfigured", "message": str(exc)},
        ) from exc
    await enforce_key_quotas(request, principal)
    request.state.decision_api_principal = principal
    return principal


def require_scope(scope: str) -> Callable[..., Any]:
    async def _inner(principal: Annotated[dict[str, Any], Depends(require_decision_api_key)]) -> dict[str, Any]:
        if not principal_has_scope(principal, scope):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "insufficient_scope",
                    "message": f"API key is missing required scope: {scope}",
                    "required_scope": scope,
                },
            )
        return principal

    return _inner


class DecisionAPIRoute(APIRoute):
    """Attach request_id, contract headers, and a stable error envelope."""

    def get_route_handler(self):
        inner = super().get_route_handler()

        async def handler(request: Request):
            rid = request_id_of(request)
            try:
                response = await inner(request)
                err = None
            except HTTPException as exc:
                err = error_code_from_detail(exc.detail)
                body = http_exception_envelope(exc.detail, status=exc.status_code, request_id=rid)
                headers = dict(exc.headers or {})
                response = JSONResponse(body, status_code=exc.status_code, headers=headers)
            except Exception:
                from safe_errors import public_error

                err = "internal_error"
                body = http_exception_envelope(
                    {"error": "internal_error", "message": public_error(fallback="Internal error")},
                    status=500,
                    request_id=rid,
                )
                response = JSONResponse(body, status_code=500)
            await persist_decision_api_audit(request, status=response.status_code, error_code=err)
            response.headers.setdefault("X-Request-Id", rid)
            response.headers.setdefault("X-API-Version", API_VERSION)
            response.headers.setdefault("X-Blackdark-Contract", CONTRACT_NAME)
            rl = getattr(request.state, "decision_api_rl", None)
            if isinstance(rl, dict):
                response.headers.setdefault("X-RateLimit-Limit", str(rl.get("limit") or 0))
                response.headers.setdefault("X-RateLimit-Remaining", str(rl.get("remaining") or 0))
                response.headers.setdefault("X-RateLimit-Reset", str(rl.get("reset") or 60))
            return response

        return handler
