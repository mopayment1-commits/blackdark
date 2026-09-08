"""BILL-059 P0 test matrix — billing/subscription/entitlement correctness."""

from __future__ import annotations

import pytest
from datetime import UTC, datetime, timedelta


@pytest.fixture
async def billing_user():
    import database
    from database import create_user, init_db

    await init_db()
    email = f"bill-p0-{datetime.now(UTC).timestamp()}@blackdark.test"
    uid = await create_user(email, "pbkdf2_sha256$260000$deadbeef$" + "a" * 64, "P0 Test")
    return {"id": uid, "email": email}


@pytest.mark.asyncio
async def test_free_signup_entitlement(billing_user):
    from billing.entitlement_state import EntitlementState, decide_entitlement
    from billing.subscription_store import ensure_subscription_account

    sub = await ensure_subscription_account(int(billing_user["id"]), billing_user["email"], plan="free")
    decision = decide_entitlement(sub)
    assert decision.state == EntitlementState.FREE
    assert decision.effective_tier == "free"
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_paid_checkout_requires_payment_proof(billing_user):
    from billing.entitlement_state import EntitlementState, decide_entitlement
    from billing.subscription_engine import activate_checkout

    uid = int(billing_user["id"])
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    await activate_checkout(
        email=billing_user["email"],
        plan="pro",
        provider="stripe",
        provider_subscription_id=f"sub_p0_{suffix}",
        user_id=uid,
        period_end=(datetime.now(UTC) + timedelta(days=30)).isoformat(),
        provider_event_id=f"evt_p0_{suffix}",
        amount_cents=1900,
    )
    from billing.subscription_store import get_by_user_id

    sub = await get_by_user_id(uid)
    decision = decide_entitlement(sub)
    assert decision.state == EntitlementState.PAID_ACTIVE
    assert decision.effective_tier == "pro"
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_upgrade_without_payment_fails_closed(billing_user):
    from billing.entitlement_state import decide_entitlement
    from billing.subscription_store import ensure_subscription_account, get_by_user_id, update_subscription_account

    uid = int(billing_user["id"])
    await ensure_subscription_account(uid, billing_user["email"], plan="pro")
    # Simulate subscription.updated without payment proof — pending higher tier
    await update_subscription_account(uid, plan="elite", subscription_status="active", payment_status="none")
    sub = await get_by_user_id(uid)
    decision = decide_entitlement(sub)
    assert decision.allowed is False


@pytest.mark.asyncio
async def test_past_due_does_not_blind_revoke_within_paid_through(billing_user):
    from billing.entitlement_state import EntitlementState, decide_entitlement
    from billing.subscription_engine import activate_checkout, payment_failed

    uid = int(billing_user["id"])
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    period_end = (datetime.now(UTC) + timedelta(days=10)).isoformat()
    await activate_checkout(
        email=billing_user["email"],
        plan="pro",
        provider="stripe",
        provider_subscription_id=f"sub_pd_{suffix}",
        user_id=uid,
        period_end=period_end,
        provider_event_id=f"evt_pd_{suffix}",
        amount_cents=1900,
    )
    await payment_failed(
        provider_subscription_id=f"sub_pd_{suffix}",
        provider="stripe",
        provider_event_id=f"evt_fail_{suffix}",
    )
    from billing.subscription_store import get_by_user_id

    sub = await get_by_user_id(uid)
    decision = decide_entitlement(sub)
    assert decision.state == EntitlementState.PAID_RECOVERY
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_refund_revokes_entitlement(billing_user):
    from billing.subscription_engine import activate_checkout, revoke_for_financial_reversal
    from billing.subscription_store import get_by_user_id
    from billing.entitlement_state import decide_entitlement

    uid = int(billing_user["id"])
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    await activate_checkout(
        email=billing_user["email"],
        plan="elite",
        provider="stripe",
        provider_subscription_id=f"sub_ref_{suffix}",
        user_id=uid,
        period_end=(datetime.now(UTC) + timedelta(days=30)).isoformat(),
        provider_event_id=f"evt_ref_{suffix}",
        amount_cents=4900,
    )
    await revoke_for_financial_reversal(
        user_id=uid,
        provider="stripe",
        provider_event_id=f"evt_refund_{suffix}",
        reason="charge_refunded",
        payment_status="refunded",
    )
    sub = await get_by_user_id(uid)
    decision = decide_entitlement(sub)
    assert decision.allowed is False
    assert decision.effective_tier == "free"


@pytest.mark.asyncio
async def test_refund_webhook_resolves_charge(billing_user):
    from billing.subscription_engine import activate_checkout
    from billing.webhook_processor import process_stripe_event
    from billing.subscription_store import get_by_user_id

    uid = int(billing_user["id"])
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    sub_id = f"sub_wh_{suffix}"
    await activate_checkout(
        email=billing_user["email"],
        plan="pro",
        provider="stripe",
        provider_subscription_id=sub_id,
        user_id=uid,
        provider_customer_id=f"cus_{suffix}",
        period_end=(datetime.now(UTC) + timedelta(days=30)).isoformat(),
        provider_event_id=f"evt_wh_{suffix}",
        amount_cents=1900,
    )
    event = {
        "id": f"evt_charge_ref_{suffix}",
        "type": "charge.refunded",
        "data": {"object": {"id": f"ch_{suffix}", "customer": f"cus_{suffix}", "amount": 1900, "amount_refunded": 1900}},
    }
    result = await process_stripe_event(event)
    assert result.get("handled") is True
    sub = await get_by_user_id(uid)
    assert sub["plan"] == "free"


@pytest.mark.asyncio
async def test_duplicate_webhook_idempotent(billing_user):
    from billing.webhook_processor import process_stripe_event

    uid = int(billing_user["id"])
    event = {
        "id": "evt_dup_p0_fixed",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer_details": {"email": billing_user["email"]},
                "subscription": "sub_dup_p0",
                "client_reference_id": str(uid),
                "metadata": {"tier": "pro"},
            }
        },
    }
    r1 = await process_stripe_event(event)
    r2 = await process_stripe_event(event)
    assert r1.get("handled") is True
    assert r2.get("action") == "duplicate_ignored"


@pytest.mark.asyncio
async def test_out_of_order_stale_event_skipped():
    from billing.out_of_order_guard import should_apply_event
    from database import init_db

    await init_db()
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    obj = f"sub_ooo_{suffix}"
    apply1, _ = await should_apply_event(object_id=obj, event_created_at=1000, event_id=f"evt_new_{suffix}")
    apply2, reason2 = await should_apply_event(object_id=obj, event_created_at=500, event_id=f"evt_old_{suffix}")
    assert apply1 is True
    assert apply2 is False
    assert "out_of_order" in reason2


@pytest.mark.asyncio
async def test_inbox_persist_and_dedupe():
    from billing.event_inbox import persist_inbox_event
    from database import init_db

    await init_db()
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    eid = f"evt_inbox_test_{suffix}"
    id1, new1 = await persist_inbox_event(
        provider="stripe",
        stripe_event_id=eid,
        event_type="invoice.paid",
        payload={"id": eid},
    )
    id2, new2 = await persist_inbox_event(
        provider="stripe",
        stripe_event_id=eid,
        event_type="invoice.paid",
        payload={"id": eid},
    )
    assert new1 is True
    assert new2 is False
    assert id1 == id2


@pytest.mark.asyncio
async def test_reconciliation_match(billing_user):
    from billing.reconciliation import ReconciliationResult, reconcile_account
    from billing.subscription_engine import activate_checkout

    uid = int(billing_user["id"])
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    await activate_checkout(
        email=billing_user["email"],
        plan="pro",
        provider="stripe",
        provider_subscription_id=f"sub_rec_{suffix}",
        user_id=uid,
        period_end=(datetime.now(UTC) + timedelta(days=30)).isoformat(),
        provider_event_id=f"evt_rec_{suffix}",
        amount_cents=1900,
    )
    from billing.subscription_store import get_by_user_id

    sub = await get_by_user_id(uid)
    rec = await reconcile_account(sub)
    assert rec["result"] == ReconciliationResult.MATCH.value


@pytest.mark.asyncio
async def test_financial_arithmetic_no_float():
    from billing.financial_arithmetic import from_minor_units, invoice_total_minor, to_minor_units
    from decimal import Decimal

    assert to_minor_units(Decimal("19.99")) == 1999
    assert from_minor_units(1999) == Decimal("19.99")
    assert invoice_total_minor(subtotal_minor=1900, tax_minor=190, discount_minor=100) == 1990


@pytest.mark.asyncio
async def test_break_glass_dual_approval_required(billing_user):
    from billing.break_glass import create_override

    uid = int(billing_user["id"])
    with pytest.raises(ValueError, match="Dual approval"):
        await create_override(
            user_id=uid,
            actor="admin@test",
            actor_role="admin",
            reason="test",
            ticket="T-1",
            new_tier="quant",
            require_dual_approval=True,
        )


@pytest.mark.asyncio
async def test_break_glass_override_grants_temporary_access(billing_user):
    from billing.break_glass import create_override
    from billing.entitlement_state import EntitlementState, resolve_entitlement_decision
    from billing.subscription_store import ensure_subscription_account

    uid = int(billing_user["id"])
    await ensure_subscription_account(uid, billing_user["email"], plan="free")
    await create_override(
        user_id=uid,
        actor="admin@test",
        actor_role="admin",
        reason="support_escalation",
        ticket="T-2",
        new_tier="pro",
        approval_actor="lead@test",
        expires_in_hours=1,
    )
    decision = await resolve_entitlement_decision(uid)
    assert decision.state == EntitlementState.MANUAL_TEMPORARY_OVERRIDE
    assert decision.effective_tier == "pro"


@pytest.mark.asyncio
async def test_tier_capability_consistency():
    from billing.plan_registry import CANONICAL_TIERS, plan_rank

    assert CANONICAL_TIERS == ("free", "pro", "elite", "quant", "institutional")
    assert plan_rank("pro") < plan_rank("elite") < plan_rank("quant")


@pytest.mark.asyncio
async def test_cancel_at_period_end_entitlement_persists(billing_user):
    from billing.subscription_engine import activate_checkout, schedule_cancel_at_period_end
    from billing.entitlement_state import decide_entitlement

    uid = int(billing_user["id"])
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    period_end = (datetime.now(UTC) + timedelta(days=20)).isoformat()
    await activate_checkout(
        email=billing_user["email"],
        plan="pro",
        provider="stripe",
        provider_subscription_id=f"sub_cancel_{suffix}",
        user_id=uid,
        period_end=period_end,
        provider_event_id=f"evt_cancel_{suffix}",
        amount_cents=1900,
    )
    sub = await schedule_cancel_at_period_end(uid)
    decision = decide_entitlement(sub)
    assert decision.allowed is True


@pytest.mark.asyncio
async def test_fraud_decline_velocity():
    from billing.fraud_controls import check_decline_velocity, record_decline

    email = f"fraud-{datetime.now(UTC).timestamp()}@test.com"
    for _ in range(6):
        await record_decline(email, decline_code="generic_decline")
    result = await check_decline_velocity(email)
    assert result["throttled"] is True


@pytest.mark.asyncio
async def test_consent_record(billing_user):
    from billing.consent_registry import latest_consent, record_consent

    uid = int(billing_user["id"])
    await record_consent(
        user_id=uid,
        terms_version="2026-01",
        renewal_disclosure_version="2026-01",
        consent_source="checkout",
        tier="pro",
    )
    consent = await latest_consent(uid)
    assert consent is not None
    assert consent["terms_version"] == "2026-01"


@pytest.mark.asyncio
async def test_price_registry_no_scattered_ids():
    from billing.price_versioning import build_price_registry

    registry = build_price_registry(env_stripe_ids={"pro": "price_test_pro"})
    pro = next(r for r in registry if r["tier_id"] == "pro")
    assert pro["stripe_price_id"] == "price_test_pro"
    assert pro["amount_minor"] == 1900


@pytest.mark.asyncio
async def test_observability_metrics():
    from billing.observability import collect_p0_metrics

    metrics = await collect_p0_metrics()
    assert "inbox_pending" in metrics
    assert "critical_alerts" in metrics


@pytest.mark.asyncio
async def test_seat_enforcement():
    from billing.seat_enforcement import check_seat_availability, ensure_org_billing_account

    org = await ensure_org_billing_account(org_id=99001, billing_owner_user_id=1, paid_seats=2)
    assert org["paid_seats"] == 2
    avail = await check_seat_availability(99001)
    assert avail["allowed"] is True
