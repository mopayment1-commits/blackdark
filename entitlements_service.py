"""
Central entitlement checks — server-side SSOT for feature keys.

Upgrade: effective plan updates immediately when subscription engine allows.
Downgrade: pending_plan applies at period end (subscription_engine.effective_plan).
Lapsed / unpaid (after grace): entitlement_allowed false → Free features.
"""

from __future__ import annotations

from typing import Any

from entitlements_registry import (
    UNLIMITED,
    _BOOL_KEYS,
    _LIMIT_KEYS,
    entitlements_for_plan,
    normalize_entitlement_plan,
)


def _value_for_plan(plan: str, feature_key: str) -> int | bool:
    row = entitlements_for_plan(plan)
    if feature_key not in row:
        return False if feature_key in _BOOL_KEYS else 0
    return row[feature_key]


def has_entitlement_for_plan(plan: str | None, feature_key: str) -> bool | int:
    """Return bool for flags, int limit for *_limit keys (0 = denied, UNLIMITED = no cap)."""
    plan_n = normalize_entitlement_plan(plan)
    val = _value_for_plan(plan_n, feature_key)
    if feature_key in _LIMIT_KEYS:
        if not isinstance(val, int):
            return 0
        return val
    return bool(val)


def has_entitlement(user: dict[str, Any] | None, feature_key: str) -> bool | int:
    """
    Sync check when user carries pre-resolved entitlements (tests / injected context).
    Prefer async_resolve_entitlements() for live requests.
    """
    if not user:
        return has_entitlement_for_plan("free", feature_key)
    bundle = user.get("entitlements")
    if isinstance(bundle, dict) and feature_key in bundle:
        raw = bundle[feature_key]
        if feature_key in _LIMIT_KEYS:
            return int(raw) if isinstance(raw, int) else 0
        return bool(raw)
    plan = user.get("effective_plan") or user.get("tier") or "free"
    if user.get("entitlement_allowed") is False:
        plan = "free"
    return has_entitlement_for_plan(str(plan), feature_key)


def entitlement_allowed_flag(user: dict[str, Any] | None, feature_key: str) -> bool:
    val = has_entitlement(user, feature_key)
    if isinstance(val, bool):
        return val
    return val != 0


async def resolve_effective_plan_for_user(user_id: int | None) -> str:
    if not user_id:
        return "free"
    from billing.subscription_engine import resolve_entitlements_for_user

    ent = await resolve_entitlements_for_user(int(user_id))
    if not ent.get("entitlement_allowed"):
        return "free"
    return normalize_entitlement_plan(str(ent.get("effective_plan") or "free"))


async def async_resolve_entitlements(user_id: int | None) -> dict[str, Any]:
    from billing.subscription_engine import resolve_entitlements_for_user

    if not user_id:
        features = entitlements_for_plan("free")
        return {
            "effective_plan": "free",
            "entitlement_allowed": True,
            "subscription_plan": "free",
            "features": features,
            **features,
        }
    ent = await resolve_entitlements_for_user(int(user_id))
    allowed = bool(ent.get("entitlement_allowed"))
    plan = normalize_entitlement_plan(str(ent.get("effective_plan") or "free")) if allowed else "free"
    features = entitlements_for_plan(plan)
    return {
        "effective_plan": plan,
        "entitlement_allowed": allowed,
        "subscription_plan": normalize_entitlement_plan(str(ent.get("plan") or "free")),
        "subscription_status": ent.get("subscription_status"),
        "payment_status": ent.get("payment_status"),
        "pending_plan": ent.get("pending_plan"),
        "current_period_end": ent.get("current_period_end"),
        "grace_period_end": ent.get("grace_period_end"),
        "entitlements_version": ent.get("entitlements_version"),
        "features": features,
        **features,
    }


async def async_has_entitlement(user_id: int | None, feature_key: str) -> bool | int:
    bundle = await async_resolve_entitlements(user_id)
    user_ctx = {"entitlements": bundle, "effective_plan": bundle["effective_plan"], "entitlement_allowed": bundle["entitlement_allowed"]}
    return has_entitlement(user_ctx, feature_key)


def require_entitlement(user: dict[str, Any] | None, feature_key: str) -> None:
    """Raise PermissionError when a boolean feature is denied (server handlers)."""
    val = has_entitlement(user, feature_key)
    if isinstance(val, int):
        if val == 0:
            raise PermissionError(f"entitlement_denied:{feature_key}")
        return
    if not val:
        raise PermissionError(f"entitlement_denied:{feature_key}")
