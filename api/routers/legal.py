"""Legal / terms acceptance API."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request, Response

from api.deps import optional_user
from terms_consent import (
    TERMS_COOKIE,
    TERMS_VERSION,
    has_accepted_terms,
    record_terms_acceptance,
    terms_status_payload,
)

router = APIRouter(prefix="/api/legal", tags=["legal"])


@router.get("/terms-status")
async def terms_status(request: Request, user: dict | None = Depends(optional_user)):
    accepted = await has_accepted_terms(request, user)
    return terms_status_payload(accepted)


@router.post("/accept-terms")
async def accept_terms(
    request: Request,
    response: Response,
    user: dict | None = Depends(optional_user),
    body: dict = Body(default={}),
):
    ip = request.client.host if request.client else ""
    result = await record_terms_acceptance(
        user=user,
        source=str(body.get("source") or "api"),
        ip=ip,
    )
    secure = (request.url.scheme == "https")
    response.set_cookie(
        key=TERMS_COOKIE,
        value=TERMS_VERSION,
        httponly=False,  # readable by SPA gate; not a secret
        secure=secure,
        samesite="lax",
        max_age=365 * 24 * 3600,
        path="/",
    )
    return result
