"""
Visitor-facing pricing SSOT — Free · Beginner · Pro · Desk · Institution.

Internal checkout plan IDs (billing/plan_registry): free, pro, elite, quant, institutional.
Public marketing names differ; map via `plan_id` on each tier spec.
"""

from __future__ import annotations

from typing import Any, Final

# Column keys used in /pricing compare table (stable i18n suffix).
COMPARE_COLUMN_KEYS: Final[tuple[str, ...]] = (
    "free",
    "beginner",
    "pro",
    "desk",
    "institution",
)

PUBLIC_TIER_SPECS: tuple[dict[str, Any], ...] = (
    {
        "column_key": "free",
        "plan_id": "free",
        "public_name": "Free",
        "price_usd_month": 0.0,
        "price_display": "$0",
        "period": "",
        "highlight": False,
        "self_serve": True,
        "trial_days": 0,
        "cta": "Start free",
        "cta_href": "/login?tab=register&plan=free",
        "feature_keys": (
            "pricing.public.tier.free.f1",
            "pricing.public.tier.free.f2",
            "pricing.public.tier.free.f3",
            "pricing.public.tier.free.f4",
            "pricing.public.tier.free.f5",
        ),
        "feature_fallbacks": (
            "One Oracle decision (BTC & ETH only)",
            "Trust Pulse",
            "Public Accuracy Ledger",
            "One decision certificate",
            "Saved language preference",
        ),
    },
    {
        "column_key": "beginner",
        "plan_id": "pro",
        "public_name": "Beginner",
        "price_usd_month": 9.99,
        "price_display": "$9.99",
        "period": "/month",
        "highlight": False,
        "self_serve": True,
        "trial_days": 7,
        "cta": "Start 7-day trial",
        "cta_href": "/login?tab=register&plan=pro",
        "feature_keys": (
            "pricing.public.tier.beginner.f1",
            "pricing.public.tier.beginner.f2",
            "pricing.public.tier.beginner.f3",
            "pricing.public.tier.beginner.f4",
            "pricing.public.tier.beginner.f5",
            "pricing.public.tier.beginner.f6",
        ),
        "feature_fallbacks": (
            "Everything in Free",
            "Watchlist — 5 symbols",
            "One decision alert",
            "Decision log — last 20",
            "Compare 2 assets",
            "Offline · last known decision",
        ),
    },
    {
        "column_key": "pro",
        "plan_id": "elite",
        "public_name": "Pro",
        "price_usd_month": 29.0,
        "price_display": "$29",
        "period": "/month",
        "highlight": True,
        "self_serve": True,
        "trial_days": 7,
        "cta": "Start 7-day trial",
        "cta_href": "/login?tab=register&plan=elite",
        "feature_keys": (
            "pricing.public.tier.pro.f1",
            "pricing.public.tier.pro.f2",
            "pricing.public.tier.pro.f3",
            "pricing.public.tier.pro.f4",
            "pricing.public.tier.pro.f5",
            "pricing.public.tier.pro.f6",
            "pricing.public.tier.pro.f7",
        ),
        "feature_fallbacks": (
            "Everything in Beginner",
            "Watchlist — 20 symbols",
            "Unlimited decision alerts",
            "Full decision log",
            "Compare up to 5 assets",
            "Price charts",
            "Share decision · dark/light theme",
        ),
    },
    {
        "column_key": "desk",
        "plan_id": "quant",
        "public_name": "Desk",
        "price_usd_month": 79.0,
        "price_display": "$79",
        "period": "/month",
        "highlight": False,
        "self_serve": True,
        "trial_days": 7,
        "cta": "Start 7-day trial",
        "cta_href": "/login?tab=register&plan=quant",
        "feature_keys": (
            "pricing.public.tier.desk.f1",
            "pricing.public.tier.desk.f2",
            "pricing.public.tier.desk.f3",
            "pricing.public.tier.desk.f4",
            "pricing.public.tier.desk.f5",
            "pricing.public.tier.desk.f6",
        ),
        "feature_fallbacks": (
            "Everything in Pro",
            "Watchlist — all symbols",
            "Advanced decision alerts",
            "Read API access",
            "Certificate export",
            "Priority support",
        ),
    },
    {
        "column_key": "institution",
        "plan_id": "institutional",
        "public_name": "Institution",
        "price_usd_month": None,
        "price_display": None,
        "period": "",
        "highlight": False,
        "self_serve": False,
        "trial_days": 0,
        "cta": "Talk to us",
        "cta_href": "#institution",
        "feature_keys": (
            "pricing.public.tier.institution.f1",
            "pricing.public.tier.institution.f2",
            "pricing.public.tier.institution.f3",
            "pricing.public.tier.institution.f4",
            "pricing.public.tier.institution.f5",
        ),
        "feature_fallbacks": (
            "Everything in Desk",
            "Full API",
            "Custom reports",
            "SLA",
            "Extended historical data",
        ),
    },
)

COMPARE_ROW_SPECS: tuple[dict[str, Any], ...] = (
    {
        "feature_key": "pricing.public.compare.r1",
        "fallback": "Trust Pulse",
        "free": True,
        "beginner": True,
        "pro": True,
        "desk": True,
        "institution": True,
    },
    {
        "feature_key": "pricing.public.compare.r2",
        "fallback": "Public Accuracy Ledger",
        "free": True,
        "beginner": True,
        "pro": True,
        "desk": True,
        "institution": True,
    },
    {
        "feature_key": "pricing.public.compare.r3",
        "fallback": "Decision certificate / Free Proof",
        "free": True,
        "beginner": True,
        "pro": True,
        "desk": True,
        "institution": True,
    },
    {
        "feature_key": "pricing.public.compare.r4",
        "fallback": "Oracle (BTC/ETH on Free; broader on paid)",
        "free": True,
        "beginner": True,
        "pro": True,
        "desk": True,
        "institution": True,
    },
    {
        "feature_key": "pricing.public.compare.r5",
        "fallback": "Watchlist",
        "free": False,
        "beginner": True,
        "pro": True,
        "desk": True,
        "institution": True,
    },
    {
        "feature_key": "pricing.public.compare.r6",
        "fallback": "Decision alerts",
        "free": False,
        "beginner": True,
        "pro": True,
        "desk": True,
        "institution": True,
    },
    {
        "feature_key": "pricing.public.compare.r7",
        "fallback": "Offline last-known decision",
        "free": False,
        "beginner": True,
        "pro": True,
        "desk": True,
        "institution": True,
    },
    {
        "feature_key": "pricing.public.compare.r8",
        "fallback": "Charts & share decision",
        "free": False,
        "beginner": False,
        "pro": True,
        "desk": True,
        "institution": True,
    },
    {
        "feature_key": "pricing.public.compare.r9",
        "fallback": "Read API & certificate export",
        "free": False,
        "beginner": False,
        "pro": False,
        "desk": True,
        "institution": True,
    },
    {
        "feature_key": "pricing.public.compare.r10",
        "fallback": "Full API · SLA · custom reports",
        "free": False,
        "beginner": False,
        "pro": False,
        "desk": False,
        "institution": True,
    },
)


def spec_by_plan_id(plan_id: str) -> dict[str, Any] | None:
    for spec in PUBLIC_TIER_SPECS:
        if spec["plan_id"] == plan_id:
            return spec
    return None


def apply_public_pricing_to_plan_definitions(definitions: dict[str, dict[str, Any]]) -> None:
    """Sync marketing names/prices into billing PLAN_DEFINITIONS (display only)."""
    for spec in PUBLIC_TIER_SPECS:
        pid = spec["plan_id"]
        if pid not in definitions:
            continue
        row = definitions[pid]
        row["name"] = spec["public_name"]
        row["display"] = spec["public_name"].upper()
        if spec["price_usd_month"] is not None:
            row["price_usd_month"] = float(spec["price_usd_month"])
            if spec["price_usd_month"] == 0:
                row["price_display"] = "$0"
                row["price_cents"] = 0
            else:
                row["price_display"] = f"{spec['price_display']}{spec.get('period') or '/mo'}"
                row["price_cents"] = int(round(float(spec["price_usd_month"]) * 100))
        else:
            row["price_display"] = "Custom"
            row["price_note"] = "Talk to us — not self-serve checkout"
            row.pop("price_usd_month_from", None)
        row["popular"] = bool(spec.get("highlight"))
        row["trial_days"] = int(spec.get("trial_days") or 0)
        row["self_serve"] = bool(spec.get("self_serve", True))
