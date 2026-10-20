"""Owner admin dashboard — /admin HTML + admin APIs (DB-backed, deny by default)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
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
    return templates.TemplateResponse(
        request,
        "admin_dashboard.html",
        {"admin_email": admin.get("email") or ""},
    )


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
