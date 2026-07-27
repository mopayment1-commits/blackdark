"""
BLACKDARK — Stripe billing & subscription lifecycle (Priority 4).
"""

from __future__ import annotations

import logging
import os
from typing import Any

import stripe

import config

logger = logging.getLogger("BLACKDARK.Billing")

STRIPE_TIERS: dict[str, dict[str, Any]] = {
    "pro": {"amount": 2900, "name": "BLACKDARK Pro"},
    "whale": {"amount": 19900, "name": "BLACKDARK Whale"},
}

LEMON_SQUEEZY_ENV_KEYS = {
    "pro": "LEMON_SQUEEZY_CHECKOUT_PRO",
    "whale": "LEMON_SQUEEZY_CHECKOUT_WHALE",
}


def stripe_configured() -> bool:
    return bool(os.getenv("STRIPE_SECRET_KEY", ""))


def lemon_squeezy_checkout_url(tier: str) -> str | None:
    tier = tier.lower().strip()
    env_key = LEMON_SQUEEZY_ENV_KEYS.get(tier)
    if not env_key:
        return None
    url = os.getenv(env_key, "").strip()
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
                    "currency": "usd",
                    "product_data": {"name": info["name"]},
                    "unit_amount": info["amount"],
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }
        ]

    session_kwargs: dict[str, Any] = {
        "payment_method_types": ["card"],
        "line_items": line_items,
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "metadata": {"tier": tier},
        "allow_promotion_codes": True,
    }
    if customer_email:
        session_kwargs["customer_email"] = customer_email
    if user_id is not None:
        session_kwargs["client_reference_id"] = str(user_id)
    if tier == "pro" and config.PRO_TRIAL_DAYS > 0 and not price_id:
        session_kwargs["subscription_data"] = {"trial_period_days": config.PRO_TRIAL_DAYS}

    session = stripe.checkout.Session.create(**session_kwargs)
    return {"url": session.url, "session_id": session.id, "tier": tier}


def create_billing_portal_session(stripe_customer_id: str) -> dict[str, Any]:
    if not stripe_configured():
        raise RuntimeError("Stripe not configured")
    base = os.getenv("APP_BASE_URL", "http://localhost:8080").rstrip("/")
    session = stripe.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{base}/dashboard",
    )
    return {"url": session.url}


async def handle_stripe_webhook_event(event: dict[str, Any]) -> dict[str, Any]:
    from database import (
        activate_paid_subscription,
        cancel_subscription_by_stripe_id,
    )

    event_type = event.get("type", "")
    data_object = (event.get("data") or {}).get("object") or {}

    if event_type == "checkout.session.completed":
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
            logger.info("Subscription activated | email=%s tier=%s", email, tier)
        return {"handled": True, "action": "checkout_completed"}

    if event_type in {"customer.subscription.updated", "customer.subscription.created"}:
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

    if event_type == "customer.subscription.deleted":
        stripe_sub_id = str(data_object.get("id") or "")
        if stripe_sub_id:
            await cancel_subscription_by_stripe_id(stripe_sub_id)
        return {"handled": True, "action": "subscription_cancelled"}

    if event_type == "invoice.payment_failed":
        stripe_sub_id = str(data_object.get("subscription") or "")
        if stripe_sub_id:
            from database import upsert_subscription_by_stripe_id

            await upsert_subscription_by_stripe_id(stripe_sub_id, status="past_due")
        return {"handled": True, "action": "payment_failed"}

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
