"""Product entitlements — feature keys, upgrade/downgrade, lapse to Free."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from entitlements_registry import UNLIMITED
from entitlements_service import (
    async_resolve_entitlements,
    has_entitlement,
    has_entitlement_for_plan,
)
from billing.subscription_engine import effective_plan, entitlement_allowed


def test_free_vs_beginner_feature_keys():
    assert has_entitlement_for_plan("free", "watchlist_limit") == 0
    assert has_entitlement_for_plan("free", "offline") is False
    assert has_entitlement_for_plan("pro", "watchlist_limit") == 5
    assert has_entitlement_for_plan("pro", "alerts_limit") == 1
    assert has_entitlement_for_plan("pro", "offline") is True
    assert has_entitlement_for_plan("elite", "share_decision") is True
    assert has_entitlement_for_plan("elite", "compare_limit") == 5
    assert has_entitlement_for_plan("quant", "api_read") is True
    assert has_entitlement_for_plan("institutional", "api_full") is True


def test_has_entitlement_uses_bundle_not_tier_name():
    user = {
        "tier": "pro",
        "entitlements": {"watchlist_limit": 0, "offline": False},
        "effective_plan": "pro",
        "entitlement_allowed": True,
    }
    assert has_entitlement(user, "watchlist_limit") == 0
    assert has_entitlement(user, "offline") is False


def test_upgrade_effective_plan_immediate():
    now = datetime.now(UTC)
    sub = {
        "plan": "elite",
        "subscription_status": "active",
        "payment_status": "current",
        "current_period_start": now.isoformat(),
        "current_period_end": (now + timedelta(days=20)).isoformat(),
        "pending_plan": None,
    }
    plan = effective_plan(sub, now=now)
    assert plan == "elite"
    assert has_entitlement_for_plan(plan, "charts") is True
    assert has_entitlement_for_plan(plan, "watchlist_limit") == 20


def test_downgrade_applies_at_period_end_not_before():
    now = datetime.now(UTC)
    end = now + timedelta(days=10)
    sub = {
        "plan": "elite",
        "subscription_status": "canceled",
        "payment_status": "current",
        "current_period_start": (now - timedelta(days=20)).isoformat(),
        "current_period_end": end.isoformat(),
        "pending_plan": "pro",
        "cancel_at_period_end": True,
    }
    assert effective_plan(sub, now=now) == "elite"
    assert has_entitlement_for_plan(effective_plan(sub, now=now), "share_decision") is True
    after = end + timedelta(seconds=1)
    assert effective_plan(sub, now=after) == "pro"
    assert has_entitlement_for_plan(effective_plan(sub, now=after), "share_decision") is False


def test_lapsed_subscription_entitlement_denied_maps_to_free():
    now = datetime.now(UTC)
    sub = {
        "plan": "pro",
        "subscription_status": "past_due",
        "payment_status": "failed",
        "current_period_start": (now - timedelta(days=40)).isoformat(),
        "current_period_end": (now - timedelta(days=10)).isoformat(),
        "grace_period_end": (now - timedelta(days=1)).isoformat(),
    }
    assert entitlement_allowed(sub, now=now) is False
    assert effective_plan(sub, now=now) == "free"


@pytest.mark.asyncio
async def test_async_resolve_entitlements_free_user():
    bundle = await async_resolve_entitlements(None)
    assert bundle["effective_plan"] == "free"
    assert bundle["watchlist_limit"] == 0


def test_entitlements_me_api_anonymous():
    from fastapi.testclient import TestClient
    from dashboard import app

    r = TestClient(app).get("/api/entitlements/me")
    assert r.status_code == 200
    body = r.json()
    assert body["authenticated"] is False
    assert body["entitlements"]["watchlist_limit"] == 0


@pytest.mark.asyncio
async def test_async_resolve_entitlements_denied_paid_row():
    from billing.subscription_store import ensure_subscription_account, update_subscription_account

    email = f"ent-free-{datetime.now(UTC).timestamp()}@example.test"
    from database import create_user
    from auth_service import hash_password

    uid = await create_user(email, hash_password("testpass1234!"), "Ent Test")
    await ensure_subscription_account(uid, email, plan="pro")
    past = datetime.now(UTC) - timedelta(days=5)
    await update_subscription_account(
        uid,
        subscription_status="past_due",
        payment_status="failed",
        current_period_end=past.isoformat(),
        grace_period_end=(past + timedelta(hours=1)).isoformat(),
        bump_entitlements=False,
    )
    bundle = await async_resolve_entitlements(uid)
    assert bundle["effective_plan"] == "free"
    assert bundle["watchlist_limit"] == 0
    assert bundle["subscription_plan"] == "pro"
