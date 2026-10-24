"""Owner admin dashboard — /admin HTML + admin APIs (DB-backed, deny by default)."""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from api.openapi_responses import COMMON_ERROR_RESPONSES
from security_auth import require_admin_dev

_ROOT = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(_ROOT / "templates"))

router = APIRouter(tags=["owner-admin"], responses=COMMON_ERROR_RESPONSES)


@router.get("/admin", response_class=HTMLResponse)
async def admin_owner_dashboard_page(
    request: Request,
    admin: dict = Depends(require_admin_dev),
):
    from i18n_service import template_context

    ctx = template_context(request, {"admin_email": admin.get("email") or ""})
    return templates.TemplateResponse(request, "admin_dashboard.html", ctx)


@router.get("/api/admin/owner-metrics")
async def api_admin_owner_metrics(_admin: dict = Depends(require_admin_dev)):
    from owner_admin_dashboard import fetch_owner_dashboard_metrics

    return await fetch_owner_dashboard_metrics()


@router.get("/api/admin/site-health")
async def api_admin_site_health(_admin: dict = Depends(require_admin_dev)):
    from admin_console import fetch_site_health

    return await fetch_site_health()


@router.get("/api/admin/users")
async def api_admin_search_users(
    q: str = "",
    limit: int = 50,
    _admin: dict = Depends(require_admin_dev),
):
    from admin_console import search_users

    return {"users": await search_users(q, limit=limit)}


class AdminUserPatch(BaseModel):
    plan: str | None = Field(default=None, max_length=64)
    subscription_status: str | None = Field(default=None, max_length=64)


@router.patch("/api/admin/users/{user_id}")
async def api_admin_patch_user(
    user_id: int,
    body: AdminUserPatch,
    request: Request,
    admin: dict = Depends(require_admin_dev),
):
    from admin_console import payload_hash_obj, update_user_admin
    from audit_registry import record_audit_log

    if body.plan is None and body.subscription_status is None:
        raise HTTPException(status_code=400, detail="no_changes")

    payload = {"user_id": user_id, "plan": body.plan, "subscription_status": body.subscription_status}
    try:
        user = await update_user_admin(
            user_id,
            plan=body.plan,
            subscription_status=body.subscription_status,
        )
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="user_not_found") from exc
        raise

    actor = str(admin.get("email") or "admin@system")
    await record_audit_log(
        actor=actor,
        action="admin.user_update",
        payload_hash=payload_hash_obj(payload),
        outcome="ok",
        request_method=request.method,
        request_path=str(request.url.path),
        metadata={"target_user_id": user_id, **payload},
    )
    return {"user": user}


@router.get("/api/admin/audit-logs")
async def api_admin_audit_logs(
    limit: int = 100,
    actor: str | None = None,
    action: str | None = None,
    _admin: dict = Depends(require_admin_dev),
):
    from audit_registry import fetch_audit_logs

    rows = await fetch_audit_logs(actor=actor, action=action, limit=min(max(limit, 1), 500))
    return {"logs": rows}


@router.get("/api/admin/waitlist/summary")
async def api_admin_waitlist_summary(_admin: dict = Depends(require_admin_dev)):
    from waitlist_newsletter_service import waitlist_newsletter_summary

    return await waitlist_newsletter_summary()


@router.get("/api/admin/waitlist/entries")
async def api_admin_waitlist_entries(
    limit: int = 500,
    offset: int = 0,
    _admin: dict = Depends(require_admin_dev),
):
    from database import db_count_waitlist, fetch_waitlist_entries

    lim = min(max(limit, 1), 5000)
    off = max(offset, 0)
    rows = await fetch_waitlist_entries(limit=lim, offset=off)
    return {"count": await db_count_waitlist(), "entries": rows, "limit": lim, "offset": off}


@router.get("/api/admin/waitlist/export.csv")
async def api_admin_waitlist_export_csv(_admin: dict = Depends(require_admin_dev)):
    import csv
    import io

    from database import fetch_waitlist_entries

    rows = await fetch_waitlist_entries(limit=10000, offset=0)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "email", "name", "joined_at"])
    for row in rows:
        writer.writerow(
            [
                row.get("id"),
                row.get("email") or "",
                row.get("name") or "",
                row.get("joined_at") or "",
            ]
        )
    body = buf.getvalue()
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="waitlist.csv"'},
    )


class WaitlistNewsletterBody(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=20000)


@router.post("/api/admin/waitlist/newsletter")
async def api_admin_waitlist_newsletter(
    body: WaitlistNewsletterBody,
    request: Request,
    admin: dict = Depends(require_admin_dev),
):
    from admin_console import payload_hash_obj
    from audit_registry import record_audit_log
    from waitlist_newsletter_service import send_waitlist_newsletter

    try:
        result = await send_waitlist_newsletter(body.subject, body.message)
    except ValueError as exc:
        code = str(exc)
        if code in {"subject_required", "message_required"}:
            raise HTTPException(status_code=400, detail=code) from exc
        raise

    actor = str(admin.get("email") or "admin@system")
    await record_audit_log(
        actor=actor,
        action="admin.waitlist_newsletter",
        payload_hash=payload_hash_obj(
            {"subject": body.subject[:80], "total": result.get("total"), "sent": result.get("sent")}
        ),
        outcome="ok" if int(result.get("failed") or 0) == 0 else "partial",
        request_method=request.method,
        request_path=str(request.url.path),
        metadata={
            "total": result.get("total"),
            "sent": result.get("sent"),
            "failed": result.get("failed"),
            "delivery": result.get("delivery"),
        },
    )
    return {"ok": True, **result}


class ProvisionOwnerAdminBody(BaseModel):
    email: str = Field(..., max_length=320)
    password: str | None = Field(default=None, min_length=12, max_length=256)
    create: bool = True


@router.post("/api/internal/owner-admin/provision")
async def internal_provision_owner_admin(request: Request, body: ProvisionOwnerAdminBody):
    """Reset owner admin password on the live DB (bootstrap token — same as audit-chain bootstrap)."""
    from oracle_chain_bootstrap import _verify_bootstrap_token
    from security_auth import admin_emails

    _verify_bootstrap_token(request)
    email = body.email.strip().lower()
    password = body.password or f"Blackdark-Owner-{secrets.token_urlsafe(14)}"
    if len(password) < 12:
        raise HTTPException(status_code=400, detail="password_too_short")

    from owner_admin_provision import provision_owner_admin

    try:
        result = await provision_owner_admin(email, password, create_if_missing=body.create)
    except ValueError as exc:
        if str(exc) == "user_not_found":
            raise HTTPException(status_code=404, detail="user_not_found") from exc
        raise
    admins = admin_emails()
    return {
        "ok": True,
        **result,
        "password": password,
        "admin_emails_configured": bool(admins),
        "admin_email_in_admin_emails": email in admins,
        "railway_hint": (
            f"Set ADMIN_EMAILS={email} (and optional ADMIN_API_KEY) on the web service, then redeploy."
            if email not in admins
            else None
        ),
    }
