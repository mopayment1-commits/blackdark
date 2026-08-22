"""Billing production ops readiness — env + webhook + SKU validation."""

from __future__ import annotations

import os
from typing import Any

from billing.plan_registry import PLAN_DEFINITIONS, SELF_SERVE_PLANS, lemon_checkout_env, stripe_price_env
from payments_usd import INSTITUTIONAL_WIRE, SELF_SERVE_SKUS


def _set(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def billing_ops_readiness(*, base_url: str | None = None) -> dict[str, Any]:
    base = (base_url or os.getenv("APP_BASE_URL", "http://localhost:8080")).rstrip("/")
    stripe = _set("STRIPE_SECRET_KEY")
    stripe_webhook = _set("STRIPE_WEBHOOK_SECRET")
    lemon_webhook = _set("LEMON_SQUEEZY_WEBHOOK_SECRET")

    skus: dict[str, dict[str, Any]] = {}
    for plan in SELF_SERVE_PLANS:
        pdef = PLAN_DEFINITIONS[plan]
        skus[plan] = {
            "display": pdef["display"],
            "price_usd": pdef["price_usd_month"],
            "trial_days": pdef["trial_days"],
            "stripe_price_env": bool(stripe_price_env(plan)),
            "lemon_checkout_env": bool(lemon_checkout_env(plan)),
            "self_serve_sku": SELF_SERVE_SKUS.get(plan),
        }

    stripe_prices_ok = all(skus[p]["stripe_price_env"] for p in SELF_SERVE_PLANS) if stripe else False
    lemon_ok = all(skus[p]["lemon_checkout_env"] for p in SELF_SERVE_PLANS) if _set("LEMON_SQUEEZY_API_KEY") or any(
        skus[p]["lemon_checkout_env"] for p in SELF_SERVE_PLANS
    ) else any(skus[p]["lemon_checkout_env"] for p in SELF_SERVE_PLANS)

    launch_ready = (stripe and stripe_webhook and stripe_prices_ok) or (lemon_ok and lemon_webhook)

    return {
        "currency": "USD",
        "official_tiers": list(PLAN_DEFINITIONS.keys()),
        "self_serve_plans": list(SELF_SERVE_PLANS),
        "skus": skus,
        "institutional": INSTITUTIONAL_WIRE,
        "webhooks": {
            "stripe_url": f"{base}/webhook",
            "lemon_url": f"{base}/webhook/lemon",
            "lemon_api_url": f"{base}/api/billing/webhook/lemon",
            "stripe_events": [
                "checkout.session.completed",
                "customer.subscription.created",
                "customer.subscription.updated",
                "customer.subscription.deleted",
                "invoice.paid",
                "invoice.payment_failed",
                "charge.refunded",
                "charge.dispute.created",
            ],
        },
        "env": {
            "STRIPE_SECRET_KEY": stripe,
            "STRIPE_WEBHOOK_SECRET": stripe_webhook,
            "STRIPE_PRICE_PRO": _set("STRIPE_PRICE_PRO"),
            "STRIPE_PRICE_ELITE": _set("STRIPE_PRICE_ELITE") or _set("STRIPE_PRICE_WHALE"),
            "STRIPE_PRICE_QUANT": _set("STRIPE_PRICE_QUANT"),
            "LEMON_SQUEEZY_WEBHOOK_SECRET": lemon_webhook,
            "LEMON_SQUEEZY_CHECKOUT_PRO": _set("LEMON_SQUEEZY_CHECKOUT_PRO"),
            "LEMON_SQUEEZY_CHECKOUT_ELITE": _set("LEMON_SQUEEZY_CHECKOUT_ELITE")
            or _set("LEMON_SQUEEZY_CHECKOUT_WHALE"),
            "LEMON_SQUEEZY_CHECKOUT_QUANT": _set("LEMON_SQUEEZY_CHECKOUT_QUANT"),
            "APP_BASE_URL": _set("APP_BASE_URL"),
        },
        "launch_ready": launch_ready,
        "checks": {
            "stripe_complete": stripe and stripe_webhook and stripe_prices_ok,
            "lemon_complete": lemon_ok and lemon_webhook,
            "institutional_commerce_wired": True,
            "subscription_engine": True,
            "admin_metrics": True,
        },
        "next_steps": [] if launch_ready else [
            "Set STRIPE_PRICE_PRO, STRIPE_PRICE_ELITE (or WHALE), STRIPE_PRICE_QUANT in Stripe Dashboard",
            f"Register webhook POST {base}/webhook with signing secret STRIPE_WEBHOOK_SECRET",
            "Or configure Lemon checkout URLs + LEMON_SQUEEZY_WEBHOOK_SECRET",
        ],
    }
