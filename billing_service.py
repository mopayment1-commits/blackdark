"""
BLACKDARK — Stripe / Lemon Squeezy billing & subscription lifecycle.

Official tiers: FREE · PRO · ELITE · QUANT · INSTITUTIONAL (self-serve except institutional).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Any

import stripe

import config
from billing.plan_registry import (
    PAID_TRIAL_DAYS,
    PLAN_DEFINITIONS,
    SELF_SERVE_PLANS,
    lemon_checkout_env,
    normalize_plan,
    stripe_price_env,
)

logger = logging.getLogger("BLACKDARK.Billing")

STRIPE_TIERS: dict[str, dict[str, Any]] = {
    plan: {
        "amount": PLAN_DEFINITIONS[plan]["price_cents"],
        "currency": "usd",
        "name": PLAN_DEFINITIONS[plan]["name"],
        "sku": PLAN_DEFINITIONS[plan]["sku"],
        "display": PLAN_DEFINITIONS[plan]["display"],
    }
    for plan in SELF_SERVE_PLANS
}
# Legacy alias
STRIPE_TIERS["whale"] = dict(STRIPE_TIERS["elite"])

BILLING_CURRENCY = "usd"

LEMON_SQUEEZY_ENV_KEYS = {
    "pro": "LEMON_SQUEEZY_CHECKOUT_PRO",
    "elite": "LEMON_SQUEEZY_CHECKOUT_ELITE",
    "quant": "LEMON_SQUEEZY_CHECKOUT_QUANT",
    "whale": "LEMON_SQUEEZY_CHECKOUT_WHALE",
}

LEMON_SQUEEZY_PORTAL_ENV = "LEMON_SQUEEZY_CUSTOMER_PORTAL_URL"

_LEMON_TIER_HINTS = (
    ("quant", "quant"),
    ("elite", "elite"),
    ("whale", "elite"),
    ("desk", "elite"),
    ("pro", "pro"),
)


def stripe_configured() -> bool:
    return bool(os.getenv("STRIPE_SECRET_KEY", ""))


def lemon_squeezy_checkout_url(tier: str) -> str | None:
    tier = normalize_plan(tier)
    url = lemon_checkout_env(tier)
    if url:
        return url
    env_key = LEMON_SQUEEZY_ENV_KEYS.get(tier)
    if not env_key:
        return None
    return os.getenv(env_key, "").strip() or None


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
    return stripe_price_env(tier)


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

    tier = normalize_plan(tier)
    if tier not in STRIPE_TIERS:
        raise ValueError(f"Invalid tier: {tier}")

    logger.info(
        "billing_checkout_request tier=%s email=%s user_id=%s",
        str(tier).replace("\r", " ").replace("\n", " "),
        str(customer_email or "").replace("\r", " ").replace("\n", " "),
        str(user_id if user_id is not None else "").replace("\r", " ").replace("\n", " "),
    )

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
    trial_days = PAID_TRIAL_DAYS if tier in SELF_SERVE_PLANS and PAID_TRIAL_DAYS > 0 else 0
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
    response = {
        "url": session.url,
        "session_id": session.id,
        "tier": tier,
        "currency": BILLING_CURRENCY.upper(),
        "provider": "stripe",
        "trial_days": trial_days,
        "pci_note": "Card data collected only on Stripe-hosted Checkout.",
    }
    logger.info(
        "billing_checkout_response session_id=%s tier=%s provider=%s",
        str(session.id).replace("\r", " ").replace("\n", " "),
        str(tier).replace("\r", " ").replace("\n", " "),
        "stripe",
    )
    return response


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
    event_id = str(event.get("id") or "")
    event_type = str(event.get("type") or "")
    logger.info(
        "billing_stripe_webhook_request event_id=%s type=%s",
        event_id.replace("\r", " ").replace("\n", " "),
        event_type.replace("\r", " ").replace("\n", " "),
    )
    from billing.webhook_processor import process_stripe_event

    result = await process_stripe_event(event)
    logger.info(
        "billing_stripe_webhook_response event_id=%s action=%s handled=%s",
        event_id.replace("\r", " ").replace("\n", " "),
        str(result.get("action") or "").replace("\r", " ").replace("\n", " "),
        str(result.get("handled")).replace("\r", " ").replace("\n", " "),
    )
    return result


async def handle_lemon_webhook_event(event: dict[str, Any]) -> dict[str, Any]:
    ctx = _lemon_event_context(event)
    logger.info(
        "billing_lemon_webhook_request event_name=%s lemon_id=%s email=%s",
        str(ctx["event_name"]).replace("\r", " ").replace("\n", " "),
        str(ctx["lemon_id"]).replace("\r", " ").replace("\n", " "),
        str(ctx["email"]).replace("\r", " ").replace("\n", " "),
    )
    from billing.webhook_processor import process_lemon_event

    result = await process_lemon_event(event)
    logger.info(
        "billing_lemon_webhook_response event_name=%s action=%s handled=%s",
        str(ctx["event_name"]).replace("\r", " ").replace("\n", " "),
        str(result.get("action") or "").replace("\r", " ").replace("\n", " "),
        str(result.get("handled")).replace("\r", " ").replace("\n", " "),
    )
    return result


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
    from billing.plan_registry import normalize_plan

    custom = (meta or {}).get("custom_data") or {}
    if isinstance(custom, dict):
        hinted = normalize_plan(str(custom.get("tier") or ""))
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


def _lemon_event_context(event: dict[str, Any]) -> dict[str, Any]:
    meta = event.get("meta") or {}
    data = event.get("data") or {}
    attrs = data.get("attributes") or {}
    event_name = str(meta.get("event_name") or "").strip()
    lemon_id = str(data.get("id") or attrs.get("subscription_id") or "").strip()
    webhook_id = str(meta.get("webhook_id") or event.get("webhook_id") or "").strip()
    dedupe_key = webhook_id or f"{event_name}:{lemon_id}:{attrs.get('updated_at') or attrs.get('created_at') or ''}"
    if lemon_id and not lemon_id.startswith("lemon_"):
        lemon_id = f"lemon_{lemon_id}"
    return {
        "meta": meta,
        "attrs": attrs,
        "event_name": event_name,
        "lemon_id": lemon_id,
        "dedupe_key": dedupe_key,
        "email": str(attrs.get("user_email") or attrs.get("customer_email") or attrs.get("email") or "").strip().lower(),
        "tier": _lemon_infer_tier(attrs, meta if isinstance(meta, dict) else None),
        "status": _map_lemon_status(str(attrs.get("status") or "active")),
    }


def billing_status() -> dict[str, Any]:
    """Institutional billing readiness surface for capability bindings."""
    from institutional_commerce import commerce_status

    commerce = commerce_status()
    return {
        "provider": billing_provider(),
        "configured": billing_configured(),
        "stripe_configured": stripe_configured(),
        "tiers": list(STRIPE_TIERS.keys()),
        "currencies": ["usd", "eur", "gbp"],
        "multi_currency_ready": True,
        "commerce": commerce,
        "success": True,
    }
