"""Product/Price registry with versioning (BILL-013, BILL-014)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from billing.plan_registry import CANONICAL_TIERS, PLAN_DEFINITIONS, normalize_plan


def build_price_registry(*, env_stripe_ids: dict[str, str] | None = None) -> list[dict[str, Any]]:
    """Canonical product/price registry — no scattered hard-coded IDs."""
    env_stripe_ids = env_stripe_ids or {}
    now = datetime.now(UTC).isoformat()
    records: list[dict[str, Any]] = []
    for tier in CANONICAL_TIERS:
        pdef = PLAN_DEFINITIONS[tier]
        records.append(
            {
                "tier_id": tier,
                "stripe_product_id": env_stripe_ids.get(f"product_{tier}"),
                "stripe_price_id": env_stripe_ids.get(tier) or env_stripe_ids.get(f"price_{tier}"),
                "currency": "usd",
                "billing_interval": "month" if tier != "free" else None,
                "amount_minor": int(pdef.get("price_cents") or 0),
                "price_version": 1,
                "effective_from": now,
                "effective_to": None,
                "grandfathering_policy": "existing_subscribers_retain_price_version",
                "tax_behavior": "exclusive",
                "entitlement_profile": f"{tier}_v1",
                "active": True,
            }
        )
    return records


def resolve_price_for_tier(tier: str, *, price_version: int | None = None) -> dict[str, Any]:
    canonical = normalize_plan(tier)
    pdef = PLAN_DEFINITIONS[canonical]
    return {
        "tier_id": canonical,
        "amount_minor": int(pdef.get("price_cents") or 0),
        "price_version": price_version or 1,
        "entitlement_profile": f"{canonical}_v{price_version or 1}",
    }
