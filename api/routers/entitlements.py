"""Entitlements API — server-resolved feature keys (no client tier trust)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

from api.deps import optional_user
from api.openapi_responses import COMMON_ERROR_RESPONSES
from entitlements_registry import entitlement_catalog, entitlements_for_plan
from entitlements_service import async_resolve_entitlements
from live_refresh_policy import live_refresh_policy_for_plan

logger = logging.getLogger("BLACKDARK.EntitlementsAPI")

router = APIRouter(prefix="/api/entitlements", tags=["entitlements"], responses=COMMON_ERROR_RESPONSES)


@router.get("/catalog")
async def entitlements_catalog():
    return entitlement_catalog()


@router.get("/refresh-policy")
async def live_refresh_policy(user: dict | None = Depends(optional_user)):
    from live_refresh_policy import resolve_live_refresh_policy

    try:
        uid = int(user["id"]) if user else None
        return await resolve_live_refresh_policy(uid)
    except Exception:
        logger.exception("refresh-policy failed; returning free defaults")
        policy = live_refresh_policy_for_plan("free")
        policy["entitlement_allowed"] = True
        return policy


@router.get("/me")
async def entitlements_me(user: dict | None = Depends(optional_user)):
    try:
        if not user:
            bundle = await async_resolve_entitlements(None)
            return {"authenticated": False, "entitlements": bundle}
        bundle = await async_resolve_entitlements(int(user["id"]))
        return {
            "authenticated": True,
            "user_id": user["id"],
            "entitlements": bundle,
        }
    except Exception:
        logger.exception("entitlements/me failed; returning anonymous free bundle")
        features = entitlements_for_plan("free")
        bundle = {
            "effective_plan": "free",
            "entitlement_allowed": True,
            "subscription_plan": "free",
            "features": features,
            **features,
        }
        return {"authenticated": False, "entitlements": bundle}
