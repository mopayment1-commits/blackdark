"""GDPR / privacy API router."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from security_auth import require_authenticated

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.get("/status")
async def privacy_status():
    from gdpr_service import gdpr_compliance_status

    return gdpr_compliance_status()


@router.post("/dsr/export")
async def dsr_export(user: dict = Depends(require_authenticated)):
    """Authenticated user exports their own data (GDPR Art. 15/20)."""
    from gdpr_service import export_user_data

    email = str(user.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="No email on account")
    return await export_user_data(email)


@router.post("/dsr/erase")
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
