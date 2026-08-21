"""RVM API — single governing reference for requirement status."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.openapi_responses import COMMON_ERROR_RESPONSES
from rvm.baseline import load_baseline
from rvm.run import load_rvm, load_rvm_summary

router = APIRouter(prefix="/api/rvm", tags=["rvm"], responses=COMMON_ERROR_RESPONSES)


@router.get("/summary")
async def rvm_summary() -> dict[str, Any]:
    summary = load_rvm_summary()
    if not summary:
        raise HTTPException(status_code=404, detail="rvm_not_generated — run scripts/run_rvm_verification.py")
    return summary


@router.get("/baseline")
async def rvm_baseline() -> dict[str, Any]:
    return load_baseline()


@router.get("/matrix")
async def rvm_matrix(
    status: str | None = Query(None, description="Filter: PASS, FAIL, EXTERNAL_EVIDENCE_REQUIRED"),
    kind: str | None = Query(None, description="Filter: capability, control, platform, commercial, institutional"),
    limit: int = Query(100, ge=1, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    data = load_rvm()
    if not data:
        raise HTTPException(status_code=404, detail="rvm_not_generated")
    rows = data.get("requirements", [])
    if status:
        rows = [r for r in rows if r.get("final_status") == status.upper()]
    if kind:
        rows = [r for r in rows if r.get("kind") == kind]
    total = len(rows)
    page = rows[offset : offset + limit]
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "summary": data.get("summary"),
        "requirements": page,
    }


@router.get("/requirement/{req_id}")
async def rvm_requirement(req_id: str) -> dict[str, Any]:
    data = load_rvm()
    if not data:
        raise HTTPException(status_code=404, detail="rvm_not_generated")
    for row in data.get("requirements", []):
        if row.get("id") == req_id.upper() or row.get("id") == req_id:
            return row
    raise HTTPException(status_code=404, detail="requirement_not_found")
