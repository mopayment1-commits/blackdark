"""
Monetization Tiers Core — Feature #126 (Sprint 1 — non-negotiable).

Commercial 3-tier model (user-facing) mapped to canonical billing plans + Stripe.

Tiers:
  Free     — 3 Oracle queries/day, Market Radar +15min delay, basic alerts
  Pro      — $29/mo — unlimited Oracle, real-time Radar, Portfolio AI, 10 alerts
  Institution — $199/mo — API, On-Chain Intelligence, White Label reports, support

A/B testing: variant A (default $29/$199) vs variant B ($24.99/$179) by user hash.
"""

from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime
from typing import Any, Literal

from billing.plan_registry import PLAN_DEFINITIONS, STRIPE_PRICE_ENV_KEYS, normalize_plan

AbVariant = Literal["A", "B"]

MANDATORY_DISCLAIMER = (
    "Subscriptions provide access to analytics tools — not investment advice. "
    "Past performance does not guarantee future results."
)

# Canonical mapping: commercial tier → internal plan id for Stripe/entitlements
CANONICAL_MAP: dict[str, str] = {
    "free": "free",
    "pro": "pro",
    "institution": "elite",  # $199 self-serve institution bundle → elite entitlements
}

PRICING_VARIANTS: dict[str, dict[str, dict[str, Any]]] = {
    "A": {
        "pro": {"price_usd_month": 29.0, "price_cents": 2900, "price_display": "$29/mo"},
        "institution": {"price_usd_month": 199.0, "price_cents": 19900, "price_display": "$199/mo"},
    },
    "B": {
        "pro": {"price_usd_month": 24.99, "price_cents": 2499, "price_display": "$24.99/mo"},
        "institution": {"price_usd_month": 179.0, "price_cents": 17900, "price_display": "$179/mo"},
    },
}

TIER_ENTITLEMENTS: dict[str, dict[str, Any]] = {
    "free": {
        "oracle_daily_limit": 3,
        "market_radar_delay_minutes": 15,
        "market_radar_realtime": False,
        "alerts_max": 3,
        "alerts_tier": "basic",
        "portfolio_ai": False,
        "api_access": False,
        "onchain_intelligence": False,
        "white_label_reports": False,
        "priority_support": False,
    },
    "pro": {
        "oracle_daily_limit": None,
        "market_radar_delay_minutes": 0,
        "market_radar_realtime": True,
        "alerts_max": 10,
        "alerts_tier": "standard",
        "portfolio_ai": True,
        "api_access": False,
        "onchain_intelligence": False,
        "white_label_reports": False,
        "priority_support": False,
    },
    "institution": {
        "oracle_daily_limit": None,
        "market_radar_delay_minutes": 0,
        "market_radar_realtime": True,
        "alerts_max": None,
        "alerts_tier": "unlimited",
        "portfolio_ai": True,
        "api_access": True,
        "onchain_intelligence": True,
        "white_label_reports": True,
        "priority_support": True,
    },
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def resolve_ab_variant(*, user_id: str | None = None, email: str | None = None) -> AbVariant:
    """Deterministic A/B bucket — override with MONETIZATION_AB_VARIANT env."""
    forced = (os.getenv("MONETIZATION_AB_VARIANT") or "").strip().upper()
    if forced in {"A", "B"}:
        return forced  # type: ignore[return-value]

    key = (user_id or email or "anonymous").strip().lower()
    digest = hashlib.sha256(f"monetization-ab:{key}".encode()).hexdigest()
    return "B" if int(digest[:8], 16) % 100 < 50 else "A"


def _tier_card(tier_id: str, variant: AbVariant) -> dict[str, Any]:
    prices = PRICING_VARIANTS[variant][tier_id] if tier_id != "free" else {
        "price_usd_month": 0.0,
        "price_cents": 0,
        "price_display": "$0",
    }
    ent = TIER_ENTITLEMENTS[tier_id]
    canonical = CANONICAL_MAP[tier_id]

    names = {
        "free": "Free",
        "pro": "Pro",
        "institution": "Institution",
    }
    promises = {
        "free": "Useful daily proof — 3 Oracle queries, delayed Radar, basic alerts",
        "pro": "Daily verified habit — unlimited Oracle, live Radar, Portfolio AI",
        "institution": "Desk-grade intelligence — API, on-chain, white-label reports",
    }
    features = {
        "free": [
            "3 Single-Sentence Oracle queries / day",
            "Market Radar (15-minute delay)",
            "Basic alerts (up to 3)",
            "Decision journal",
        ],
        "pro": [
            "Unlimited Oracle queries",
            "Real-time Market Radar",
            "Portfolio AI",
            "Up to 10 custom alerts",
            "7-day free trial",
        ],
        "institution": [
            "Everything in Pro",
            "B2B API access",
            "On-Chain Intelligence module",
            "White-label reports",
            "Priority technical support",
        ],
    }

    card: dict[str, Any] = {
        "id": tier_id,
        "name": names[tier_id],
        "canonical_plan": canonical,
        "price_usd_month": prices["price_usd_month"],
        "price_cents": prices["price_cents"],
        "price_display": prices["price_display"],
        "promise": promises[tier_id],
        "features": features[tier_id],
        "entitlements": ent,
        "self_serve": tier_id != "free",
    }

    if tier_id == "pro":
        card["popular"] = True
        card["cta"] = "Start 7-Day Trial"
        card["checkout_tier"] = "pro"
        card["stripe_price_env"] = STRIPE_PRICE_ENV_KEYS.get("pro", "STRIPE_PRICE_PRO")
        card["checkout_href"] = "/create-checkout-session?tier=pro"
    elif tier_id == "institution":
        card["cta"] = "Subscribe"
        card["checkout_tier"] = "elite"
        card["stripe_price_env"] = STRIPE_PRICE_ENV_KEYS.get("elite", "STRIPE_PRICE_ELITE")
        card["checkout_href"] = "/create-checkout-session?tier=elite"
        card["note"] = "Institution bundle maps to Elite entitlements + API pack"
    else:
        card["cta"] = "Start free"
        card["checkout_href"] = "/login?tab=register&plan=free"

    return card


def monetization_catalog(
    *,
    variant: AbVariant | None = None,
    user_id: str | None = None,
    email: str | None = None,
) -> dict[str, Any]:
    """Full #126 commercial catalog with A/B pricing."""
    ab = variant or resolve_ab_variant(user_id=user_id, email=email)
    tiers = [_tier_card(tid, ab) for tid in ("free", "pro", "institution")]

    return {
        "ok": True,
        "feature_id": 126,
        "engine": "Monetization Tiers Core",
        "currency": "USD",
        "billing_interval": "month",
        "tier_count": 3,
        "tiers": tiers,
        "ab_test": {
            "variant": ab,
            "experiment": "pricing_pro_institution_v1",
            "variants": {
                "A": {"pro_usd": 29, "institution_usd": 199},
                "B": {"pro_usd": 24.99, "institution_usd": 179},
            },
            "override_env": "MONETIZATION_AB_VARIANT",
        },
        "golden_rule": (
            "Free tier must be useful enough to retain users, "
            "limited enough to convert — never disabled."
        ),
        "stripe_integration": True,
        "checkout_base": "/create-checkout-session",
        "disclaimer": MANDATORY_DISCLAIMER,
        "timestamp": _utcnow(),
    }


def entitlements_for_commercial_tier(tier_id: str) -> dict[str, Any]:
    """Resolve #126 entitlements; accepts commercial or canonical plan ids."""
    tid = tier_id.lower().strip()
    reverse = {v: k for k, v in CANONICAL_MAP.items()}
    if tid in reverse:
        tid = reverse[tid]
    if tid not in TIER_ENTITLEMENTS:
        tid = "free"
    return {
        "commercial_tier": tid,
        "canonical_plan": CANONICAL_MAP.get(tid, "free"),
        **TIER_ENTITLEMENTS[tid],
    }


def market_radar_delay_for_user(user: dict[str, Any] | None) -> int:
    """Minutes of delay for Market Radar feed (#126 free tier = 15 min)."""
    from auth_service import normalize_tier

    tier = normalize_tier((user or {}).get("tier") or "free")
    commercial = "free"
    for cid, canonical in CANONICAL_MAP.items():
        if canonical == tier:
            commercial = cid
            break
    if tier in {"elite", "quant", "institutional"}:
        commercial = "institution"
    elif tier == "pro":
        commercial = "pro"
    return int(TIER_ENTITLEMENTS.get(commercial, TIER_ENTITLEMENTS["free"])["market_radar_delay_minutes"])


def monetization_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": 126,
        "role": "monetization_core",
        "commercial_tiers": list(TIER_ENTITLEMENTS.keys()),
        "canonical_plans": PLAN_DEFINITIONS.keys(),
        "stripe_env_keys": list(STRIPE_PRICE_ENV_KEYS.values()),
        "ab_testing_enabled": True,
        "timestamp": _utcnow(),
    }
