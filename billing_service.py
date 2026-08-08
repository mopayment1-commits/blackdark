"""
BLACKDARK — Stripe / Lemon Squeezy billing & subscription lifecycle (Priority 4).
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
    "pro": {"amount": 2900, "name": "BLACKDARK Pro"},
    "whale": {"amount": 19900, "name": "BLACKDARK Whale"},
}

LEMON_SQUEEZY_ENV_KEYS = {
    "pro": "LEMON_SQUEEZY_CHECKOUT_PRO",
    "whale": "LEMON_SQUEEZY_CHECKOUT_WHALE",
}

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
        upsert_subscription_by_stripe_id,
    )

    meta = event.get("meta") or {}
    event_name = str(meta.get("event_name") or "").strip()
    data = event.get("data") or {}
    attrs = data.get("attributes") or {}
    lemon_id = str(data.get("id") or attrs.get("subscription_id") or "").strip()
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
            logger.info("Lemon subscription activated | email=%s tier=%s id=%s", email, tier, lemon_id)
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


def _tier_mrr_usd(tier: str) -> float:
    meta = STRIPE_TIERS.get((tier or "").lower().strip())
    if not meta:
        return 0.0
    return float(meta["amount"]) / 100.0


def _parse_iso(ts: str | None):
    from datetime import datetime, timezone

    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None


async def generate_mrr_report() -> dict[str, Any]:
    """
    Investor-facing MRR snapshot from local subscriptions table.
    Counts active + trial (converted commercial value of paid tiers only for active).
    """
    from datetime import datetime, timezone

    from database import fetch_subscription_revenue_rows

    rows = await fetch_subscription_revenue_rows()
    now = datetime.now(timezone.utc)
    by_tier: dict[str, dict[str, Any]] = {
        "pro": {"active": 0, "trial": 0, "past_due": 0, "mrr_usd": 0.0},
        "whale": {"active": 0, "trial": 0, "past_due": 0, "mrr_usd": 0.0},
    }
    active_paying = 0
    trial_count = 0
    past_due = 0
    expired = 0

    for row in rows:
        tier = str(row.get("tier") or "pro").lower()
        status = str(row.get("status") or "").lower()
        if tier not in by_tier:
            by_tier[tier] = {"active": 0, "trial": 0, "past_due": 0, "mrr_usd": 0.0}
        if status == "active":
            by_tier[tier]["active"] += 1
            mrr = _tier_mrr_usd(tier)
            by_tier[tier]["mrr_usd"] += mrr
            active_paying += 1
        elif status == "trial":
            by_tier[tier]["trial"] += 1
            trial_count += 1
        elif status == "past_due":
            by_tier[tier]["past_due"] += 1
            past_due += 1
        elif status in {"expired", "cancelled", "canceled"}:
            expired += 1

    mrr_usd = round(sum(v["mrr_usd"] for v in by_tier.values()), 2)
    arr_usd = round(mrr_usd * 12, 2)
    return {
        "as_of": now.isoformat(),
        "currency": "USD",
        "mrr_usd": mrr_usd,
        "arr_usd": arr_usd,
        "active_paying_subscriptions": active_paying,
        "trial_subscriptions": trial_count,
        "past_due_subscriptions": past_due,
        "expired_or_cancelled": expired,
        "by_tier": by_tier,
        "unit_prices_usd": {k: _tier_mrr_usd(k) for k in STRIPE_TIERS},
        "source": "subscriptions_table",
        "note": "MRR uses configured STRIPE_TIERS amounts; Lemon tiers map to the same catalog.",
    }


async def compute_churn_rate(*, window_days: int = 30) -> dict[str, Any]:
    """
    Logo churn over a trailing window:
      churned / (active_at_window_start_estimate)
    where churned = subscriptions that moved to expired/cancelled with created_at before window end.
    """
    from datetime import datetime, timedelta, timezone

    from database import fetch_subscription_revenue_rows

    window_days = max(1, min(int(window_days), 365))
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=window_days)
    rows = await fetch_subscription_revenue_rows()

    active_now = 0
    churned_in_window = 0
    created_in_window = 0
    for row in rows:
        status = str(row.get("status") or "").lower()
        created = _parse_iso(row.get("created_at"))
        if status == "active":
            active_now += 1
        if created and start <= created <= now:
            created_in_window += 1
        if status in {"expired", "cancelled", "canceled"}:
            # Without a dedicated cancelled_at column, treat updated commercial end as "created_at"
            # for trials that expired, and count expired rows created before window end as churn events
            # if they are not still active — conservative logo churn proxy.
            if created is None or created <= now:
                # Count only rows that likely left during/after window start:
                # prefer past_due_at when present.
                left_at = _parse_iso(row.get("past_due_at")) or created
                if left_at and left_at >= start:
                    churned_in_window += 1

    # Starting base ≈ current active + churned in window - new creates (clamp ≥ 1 when activity exists)
    start_base = active_now + churned_in_window - created_in_window
    if start_base < 0:
        start_base = active_now + churned_in_window
    denominator = max(start_base, 1) if (active_now or churned_in_window) else 0
    rate = (churned_in_window / denominator) if denominator else 0.0

    return {
        "as_of": now.isoformat(),
        "window_days": window_days,
        "window_start": start.isoformat(),
        "active_now": active_now,
        "churned_in_window": churned_in_window,
        "created_in_window": created_in_window,
        "start_base_estimate": start_base if denominator else 0,
        "churn_rate": round(rate, 4),
        "churn_rate_percent": round(rate * 100, 2),
        "method": "logo_churn_proxy_from_subscriptions",
        "note": "Add cancelled_at column later for exact cohort churn; this is diligence-grade from current schema.",
    }
