"""
Institutional entitlement engine — ID161 backbone.

Backend-enforced tier + org RBAC + capability scope. Never UI-only gating.
"""

from __future__ import annotations

from typing import Any

from cap646.catalog import catalog_by_id, is_external

# capability_id -> minimum consumer tier
_TIER_REQUIREMENTS: dict[int, str] = {
    103: "whale",
    574: "whale",
    161: "whale",
    47: "pro",
    48: "pro",
    103: "pro",
}

# capability_id -> org permission key
_ORG_PERMISSIONS: dict[int, str] = {
    161: "billing.manage",
    574: "org.manage",
    103: "decisions.view",
    638: "compliance.view",
    641: "compliance.export",
}


def _user_tier(user: dict[str, Any] | None) -> str:
    if not user:
        return "free"
    tier = str(user.get("tier") or user.get("subscription_tier") or "free").lower()
    return tier if tier in {"free", "pro", "whale"} else "free"


def _tier_rank(tier: str) -> int:
    return {"free": 0, "pro": 1, "whale": 2}.get(tier, 0)


class EntitlementEngine:
    def check(
        self,
        capability_id: int,
        *,
        user: dict[str, Any] | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        if is_external(capability_id):
            return {
                "allowed": False,
                "reason": "external_blocked",
                "capability_id": capability_id,
            }

        row = catalog_by_id().get(capability_id, {})
        min_tier = _TIER_REQUIREMENTS.get(capability_id, "free")
        tier = _user_tier(user)

        if _tier_rank(tier) < _tier_rank(min_tier):
            return {
                "allowed": False,
                "reason": "tier_insufficient",
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
                        "org_id": org_id,
                    }
            except Exception:
                pass

        try:
            from auth_service import feature_allowed

            feature_key = _capability_feature_key(capability_id)
            if feature_key and user:
                email = str(user.get("email") or "")
                if email and not feature_allowed(email, feature_key):
                    return {
                        "allowed": False,
                        "reason": "feature_not_allowed",
                        "feature": feature_key,
                    }
        except Exception:
            pass

        return {
            "allowed": True,
            "tier": tier,
            "capability_id": capability_id,
            "capability": row.get("capability"),
        }


def _capability_feature_key(capability_id: int) -> str | None:
    if capability_id in {47, 48, 86, 88, 126, 205}:
        return "market_radar"
    if capability_id in {610, 612, 584}:
        return "arbitrage"
    if capability_id in {17, 629, 60}:
        return "alerts"
    if capability_id in {103, 574, 161}:
        return "b2b_api"
    return None


entitlement_engine = EntitlementEngine()
