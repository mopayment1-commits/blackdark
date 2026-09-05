"""
Subscription Lifecycle Hub — Feature #9 Phase 1.

Stripe webhooks + grace period + immediate cutoff + 5-day renewal warnings.
Built on billing/subscription_engine SSOT — no duplicate state machine.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import config

from billing.plan_registry import normalize_plan
from billing.subscription_engine import effective_plan, entitlement_allowed, resolve_entitlements_for_user
from billing.subscription_store import get_by_user_id
from pricing_catalog import next_upgrade


def _days_until(iso: str | None) -> int | None:
    if not iso:
        return None
    try:
        end = datetime.fromisoformat(str(iso))
        if end.tzinfo is None:
            end = end.replace(tzinfo=UTC)
        return max(0, (end - datetime.now(UTC)).days)
    except ValueError:
        return None


async def user_lifecycle_status(user_id: int) -> dict[str, Any]:
    """Full subscription lifecycle view for a user."""
    t0 = time.perf_counter()
    sub = await get_by_user_id(int(user_id))
    entitlements = await resolve_entitlements_for_user(int(user_id))
    plan = entitlements.get("effective_plan") or "free"
    allowed = bool(entitlements.get("entitlement_allowed"))
    period_end = entitlements.get("current_period_end") or (sub or {}).get("current_period_end")
    days_left = _days_until(period_end)
    warning_days = int(getattr(config, "BILLING_RENEWAL_WARNING_DAYS", 5))
    renewal_warning = (
        days_left is not None
        and days_left <= warning_days
        and normalize_plan(plan) != "free"
        and allowed
    )
    upgrade = next_upgrade(plan)
    return {
        "ok": True,
        "surface": "subscription_lifecycle",
        "feature": "#9-phase1",
        "user_id": int(user_id),
        "plan": normalize_plan(str((sub or {}).get("plan") or plan)),
        "effective_plan": plan,
        "entitlement_allowed": allowed,
        "features_active": allowed,
        "subscription_status": entitlements.get("subscription_status"),
        "payment_status": entitlements.get("payment_status"),
        "current_period_end": period_end,
        "grace_period_end": entitlements.get("grace_period_end") or (sub or {}).get("grace_period_end"),
        "days_until_renewal": days_left,
        "renewal_warning": renewal_warning,
        "renewal_warning_days": warning_days,
        "cancel_at_period_end": bool(entitlements.get("cancel_at_period_end")),
        "upgrade_path": upgrade,
        "acceptance": {
            "immediate_cutoff_on_expiry": True,
            "grace_period_days": int(getattr(config, "BILLING_RENEWAL_GRACE_DAYS", 3)),
            "renewal_warning_days": warning_days,
        },
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
    }


async def initiate_upgrade(user_id: int, *, target_plan: str | None = None) -> dict[str, Any]:
    """Return checkout path for contextual upgrade (delegates to pricing ladder)."""
    sub = await get_by_user_id(int(user_id))
    current = effective_plan(sub) if sub else "free"
    step = next_upgrade(current)
    plan = normalize_plan(target_plan or step.get("next_id") or "pro")
    href = step.get("href") or f"/create-checkout-session?tier={plan}"
    if normalize_plan(target_plan or "") and normalize_plan(target_plan) != step.get("next_id"):
        href = f"/create-checkout-session?tier={plan}"
    try:
        from distribution_compounding import track_subscription_event

        await track_subscription_event(
            event_type="upgrade_cta_clicked",
            user_id=int(user_id),
            payload={"from_plan": current, "target_plan": plan, "href": href},
        )
    except Exception:
        pass
    return {
        "ok": True,
        "surface": "subscription_lifecycle",
        "feature": "#9-phase1",
        "current_plan": current,
        "target_plan": plan,
        "checkout_href": href,
        "upgrade_ladder": step,
    }
