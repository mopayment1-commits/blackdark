"""CAP646 capability closure API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.openapi_responses import COMMON_ERROR_RESPONSES
from cap646.catalog import catalog_by_id, matrix_by_id
from cap646.closure import final_institutional_verification, get_closure_status, verify_capability
from cap646.dod import verify_dod, verify_wave
from cap646.functional_dod import verify_functional
from cap646.institutional_gateway import gateway_audit_log, gateway_execute
from cap646.institutional_controls import verify_all_controls
from cap646.platform_chain import verify_data_platform_chain
from cap646.runtime import execute_capability
from cap646.triple_closure import triple_institutional_closure
from cap646.ui_pages import hub_context, user_surface_for
from cap646.waves import WAVE_A, WAVE_B, WAVE_C, WAVE_D
from security_auth import optional_user_from_request

router = APIRouter(prefix="/api/cap646", tags=["cap646"], responses=COMMON_ERROR_RESPONSES)


class ExecuteBody(BaseModel):
    params: dict[str, Any] = Field(default_factory=dict)
    org_id: str | None = None


@router.get("/wave/{wave_id}/ids")
async def cap646_wave_ids(wave_id: str) -> dict[str, Any]:
    mapping = {"A": WAVE_A, "B": WAVE_B, "C": WAVE_C, "D": WAVE_D}
    ids = mapping.get(wave_id.upper())
    if not ids:
        raise HTTPException(status_code=404, detail="unknown_wave")
    return {"wave": wave_id.upper(), "ids": list(ids)}


@router.get("/wave/{wave_id}/dod")
async def cap646_wave_dod(wave_id: str) -> dict[str, Any]:
    mapping = {"A": WAVE_A, "B": WAVE_B, "C": WAVE_C, "D": WAVE_D}
    ids = mapping.get(wave_id.upper())
    if not ids:
        raise HTTPException(status_code=404, detail="unknown_wave")
    return await verify_wave(ids)


@router.get("/catalog")
async def cap646_catalog(limit: int = Query(646, ge=1, le=646)) -> dict[str, Any]:
    rows = list(catalog_by_id().values())[:limit]
    return {"count": len(rows), "items": rows}


@router.get("/closure/triple")
async def cap646_triple_closure(sample: bool = Query(False)) -> dict[str, Any]:
    if sample:
        from cap646.waves import WAVE_A, WAVE_B, WAVE_C

        sample_ids = list(WAVE_A) + list(WAVE_B) + list(WAVE_C) + list(WAVE_D[:20])
        return await triple_institutional_closure(sample_cap_ids=sample_ids)
    return await triple_institutional_closure()


@router.get("/controls")
async def cap646_controls() -> dict[str, Any]:
    return await verify_all_controls()


@router.get("/platform-chain")
async def cap646_platform_chain(symbol: str = Query("BTC")) -> dict[str, Any]:
    return await verify_data_platform_chain(symbol=symbol)


@router.get("/platform-chain/e2e")
async def cap646_platform_chain_e2e(symbol: str = Query("BTC")) -> dict[str, Any]:
    from platform_chain_e2e import run_platform_compounding_e2e

    return await run_platform_compounding_e2e(symbol=symbol)


@router.get("/functional/{capability_id}")
async def cap646_functional(capability_id: int) -> dict[str, Any]:
    if capability_id < 1 or capability_id > 646:
        raise HTTPException(status_code=404, detail="capability_id_out_of_range")
    return await verify_functional(capability_id)


@router.get("/user-surface/{capability_id}")
async def cap646_user_surface(capability_id: int) -> dict[str, Any]:
    surface = user_surface_for(capability_id)
    if not surface:
        raise HTTPException(status_code=404, detail="not_user_facing")
    return {"capability_id": capability_id, **surface}


@router.get("/hub/context")
async def cap646_hub_context() -> dict[str, Any]:
    return hub_context()


@router.get("/closure/978")
async def cap978_closure() -> dict[str, Any]:
    from cap978.closure import institutional_closure_978

    return await institutional_closure_978()


@router.get("/978/{capability_id}")
async def cap978_execute(
    capability_id: int,
    symbol: str = Query("BTC"),
    user: Annotated[dict | None, Depends(optional_user_from_request)] = None,
) -> dict[str, Any]:
    if capability_id < 647 or capability_id > 978:
        raise HTTPException(status_code=404, detail="capability_id_out_of_978_extension_range")
    from cap978.verify import execute_extension

    return await execute_extension(capability_id, user=user, params={"symbol": symbol, "tier": (user or {}).get("tier") or "pro"})


@router.get("/978/catalog")
async def cap978_catalog(limit: int = Query(978, ge=1, le=978)) -> dict[str, Any]:
    from cap978.catalog import load_catalog

    rows = load_catalog()[:limit]
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
    symbol: str = Query("BTC"),
    user: Annotated[dict | None, Depends(optional_user_from_request)] = None,
) -> dict[str, Any]:
    if capability_id < 1 or capability_id > 646:
        raise HTTPException(status_code=404, detail="capability_id_out_of_range")
    return await execute_capability(capability_id, user=user, params={"symbol": symbol, "tier": (user or {}).get("tier") or "pro"})


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
