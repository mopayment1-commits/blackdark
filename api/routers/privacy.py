"""GDPR / privacy API router."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES
from privileged_access.deps import financial_privilege_dep
from privileged_access.operations import ProtectedOperation
from security_auth import require_authenticated

router = APIRouter(prefix="/api/privacy", tags=["privacy"], responses=COMMON_ERROR_RESPONSES)


@router.get("/status")
async def privacy_status():
    from gdpr_service import gdpr_compliance_status

    return gdpr_compliance_status()


@router.get("/dsr/status", responses=COMMON_ERROR_RESPONSES)
async def dsr_status(user: dict = Depends(require_authenticated)):
    from gdpr_service import dsr_status_for_user

    return await dsr_status_for_user(int(user["id"]))


@router.post("/dsr/export", responses=COMMON_ERROR_RESPONSES)
async def dsr_export(
    request: Request,
    user: dict = Depends(financial_privilege_dep(ProtectedOperation.PRIVACY_DSR_EXPORT)),
):
    """Authenticated user exports their own data (GDPR Art. 15/20)."""
    from gdpr_service import export_user_data
    from identity_audit import log_identity_auth_event

    email = str(user.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="No email on account")
    payload = await export_user_data(email)
    log_identity_auth_event(
        "dsr_export",
        actor=email,
        user_id=int(user["id"]),
        request=request,
    )
    return payload


@router.post("/dsr/erase", responses=COMMON_ERROR_RESPONSES)
async def dsr_erase(
    request: Request,
    user: dict = Depends(financial_privilege_dep(ProtectedOperation.PRIVACY_DSR_ERASE)),
    body: dict = Body(default={}),
):
    """Authenticated user requests erasure (GDPR Art. 17)."""
    from gdpr_service import erase_user_data
    from identity_audit import log_identity_auth_event

    email = str(user.get("email") or "")
    if not email:
        raise HTTPException(status_code=400, detail="No email on account")
    confirm = body.get("confirm") in {True, "true", "1"}
    result = await erase_user_data(email, confirmed=confirm)
    kind = "dsr_erase_completed" if result.get("status") == "erased" else "dsr_erase_requested"
    log_identity_auth_event(
        kind,
        actor=email,
        user_id=int(user["id"]),
        request=request,
        detail={"status": result.get("status")},
    )
    return result
