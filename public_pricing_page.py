"""Visitor-facing /pricing page content (marketing names ≠ internal SKUs)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_TIER_BLUEPRINT: tuple[dict[str, Any], ...] = (
    {
        "id": "free",
        "name_key": "pricing.public.tier.free.name",
        "price_display": "$0",
        "period": "",
        "highlight": False,
        "feature_keys": (
            "pricing.public.tier.free.f1",
            "pricing.public.tier.free.f2",
            "pricing.public.tier.free.f3",
            "pricing.public.tier.free.f4",
            "pricing.public.tier.free.f5",
        ),
        "cta_key": "pricing.public.tier.free.cta",
        "cta_href": "/login?tab=register&plan=free",
    },
    {
        "id": "plus",
        "name_key": "pricing.public.tier.plus.name",
        "price_display": "$29",
        "period": "/month",
        "highlight": True,
        "feature_keys": (
            "pricing.public.tier.plus.f1",
            "pricing.public.tier.plus.f2",
            "pricing.public.tier.plus.f3",
            "pricing.public.tier.plus.f4",
            "pricing.public.tier.plus.f5",
        ),
        "cta_key": "pricing.public.tier.plus.cta",
        "cta_href": "/login?tab=register&plan=pro",
    },
    {
        "id": "pro",
        "name_key": "pricing.public.tier.pro.name",
        "price_display": "$49",
        "period": "/month",
        "highlight": False,
        "feature_keys": (
            "pricing.public.tier.pro.f1",
            "pricing.public.tier.pro.f2",
            "pricing.public.tier.pro.f3",
            "pricing.public.tier.pro.f4",
            "pricing.public.tier.pro.f5",
        ),
        "cta_key": "pricing.public.tier.pro.cta",
        "cta_href": "/login?tab=register&plan=whale",
    },
    {
        "id": "enterprise",
        "name_key": "pricing.public.tier.enterprise.name",
        "price_display": None,
        "period": "",
        "highlight": False,
        "feature_keys": (
            "pricing.public.tier.enterprise.f1",
            "pricing.public.tier.enterprise.f2",
            "pricing.public.tier.enterprise.f3",
            "pricing.public.tier.enterprise.f4",
        ),
        "cta_key": "pricing.public.tier.enterprise.cta",
        "cta_href": "#enterprise",
    },
)

_COMPARE_BLUEPRINT: tuple[dict[str, Any], ...] = (
    {
        "feature_key": "pricing.public.compare.r1",
        "free": True,
        "plus": True,
        "pro": True,
        "enterprise": True,
    },
    {
        "feature_key": "pricing.public.compare.r2",
        "free": True,
        "plus": True,
        "pro": True,
        "enterprise": True,
    },
    {
        "feature_key": "pricing.public.compare.r3",
        "free": True,
        "plus": True,
        "pro": True,
        "enterprise": True,
    },
    {
        "feature_key": "pricing.public.compare.r4",
        "free": False,
        "plus": True,
        "pro": True,
        "enterprise": True,
    },
    {
        "feature_key": "pricing.public.compare.r5",
        "free": False,
        "plus": True,
        "pro": True,
        "enterprise": True,
    },
    {
        "feature_key": "pricing.public.compare.r6",
        "free": False,
        "plus": False,
        "pro": True,
        "enterprise": True,
    },
    {
        "feature_key": "pricing.public.compare.r7",
        "free": False,
        "plus": False,
        "pro": False,
        "enterprise": True,
    },
)


def public_pricing_page_context(t: Callable[[str], str] | None = None) -> dict[str, Any]:
    def tr(key: str, fallback: str = "") -> str:
        if not t:
            return fallback
        val = (t(key) or "").strip()
        return val if val else fallback

    tiers: list[dict[str, Any]] = []
    for spec in _TIER_BLUEPRINT:
        tiers.append(
            {
                "id": spec["id"],
                "name": tr(spec["name_key"], spec["id"].title()),
                "price_display": spec["price_display"],
                "period": spec["period"],
                "highlight": spec["highlight"],
                "features": [tr(k, k) for k in spec["feature_keys"]],
                "cta": tr(spec["cta_key"], spec["cta_key"]),
                "cta_href": spec["cta_href"],
            }
        )

    compare_rows: list[dict[str, Any]] = []
    for row in _COMPARE_BLUEPRINT:
        compare_rows.append(
            {
                "feature": tr(row["feature_key"], row["feature_key"]),
                "free": row["free"],
                "plus": row["plus"],
                "pro": row["pro"],
                "enterprise": row["enterprise"],
            }
        )

    return {
        "page_title": tr("pricing.public.title", "Pricing — BLACKDARK"),
        "headline": tr("pricing.public.headline", "One Trust OS. Four depths."),
        "subhead": tr(
            "pricing.public.subhead",
            "Reviewable decisions and shareable proof — not mystery scores. Not financial advice.",
        ),
        "tiers": tiers,
        "compare_rows": compare_rows,
    }
