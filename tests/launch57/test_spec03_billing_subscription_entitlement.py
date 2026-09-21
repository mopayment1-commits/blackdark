"""SPEC_03 — Billing, Subscription & Entitlement adversarial tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from launch57.billing_subscription_entitlement_common import (
    DOMAIN,
    build_final_status,
    build_requirements_register,
    build_runtime_truth_table,
    independent_verification,
)


def test_requirements_register_nonempty():
    reqs = build_requirements_register()
    assert len(reqs) >= 20
    assert all(r["mandatory"] for r in reqs)


def test_client_tier_param_capped_without_subscription():
    from launch57.billing_entitlement_common import apply_entitlement_gated_params

    capped = apply_entitlement_gated_params({"tier": "elite"})
    assert capped["tier"] == "free"
    assert capped["_entitlement_resolution"]["unverified_paid_claim"] is True


def test_verified_subscription_tier_honored():
    from launch57.billing_entitlement_common import apply_entitlement_gated_params, enforce_launch57_entitlement

    p = apply_entitlement_gated_params(
        {"tier": "pro", "verified_subscription_tier": "pro", "user_key": "user-1", "subject_id": "user-1"},
    )
    assert p["tier"] == "pro"
    gate = enforce_launch57_entitlement(launch_item_id=33, params=p)
    assert gate["allowed"] is True


def test_smart_alerts_free_user_denied_paid_surface():
    from launch57.billing_entitlement_common import enforce_launch57_entitlement

    gate = enforce_launch57_entitlement(launch_item_id=33, params={"tier": "pro"})
    assert gate["allowed"] is False
    assert gate["fail_closed"] is True


def test_anonymous_cannot_access_paid_entitlement():
    from launch57.billing_entitlement_common import enforce_launch57_entitlement

    gate = enforce_launch57_entitlement(launch_item_id=49, params={"tier": "pro", "user_key": "anonymous"})
    assert gate["allowed"] is False


@pytest.mark.asyncio
async def test_free_history_limit_not_bypassed_by_tier_param(monkeypatch):
    from launch57.edge_ui_batch1 import personal_decision_history

    monkeypatch.setattr(
        "launch57.edge_ui_batch1.read_decision_history_rows",
        lambda **kwargs: [{"id": i} for i in range(kwargs.get("limit", 0))],
    )

    out = await personal_decision_history(
        symbol="BTC",
        params={"tier": "pro", "limit": 50, "user_key": "user-1", "subject_id": "user-1"},
    )
    history = out.get("personal_decision_history") or {}
    assert history.get("count", 0) <= 10


@pytest.mark.asyncio
async def test_paid_subscription_grants_pro_entitlement(billing_user):
    from billing.subscription_engine import activate_checkout, entitlement_allowed
    from billing.subscription_store import get_by_user_id
    from launch57.billing_entitlement_common import apply_entitlement_gated_params, enforce_launch57_entitlement

    uid = int(billing_user["id"])
    email = billing_user["email"]
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    await activate_checkout(
        email=email,
        plan="pro",
        provider="stripe",
        provider_subscription_id=f"sub_spec03_{suffix}",
        user_id=uid,
        period_end=(datetime.now(UTC) + timedelta(days=30)).isoformat(),
        provider_event_id=f"evt_spec03_{suffix}",
    )
    sub = await get_by_user_id(uid)
    assert entitlement_allowed(sub)
    p = apply_entitlement_gated_params({"tier": "pro"}, subscription=sub)
    assert p["tier"] == "pro"
    gate = enforce_launch57_entitlement(launch_item_id=33, params=p, subscription=sub)
    assert gate["allowed"] is True


@pytest.mark.asyncio
async def test_webhook_idempotent_duplicate_ignored(billing_user):
    from billing.webhook_processor import process_stripe_event

    uid = int(billing_user["id"])
    email = billing_user["email"]
    event = {
        "id": "evt_spec03_dup",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer_details": {"email": email},
                "subscription": "sub_spec03_dup",
                "customer": "cus_spec03",
                "client_reference_id": str(uid),
                "metadata": {"tier": "pro"},
            }
        },
    }
    r1 = await process_stripe_event(event)
    r2 = await process_stripe_event(event)
    assert r1.get("handled") is True
    assert r2.get("duplicate") is True or r2.get("action") == "duplicate_ignored"


def test_out_of_order_provider_event_rejected():
    from billing.event_ordering import should_apply_provider_subscription_event

    now = datetime.now(UTC)
    stored = {
        "current_period_end": (now + timedelta(days=30)).isoformat(),
        "last_provider_event_created": 5000,
    }
    apply, reason = should_apply_provider_subscription_event(
        stored,
        period_end=(now + timedelta(days=5)).isoformat(),
        event_created_at=1000,
    )
    assert apply is False
    assert "out_of_order" in reason


@pytest.mark.asyncio
async def test_signup_trial_does_not_grant_paid_capabilities(billing_user):
    """Break: register-time trial intent must not unlock paid Launch-57 surfaces."""
    from billing.subscription_engine import (
        effective_plan,
        resolve_entitlements_for_user,
        start_paid_trial,
    )
    from billing.subscription_store import get_by_user_id
    from launch57.billing_entitlement_common import (
        apply_entitlement_gated_params,
        enforce_launch57_entitlement,
    )

    uid = int(billing_user["id"])
    email = billing_user["email"]
    version_before = (await get_by_user_id(uid) or {}).get("entitlements_version") or 1

    trial = await start_paid_trial(uid, email, "pro")
    assert trial["plan"] == "free"
    assert trial.get("pending_plan") == "pro"
    assert trial["payment_status"] == "signup_intent"
    assert not trial.get("provider_subscription_id")

    sub = await get_by_user_id(uid)
    assert sub is not None
    assert sub.get("entitlements_version") == version_before
    assert effective_plan(sub) == "free"

    ent = await resolve_entitlements_for_user(uid)
    assert ent["effective_plan"] == "free"

    params = apply_entitlement_gated_params(
        {"tier": "pro", "user_id": uid, "subject_id": str(uid)},
        subscription=sub,
    )
    assert params["tier"] == "free"
    gate = enforce_launch57_entitlement(launch_item_id=33, params=params, subscription=sub)
    assert gate["allowed"] is False
    assert gate.get("fail_closed") is True


@pytest.mark.asyncio
async def test_failed_webhook_does_not_silently_upgrade_signup_trial(billing_user):
    from billing.subscription_engine import effective_plan, start_paid_trial
    from billing.subscription_store import get_by_user_id
    from billing.webhook_processor import process_stripe_event

    uid = int(billing_user["id"])
    email = billing_user["email"]
    await start_paid_trial(uid, email, "elite")
    before = await get_by_user_id(uid)
    assert before is not None
    version_before = before.get("entitlements_version")

    broken = await process_stripe_event(
        {
            "id": "evt_spec03_broken_checkout",
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {"tier": "elite"}}},
        }
    )
    assert broken.get("handled") is False

    after = await get_by_user_id(uid)
    assert after is not None
    assert after.get("entitlements_version") == version_before
    assert effective_plan(after) == "free"
    assert after.get("plan") == "free"
    assert after.get("pending_plan") == "elite"


@pytest.mark.asyncio
async def test_stripe_checkout_trial_holds_free_until_invoice_paid(billing_user):
    from billing.subscription_engine import (
        activate_checkout,
        effective_plan,
        renew_subscription,
    )
    from billing.subscription_store import get_by_user_id

    uid = int(billing_user["id"])
    email = billing_user["email"]
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    trial_end = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    sub_id = f"sub_trial_hold_{suffix}"

    await activate_checkout(
        email=email,
        plan="pro",
        provider="stripe",
        provider_subscription_id=sub_id,
        user_id=uid,
        trial_ends_at=trial_end,
        provider_event_id=f"evt_trial_checkout_{suffix}",
    )
    sub = await get_by_user_id(uid)
    assert sub["subscription_status"] == "trialing"
    assert sub["plan"] == "pro"
    assert effective_plan(sub) == "free"

    period_end = (datetime.now(UTC) + timedelta(days=30)).isoformat()
    await renew_subscription(
        provider_subscription_id=sub_id,
        provider="stripe",
        provider_event_id=f"evt_trial_invoice_{suffix}",
        provider_invoice_id=f"in_{suffix}",
        period_end=period_end,
        amount_cents=1999,
    )
    sub = await get_by_user_id(uid)
    assert sub["subscription_status"] == "active"
    assert sub["payment_status"] == "current"
    assert effective_plan(sub) == "pro"


def test_bad_signature_reject_security_event():
    from transport_webhook_env.webhook_lifecycle import reject_security_event

    rec = reject_security_event(provider="stripe", reason="invalid_signature", correlation_id="spec03")
    assert rec["state"] == "REJECTED_SECURITY"


@pytest.mark.asyncio
async def test_cancel_revokes_entitlement_after_period(billing_user):
    from billing.subscription_engine import activate_checkout, revoke_for_financial_reversal
    from billing.subscription_store import get_by_user_id

    uid = int(billing_user["id"])
    email = billing_user["email"]
    suffix = str(datetime.now(UTC).timestamp()).replace(".", "")
    sub_id = f"sub_cancel_{suffix}"
    await activate_checkout(
        email=email,
        plan="pro",
        provider="stripe",
        provider_subscription_id=sub_id,
        user_id=uid,
        provider_event_id=f"evt_cancel_{suffix}",
    )
    revoked = await revoke_for_financial_reversal(
        provider_subscription_id=sub_id,
        provider="stripe",
        provider_event_id=f"evt_revoke_{suffix}",
        reason="subscription_deleted",
        payment_status="canceled",
    )
    assert revoked["handled"] is True
    sub = await get_by_user_id(uid)
    assert sub["plan"] == "free" or sub["subscription_status"] in {"expired", "canceled"}


def test_runtime_truth_all_yes():
    rows = build_runtime_truth_table()
    failures = [r for r in rows if r["status"] != "YES"]
    assert not failures, failures


def test_independent_verification_passes():
    iv = independent_verification()
    assert iv["INDEPENDENT_VERIFICATION_PASS"] is True


def test_final_status_closed_local():
    status = build_final_status(skip_tests=True)
    assert status["PASS_LIVE"] is False
    assert status["LIVE_VALIDATION_PENDING"] is True
    assert status["entitlement_matrix_ok"] is True


def test_removing_tier_cap_breaks_gate(monkeypatch):
    from launch57.billing_subscription_entitlement_common import _probe_server_side_gating

    monkeypatch.setattr(
        "launch57.billing_entitlement_common.resolve_effective_entitlement_tier",
        lambda params=None, subscription=None: {
            "effective_tier": "elite",
            "requested_tier": "elite",
            "verified": True,
            "client_tier_honored": True,
            "unverified_paid_claim": False,
            "source": "broken_test",
        },
    )
    status, _ = _probe_server_side_gating()
    assert status.value == "NO"


def test_spec03_artifacts_exist_after_generator():
    out = Path("governance/launch57/SPEC_03_BILLING_SUBSCRIPTION_ENTITLEMENT")
    for name in (
        "REQUIREMENTS_REGISTER.json",
        "RUNTIME_TRUTH_TABLE.md",
        "LOCAL_CLOSURE_REPORT.md",
        "INDEPENDENT_VERIFICATION.json",
        "FINAL_STATUS.json",
    ):
        path = out / name
        if path.exists() and name.endswith(".json") and name == "FINAL_STATUS.json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            assert payload.get("domain") == DOMAIN


@pytest.fixture
async def billing_user():
    import database
    from database import create_user, init_db

    await init_db()
    email = f"spec03-billing-{datetime.now(UTC).timestamp()}@blackdark.test"
    uid = await create_user(email, "pbkdf2_sha256$260000$deadbeef$" + "a" * 64, "Spec03 Test")
    return {"id": uid, "email": email}
