"""Launch-57 Phase 7 — edge + UI consumer API routes."""

from __future__ import annotations

from fastapi import APIRouter, Body, HTTPException, Query, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(tags=["launch57-edge-ui"], responses=COMMON_ERROR_RESPONSES)


def _require_launch57_auth(request: Request, launch_item_id: int) -> None:
    from anonymous_route_foundation import request_has_authentication_signal
    from launch57.anonymous_visitor_common import enforce_launch57_anonymous_boundary

    boundary = enforce_launch57_anonymous_boundary(
        launch_item_id,
        has_auth_signal=request_has_authentication_signal(request),
    )
    if not boundary.get("allowed"):
        raise HTTPException(
            status_code=401,
            detail={
                "detail": "Anonymous access denied",
                "launch_item_id": launch_item_id,
                "reason": boundary.get("reason"),
                "auth_state_required": boundary.get("auth_state_required", "AUTHENTICATED"),
            },
            headers={"X-Blackdark-Auth-Boundary": "launch57-anonymous-denied"},
        )


@router.get("/api/launch57/guest-trust")
async def launch57_guest_trust(symbol: str = Query("BTC")):
    from launch57.trust_batch2 import guest_trust_surface

    return await guest_trust_surface(symbol=symbol, params={"symbol": symbol, "user_key": "anonymous"})


@router.get("/api/launch57/command-home")
async def launch57_command_home(
    request: Request,
    symbol: str = Query("BTC"),
    command_view: bool = Query(True),
):
    _require_launch57_auth(request, 1)
    from launch57.edge_ui_batch2 import six_heroes_command_home

    return await six_heroes_command_home(symbol=symbol, params={"symbol": symbol, "command_view": command_view})


@router.get("/api/launch57/decision-history")
async def launch57_decision_history(
    request: Request,
    symbol: str = Query("BTC"),
    tier: str = Query("free"),
    limit: int = Query(10, ge=1, le=100),
):
    _require_launch57_auth(request, 49)
    from launch57.edge_ui_batch1 import personal_decision_history

    return await personal_decision_history(symbol=symbol, params={"symbol": symbol, "tier": tier, "limit": limit})


@router.get("/api/launch57/discipline-mirror")
async def launch57_discipline_mirror(
    request: Request,
    user_key: str = Query("anonymous"),
    limit: int = Query(20, ge=1, le=100),
):
    _require_launch57_auth(request, 50)
    from launch57.edge_ui_batch1 import discipline_mirror_light

    return await discipline_mirror_light(symbol="BTC", params={"user_key": user_key, "limit": limit})


@router.get("/api/launch57/capability-library")
async def launch57_capability_library(
    q: str | None = Query(None),
    area: str | None = Query(None),
    locale: str | None = Query(None),
    include_parked: bool = Query(False),
):
    from launch57.edge_ui_batch1 import capability_library_search

    return await capability_library_search(
        symbol="BTC",
        params={
            "query": q or "",
            "functional_area": area,
            "locale": locale,
            "include_parked": include_parked,
        },
    )


@router.get("/api/launch57/capability-library/compare")
async def launch57_capability_library_compare(compare: str = Query(..., description="Comma-separated launch numbers")):
    from launch57.edge_ui_batch1 import capability_library_compare

    return await capability_library_compare(symbol="BTC", params={"compare": compare})


@router.get("/api/launch57/capability-library/{launch_number}")
async def launch57_capability_library_detail(
    launch_number: int,
    user_key: str = Query("anonymous"),
):
    from launch57.edge_ui_batch1 import capability_library_detail

    return await capability_library_detail(
        symbol="BTC",
        params={"launch_number": launch_number, "user_key": user_key},
    )
