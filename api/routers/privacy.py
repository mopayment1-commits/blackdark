"""GDPR / privacy API router."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from security_auth import require_authenticated

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/api/privacy", tags=["privacy"], responses=COMMON_ERROR_RESPONSES)


@router.get("/status")
async def privacy_status():
    from gdpr_service import gdpr_compliance_status

    return gdpr_compliance_status()


@router.get("/optional-analytics-banner")
async def optional_analytics_banner(request: Request):
    from supplemental_public_compliance import optional_analytics_banner_payload

    return optional_analytics_banner_payload(request)


def _consent_cookie_kwargs() -> dict:
    from security_middleware import cookie_session_kwargs

    base = cookie_session_kwargs(max_age=60 * 60 * 24 * 365)
    base.pop("key", None)
    base["httponly"] = False
    base["samesite"] = "lax"
    return base


@router.post("/optional-analytics-consent")
async def optional_analytics_consent(request: Request, body: dict = Body(default={})):
    from supplemental_public_compliance import (
        CONSENT_CHOICE_ACCEPT,
        CONSENT_CHOICE_REJECT,
        CONSENT_COOKIE,
        CONSENT_DISMISS_COOKIE,
        record_optional_analytics_consent,
    )

    choice = str(body.get("choice") or "").strip().lower()
    if choice not in {CONSENT_CHOICE_ACCEPT, CONSENT_CHOICE_REJECT}:
        raise HTTPException(status_code=400, detail="choice must be accept or reject")
    user_email = str(body.get("email") or "").strip().lower() or None
    result = record_optional_analytics_consent(choice=choice, request=request, user_email=user_email)
    resp = JSONResponse(result)
    kwargs = _consent_cookie_kwargs()
    resp.set_cookie(CONSENT_COOKIE, choice, **kwargs)
    resp.set_cookie(CONSENT_DISMISS_COOKIE, "1", **kwargs)
    return resp


@router.post("/optional-analytics-dismiss")
async def optional_analytics_dismiss(request: Request):
    """Close banner without granting optional analytics consent."""
    from supplemental_public_compliance import CONSENT_DISMISS_COOKIE

    resp = JSONResponse({"ok": True, "dismissed": True, "consent_recorded": False})
    resp.set_cookie(CONSENT_DISMISS_COOKIE, "1", **_consent_cookie_kwargs())
    return resp


@router.post("/dsr/export", responses=COMMON_ERROR_RESPONSES)
async def dsr_export(user: dict = Depends(require_authenticated)):
    """Authenticated user exports their own data (GDPR Art. 15/20)."""
    from gdpr_service import export_user_data

    email = str(user.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="No email on account")
    return await export_user_data(email)


@router.post("/dsr/erase", responses=COMMON_ERROR_RESPONSES)
async def dsr_erase(
    user: dict = Depends(require_authenticated),
    body: dict = Body(default={}),
):
    """Authenticated user requests erasure (GDPR Art. 17)."""
    from gdpr_service import erase_user_data

    email = str(user.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="No email on account")
    confirm = body.get("confirm") in {True, "true", "1"}
    return await erase_user_data(email, confirmed=confirm)
