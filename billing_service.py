"""
BLACKDARK — Stripe / Lemon Squeezy billing & subscription lifecycle.

Self-serve: Decision Pro ($29) and Decision Desk ($49).
Free = Proof Pass ($0). Institutional = Talk to us from $3,000 → open (not a Stripe SKU).
"""

from __future__ import annotations

import hashlib
import hmac
import json
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
    return bool(os.getenv("STRIPE_SECRET_KEY", "").strip())


def ensure_stripe_api_key() -> str:
    """Load STRIPE_SECRET_KEY into the Stripe SDK. Never logs the value."""
    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    stripe.api_key = key
    return key


def stripe_secret_presence() -> dict[str, bool]:
    """Presence/shape flags only. Never returns secret or price-id values."""
    key = (os.getenv("STRIPE_SECRET_KEY") or "").strip()
    price = (os.getenv("STRIPE_PRICE_PRO") or "").strip()
    return {
        "secret_key_present": bool(key),
        "secret_key_is_test": key.startswith("sk_test_"),
        "secret_key_is_live": key.startswith("sk_live_"),
        "price_pro_present": bool(price) and price.startswith("price_"),
    }


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


def unpaid_upgrade_path() -> dict[str, Any]:
    """Complete unpaid upgrade surface — live PSP charge remains owner ops."""
    import config

    return {
        "ok": True,
        "unpaid_path_complete": True,
        "live_charge_ready": billing_configured(),
        "billing_provider": billing_provider(),
        "product_complete": False,
        "paths": {
            "promo_redeem": "/api/promo/redeem",
            "institutional_inquiry": "/api/billing/institutional-inquiry",
            "checkout": "/api/billing/checkout",
            "status": "/api/billing/status",
        },
        "promo_codes_configured": bool(getattr(config, "LAUNCH_PROMO_CODES", None)),
        "checkout_without_psp": "HTTP 503 Billing not configured",
        "note": (
            "Trial/promo/institutional inquiry work without PSP secrets. "
            "Self-serve live charge needs Stripe or Lemon Squeezy credentials."
        ),
    }


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
    if not ensure_stripe_api_key():
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


def _prefix(value: Any, n: int = 12) -> str | None:
    text = str(value or "").strip()
    return text[:n] if text else None


def _stripe_err_type(exc: BaseException) -> str:
    return type(exc).__name__


def prove_stripe_test_cycle() -> dict[str, Any]:
    """Live Stripe TEST cycle for D13. Never logs secrets or full price ids.

    Required: sk_test_ Account.retrieve, STRIPE_PRICE_PRO retrieve (recurring),
    billing_service.create_checkout_session('pro'), TEST subscription via tok_visa,
    then cancel + expire. sk_live_ is refused.
    """
    presence = stripe_secret_presence()
    receipt: dict[str, Any] = {
        "ok": False,
        "reason": "not_started",
        "livemode": None,
        "price_recurring": None,
        "price_active": None,
        "checkout_session_prefix": None,
        "checkout_url_https": False,
        "checkout_mode": None,
        "used_blackdark_checkout": False,
        "subscription_prefix": None,
        "subscription_status": None,
        "subscription_canceled": False,
        "customer_cleaned": False,
        "error_type": None,
        **presence,
    }
    if not presence["secret_key_present"]:
        receipt["reason"] = "secrets_missing"
        return receipt
    if presence["secret_key_is_live"]:
        receipt["reason"] = "sk_live_refused"
        return receipt
    if not presence["secret_key_is_test"]:
        receipt["reason"] = "not_sk_test"
        return receipt
    if not presence["price_pro_present"]:
        receipt["reason"] = "price_pro_missing"
        return receipt

    ensure_stripe_api_key()
    price_id = _price_id_for_tier("pro") or ""
    customer_id = None
    subscription_id = None
    session_id = None
    try:
        acct = stripe.Account.retrieve()
        livemode = getattr(acct, "livemode", None)
        if livemode is None:
            livemode = bool(getattr(stripe.Balance.retrieve(), "livemode", False))
        else:
            livemode = bool(livemode)
        receipt["livemode"] = livemode
        if livemode:
            receipt["reason"] = "account_livemode_true"
            return receipt

        try:
            price = stripe.Price.retrieve(price_id)
        except Exception as exc:
            receipt["error_type"] = _stripe_err_type(exc)
            code = getattr(exc, "code", None)
            receipt["reason"] = (
                "price_pro_not_on_account" if code == "resource_missing" else "price_retrieve_failed"
            )
            return receipt
        price_live = bool(getattr(price, "livemode", False))
        recurring = getattr(price, "type", None) == "recurring" or bool(getattr(price, "recurring", None))
        active = bool(getattr(price, "active", False))
        receipt["price_recurring"] = recurring
        receipt["price_active"] = active
        if price_live:
            receipt["reason"] = "price_livemode_true"
            return receipt
        if not recurring or not active:
            receipt["reason"] = "price_not_active_recurring"
            return receipt

        checkout = create_checkout_session(
            "pro",
            customer_email="launch-cert-probe@blackdark.invalid",
        )
        session_id = str(checkout.get("session_id") or "")
        url = str(checkout.get("url") or "")
        receipt["used_blackdark_checkout"] = True
        receipt["checkout_session_prefix"] = _prefix(session_id)
        receipt["checkout_url_https"] = url.startswith("https://")
        fetched = stripe.checkout.Session.retrieve(session_id) if session_id else None
        receipt["checkout_mode"] = getattr(fetched, "mode", None) if fetched is not None else None
        checkout_ok = (
            session_id.startswith("cs_")
            and receipt["checkout_url_https"]
            and receipt["checkout_mode"] == "subscription"
        )
        if not checkout_ok:
            receipt["reason"] = "checkout_session_invalid"
            return receipt

        customer = stripe.Customer.create(
            email="launch-cert-probe@blackdark.invalid",
            metadata={"blackdark_purpose": "launch_cert_stripe_test"},
        )
        customer_id = str(getattr(customer, "id", "") or "")
        default_pm = None
        try:
            pm = stripe.PaymentMethod.create(type="card", card={"token": "tok_visa"})
            stripe.PaymentMethod.attach(pm.id, customer=customer_id)
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": pm.id},
            )
            default_pm = pm.id
        except Exception:
            stripe.Customer.modify(customer_id, source="tok_visa")
        sub_kwargs: dict[str, Any] = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "payment_behavior": "error_if_incomplete",
            "metadata": {"blackdark_purpose": "launch_cert_stripe_test"},
        }
        if default_pm:
            sub_kwargs["default_payment_method"] = default_pm
        sub = stripe.Subscription.create(**sub_kwargs)
        subscription_id = str(getattr(sub, "id", "") or "")
        status = str(getattr(sub, "status", "") or "")
        receipt["subscription_prefix"] = _prefix(subscription_id)
        receipt["subscription_status"] = status
        if not (subscription_id.startswith("sub_") and status in {"active", "trialing"}):
            receipt["reason"] = "subscription_not_active"
            return receipt

        canceled = stripe.Subscription.cancel(subscription_id)
        receipt["subscription_canceled"] = str(getattr(canceled, "status", "") or "") in {
            "canceled",
            "cancelled",
        }
        if not receipt["subscription_canceled"]:
            receipt["reason"] = "subscription_cancel_failed"
            return receipt

        receipt["ok"] = True
        receipt["reason"] = "ok"
        return receipt
    except Exception as exc:
        receipt["error_type"] = _stripe_err_type(exc)
        if receipt["reason"] in {"not_started"}:
            receipt["reason"] = (
                "authentication_rejected"
                if receipt["error_type"] == "AuthenticationError"
                else "stripe_api_error"
            )
        return receipt
    finally:
        try:
            if session_id:
                stripe.checkout.Session.expire(session_id)
        except Exception:
            pass
        try:
            if subscription_id and not receipt.get("subscription_canceled"):
                stripe.Subscription.cancel(subscription_id)
                receipt["subscription_canceled"] = True
        except Exception:
            pass
        try:
            if customer_id:
                stripe.Customer.delete(customer_id)
                receipt["customer_cleaned"] = True
        except Exception:
            pass


def stripe_test_evidence_path():
    from pathlib import Path

    override = os.getenv("STRIPE_TEST_EVIDENCE_PATH", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "docs" / "dd" / "BLACKDARK_STRIPE_TEST_EVIDENCE.json"


def stripe_test_cycle_proved() -> bool:
    path = stripe_test_evidence_path()
    if not path.is_file():
        return False
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return (
        body.get("verdict") == "PASS"
        and bool(body.get("ok"))
        and str(body.get("checkout_session_prefix") or "").startswith("cs_")
        and str(body.get("subscription_prefix") or "").startswith("sub_")
        and body.get("subscription_canceled") is True
        and body.get("livemode") is False
    )


def create_billing_portal_session(stripe_customer_id: str) -> dict[str, Any]:
    if not ensure_stripe_api_key():
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


async def _claim_lemon_webhook(ctx: dict[str, Any]) -> dict[str, Any] | None:
    dedupe_key = str(ctx["dedupe_key"])
    if not dedupe_key.strip(":"):
        return None
    from database import claim_billing_webhook_event

    claimed = await claim_billing_webhook_event(
        provider="lemon_squeezy",
        event_id=dedupe_key[:240],
        event_type=ctx["event_name"] or "unknown",
    )
    if claimed:
        return None
    return {
        "handled": True,
        "action": "duplicate_ignored",
        "provider": "lemon_squeezy",
        "event_id": dedupe_key[:240],
    }


async def _handle_lemon_activation(ctx: dict[str, Any]) -> dict[str, Any]:
    if not (ctx["email"] and ctx["lemon_id"]):
        return {"handled": False, "reason": "missing_email_or_id", "event": ctx["event_name"]}
    from database import activate_paid_subscription

    await activate_paid_subscription(ctx["email"], ctx["tier"], ctx["lemon_id"])
    logger.info(
        "Lemon subscription activated | email=%s tier=%s id=%s",
        str(ctx["email"]).replace("\r", " ").replace("\n", " "),
        str(ctx["tier"]).replace("\r", " ").replace("\n", " "),
        str(ctx["lemon_id"]).replace("\r", " ").replace("\n", " "),
    )
    return {"handled": True, "action": "checkout_completed", "provider": "lemon_squeezy"}


async def _handle_lemon_update(ctx: dict[str, Any]) -> dict[str, Any]:
    if not ctx["lemon_id"]:
        return {"handled": False, "reason": "missing_id", "event": ctx["event_name"]}
    from database import upsert_subscription_by_stripe_id

    await upsert_subscription_by_stripe_id(
        ctx["lemon_id"],
        tier=ctx["tier"],
        status=ctx["status"],
        email=ctx["email"] or None,
    )
    return {"handled": True, "action": "subscription_updated", "provider": "lemon_squeezy"}


async def _handle_lemon_inactive(ctx: dict[str, Any]) -> dict[str, Any]:
    if not ctx["lemon_id"]:
        return {"handled": False, "reason": "missing_id", "event": ctx["event_name"]}
    if ctx["event_name"] in {"subscription_cancelled", "subscription_expired"}:
        from database import cancel_subscription_by_stripe_id

        await cancel_subscription_by_stripe_id(ctx["lemon_id"])
        return {"handled": True, "action": "subscription_cancelled", "provider": "lemon_squeezy"}
    from database import upsert_subscription_by_stripe_id

    await upsert_subscription_by_stripe_id(ctx["lemon_id"], status="past_due", email=ctx["email"] or None)
    return {"handled": True, "action": "payment_failed", "provider": "lemon_squeezy"}

async def handle_lemon_webhook_event(event: dict[str, Any]) -> dict[str, Any]:
    """Activate / update / cancel entitlements from Lemon Squeezy webhooks."""
    ctx = _lemon_event_context(event)
    duplicate = await _claim_lemon_webhook(ctx)
    if duplicate:
        return duplicate
    event_name = ctx["event_name"]
    if event_name in {"subscription_created", "subscription_payment_success", "order_created"}:
        return await _handle_lemon_activation(ctx)
    if event_name in {"subscription_updated", "subscription_resumed", "subscription_unpaused"}:
        return await _handle_lemon_update(ctx)
    if event_name in {
        "subscription_cancelled",
        "subscription_expired",
        "subscription_payment_failed",
        "subscription_paused",
    }:
        return await _handle_lemon_inactive(ctx)
    return {"handled": False, "type": event_name, "provider": "lemon_squeezy"}
