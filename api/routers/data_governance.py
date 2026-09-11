"""Data Governance API (DIG index bindings)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

router = APIRouter(tags=["data-governance"])


@router.get("/api/data-governance/status")
async def data_governance_status() -> dict[str, Any]:
    from data_governance import usage_rights_status
    from data_governance.registry import list_sources

    return {**usage_rights_status(), "sources": list_sources()}


@router.post("/api/data-governance/admit")
async def data_governance_admit(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from data_governance.freshness import gate_admission

    return gate_admission(body)


@router.get("/api/data-governance/sources")
async def data_governance_sources() -> dict[str, Any]:
    from data_governance.registry import list_sources

    return {"count": len(list_sources()), "items": list_sources()}


@router.get("/api/data-governance/rights/{source_id}")
async def data_governance_rights(source_id: str, purpose: str = "analytics") -> dict[str, Any]:
    from data_governance import assert_usage_allowed

    result = assert_usage_allowed(source_id, purpose=purpose)
    if not result["allowed"]:
        raise HTTPException(status_code=403, detail=result)
    return result
