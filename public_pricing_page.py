"""Visitor-facing /pricing page content (marketing names ≠ internal SKUs)."""

from __future__ import annotations

from typing import Any

PUBLIC_PRICING_TIERS: tuple[dict[str, Any], ...] = (
    {
        "id": "free",
        "name": "Free",
        "price_display": "$0",
        "period": "",
        "highlight": False,
        "features": [
            "Trust Pulse + Act/Wait with Why",
            "Public Accuracy Ledger (hits and misses)",
            "Shareable Decision Certificate",
            "Limited daily Oracle decisions",
            "Free Proof watermark",
        ],
        "cta": "Start free",
        "cta_href": "/login?tab=register&plan=free",
    },
    {
        "id": "plus",
        "name": "Plus",
        "price_display": "$29",
        "period": "/month",
        "highlight": True,
        "features": [
            "Everything in Free",
            "Higher daily decision ceiling",
            "Since-you-left continuity",
            "Portfolio AI + alerts",
            "AI Chat without Free watermark",
        ],
        "cta": "Start 7-day trial",
        "cta_href": "/login?tab=register&plan=pro",
    },
    {
        "id": "pro",
        "name": "Pro",
        "price_display": "$49",
        "period": "/month",
        "highlight": False,
        "features": [
            "Everything in Plus",
            "Whale Signal vs Noise",
            "Stealth advisory views",
            "Evidence Pack + API priority",
            "Arbitrage scanner depth",
        ],
        "cta": "Upgrade to Pro",
        "cta_href": "/login?tab=register&plan=whale",
    },
    {
        "id": "enterprise",
        "name": "Enterprise",
        "price_display": None,
        "period": "",
        "highlight": False,
        "features": [
            "Data Room + compliance pack",
            "SSO / enforced MFA",
            "SLA + integration addendum",
            "Dedicated onboarding",
        ],
        "cta": "Talk to us",
        "cta_href": "#enterprise",
    },
)

PUBLIC_PRICING_COMPARE_ROWS: tuple[dict[str, Any], ...] = (
    {"feature": "Trust Pulse + Verify on Ledger", "free": True, "plus": True, "pro": True, "enterprise": True},
    {"feature": "Decision Certificate / Free Proof", "free": True, "plus": True, "pro": True, "enterprise": True},
    {"feature": "Public Accuracy Ledger", "free": True, "plus": True, "pro": True, "enterprise": True},
    {"feature": "Unlimited certified Oracle", "free": False, "plus": True, "pro": True, "enterprise": True},
    {"feature": "Portfolio AI + alerts", "free": False, "plus": True, "pro": True, "enterprise": True},
    {"feature": "Stealth + Evidence Pack", "free": False, "plus": False, "pro": True, "enterprise": True},
    {"feature": "Data Room + SSO / SLA", "free": False, "plus": False, "pro": False, "enterprise": True},
)


def public_pricing_page_context() -> dict[str, Any]:
    return {
        "page_title": "Pricing — BLACKDARK",
        "headline": "One Trust OS. Four depths.",
        "subhead": "Reviewable decisions and shareable proof — not mystery scores. Not financial advice.",
        "tiers": list(PUBLIC_PRICING_TIERS),
        "compare_rows": list(PUBLIC_PRICING_COMPARE_ROWS),
    }
