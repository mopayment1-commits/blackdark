"""GDPR / privacy API router."""

from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException

from security_auth import optional_user_from_request, require_authenticated

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
    confirm = body.get("confirm") in {True, "true", 1, "1"}
    return await erase_user_data(email, confirmed=confirm)


@router.post("/request-deletion")
async def request_deletion(
    body: dict = Body(default={}),
    user: dict | None = Depends(optional_user_from_request),
):
    """Public GDPR deletion request intake (ticketed; may require verification)."""
    from database import insert_privacy_request
    from security_auth import persist_auth_audit

    email = str(body.get("email") or (user or {}).get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email required")
    details = str(body.get("details") or "")
    request_id = await insert_privacy_request(email, "deletion", details)
    persist_auth_audit(
        event="privacy_deletion_request",
        subject=email,
        reason="request-deletion",
        meta={"request_id": request_id},
    )
    return {
        "success": True,
        "request_id": request_id,
        "status": "received",
        "message": "Deletion request logged. Verified accounts may also use POST /api/privacy/dsr/erase.",
        "immediate_erase_api": "/api/privacy/dsr/erase",
    }


@router.post("/report-issue")
async def report_issue(
    body: dict = Body(default={}),
    user: dict | None = Depends(optional_user_from_request),
):
    """Public issue / inaccuracy report intake."""
    from database import insert_privacy_request
    from security_auth import persist_auth_audit

    email = str(body.get("email") or (user or {}).get("email") or "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email required")
    category = str(body.get("category") or "other").strip().lower()[:32]
    details = str(body.get("details") or "").strip()
    if len(details) < 8:
        raise HTTPException(status_code=400, detail="Please describe the issue (8+ characters)")
    request_id = await insert_privacy_request(email, f"issue:{category}", details)
    persist_auth_audit(
        event="issue_report",
        subject=email,
        reason=category,
        meta={"request_id": request_id},
    )
    return {
        "success": True,
        "request_id": request_id,
        "status": "received",
        "category": category,
    }
