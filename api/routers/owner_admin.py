"""Owner admin dashboard — /admin HTML + /api/admin/owner-metrics (DB-backed)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from api.openapi_responses import COMMON_ERROR_RESPONSES
from security_auth import require_admin_dev

_ROOT = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=str(_ROOT / "templates"))

router = APIRouter(tags=["owner-admin"], responses=COMMON_ERROR_RESPONSES)


@router.get("/admin", response_class=HTMLResponse)
async def admin_owner_dashboard_page(
    request: Request,
    _admin: dict = Depends(require_admin_dev),
):
    return templates.TemplateResponse(request, "admin_dashboard.html")


@router.get("/api/admin/owner-metrics")
async def api_admin_owner_metrics(_admin: dict = Depends(require_admin_dev)):
    from owner_admin_dashboard import fetch_owner_dashboard_metrics

    return await fetch_owner_dashboard_metrics()
