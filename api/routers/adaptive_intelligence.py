"""Adaptive Intelligence Experience v4 API — canonical runtime bindings."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Query

router = APIRouter(tags=["adaptive-intelligence"])


@router.get("/api/adaptive/status")
async def adaptive_status() -> dict[str, Any]:
    from governance.adaptive_ux_governance import adaptive_ux_status

    return adaptive_ux_status()


@router.get("/api/adaptive/calm-surface")
async def adaptive_calm_surface() -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.calm_surface import calm_surface_manifest

    return calm_surface_manifest()


@router.get("/api/adaptive/today-focus")
async def adaptive_today_focus() -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.today_focus import build_today_focus

    return build_today_focus()


@router.post("/api/adaptive/command")
async def adaptive_command(body: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.universal_command import universal_command_search

    return universal_command_search(
        query=str(body.get("query") or ""),
        asset=body.get("asset"),
        horizon=body.get("horizon"),
    )


@router.post("/api/adaptive/route")
async def adaptive_route(body: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request

    return route_intelligence_request(
        query=body.get("query"),
        intent_id=body.get("intent_id"),
        asset=body.get("asset"),
        horizon=body.get("horizon"),
        decision_type=body.get("decision_type"),
    )


@router.post("/api/adaptive/decision-contract")
async def adaptive_decision_contract(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.decision_contract import build_adaptive_decision_contract

    opp = dict(body.get("opportunity") or body)
    return build_adaptive_decision_contract(
        opp,
        symbol=body.get("symbol") or opp.get("symbol"),
        router_result=body.get("router_result"),
    )


@router.get("/api/adaptive/explorer")
async def adaptive_explorer(
    q: str = Query("", alias="query"),
    category: str | None = Query(None),
    limit: int = Query(24, ge=1, le=100),
) -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.capability_explorer import search_explorer

    cards = search_explorer(query=q, category=category, limit=limit)
    return {"count": len(cards), "items": cards}


@router.get("/api/adaptive/data-room/{capability_id}")
async def adaptive_data_room(capability_id: int) -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.data_room_view import capability_data_room_view

    return capability_data_room_view(capability_id)


@router.get("/api/adaptive/workspaces")
async def adaptive_workspaces() -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.workspaces import list_workspaces

    return {"items": list_workspaces()}


@router.get("/api/adaptive/heroes")
async def adaptive_heroes() -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.heroes import heroes_manifest

    return heroes_manifest()


@router.get("/api/adaptive/my-stack/{user_id}")
async def adaptive_my_stack(user_id: str) -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.my_stack import get_stack

    return get_stack(user_id)


@router.get("/api/adaptive/human-validation/status")
async def adaptive_human_validation_status() -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.human_validation import infrastructure_status

    return infrastructure_status()


@router.get("/api/adaptive/accessibility/checklist")
async def adaptive_accessibility_checklist() -> dict[str, Any]:
    from bd_platform.adaptive_intelligence.accessibility import accessibility_checklist

    return accessibility_checklist()
