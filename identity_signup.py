"""Signup plan deferral until email verification."""

from __future__ import annotations

from typing import Any


async def defer_paid_signup_plan(user_id: int, email: str, plan: str) -> dict[str, Any]:
    """Store paid plan as pending — entitlement stays free until email verified."""
    from billing.plan_registry import normalize_plan
    from billing.subscription_store import ensure_subscription_account, update_subscription_account

    canonical = normalize_plan(plan)
    if canonical == "free":
        return {"pending_until_verification": False, "plan": "free"}
    await ensure_subscription_account(user_id, email, plan="free")
    await update_subscription_account(user_id, pending_plan=canonical)
    return {"pending_until_verification": True, "plan": canonical}


async def activate_pending_signup_plan(user_id: int) -> dict[str, Any] | None:
    """Start paid trial when email is verified and a signup plan was deferred."""
    from billing.plan_registry import normalize_plan
    from billing.subscription_engine import start_paid_trial
    from billing.subscription_store import get_by_user_id, update_subscription_account
    from database import fetch_user_by_id

    sub = await get_by_user_id(user_id)
    if not sub:
        return None
    pending = normalize_plan(str(sub.get("pending_plan") or "free"))
    if pending == "free":
        return None
    user = await fetch_user_by_id(user_id)
    if not user:
        return None
    trial = await start_paid_trial(user_id, str(user["email"]), pending)
    await update_subscription_account(user_id, pending_plan=None)
    return {"plan": pending, "trial": trial}
