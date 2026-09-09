"""Failure system API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request

from failure.correlation import require_correlation_id
from failure.incident import component_status_report, global_banner_payload
from failure.injection import FAULT_MATRIX, FaultKind, inject_fault
from failure.support import support_handoff
from i18n_service import resolve_request_lang

router = APIRouter(prefix="/api/failure", tags=["failure"])


@router.get("/status/components")
async def failure_component_status() -> dict[str, Any]:
    base = component_status_report()
    try:
        from site_services import public_status_report

        merged = public_status_report()
        merged["failure_components"] = base["components"]
        merged["open_incidents"] = base.get("incidents") or []
        return merged
    except Exception:
        return base


@router.get("/incident/banner")
async def failure_incident_banner(request: Request) -> dict[str, Any]:
    lang = resolve_request_lang(request)
    banner = global_banner_payload(lang=lang)
    return {"banner": banner}


@router.get("/support/handoff")
async def failure_support(
    request: Request,
    component: str = Query("api"),
    action: str = Query("unknown"),
    summary_key: str = Query("error.generic"),
) -> dict[str, Any]:
    lang = resolve_request_lang(request)
    return support_handoff(
        correlation_id=require_correlation_id(),
        component=component,
        action=action,
        summary_key=summary_key,
        lang=lang,
    )


@router.get("/inject/{fault}")
async def failure_inject(fault: str) -> dict[str, Any]:
    kind = FaultKind(fault)
    return inject_fault(kind, correlation_id=require_correlation_id())
