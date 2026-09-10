"""Capability spine API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES
from capability_spine.closure import build_reconciliation_manifest, write_manifest
from capability_spine.integration import enrich_opportunity_capabilities
from capability_spine.registry import CAPABILITY_REGISTRY, scoped_capability_ids

router = APIRouter(prefix="/api/capability-spine", tags=["capability-spine"], responses=COMMON_ERROR_RESPONSES)


@router.get("/registry")
async def capability_registry() -> dict[str, Any]:
    return {
        "ok": True,
        "scope_count": len(scoped_capability_ids()),
        "capabilities": CAPABILITY_REGISTRY,
    }


@router.post("/evaluate")
async def capability_evaluate(
    request: Request,
    payload: dict[str, Any] = Body(default={}),
) -> dict[str, Any]:
    portfolio = payload.get("portfolio") if isinstance(payload.get("portfolio"), dict) else {}
    opp = payload.get("opportunity") if isinstance(payload.get("opportunity"), dict) else payload
    headers = dict(request.headers)
    enriched = enrich_opportunity_capabilities(opp, portfolio=portfolio, headers=headers)
    return {"ok": True, "opportunity": enriched, "capability_spine": enriched.get("capability_spine")}


@router.get("/closure-manifest")
async def closure_manifest() -> dict[str, Any]:
    return build_reconciliation_manifest()


@router.post("/closure-manifest/write")
async def closure_manifest_write() -> dict[str, Any]:
    path = write_manifest()
    return {"ok": True, "path": str(path)}
