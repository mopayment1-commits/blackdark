"""
BLACKDARK — Stripe / Lemon Squeezy billing & subscription lifecycle.

Self-serve: Decision Pro ($29) and Decision Desk ($49).
Free = Proof Pass ($0). Institutional = Talk to us from $3,000 → open (not a Stripe SKU).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

import stripe

import config
logger = logging.getLogger("BLACKDARK.Billing")

STRIPE_TIERS: dict[str, dict[str, Any]] = {
    "pro": {
        "amount": 2900,
        "currency": "usd",
        "name": "Decision Pro",
        "sku": "decision_pro",
    },
    "whale": {
        "amount": 4900,
        "currency": "usd",
        "name": "Decision Desk",
        "sku": "decision_desk",
    },
}

BILLING_CURRENCY = "usd"

LEMON_SQUEEZY_ENV_KEYS = {
    "pro": "LEMON_SQUEEZY_CHECKOUT_PRO",
    "whale": "LEMON_SQUEEZY_CHECKOUT_WHALE",
}

# Optional customer portal / billing manage URL (Lemon dashboard).
LEMON_SQUEEZY_PORTAL_ENV = "LEMON_SQUEEZY_CUSTOMER_PORTAL_URL"

# Map Lemon variant/product name hints → internal tiers.
_LEMON_TIER_HINTS = (
    ("whale", "whale"),
    ("pro", "pro"),
)


def stripe_configured() -> bool:
    return bool(os.getenv("STRIPE_SECRET_KEY", ""))


def lemon_squeezy_checkout_url(tier: str) -> str | None:
    tier = tier.lower().strip()
    env_key = LEMON_SQUEEZY_ENV_KEYS.get(tier)
    if not env_key:
        return None
    url = os.getenv(env_key, "").strip()
    return url or None


def lemon_squeezy_portal_url() -> str | None:
    url = os.getenv(LEMON_SQUEEZY_PORTAL_ENV, "").strip()
    return url or None


def billing_configured() -> bool:
    return stripe_configured() or bool(lemon_squeezy_checkout_url("pro"))


def billing_provider() -> str:
    if stripe_configured():
        return "stripe"
    if lemon_squeezy_checkout_url("pro"):
        return "lemon_squeezy"
    return "none"


def _price_id_for_tier(tier: str) -> str | None:
    env_key = f"STRIPE_PRICE_{tier.upper()}"
    value = os.getenv(env_key, "").strip()
    return value or None


def _base_urls() -> tuple[str, str]:
    base = os.getenv("APP_BASE_URL", "http://localhost:8080").rstrip("/")
    success = os.getenv(
        "STRIPE_SUCCESS_URL",
        f"{base}/success?session_id={{CHECKOUT_SESSION_ID}}",
    )
    cancel = os.getenv("STRIPE_CANCEL_URL", f"{base}/cancel")
    return success, cancel


def create_checkout_session(
    tier: str,
    *,
    customer_email: str | None = None,
    user_id: int | None = None,
) -> dict[str, Any]:
    if not stripe_configured():
        raise RuntimeError("Stripe not configured")

    tier = tier.lower().strip()
    if tier not in STRIPE_TIERS:
        raise ValueError(f"Invalid tier: {tier}")

    success_url, cancel_url = _base_urls()
    price_id = _price_id_for_tier(tier)

    if price_id:
        line_items = [{"price": price_id, "quantity": 1}]
    else:
        info = STRIPE_TIERS[tier]
        line_items = [
            {
                "price_data": {
                    "currency": BILLING_CURRENCY,
                    "product_data": {"name": info["name"]},
                    "unit_amount": info["amount"],
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }
        ]

    # Hosted Checkout: card + wallets (Apple Pay / Google Pay when enabled on Stripe).
    # PAN/CVV never touch our servers (PCI SAQ A target).
    trial_days = int(config.PRO_TRIAL_DAYS) if tier == "pro" and config.PRO_TRIAL_DAYS > 0 else 0
    meta = {
        "tier": tier,
        "currency": BILLING_CURRENCY,
        "sku": STRIPE_TIERS[tier]["sku"],
        "product": "trust_os",
    }
    session_kwargs: dict[str, Any] = {
        "mode": "subscription",
        "line_items": line_items,
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": meta,
        "allow_promotion_codes": True,
        "billing_address_collection": "auto",
        # Card + wallets (Apple Pay / Google Pay) via Stripe Checkout when domain verified.
        "payment_method_types": ["card"],
    }
    if customer_email:
        session_kwargs["customer_email"] = customer_email
    if user_id is not None:
        session_kwargs["client_reference_id"] = str(user_id)
    sub_data: dict[str, Any] = {"metadata": meta}
    if trial_days:
        sub_data["trial_period_days"] = trial_days
    session_kwargs["subscription_data"] = sub_data

    session = stripe.checkout.Session.create(**session_kwargs)
    return {
        "url": session.url,
        "session_id": session.id,
        "tier": tier,
        "currency": BILLING_CURRENCY.upper(),
        "provider": "stripe",
        "trial_days": trial_days,
        "pci_note": "Card data collected only on Stripe-hosted Checkout.",
    }


def create_billing_portal_session(stripe_customer_id: str) -> dict[str, Any]:
    if not stripe_configured():
        raise RuntimeError("Stripe not configured")
    base = os.getenv("APP_BASE_URL", "http://localhost:8080").rstrip("/")
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{base}/dashboard",
    )
    return {"url": session.url}


async def _claim_stripe_webhook_event(event_id: str, event_type: Any) -> dict[str, Any] | None:
    if not event_id:
        return None
    from database import claim_billing_webhook_event

    claimed = await claim_billing_webhook_event(
        provider="stripe",
        event_id=event_id,
        event_type=str(event_type),
    )
    if claimed:
        return None
    return {"handled": True, "action": "duplicate_ignored", "event_id": event_id}


async def _handle_stripe_checkout_completed(data_object: dict[str, Any]) -> dict[str, Any]:
    from database import activate_paid_subscription

    email = (
        (data_object.get("customer_details") or {}).get("email")
        or data_object.get("customer_email")
        or ""
    )
    tier = (data_object.get("metadata") or {}).get("tier", "pro")
    stripe_sub_id = data_object.get("subscription")
    stripe_customer_id = data_object.get("customer")
    if email and stripe_sub_id:
        await activate_paid_subscription(
            email,
            tier,
            str(stripe_sub_id),
            stripe_customer_id=str(stripe_customer_id) if stripe_customer_id else None,
        )
        logger.info(
            "Subscription activated | email=%s tier=%s currency=USD",
            str(email).replace("\r", " ").replace("\n", " "),
            str(tier).replace("\r", " ").replace("\n", " "),
        )
    return {"handled": True, "action": "checkout_completed", "currency": "USD"}


async def _handle_stripe_subscription_updated(data_object: dict[str, Any]) -> dict[str, Any]:
    stripe_sub_id = str(data_object.get("id") or "")
    status = str(data_object.get("status") or "active")
    tier = (data_object.get("metadata") or {}).get("tier", "pro")
    if stripe_sub_id:
        from database import upsert_subscription_by_stripe_id

        await upsert_subscription_by_stripe_id(
            stripe_sub_id,
            tier=tier,
            status=_map_stripe_status(status),
        )
    return {"handled": True, "action": "subscription_updated"}


async def _handle_stripe_subscription_deleted(data_object: dict[str, Any]) -> dict[str, Any]:
    from database import cancel_subscription_by_stripe_id

    stripe_sub_id = str(data_object.get("id") or "")
    if stripe_sub_id:
        await cancel_subscription_by_stripe_id(stripe_sub_id)
    return {"handled": True, "action": "subscription_cancelled"}


async def _handle_stripe_payment_failed(
    data_object: dict[str, Any],
    event_type: Any,
) -> dict[str, Any]:
    stripe_sub_id = str(data_object.get("subscription") or "")
    if stripe_sub_id:
        from database import upsert_subscription_by_stripe_id

        await upsert_subscription_by_stripe_id(stripe_sub_id, status="past_due")
        logger.warning(
            "Stripe dunning | sub=%s event=%s",
            str(stripe_sub_id).replace("\r", " ").replace("\n", " "),
            str(event_type).replace("\r", " ").replace("\n", " "),
        )
    return {"handled": True, "action": "payment_failed", "dunning": True}


async def _handle_stripe_invoice_paid(data_object: dict[str, Any]) -> dict[str, Any]:
    stripe_sub_id = str(data_object.get("subscription") or "")
    if stripe_sub_id:
        from database import upsert_subscription_by_stripe_id

        await upsert_subscription_by_stripe_id(stripe_sub_id, status="active")
    return {"handled": True, "action": "invoice_paid", "currency": "USD"}


def _handle_stripe_refund_or_dispute(data_object: dict[str, Any], event_type: Any) -> dict[str, Any]:
    # Entitlement stays until subscription cancels unless ops force-expire.
    logger.info(
        "Stripe refund/dispute recorded | type=%s id=%s",
        str(event_type).replace("\r", " ").replace("\n", " "),
        str(data_object.get("id")).replace("\r", " ").replace("\n", " "),
    )
    return {"handled": True, "action": "refund_or_dispute_logged", "type": event_type}


async def handle_stripe_webhook_event(event: dict[str, Any]) -> dict[str, Any]:
    from database import (
        claim_billing_webhook_event,
    )

    event_id = str(event.get("id") or "").strip()
    event_type = event.get("type", "")
    if event_id:
        claimed = await claim_billing_webhook_event(
            provider="stripe",
            event_id=event_id,
            event_type=str(event_type),
        )
        if not claimed:
            return {"handled": True, "action": "duplicate_ignored", "event_id": event_id}

    data_object = (event.get("data") or {}).get("object") or {}

    if event_type == "checkout.session.completed":
        return await _handle_stripe_checkout_completed(data_object)

    if event_type in {"customer.subscription.updated", "customer.subscription.created"}:
        return await _handle_stripe_subscription_updated(data_object)

    if event_type == "customer.subscription.deleted":
        return await _handle_stripe_subscription_deleted(data_object)

    if event_type in {"invoice.payment_failed", "invoice.payment_action_required"}:
        return await _handle_stripe_payment_failed(data_object, event_type)

    if event_type == "invoice.paid":
        return await _handle_stripe_invoice_paid(data_object)

    if event_type in {"charge.refunded", "charge.dispute.created"}:
        return _handle_stripe_refund_or_dispute(data_object, event_type)

    return {"handled": False, "type": event_type}


def _map_stripe_status(stripe_status: str) -> str:
    mapping = {
        "active": "active",
        "trialing": "trial",
        "past_due": "past_due",
        "canceled": "expired",
        "unpaid": "past_due",
        "incomplete": "past_due",
        "incomplete_expired": "expired",
    }
    return mapping.get(stripe_status, "active")


def verify_lemon_webhook_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Lemon Squeezy signs the raw body with HMAC-SHA256 (hex digest in X-Signature)."""
    secret = os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "").strip()
    if not secret:
        return False
    provided = (signature_header or "").strip()
    if not provided:
        return False
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, provided)


def _lemon_infer_tier(attrs: dict[str, Any], meta: dict[str, Any] | None = None) -> str:
    custom = (meta or {}).get("custom_data") or {}
    if isinstance(custom, dict):
        hinted = str(custom.get("tier") or "").strip().lower()
        if hinted in STRIPE_TIERS:
            return hinted
    blob = " ".join(
        str(attrs.get(k) or "")
        for k in ("product_name", "variant_name", "product_id", "variant_id")
    ).lower()
    for needle, tier in _LEMON_TIER_HINTS:
        if needle in blob:
            return tier
    return "pro"


def _map_lemon_status(status: str) -> str:
    mapping = {
        "active": "active",
        "on_trial": "trial",
        "past_due": "past_due",
        "unpaid": "past_due",
        "cancelled": "expired",
        "canceled": "expired",
        "expired": "expired",
        "paused": "past_due",
    }
    return mapping.get((status or "").strip().lower(), "active")


async def handle_lemon_webhook_event(event: dict[str, Any]) -> dict[str, Any]:
    """Activate / update / cancel entitlements from Lemon Squeezy webhooks."""
    from database import (
        activate_paid_subscription,
        cancel_subscription_by_stripe_id,
        claim_billing_webhook_event,
        upsert_subscription_by_stripe_id,
    )

    meta = event.get("meta") or {}
    event_name = str(meta.get("event_name") or "").strip()
    data = event.get("data") or {}
    attrs = data.get("attributes") or {}
    webhook_id = str(meta.get("webhook_id") or event.get("webhook_id") or "").strip()
    lemon_id = str(data.get("id") or attrs.get("subscription_id") or "").strip()
    dedupe_key = webhook_id or f"{event_name}:{lemon_id}:{attrs.get('updated_at') or attrs.get('created_at') or ''}"
    if dedupe_key.strip(":"):
        claimed = await claim_billing_webhook_event(
            provider="lemon_squeezy",
            event_id=dedupe_key[:240],
            event_type=event_name or "unknown",
        )
        if not claimed:
            return {
                "handled": True,
                "action": "duplicate_ignored",
                "provider": "lemon_squeezy",
                "event_id": dedupe_key[:240],
            }
    if lemon_id and not lemon_id.startswith("lemon_"):
        lemon_id = f"lemon_{lemon_id}"

    email = (
        str(attrs.get("user_email") or attrs.get("customer_email") or attrs.get("email") or "")
        .strip()
        .lower()
    )
    tier = _lemon_infer_tier(attrs, meta if isinstance(meta, dict) else None)
    status = _map_lemon_status(str(attrs.get("status") or "active"))

    if event_name in {
        "subscription_created",
        "subscription_payment_success",
        "order_created",
    }:
        if email and lemon_id:
            await activate_paid_subscription(email, tier, lemon_id)
            logger.info(
                "Lemon subscription activated | email=%s tier=%s id=%s",
                str(email).replace("\r", " ").replace("\n", " "),
                str(tier).replace("\r", " ").replace("\n", " "),
                str(lemon_id).replace("\r", " ").replace("\n", " "),
            )
            return {"handled": True, "action": "checkout_completed", "provider": "lemon_squeezy"}
        return {"handled": False, "reason": "missing_email_or_id", "event": event_name}

    if event_name in {"subscription_updated", "subscription_resumed", "subscription_unpaused"}:
        if lemon_id:
            await upsert_subscription_by_stripe_id(
                lemon_id,
                tier=tier,
                status=status,
                email=email or None,
            )
            return {"handled": True, "action": "subscription_updated", "provider": "lemon_squeezy"}
        return {"handled": False, "reason": "missing_id", "event": event_name}

    if event_name in {
        "subscription_cancelled",
        "subscription_expired",
        "subscription_payment_failed",
        "subscription_paused",
    }:
        if lemon_id:
            if event_name in {"subscription_cancelled", "subscription_expired"}:
                await cancel_subscription_by_stripe_id(lemon_id)
                return {"handled": True, "action": "subscription_cancelled", "provider": "lemon_squeezy"}
            await upsert_subscription_by_stripe_id(lemon_id, status="past_due", email=email or None)
            return {"handled": True, "action": "payment_failed", "provider": "lemon_squeezy"}
        return {"handled": False, "reason": "missing_id", "event": event_name}

    return {"handled": False, "type": event_name, "provider": "lemon_squeezy"}
