"""Visitor-facing /pricing page content — built from site_pricing_tiers SSOT."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from site_pricing_tiers import COMPARE_COLUMN_KEYS, COMPARE_ROW_SPECS, PUBLIC_TIER_SPECS


def public_pricing_page_context(t: Callable[[str], str] | None = None) -> dict[str, Any]:
    def tr(key: str, fallback: str = "") -> str:
        if not t:
            return fallback
        val = (t(key) or "").strip()
        return val if val else fallback

    tiers: list[dict[str, Any]] = []
    for spec in PUBLIC_TIER_SPECS:
        features = [
            tr(k, fb)
            for k, fb in zip(spec["feature_keys"], spec["feature_fallbacks"], strict=False)
        ]
        tiers.append(
            {
                "id": spec["column_key"],
                "plan_id": spec["plan_id"],
                "name": tr(f"pricing.public.tier.{spec['column_key']}.name", spec["public_name"]),
                "price_display": spec["price_display"],
                "period": spec.get("period") or "",
                "highlight": spec.get("highlight"),
                "features": features,
                "cta": tr(f"pricing.public.tier.{spec['column_key']}.cta", spec["cta"]),
                "cta_href": spec["cta_href"],
            }
        )

    compare_rows: list[dict[str, Any]] = []
    for row in COMPARE_ROW_SPECS:
        entry: dict[str, Any] = {
            "feature": tr(row["feature_key"], row.get("fallback", row["feature_key"])),
        }
        for col in COMPARE_COLUMN_KEYS:
            entry[col] = bool(row.get(col))
        compare_rows.append(entry)

    column_labels = {
        col: tr(f"pricing.public.col.{col}", col.title())
        for col in COMPARE_COLUMN_KEYS
    }

    return {
        "page_title": tr("pricing.public.title", "Pricing — BLACKDARK"),
        "headline": tr("pricing.public.headline", "Five levels. One Trust OS."),
        "subhead": tr(
            "pricing.public.subhead",
            "Reviewable decisions and shareable proof — not mystery scores. Not financial advice.",
        ),
        "tiers": tiers,
        "compare_rows": compare_rows,
        "compare_columns": COMPARE_COLUMN_KEYS,
        "column_labels": column_labels,
    }
