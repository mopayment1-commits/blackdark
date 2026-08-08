"""
BLACKDARK — USD payments architecture (binding).

Currency: USD only for self-serve SKUs.
Cards / wallets: hosted by Lemon Squeezy (MoR) or Stripe — never on our servers.
Institutional: invoice + wire (Talk to us) — not a Checkout SKU.

PCI posture: SAQ A target — PAN/CVV never touch application memory or DB.
"""

from __future__ import annotations

import os
from typing import Any

# Canonical settlement / display currency for Trust OS self-serve.
BILLING_CURRENCY = "usd"
BILLING_CURRENCY_DISPLAY = "USD"

SELF_SERVE_SKUS: dict[str, dict[str, Any]] = {
    "pro": {
        "tier": "pro",
        "name": "Decision Pro",
        "amount_cents": 2900,
        "amount_usd": 29,
        "interval": "month",
        "trial_days": int(os.getenv("PRO_TRIAL_DAYS", "7")),
        "checkout_env": "LEMON_SQUEEZY_CHECKOUT_PRO",
        "stripe_price_env": "STRIPE_PRICE_PRO",
    },
    "whale": {
        "tier": "whale",
        "name": "Decision Desk",
        "amount_cents": 4900,
        "amount_usd": 49,
        "interval": "month",
        "trial_days": 0,
        "checkout_env": "LEMON_SQUEEZY_CHECKOUT_WHALE",
        "stripe_price_env": "STRIPE_PRICE_WHALE",
    },
}

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
            "Decision Pro includes a 7-day trial when configured. "
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
    "price_from_usd_month": 3000,
    "methods": ["commercial_invoice", "wire_transfer_usd", "ach_usd_when_available"],
    "cta": "/data-room",
    "inquiry_api": "/api/billing/institutional-inquiry",
    "note": (
        "Not a Stripe/Lemon SKU. Sales-led Integration Addendum: licensing, API, SLA, SSO, DD."
    ),
}


def payments_architecture() -> dict[str, Any]:
    """Public-safe architecture document for operators and /api/billing/payments."""
    from billing_service import billing_configured, billing_provider, lemon_squeezy_checkout_url, stripe_configured

    lemon_pro = bool(lemon_squeezy_checkout_url("pro"))
    lemon_whale = bool(lemon_squeezy_checkout_url("whale"))
    lemon_webhook = bool(os.getenv("LEMON_SQUEEZY_WEBHOOK_SECRET", "").strip())
    stripe = stripe_configured()
    stripe_webhook = bool(os.getenv("STRIPE_WEBHOOK_SECRET", "").strip())

    return {
        "product": "BLACKDARK Trust OS",
        "currency": BILLING_CURRENCY_DISPLAY,
        "currency_code": BILLING_CURRENCY,
        "story": "USD depth ladder — Proof Pass free; Decision Pro / Whale Desk self-serve; Institutional wire.",
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
            "lemon_checkout_pro": lemon_pro,
            "lemon_checkout_whale": lemon_whale,
            "lemon_webhook_secret": lemon_webhook,
            "stripe_secret": stripe,
            "stripe_webhook_secret": stripe_webhook,
            "stripe_price_pro": bool(os.getenv("STRIPE_PRICE_PRO", "").strip()),
            "stripe_price_whale": bool(os.getenv("STRIPE_PRICE_WHALE", "").strip()),
            "launch_ready": (lemon_pro and lemon_webhook) or (stripe and stripe_webhook),
            "whale_ready": lemon_whale or bool(os.getenv("STRIPE_PRICE_WHALE", "").strip()) or stripe,
        },
        "endpoints": {
            "checkout": "/api/billing/checkout",
            "portal": "/api/billing/portal",
            "status": "/api/billing/status",
            "payments": "/api/billing/payments",
            "refund_policy": "/api/billing/refund-policy",
            "institutional_inquiry": "/api/billing/institutional-inquiry",
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
