"""
BLACKDARK Trust OS — Pricing catalog (single product, depth ladder).

Canon (morning session final binding):
Proof Pass $0 · Decision Pro $29 · Decision Desk $49 · Institutional from $3,000 → open.
"""

from __future__ import annotations

from typing import Any

# Self-serve SKUs map to auth tiers free/pro/whale (whale = Decision Desk @ $49).
# Institutional is sales-led (not a Stripe SKU).

PRICING_STORY = (
    "Proof → daily decision habit → desk packaging → institutional trust room. "
    "One Trust OS. Depth of use is what you pay for — not separate platforms."
)

TIERS: list[dict[str, Any]] = [
    {
        "id": "free",
        "sku": "proof_pass",
        "name": "Proof Pass",
        "price_usd_month": 0,
        "price_display": "$0",
        "cta": "Get Started",
        "cta_href": "/login",
        "self_serve": True,
        "promise": "Take a clear decision… and prove it publicly.",
        "highlights": [
            "OQS Why — understandable bull / bear / neutral reason",
            "Shareable Decision Certificate (Proof Card)",
            "3 certified decisions / day",
            "Unlimited public sharing of your Proof Cards",
            "Live Public Accuracy Ledger",
        ],
        "limits": {"oracle_daily_limit": 3, "certificate_watermark": "Free Proof"},
        "viral_role": "Each Proof Card is an invite: see why this decision was made.",
    },
    {
        "id": "pro",
        "sku": "decision_pro",
        "name": "Decision Pro",
        "price_usd_month": 29,
        "price_cents": 2900,
        "price_display": "$29",
        "popular": True,
        "cta": "Start 7-Day Trial",
        "cta_href": "/create-checkout-session?tier=pro",
        "self_serve": True,
        "promise": "From one-off proof → a daily decision system.",
        "highlights": [
            "Unlimited certified Oracle decisions",
            "Portfolio AI + full Market Radar",
            "Oracle alerts (Telegram / in-app) without free caps",
            "Personal decision history + accuracy",
            "No Free Proof watermark on certificates",
            "Research Lab + Arbitrage catalog + AI Chat",
        ],
        "trial_days": 7,
        "conversion_from_free": "You liked the proof — make it a daily habit without the 3/day ceiling.",
    },
    {
        "id": "whale",
        "sku": "decision_desk",
        "name": "Decision Desk",
        "price_usd_month": 49,
        "price_cents": 4900,
        "price_display": "$49",
        "cta": "Upgrade to Decision Desk",
        "cta_href": "/create-checkout-session?tier=whale",
        "self_serve": True,
        "promise": "Market edge + serious desk tools — easy step up from $29.",
        "highlights": [
            "Everything in Decision Pro",
            "Whale Signal-to-Noise filtering",
            "Stealth / fund-facing views (prove-it honest)",
            "B2B feed / API key",
            "Acquirer Evidence Pack export",
            "Higher rate-limit priority under viral load",
        ],
        "conversion_from_pro": "When you need to convince someone else — partner, client, or committee.",
    },
    {
        "id": "institutional",
        "sku": "trust_os_institutional",
        "name": "Trust OS Institutional",
        "price_usd_month_from": 3000,
        "price_display": "From $3,000/mo → open",
        "price_note": "Custom annual contracts. Not self-serve checkout.",
        "cta": "Talk to us",
        "cta_href": "/data-room",
        "self_serve": False,
        "promise": "Trust system inside the official decision room.",
        "highlights": [
            "Everything in Decision Desk",
            "Data Room + Compliance pack",
            "SSO / enforced MFA for teams",
            "SLA + optional private deploy",
            "Roles: Analyst / PM / Compliance",
            "DD evidence export + Integration Addendum",
        ],
        "viral_role": "Reverse prestige — same OS funds negotiate lifts Free/Pro trust.",
    },
]


INTEGRATION_ADDENDUM: list[dict[str, str]] = [
    {"item": "Data licensing", "default": "Internal use only; redistribution negotiated"},
    {"item": "Model access", "default": "Decision API / batch / webhook — rate + universe scoped"},
    {"item": "Audit rights", "default": "Methodology glass-box — not raw model weights"},
    {"item": "Latency / SLA", "default": "Tied to production HA / viral readiness posture"},
    {"item": "Indemnity / disclaimer", "default": "Not financial advice — mandatory"},
    {"item": "Custom universe", "default": "Extra assets/markets priced separately"},
    {"item": "On-prem / private deploy", "default": "Highest institutional band"},
    {"item": "Human-in-the-loop", "default": "Human approval before any live execution"},
    {"item": "Logo / case study", "default": "Optional discount for public reference"},
]


def pricing_catalog() -> dict[str, Any]:
    return {
        "product": "BLACKDARK",
        "surface": "trust_os_pricing",
        "currency": "USD",
        "canon": "1 product · 4 value layers · 6 heroes — depth ladder, not multi-platform SKUs",
        "binding": "docs/MORNING_SESSION_FINAL_BINDING.md",
        "story": PRICING_STORY,
        "tiers": TIERS,
        "integration_addendum": INTEGRATION_ADDENDUM,
        "honesty": {
            "guaranteed_accuracy_claimed": False,
            "note": "We sell reviewable decisions and proof — not guaranteed returns.",
        },
        "checkout": {
            "pro": "/create-checkout-session?tier=pro",
            "whale": "/create-checkout-session?tier=whale",
            "institutional": "/data-room",
        },
    }
