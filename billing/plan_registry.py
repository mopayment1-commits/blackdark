"""
BLACKDARK — Canonical subscription plans (binding).

Official tiers: FREE · PRO · ELITE · QUANT · INSTITUTIONAL
Legacy aliases (whale, decision_desk, etc.) normalize to canonical IDs.
"""

from __future__ import annotations

import os
from typing import Any, Final

PAID_TRIAL_DAYS: Final[int] = int(os.getenv("PAID_TRIAL_DAYS", os.getenv("PRO_TRIAL_DAYS", "7")))

CANONICAL_TIERS: Final[tuple[str, ...]] = (
    "free",
    "pro",
    "elite",
    "quant",
    "institutional",
)

PLAN_ALIASES: dict[str, str] = {
    "proof": "free",
    "proof_pass": "free",
    "decision_pro": "pro",
    "whale": "elite",
    "desk": "elite",
    "decision_desk": "elite",
    "inst": "institutional",
    "trust_os_institutional": "institutional",
}

PLAN_RANK: dict[str, int] = {
    "free": 0,
    "pro": 1,
    "elite": 2,
    "quant": 3,
    "institutional": 4,
}

PLAN_DISPLAY: dict[str, str] = {
    "free": "FREE",
    "pro": "PRO",
    "elite": "ELITE",
    "quant": "QUANT",
    "institutional": "INSTITUTIONAL",
}

# Display SSOT (Launch-57): user-facing prices only. Billing cents may lag — see price_cents + billing_note.
PLAN_DEFINITIONS: dict[str, dict[str, Any]] = {
    "free": {
        "id": "free",
        "display": "FREE",
        "sku": "proof_pass",
        "name": "DISCOVER / FREE",
        "price_cents": 0,
        "price_usd_month": 0.0,
        "price_display": "$0",
        "self_serve": True,
        "trial_days": 0,
        "popular": False,
    },
    "pro": {
        "id": "pro",
        "display": "PRO",
        "sku": "decision_pro",
        "name": "DECIDE / PRO",
        "price_cents": 2900,
        "billing_note": "BLOCKED_EXTERNAL: Stripe/Lemon price IDs may still map to legacy $29 until rotated",
        "price_usd_month": 19.99,
        "price_usd_year": 199.0,
        "price_display": "$19.99/mo or $199/yr",
        "self_serve": True,
        "trial_days": PAID_TRIAL_DAYS,
        "popular": True,
    },
    "elite": {
        "id": "elite",
        "display": "ELITE",
        "sku": "decision_elite",
        "name": "SEE THE EDGE / ELITE",
        "price_cents": 4900,
        "billing_note": "BLOCKED_EXTERNAL: Stripe/Lemon price IDs may still map to legacy $49 until rotated",
        "price_usd_month": 49.99,
        "price_usd_year": 499.0,
        "price_display": "$49.99/mo or $499/yr",
        "self_serve": True,
        "trial_days": PAID_TRIAL_DAYS,
        "popular": False,
    },
    "quant": {
        "id": "quant",
        "display": "QUANT",
        "sku": "decision_quant",
        "name": "EXECUTE THE EDGE / QUANT",
        "price_cents": 19900,
        "billing_note": "BLOCKED_EXTERNAL: Stripe/Lemon price IDs may still map to legacy $199 until rotated",
        "price_usd_month": 129.99,
        "price_usd_year": 1299.0,
        "price_display": "$129.99/mo or $1,299/yr",
        "self_serve": True,
        "trial_days": PAID_TRIAL_DAYS,
        "popular": False,
    },
    "institutional": {
        "id": "institutional",
        "display": "INSTITUTIONAL",
        "sku": "trust_os_institutional",
        "name": "SCALE THE EDGE / INSTITUTIONAL",
        "price_cents": 0,
        "price_usd_month": 0.0,
        "price_usd_month_from": 999.0,
        "price_display": "From $999/mo",
        "price_note": "Talk to us — not self-serve checkout",
        "self_serve": False,
        "trial_days": 0,
        "popular": False,
    },
}

SELF_SERVE_PLANS: tuple[str, ...] = ("pro", "elite", "quant")

# Stripe / Lemon env key mapping (legacy WHALE env vars still work for elite).
CHECKOUT_ENV_KEYS: dict[str, str] = {
    "pro": "LEMON_SQUEEZY_CHECKOUT_PRO",
    "elite": "LEMON_SQUEEZY_CHECKOUT_ELITE",
    "quant": "LEMON_SQUEEZY_CHECKOUT_QUANT",
}

STRIPE_PRICE_ENV_KEYS: dict[str, str] = {
    "pro": "STRIPE_PRICE_PRO",
    "elite": "STRIPE_PRICE_ELITE",
    "quant": "STRIPE_PRICE_QUANT",
}

# Backward-compatible env fallbacks.
_LEGACY_STRIPE_PRICE_ENV: dict[str, str] = {
    "elite": "STRIPE_PRICE_WHALE",
}

_LEGACY_LEMON_ENV: dict[str, str] = {
    "elite": "LEMON_SQUEEZY_CHECKOUT_WHALE",
}


def normalize_plan(plan: str | None) -> str:
    raw = (plan or "free").strip().lower()
    raw = PLAN_ALIASES.get(raw, raw)
    return raw if raw in PLAN_RANK else "free"


def plan_rank(plan: str | None) -> int:
    return PLAN_RANK.get(normalize_plan(plan), 0)


def plan_def(plan: str | None) -> dict[str, Any]:
    return dict(PLAN_DEFINITIONS[normalize_plan(plan)])


def stripe_price_env(plan: str) -> str | None:
    canonical = normalize_plan(plan)
    if canonical not in SELF_SERVE_PLANS:
        return None
    key = STRIPE_PRICE_ENV_KEYS.get(canonical, "")
    value = os.getenv(key, "").strip()
    if value:
        return value
    legacy = _LEGACY_STRIPE_PRICE_ENV.get(canonical)
    if legacy:
        return os.getenv(legacy, "").strip() or None
    return None


def lemon_checkout_env(plan: str) -> str | None:
    canonical = normalize_plan(plan)
    if canonical not in SELF_SERVE_PLANS:
        return None
    key = CHECKOUT_ENV_KEYS.get(canonical, "")
    value = os.getenv(key, "").strip()
    if value:
        return value
    legacy = _LEGACY_LEMON_ENV.get(canonical)
    if legacy:
        return os.getenv(legacy, "").strip() or None
    return None


def upgrade_ladder() -> dict[str, dict[str, Any]]:
    steps = [
        ("free", "pro"),
        ("pro", "elite"),
        ("elite", "quant"),
        ("quant", "institutional"),
    ]
    out: dict[str, dict[str, Any]] = {}
    for current, nxt in steps:
        nxt_def = PLAN_DEFINITIONS[nxt]
        out[current] = {
            "current_id": current,
            "next_id": nxt,
            "label": f"{nxt_def['display']} {nxt_def['price_display']}",
            "checkout_tier": nxt if nxt_def["self_serve"] else None,
            "has_upgrade": True,
        }
    out["institutional"] = {
        "current_id": "institutional",
        "next_id": None,
        "label": None,
        "checkout_tier": None,
        "has_upgrade": False,
    }
    return out
