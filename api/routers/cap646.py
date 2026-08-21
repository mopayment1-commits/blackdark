"""CAP646 capability closure API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.openapi_responses import COMMON_ERROR_RESPONSES
from cap646.catalog import catalog_by_id, matrix_by_id
from cap646.closure import final_institutional_verification, get_closure_status, verify_capability
from cap646.institutional_gateway import gateway_audit_log, gateway_execute
from cap646.runtime import execute_capability
from security_auth import optional_user_from_request

router = APIRouter(prefix="/api/cap646", tags=["cap646"], responses=COMMON_ERROR_RESPONSES)


class ExecuteBody(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)
    org_id: str | None = None


@router.get("/catalog")
async def cap646_catalog(limit: int = Query(646, ge=1, le=646)) -> dict[str, Any]:
    rows = list(catalog_by_id().values())[:limit]
    return {"count": len(rows), "items": rows}


@router.get("/closure/status")
async def cap646_closure_status(sample: bool = Query(True)) -> dict[str, Any]:
    if sample:
        return await final_institutional_verification(sample_only=True)
    return await get_closure_status()


@router.get("/closure/verify/{capability_id}")
async def cap646_verify(capability_id: int) -> dict[str, Any]:
    if capability_id < 1 or capability_id > 646:
        raise HTTPException(status_code=404, detail="capability_id_out_of_range")
    return await verify_capability(capability_id)


@router.get("/gateway/audit")
async def cap646_gateway_audit(limit: int = Query(50, ge=1, le=500)) -> dict[str, Any]:
    return {"items": gateway_audit_log(limit)}


@router.get("/matrix/{capability_id}")
async def cap646_matrix_row(capability_id: int) -> dict[str, Any]:
    if capability_id < 1 or capability_id > 646:
        raise HTTPException(status_code=404, detail="capability_id_out_of_range")
    return matrix_by_id()[capability_id]


@router.get("/{capability_id}")
async def cap646_get(
    capability_id: int,
    user: Annotated[dict | None, Depends(optional_user_from_request)] = None,
) -> dict[str, Any]:
    if capability_id < 1 or capability_id > 646:
        raise HTTPException(status_code=404, detail="capability_id_out_of_range")
    return await execute_capability(capability_id, user=user, params={"symbol": "BTC"})


@router.post("/{capability_id}/execute")
async def cap646_execute(
    capability_id: int,
    body: ExecuteBody,
    user: Annotated[dict | None, Depends(optional_user_from_request)] = None,
) -> dict[str, Any]:
    if capability_id < 1 or capability_id > 646:
        raise HTTPException(status_code=404, detail="capability_id_out_of_range")
    return await gateway_execute(
        capability_id,
        user=user,
        org_id=body.org_id,
        params=body.params,
    )
