"""End-to-end billing / subscription / entitlement engine tests."""

from __future__ import annotations

import pytest
from datetime import UTC, datetime, timedelta


@pytest.fixture
async def billing_user():
    import database
    from database import create_user, init_db

    await init_db()
    email = f"billing-e2e-{datetime.now(UTC).timestamp()}@blackdark.test"
    uid = await create_user(email, "pbkdf2_sha256$260000$deadbeef$" + "a" * 64, "Billing Test")
    return {"id": uid, "email": email}


@pytest.mark.asyncio
async def test_plan_registry_official_prices():
    from billing.plan_registry import PLAN_DEFINITIONS, normalize_plan

    assert normalize_plan("whale") == "elite"
    assert PLAN_DEFINITIONS["pro"]["price_cents"] == 1999
    assert PLAN_DEFINITIONS["elite"]["price_cents"] == 4999
    assert PLAN_DEFINITIONS["quant"]["price_cents"] == 14999
    assert PLAN_DEFINITIONS["institutional"]["price_usd_month_from"] == 999.0
    assert PLAN_DEFINITIONS["pro"]["trial_days"] == 7
    assert PLAN_DEFINITIONS["quant"]["trial_days"] == 7
    assert PLAN_DEFINITIONS["free"]["trial_days"] == 0


@pytest.mark.asyncio
async def test_subscription_lifecycle_activate_renew_cancel_expire(billing_user):
    from billing.subscription_engine import (
        activate_checkout,
        effective_plan,
        entitlement_allowed,
        payment_failed,
        renew_subscription,
        schedule_cancel_at_period_end,
    )
    from billing.subscription_store import get_by_user_id

    uid = int(billing_user["id"])
    email = billing_user["email"]
    now = datetime.now(UTC)
    period_end = (now + timedelta(days=30)).isoformat()
    suffix = str(now.timestamp()).replace(".", "")

    result = await activate_checkout(
        email=email,
        plan="pro",
        provider="stripe",
        provider_subscription_id=f"sub_test_pro_{suffix}",
        user_id=uid,
        period_start=now.isoformat(),
        period_end=period_end,
        auto_renew_consent=True,
        provider_event_id=f"evt_checkout_{suffix}",
        amount_cents=1999,
    )
    assert result["duplicate"] is False
    sub = await get_by_user_id(uid)
    assert sub is not None
    assert sub["plan"] == "pro"
    assert sub["subscription_status"] == "active"
    assert entitlement_allowed(sub)
    assert effective_plan(sub) == "pro"

    dup = await activate_checkout(
        email=email,
        plan="pro",
        provider="stripe",
        provider_subscription_id=f"sub_test_pro_{suffix}",
        user_id=uid,
        provider_event_id=f"evt_checkout_{suffix}",
    )
    assert dup["duplicate"] is True

    new_end = (now + timedelta(days=60)).isoformat()
    renew = await renew_subscription(
        provider_subscription_id=f"sub_test_pro_{suffix}",
        provider="stripe",
        provider_event_id=f"evt_invoice_{suffix}",
        provider_invoice_id=f"in_{suffix}",
        period_end=new_end,
        amount_cents=1999,
    )
    assert renew["handled"] is True
    sub = await get_by_user_id(uid)
    assert sub["current_period_end"] == new_end
    assert sub["entitlements_version"] >= 2

    cancelled = await schedule_cancel_at_period_end(uid)
    assert cancelled["cancel_at_period_end"] is True
    assert cancelled["auto_renew_enabled"] is False
    assert entitlement_allowed(cancelled)

    failed = await payment_failed(
        provider_subscription_id=f"sub_test_pro_{suffix}",
        provider="stripe",
        provider_event_id=f"evt_fail_{suffix}",
    )
    assert failed["handled"] is True
    sub = await get_by_user_id(uid)
    assert sub["subscription_status"] == "past_due"
    assert sub["grace_period_end"] is not None


@pytest.mark.asyncio
async def test_upgrade_downgrade_and_refund_revoke(billing_user):
    from billing.subscription_engine import (
        apply_upgrade,
        revoke_for_financial_reversal,
        schedule_downgrade,
        start_paid_trial,
    )
    from billing.subscription_store import get_by_user_id

    uid = int(billing_user["id"])
    email = billing_user["email"]
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")

    trial = await start_paid_trial(uid, email, "elite")
    assert trial["subscription_status"] == "trialing"
    assert trial["plan"] == "elite"

    upgraded = await apply_upgrade(
        uid,
        "quant",
        provider="stripe",
        provider_event_id=f"evt_upgrade_{suffix}",
        amount_cents=14999,
    )
    assert upgraded["subscription"]["plan"] == "quant"

    down = await schedule_downgrade(uid, "pro")
    assert down["pending_plan"] == "pro"

    revoked = await revoke_for_financial_reversal(
        user_id=uid,
        provider="stripe",
        provider_event_id=f"evt_refund_{suffix}",
        reason="charge_refunded",
        payment_status="refunded",
    )
    assert revoked["handled"] is True
    sub = await get_by_user_id(uid)
    assert sub["plan"] == "free"
    assert sub["subscription_status"] == "expired"


@pytest.mark.asyncio
async def test_webhook_idempotency_stripe_checkout(billing_user):
    from billing.webhook_processor import process_stripe_event

    uid = int(billing_user["id"])
    email = billing_user["email"]
    event = {
        "id": "evt_stripe_dup_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer_details": {"email": email},
                "subscription": "sub_stripe_dup",
                "customer": "cus_dup",
                "client_reference_id": str(uid),
                "metadata": {"tier": "quant"},
            }
        },
    }
    r1 = await process_stripe_event(event)
    r2 = await process_stripe_event(event)
    assert r1.get("handled") is True
    assert r2.get("action") == "duplicate_ignored"


@pytest.mark.asyncio
async def test_resolve_user_tier_from_subscription(billing_user):
    from auth_service import resolve_user_tier
    from billing.subscription_engine import activate_checkout

    uid = int(billing_user["id"])
    email = billing_user["email"]
    await activate_checkout(
        email=email,
        plan="elite",
        provider="stripe",
        provider_subscription_id="sub_tier_elite",
        user_id=uid,
        provider_event_id="evt_tier_1",
    )
    tier = await resolve_user_tier(email)
    assert tier == "elite"


@pytest.mark.asyncio
async def test_pricing_catalog_five_tiers():
    from pricing_catalog import pricing_catalog

    cat = pricing_catalog()
    ids = [t["id"] for t in cat["tiers"]]
    assert ids == ["free", "pro", "elite", "quant", "institutional"]
    by_id = {t["id"]: t for t in cat["tiers"]}
    assert by_id["pro"]["price_usd_month"] == 19.99
    assert by_id["elite"]["price_usd_month"] == 49.99
    assert by_id["quant"]["price_usd_month"] == 149.99


@pytest.mark.asyncio
async def test_usage_meter_enforces_free_limit(billing_user):
    from billing.usage_meter import check_and_increment

    uid = int(billing_user["id"])
    for i in range(3):
        r = await check_and_increment(uid, "free", "oracle_decision")
        assert r["allowed"] is True
    blocked = await check_and_increment(uid, "free", "oracle_decision")
    assert blocked["allowed"] is False
    assert blocked["reason"] == "usage_exceeded"


@pytest.mark.asyncio
async def test_institutional_invoice_activates_subscription(billing_user):
    from billing.institutional_activation import activate_institutional_from_invoice
    from billing.subscription_engine import resolve_entitlements_for_user
    from institutional_commerce import create_invoice, mark_invoice_paid

    uid = int(billing_user["id"])
    email = billing_user["email"]
    inv = create_invoice(email=email, amount_usd=999.0, plan="institutional", method="wire_usd")
    mark_invoice_paid(inv["invoice_id"], source="sandbox_test")

    result = await activate_institutional_from_invoice(
        email=email,
        invoice_id=inv["invoice_id"],
        amount_usd=999.0,
        plan="institutional",
        source="sandbox_test",
    )
    assert result["duplicate"] is False
    assert result["subscription"]["plan"] == "institutional"
    ent = await resolve_entitlements_for_user(uid)
    assert ent["effective_plan"] == "institutional"
    assert ent["entitlement_allowed"] is True

    dup = await activate_institutional_from_invoice(
        email=email,
        invoice_id=inv["invoice_id"],
        amount_usd=999.0,
        source="sandbox_test",
    )
    assert dup["duplicate"] is True


@pytest.mark.asyncio
async def test_billing_ops_readiness():
    from billing.ops_readiness import billing_ops_readiness

    r = billing_ops_readiness()
    assert r["self_serve_plans"] == ["pro", "elite", "quant"]
    assert "stripe_url" in r["webhooks"]
    assert r["checks"]["institutional_commerce_wired"] is True
