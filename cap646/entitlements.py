"""
Institutional entitlement engine — ID161 backbone.

Backend-enforced tier + org RBAC + capability scope. Never UI-only gating.
Reads subscription SSOT (subscription_accounts) — not UI tier alone.
"""

from __future__ import annotations

from typing import Any

from auth_service import TIER_FEATURES, normalize_tier
from billing.plan_registry import plan_rank
from billing.subscription_engine import entitlement_allowed, effective_plan, resolve_entitlements_for_user
from cap646.catalog import catalog_by_id as catalog646_by_id, is_external as is_external646

# capability_id -> minimum consumer tier
_TIER_REQUIREMENTS: dict[int, str] = {
    103: "elite",
    574: "elite",
    161: "elite",
    47: "pro",
    48: "pro",
}

# capability_id -> org permission key
_ORG_PERMISSIONS: dict[int, str] = {
    161: "billing.manage",
    574: "org.manage",
    103: "decisions.view",
    638: "compliance.view",
    641: "compliance.export",
}


def _tier_rank(tier: str) -> int:
    return plan_rank(tier)


async def _subscription_for_user(user: dict[str, Any] | None) -> dict[str, Any] | None:
    if not user or not user.get("id"):
        return None
    from billing.subscription_store import get_by_user_id

    return await get_by_user_id(int(user["id"]))


class EntitlementEngine:
    async def check(
        self,
        capability_id: int,
        *,
        user: dict[str, Any] | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        if is_external646(capability_id):
            return {
                "allowed": False,
                "reason": "external_blocked",
                "capability_id": capability_id,
            }
        if capability_id >= 647:
            try:
                from cap978.catalog import is_external as is_external978

                if is_external978(capability_id):
                    return {
                        "allowed": False,
                        "reason": "external_blocked",
                        "capability_id": capability_id,
                    }
            except Exception:
                pass

        row = catalog646_by_id().get(capability_id) or {}
        if capability_id >= 647 and not row:
            try:
                from cap978.catalog import catalog_by_id as catalog978_by_id

                row = catalog978_by_id().get(capability_id, {})
            except Exception:
                row = {}

        sub = await _subscription_for_user(user)
        if user and user.get("id"):
            ent = await resolve_entitlements_for_user(int(user["id"]))
            tier = normalize_tier(str(ent.get("effective_plan") or "free"))
            if not ent.get("entitlement_allowed") and tier != "free":
                return {
                    "allowed": False,
                    "reason": "subscription_inactive",
                    "capability_id": capability_id,
                    "subscription_status": ent.get("subscription_status"),
                    "payment_status": ent.get("payment_status"),
                }
        else:
            tier = normalize_tier((user or {}).get("tier"))

        if sub and not entitlement_allowed(sub):
            tier = "free"

        min_tier = normalize_tier(_TIER_REQUIREMENTS.get(capability_id, "free"))
        if _tier_rank(tier) < _tier_rank(min_tier):
            teaser = tier == "free" and min_tier != "free"
            return {
                "allowed": False,
                "reason": "teaser" if teaser else "tier_insufficient",
                "required_tier": min_tier,
                "actual_tier": tier,
                "capability_id": capability_id,
                "capability": row.get("capability"),
            }

        perm = _ORG_PERMISSIONS.get(capability_id)
        if perm and org_id and user:
            try:
                from org_rbac import has_permission

                email = str(user.get("email") or "")
                if email and not has_permission(org_id, email, perm):
                    return {
                        "allowed": False,
                        "reason": "missing_org_permission",
                        "permission": perm,
                        "capability_id": capability_id,
                    }
            except Exception:
                pass

        try:
            from auth_service import feature_allowed

            feature_key = row.get("feature_key")
            if feature_key and user and not feature_allowed(user, feature_key):
                return {
                    "allowed": False,
                    "reason": "feature_disabled",
                    "feature": feature_key,
                    "capability_id": capability_id,
                }
        except Exception:
            pass

        if user and user.get("id"):
            from billing.usage_meter import check_and_increment

            cap_key = row.get("usage_meter_key")
            if cap_key:
                usage = await check_and_increment(int(user["id"]), tier, str(cap_key))
                if not usage.get("allowed"):
                    return {
                        "allowed": False,
                        "reason": usage.get("reason", "usage_exceeded"),
                        "capability_id": capability_id,
                        "usage": usage,
                    }

        return {
            "allowed": True,
            "tier": tier,
            "capability_id": capability_id,
            "entitlements_version": (sub or {}).get("entitlements_version"),
        }


def tier_features(tier: str) -> dict[str, Any]:
    return TIER_FEATURES.get(normalize_tier(tier), TIER_FEATURES["free"])


entitlement_engine = EntitlementEngine()
