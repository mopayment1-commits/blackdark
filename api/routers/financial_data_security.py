"""Financial Data Security API routes — FDS-01→FDS-25 evidence surface."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Query

from api.openapi_responses import COMMON_ERROR_RESPONSES
from financial_data_security.controls import evaluate_fds_controls, fds_control_matrix
from financial_data_security.evidence import collect_fds_evidence

router = APIRouter(
    prefix="/api/financial-data-security",
    tags=["financial-data-security"],
    responses=COMMON_ERROR_RESPONSES,
)


@router.get("/status")
async def financial_data_security_status() -> dict[str, Any]:
    return {"ok": True, **evaluate_fds_controls()}


@router.get("/matrix")
async def financial_data_security_matrix(
    head: str | None = Query(None, description="Optional git SHA for evidence pinning"),
) -> dict[str, Any]:
    matrix = fds_control_matrix(head=head)
    return {"ok": True, "matrix": matrix, "total": len(matrix)}


@router.get("/evidence")
async def financial_data_security_evidence(
    head: str | None = Query(None),
) -> dict[str, Any]:
    return {"ok": True, **collect_fds_evidence(head=head)}


@router.post("/evaluate")
async def financial_data_security_evaluate(
    payload: dict[str, Any] = Body(default={}),
) -> dict[str, Any]:
    head = payload.get("head")
    result = evaluate_fds_controls(head=str(head) if head else None)
    return {"ok": True, "evaluation": result}
