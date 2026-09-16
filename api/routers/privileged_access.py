"""Privileged access API — step-up, break-glass, access review."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Header, HTTPException

from api.openapi_responses import COMMON_ERROR_RESPONSES
from privileged_access.access_review import access_review_status, list_access_reviews, overdue_reviews, record_access_review
from privileged_access.break_glass import (
    activate_break_glass,
    break_glass_enabled,
    break_glass_status,
    complete_post_use_review,
)
from privileged_access.deps import issue_step_up_for_user
from privileged_access.operations import ProtectedOperation, protected_operation_inventory
from privileged_access.policy import AuthorizationContext, AuthorizationDenied, authorize_financial_operation
from privileged_access.sessions import privileged_session_status
from security_auth import require_admin, require_authenticated

router = APIRouter(prefix="/api/privileged", tags=["privileged-access"], responses=COMMON_ERROR_RESPONSES)


@router.get("/operations")
async def privileged_operations_inventory(_admin: dict = Depends(require_admin)):
    return {"operations": protected_operation_inventory()}


@router.post("/step-up")
async def create_step_up_grant(
    body: dict = Body(default={}),
    user: dict = Depends(require_authenticated),
    x_admin_totp: str | None = Header(default=None, alias="X-Admin-TOTP"),
    x_mfa_code: str | None = Header(default=None, alias="X-MFA-Code"),
):
    operation = str(body.get("operation") or "")
    try:
        op = ProtectedOperation(operation)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_operation") from None
    return await issue_step_up_for_user(
        user=user,
        operation=op,
        x_admin_totp=x_admin_totp,
        x_mfa_code=x_mfa_code,
    )


@router.get("/session")
async def privileged_session(user: dict = Depends(require_authenticated)):
    subject = str(user.get("id") or user.get("email") or "")
    return privileged_session_status(subject)


@router.post("/break-glass/activate")
async def break_glass_activate(
    body: dict = Body(default={}),
    admin: dict = Depends(require_admin),
    x_step_up_token: str | None = Header(default=None, alias="X-Step-Up-Token"),
    x_actor_email: str | None = Header(default=None, alias="X-Actor-Email"),
    x_admin_totp: str | None = Header(default=None, alias="X-Admin-TOTP"),
    x_mfa_code: str | None = Header(default=None, alias="X-MFA-Code"),
):
    ctx = AuthorizationContext(
        subject_id=str(admin.get("email") or admin.get("id") or ""),
        subject_email=str(admin.get("email") or x_actor_email or ""),
        operation=ProtectedOperation.BREAK_GLASS_ACTIVATE,
        is_admin=True,
    )
    try:
        await authorize_financial_operation(
            ctx,
            user=admin,
            x_step_up_token=x_step_up_token,
            x_actor_email=x_actor_email,
            x_admin_totp=x_admin_totp,
            x_mfa_code=x_mfa_code,
        )
    except AuthorizationDenied as exc:
        raise HTTPException(status_code=exc.status_code, detail={"error": exc.reason}) from exc
    if not break_glass_enabled():
        raise HTTPException(status_code=403, detail={"error": "break_glass_disabled"})
    try:
        rec = activate_break_glass(
            actor_id=str(admin.get("id") or admin.get("email")),
            actor_email=str(admin.get("email") or x_actor_email or ""),
            reason=str(body.get("reason") or ""),
            scope=str(body.get("scope") or "financial_read"),
        )
    except PermissionError:
        raise HTTPException(status_code=403, detail={"error": "break_glass_disabled"}) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": str(exc)}) from exc
    return rec


@router.get("/break-glass/status")
async def break_glass_state(_admin: dict = Depends(require_admin)):
    return break_glass_status()


@router.post("/break-glass/review")
async def break_glass_post_use_review(
    body: dict = Body(default={}),
    admin: dict = Depends(require_admin),
):
    try:
        return complete_post_use_review(
            str(body.get("grant_id") or ""),
            reviewer=str(admin.get("email") or ""),
            outcome=str(body.get("outcome") or "reviewed"),
            notes=str(body.get("notes") or ""),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail={"error": str(exc)}) from exc


@router.post("/access-review")
async def submit_access_review(
    body: dict = Body(default={}),
    admin: dict = Depends(require_admin),
):
    decision = str(body.get("decision") or "").upper()
    if decision not in {"KEEP", "REVOKE", "MODIFY"}:
        raise HTTPException(status_code=400, detail="invalid_decision")
    return record_access_review(
        reviewer=str(admin.get("email") or ""),
        subject=str(body.get("subject") or ""),
        grant_type=str(body.get("grant_type") or "privileged"),
        decision=decision,  # type: ignore[arg-type]
        reason=str(body.get("reason") or ""),
    )


@router.get("/access-review/status")
async def access_review_state(_admin: dict = Depends(require_admin)):
    return {
        **access_review_status(),
        "overdue": overdue_reviews(),
        "recent": list_access_reviews(limit=20),
    }
