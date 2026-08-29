"""GDPR / privacy API router."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from security_auth import require_authenticated

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/api/privacy", tags=["privacy"], responses=COMMON_ERROR_RESPONSES)


@router.get("/status")
async def privacy_status():
    from gdpr_service import gdpr_compliance_status

    return gdpr_compliance_status()


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


@router.post("/consent")
async def record_consent(
    user: dict = Depends(require_authenticated),
    body: dict = Body(default={}),
):
    """#58 — explicit GDPR consent logging."""
    from bd_platform.legal_commercial_layer import record_gdpr_consent_58

    email = str(user.get("email") or body.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="No email")
    return record_gdpr_consent_58(
        user_email=email,
        marketing=bool(body.get("marketing", False)),
        cookies=bool(body.get("cookies", True)),
        locale=str(body.get("locale", "en")),
        country=str(body.get("country", "")),
    )


@router.get("/gdpr/status")
async def gdpr_layer_status():
    """#58 — GDPR compliance layer status."""
    from bd_platform.legal_commercial_layer import gdpr_compliance_status_58

    return gdpr_compliance_status_58()
