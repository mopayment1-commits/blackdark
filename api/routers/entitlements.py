"""Entitlements API — server-resolved feature keys (no client tier trust)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import optional_user
from api.openapi_responses import COMMON_ERROR_RESPONSES
from entitlements_registry import entitlement_catalog
from entitlements_service import async_resolve_entitlements

router = APIRouter(prefix="/api/entitlements", tags=["entitlements"], responses=COMMON_ERROR_RESPONSES)


@router.get("/catalog")
async def entitlements_catalog():
    return entitlement_catalog()


@router.get("/me")
async def entitlements_me(user: dict | None = Depends(optional_user)):
    if not user:
        bundle = await async_resolve_entitlements(None)
        return {"authenticated": False, "entitlements": bundle}
    bundle = await async_resolve_entitlements(int(user["id"]))
    return {
        "authenticated": True,
        "user_id": user["id"],
        "entitlements": bundle,
    }
