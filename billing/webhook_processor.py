"""Unified webhook processor — Stripe + Lemon → subscription engine."""

from __future__ import annotations

import logging
from typing import Any

from billing.plan_registry import normalize_plan, PAID_TRIAL_DAYS
from billing.subscription_engine import (
    activate_checkout,
    payment_failed,
    renew_subscription,
    revoke_for_financial_reversal,
    sync_from_stripe_subscription,
    _period_from_stripe,
)

logger = logging.getLogger("BLACKDARK.Billing.Webhooks")


async def process_stripe_event(event: dict[str, Any]) -> dict[str, Any]:
    from database import claim_billing_webhook_event

    event_id = str(event.get("id") or "").strip()
    event_type = str(event.get("type") or "")
    if event_id:
        claimed = await claim_billing_webhook_event(
            provider="stripe",
            event_id=event_id,
            event_type=event_type,
        )
        if not claimed:
            return {"handled": True, "action": "duplicate_ignored", "event_id": event_id}

    data_object = (event.get("data") or {}).get("object") or {}

    if event_type == "checkout.session.completed":
        email = (
            (data_object.get("customer_details") or {}).get("email")
            or data_object.get("customer_email")
            or ""
        )
        tier = normalize_plan((data_object.get("metadata") or {}).get("tier", "pro"))
        stripe_sub_id = str(data_object.get("subscription") or "")
        stripe_customer_id = data_object.get("customer")
        client_ref = data_object.get("client_reference_id")
        user_id = int(client_ref) if client_ref and str(client_ref).isdigit() else None
        if email and stripe_sub_id:
            trial_days = PAID_TRIAL_DAYS if tier != "free" else 0
            from datetime import UTC, datetime, timedelta

            now = datetime.now(UTC)
            trial_end = (now + timedelta(days=trial_days)).isoformat() if trial_days else None
            result = await activate_checkout(
                email=email,
                plan=tier,
                provider="stripe",
                provider_subscription_id=stripe_sub_id,
                provider_customer_id=str(stripe_customer_id) if stripe_customer_id else None,
                user_id=user_id,
                trial_ends_at=trial_end if trial_days else None,
                auto_renew_consent=True,
                provider_event_id=event_id,
            )
            return {"handled": True, "action": "checkout_completed", **result}
        return {"handled": False, "reason": "missing_email_or_subscription"}

    if event_type in {"customer.subscription.updated", "customer.subscription.created"}:
        result = await sync_from_stripe_subscription(
            data_object,
            provider="stripe",
            provider_event_id=event_id,
        )
        return {"handled": True, "action": "subscription_updated", **result}

    if event_type == "customer.subscription.deleted":
        stripe_sub_id = str(data_object.get("id") or "")
        result = await revoke_for_financial_reversal(
            provider_subscription_id=stripe_sub_id,
            provider="stripe",
            provider_event_id=event_id,
            reason="subscription_deleted",
            payment_status="canceled",
        )
        return {"handled": True, "action": "subscription_cancelled", **result}

    if event_type in {"invoice.payment_failed", "invoice.payment_action_required"}:
        stripe_sub_id = str(data_object.get("subscription") or "")
        if stripe_sub_id:
            result = await payment_failed(
                provider_subscription_id=stripe_sub_id,
                provider="stripe",
                provider_event_id=event_id,
            )
            return {"handled": True, "action": "payment_failed", **result}
        return {"handled": False, "reason": "missing_subscription"}

    if event_type == "invoice.paid":
        stripe_sub_id = str(data_object.get("subscription") or "")
        billing_reason = str(data_object.get("billing_reason") or "")
        amount = data_object.get("amount_paid")
        p_start, p_end = _period_from_stripe(data_object)
        if stripe_sub_id:
            if billing_reason in {"subscription_cycle", "subscription_update"}:
                result = await renew_subscription(
                    provider_subscription_id=stripe_sub_id,
                    provider="stripe",
                    provider_event_id=event_id,
                    provider_invoice_id=str(data_object.get("id") or ""),
                    period_start=p_start,
                    period_end=p_end,
                    amount_cents=int(amount) if amount is not None else None,
                )
                return {"handled": True, "action": "invoice_paid", **result}
            result = await sync_from_stripe_subscription(
                {"id": stripe_sub_id, "current_period_start": data_object.get("period_start"), "current_period_end": data_object.get("period_end"), "status": "active"},
                provider="stripe",
                provider_event_id=event_id,
            )
            return {"handled": True, "action": "invoice_paid_sync", **result}
        return {"handled": False, "reason": "missing_subscription"}

    if event_type == "charge.refunded":
        result = await revoke_for_financial_reversal(
            provider_subscription_id=None,
            provider="stripe",
            provider_event_id=event_id,
            reason="charge_refunded",
            payment_status="refunded",
        )
        return {"handled": True, "action": "refund", **result}

    if event_type == "charge.dispute.created":
        result = await revoke_for_financial_reversal(
            provider_subscription_id=None,
            provider="stripe",
            provider_event_id=event_id,
            reason="charge_dispute",
            payment_status="disputed",
        )
        return {"handled": True, "action": "dispute", **result}

    return {"handled": False, "type": event_type}


async def process_lemon_event(event: dict[str, Any]) -> dict[str, Any]:
    from billing_service import _lemon_event_context, verify_lemon_webhook_signature
    from database import claim_billing_webhook_event

    ctx = _lemon_event_context(event)
    dedupe_key = str(ctx["dedupe_key"])
    if dedupe_key.strip(":"):
        claimed = await claim_billing_webhook_event(
            provider="lemon_squeezy",
            event_id=dedupe_key[:240],
            event_type=ctx["event_name"] or "unknown",
        )
        if not claimed:
            return {
                "handled": True,
                "action": "duplicate_ignored",
                "provider": "lemon_squeezy",
                "event_id": dedupe_key[:240],
            }

    event_name = ctx["event_name"]
    tier = normalize_plan(ctx["tier"])
    email = ctx["email"]
    lemon_id = ctx["lemon_id"]

    if event_name in {"subscription_created", "subscription_payment_success", "order_created"}:
        if not (email and lemon_id):
            return {"handled": False, "reason": "missing_email_or_id"}
        result = await activate_checkout(
            email=email,
            plan=tier,
            provider="lemon_squeezy",
            provider_subscription_id=lemon_id,
            auto_renew_consent=True,
            provider_event_id=dedupe_key[:240],
        )
        return {"handled": True, "action": "checkout_completed", "provider": "lemon_squeezy", **result}

    if event_name in {"subscription_updated", "subscription_resumed", "subscription_unpaused"}:
        if lemon_id:
            from billing.subscription_store import get_by_provider_subscription_id, update_subscription_account

            sub = await get_by_provider_subscription_id(lemon_id)
            if sub:
                await update_subscription_account(
                    int(sub["user_id"]),
                    plan=tier,
                    subscription_status=ctx["status"] if ctx["status"] != "trial" else "trialing",
                    bump_entitlements=False,
                )
        return {"handled": True, "action": "subscription_updated", "provider": "lemon_squeezy"}

    if event_name in {"subscription_cancelled", "subscription_expired"}:
        result = await revoke_for_financial_reversal(
            provider_subscription_id=lemon_id,
            provider="lemon_squeezy",
            provider_event_id=dedupe_key[:240],
            reason=event_name,
            payment_status="canceled",
        )
        return {"handled": True, "action": "subscription_cancelled", **result}

    if event_name in {"subscription_payment_failed", "subscription_paused"}:
        if lemon_id:
            result = await payment_failed(
                provider_subscription_id=lemon_id,
                provider="lemon_squeezy",
                provider_event_id=dedupe_key[:240],
            )
            return {"handled": True, "action": "payment_failed", **result}
    return {"handled": False, "type": event_name, "provider": "lemon_squeezy"}
