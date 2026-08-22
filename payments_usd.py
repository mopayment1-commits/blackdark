"""
BLACKDARK — USD payments architecture (binding).

Official tiers: FREE · PRO · ELITE · QUANT · INSTITUTIONAL
"""

from __future__ import annotations

import os
from typing import Any

from billing.plan_registry import PAID_TRIAL_DAYS, PLAN_DEFINITIONS, SELF_SERVE_PLANS, normalize_plan

BILLING_CURRENCY = "usd"
BILLING_CURRENCY_DISPLAY = "USD"

SELF_SERVE_SKUS: dict[str, dict[str, Any]] = {}
for _plan in SELF_SERVE_PLANS:
    _def = PLAN_DEFINITIONS[_plan]
    SELF_SERVE_SKUS[_plan] = {
        "tier": _plan,
        "name": _def["name"],
        "display": _def["display"],
        "amount_cents": _def["price_cents"],
        "amount_usd": _def["price_usd_month"],
        "interval": "month",
        "trial_days": PAID_TRIAL_DAYS,
        "checkout_env": f"LEMON_SQUEEZY_CHECKOUT_{_plan.upper()}",
        "stripe_price_env": f"STRIPE_PRICE_{_plan.upper()}",
    }
# Legacy whale alias → elite SKU
SELF_SERVE_SKUS["whale"] = dict(SELF_SERVE_SKUS["elite"])
SELF_SERVE_SKUS["whale"]["tier"] = "elite"

PAYMENT_METHODS_LAUNCH: list[dict[str, str]] = [
    {
        "id": "card",
        "label": "Credit / Debit card (Visa, Mastercard, etc.)",
        "via": "lemon_squeezy_or_stripe_hosted_checkout",
        "currency": BILLING_CURRENCY_DISPLAY,
    },
    {
        "id": "apple_pay",
        "label": "Apple Pay",
        "via": "stripe_checkout_wallets_or_lemon",
        "currency": BILLING_CURRENCY_DISPLAY,
    },
    {
        "id": "google_pay",
        "label": "Google Pay",
        "via": "stripe_checkout_wallets_or_lemon",
        "currency": BILLING_CURRENCY_DISPLAY,
    },
]

PAYMENT_METHODS_LATER: list[str] = [
    "SEPA / ACH (when market demand proven)",
    "Local rails (only with clear volume)",
    "Crypto checkout (deferred — accounting / AML complexity)",
]

SECURITY_POSTURE: dict[str, Any] = {
    "pci_target": "SAQ_A",
    "stores_pan": False,
    "stores_cvv": False,
    "stores_full_iban_for_retail": False,
    "stores_provider_ids_only": True,
    "card_data_handler": "psp_hosted_checkout",
    "allowed_local_fields": [
        "email",
        "tier",
        "subscription_status",
        "provider_customer_id",
        "provider_subscription_id",
        "webhook_event_id",
    ],
    "forbidden_local_fields": [
        "card_number",
        "pan",
        "cvv",
        "cvc",
        "track_data",
        "pin",
        "full_magnetic_stripe",
    ],
    "transport": "TLS_1_2_plus",
    "webhook_auth": "HMAC_signature_required",
    "standards_refs": [
        "PCI DSS v4 (no sensitive auth data storage)",
        "PSD2 / SCA via PSP 3-D Secure when required",
        "OWASP ASVS (session / CSRF on account surfaces)",
        "NIST SP 800-53 / 800-63 (secrets & identity)",
    ],
}

REFUND_POLICY: dict[str, Any] = {
    "currency": BILLING_CURRENCY_DISPLAY,
    "self_serve": {
        "trial": (
            f"All paid tiers include a {PAID_TRIAL_DAYS}-day trial. "
            "Cancel before trial end to avoid the first USD charge."
        ),
        "paid_month": (
            "Monthly USD subscriptions are generally non-refundable once a paid period starts, "
            "except where required by law or a clear billing error."
        ),
        "process": "Request via support with account email + checkout/order reference.",
        "provider": "Refunds are executed by Lemon Squeezy or Stripe — never by re-entering card data into BLACKDARK.",
    },
    "institutional": (
        "Custom contracts use invoice terms (e.g. Net 15/30). Refunds follow the signed agreement."
    ),
    "disclaimer": (
        "BLACKDARK sells decision intelligence access — not guaranteed trading returns. "
        "Subscription fees are for software access."
    ),
}

INSTITUTIONAL_WIRE: dict[str, Any] = {
    "self_serve": False,
    "currency": BILLING_CURRENCY_DISPLAY,
    "price_from_usd_month": 999,
    "methods": ["commercial_invoice", "wire_transfer_usd", "ach_usd_when_available"],
    "cta": "/data-room",
    "inquiry_api": "/api/billing/institutional-inquiry",
    "note": (
        "Not a Stripe/Lemon SKU. Sales-led Integration Addendum: licensing, API, SLA, SSO, DD."
    ),
}


def payments_architecture() -> dict[str, Any]:
    """Public-safe architecture document for operators and /api/billing/payments."""
    from billing.plan_registry import lemon_checkout_env, stripe_price_env
    from billing_service import billing_configured, billing_provider, stripe_configured

    lemon_ready = {p: bool(lemon_checkout_env(p)) for p in SELF_SERVE_PLANS}
    stripe_prices = {p: bool(stripe_price_env(p)) for p in SELF_SERVE_PLANS}
    lemon_webhook = bool(os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "").strip())
    stripe = stripe_configured()
    stripe_webhook = bool(os.getenv("STRIPE_WEBHOOK_SECRET", "").strip())

    return {
        "product": "BLACKDARK Trust OS",
        "currency": BILLING_CURRENCY_DISPLAY,
        "currency_code": BILLING_CURRENCY,
        "story": "USD depth ladder — FREE / PRO / ELITE / QUANT self-serve; INSTITUTIONAL wire.",
        "provider_preference": [
            "lemon_squeezy_merchant_of_record (launch default)",
            "stripe_billing (institutional-grade control when entity ready)",
        ],
        "active_provider": billing_provider(),
        "billing_configured": billing_configured(),
        "self_serve_skus": SELF_SERVE_SKUS,
        "payment_methods_launch": PAYMENT_METHODS_LAUNCH,
        "payment_methods_later": PAYMENT_METHODS_LATER,
        "security": SECURITY_POSTURE,
        "refund_policy": REFUND_POLICY,
        "institutional": INSTITUTIONAL_WIRE,
        "payout": {
            "description": (
                "Customer pays the PSP in USD; PSP settles net proceeds to your linked bank account "
                "(KYC + USD-capable account required in Lemon/Stripe dashboard)."
            ),
            "operator_action": "Complete PSP KYC and attach bank payout details before campaign.",
        },
        "ops_readiness": {
            "lemon_checkout": lemon_ready,
            "lemon_webhook_secret": lemon_webhook,
            "stripe_secret": stripe,
            "stripe_webhook_secret": stripe_webhook,
            "stripe_prices": stripe_prices,
            "launch_ready": (any(lemon_ready.values()) and lemon_webhook) or (stripe and stripe_webhook),
        },
        "endpoints": {
            "checkout": "/api/billing/checkout",
            "portal": "/api/billing/portal",
            "status": "/api/billing/status",
            "subscription": "/api/billing/subscription",
            "cancel": "/api/billing/cancel",
            "downgrade": "/api/billing/downgrade",
            "payments": "/api/billing/payments",
            "refund_policy": "/api/billing/refund-policy",
            "institutional_inquiry": "/api/billing/institutional-inquiry",
            "admin_metrics": "/api/admin/billing/metrics",
            "stripe_webhook": "/webhook",
            "lemon_webhook": "/webhook/lemon",
        },
        "honesty": {
            "guaranteed_returns": False,
            "stores_card_numbers": False,
        },
    }


def refund_policy_public() -> dict[str, Any]:
    return {
        "currency": BILLING_CURRENCY_DISPLAY,
        "policy": REFUND_POLICY,
        "legal_page": "/refund",
    }
