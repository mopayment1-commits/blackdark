"""
BLACKDARK Trust OS — Pricing catalog (binding).

Official tiers: FREE · PRO · ELITE · QUANT · INSTITUTIONAL
FREE $0 · PRO $19 · ELITE $49 · QUANT $199 · INSTITUTIONAL custom pricing
7-day trial on all paid self-serve tiers.
"""

from __future__ import annotations

from typing import Any

from billing.plan_registry import (
    PAID_TRIAL_DAYS,
    PLAN_DEFINITIONS,
    SELF_SERVE_PLANS,
    normalize_plan,
    plan_def,
    upgrade_ladder as _upgrade_ladder,
)

PATH_CREATE_CHECKOUT_SESSION_TIER_ELITE = "/create-checkout-session?tier=elite"
PATH_CREATE_CHECKOUT_SESSION_TIER_QUANT = "/create-checkout-session?tier=quant"
# Legacy path alias
PATH_CREATE_CHECKOUT_SESSION_TIER_WHALE = PATH_CREATE_CHECKOUT_SESSION_TIER_ELITE

PRICING_OPTION = "B"
PRICING_STORY = (
    "Proof → daily habit → desk edge → quant depth → institutional trust room. "
    "One Trust OS. Depth of use is what you pay for."
)

VALUE_EQUATION: dict[str, Any] = {
    "principle": (
        "Pay for depth of daily use — not for a different product. "
        "Free must create proof value before money is asked."
    ),
    "why_pro_is_fair": [
        "Free delivers Act/Wait + Why + shareable Proof Card before any charge.",
        "PRO removes the 3/day ceiling for a daily verified habit.",
        "7-day trial on every paid tier — feel depth before billing.",
        "At ~$0.67/day, the bar is one clear verified decision habit.",
    ],
    "anti_waste_rules": [
        "Never charge Free users before first Proof Card aha.",
        "Never promise guaranteed returns at any tier.",
        "Upgrade CTA points to the next depth only.",
        "Institutional is Talk to us — no fake self-serve $999+ checkout without sales.",
    ],
}


def _tier_card(plan_id: str) -> dict[str, Any]:
    p = PLAN_DEFINITIONS[plan_id]
    card: dict[str, Any] = {
        "id": p["id"],
        "display": p["display"],
        "sku": p["sku"],
        "name": p["name"],
        "price_usd_month": p["price_usd_month"],
        "price_display": p["price_display"],
        "self_serve": p["self_serve"],
        "trial_days": p.get("trial_days", 0),
    }
    if "price_cents" in p:
        card["price_cents"] = p["price_cents"]
    if plan_id == "free":
        card.update(
            {
                "cta": "Start free",
                "cta_href": "/login?tab=register&plan=free",
                "signup_plan": "free",
                "promise": "Take a clear decision and prove it publicly — before you pay.",
                "limits": {"oracle_daily_limit": 3, "certificate_watermark": "Free Proof"},
            }
        )
    elif plan_id == "pro":
        card.update(
            {
                "popular": True,
                "cta": "Start 7-Day Trial",
                "cta_href": "/login?tab=register&plan=pro",
                "signup_plan": "pro",
                "promise": "Stop rationing decisions — run a daily verified habit.",
            }
        )
    elif plan_id == "elite":
        card.update(
            {
                "cta": "Start 7-Day Trial",
                "cta_href": "/login?tab=register&plan=elite",
                "signup_plan": "elite",
                "promise": "Edge tools + evidence pack for serious desks.",
            }
        )
    elif plan_id == "quant":
        card.update(
            {
                "cta": "Start 7-Day Trial",
                "cta_href": "/login?tab=register&plan=quant",
                "signup_plan": "quant",
                "promise": "Quant depth — backtesting, API scale, systematic workflows.",
            }
        )
    else:
        card.update(
            {
                "price_usd_month_from": p.get("price_usd_month_from", 999),
                "price_note": "Custom contracts. Sales-led activation.",
                "cta": "Talk to us",
                "cta_href": "/login?tab=register&plan=institutional",
                "signup_plan": "institutional",
                "promise": "Trust system inside the official decision room.",
            }
        )
    return card


TIERS: list[dict[str, Any]] = [_tier_card(pid) for pid in ("free", "pro", "elite", "quant", "institutional")]

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

UNIQUE_BY_TIER: dict[str, list[str]] = {
    "proof_pass": [
        "Single-Sentence Oracle",
        "Decision Certificate (shareable)",
        "Public Accuracy Ledger",
        "Kill-Rate Board · Contradiction Replay",
    ],
    "decision_pro": [
        "Unlimited certified decisions",
        "Market Radar + Portfolio AI",
        "Alerts + Net-Edge Truth Score",
    ],
    "decision_elite": [
        "B2B / API key",
        "Evidence Pack + Stealth Advisor",
        "Whale Signal-to-Noise filter",
    ],
    "decision_quant": [
        "Quant backtesting suite",
        "100k API calls / month",
        "40h backtest hours / month",
    ],
    "institutional": [
        "Data Room + SLA / SSO-MFA",
        "Corpus Passport + Committee PDF",
        "Anti-Hype Mode (evidence-only)",
    ],
}

SIGNUP_PLANS = ("free", "pro", "elite", "quant", "institutional")


def normalize_signup_plan(plan: str | None) -> str:
    return normalize_plan(plan) if normalize_plan(plan) in SIGNUP_PLANS else "free"


def next_upgrade(tier: str | None) -> dict[str, Any]:
    key = normalize_plan(tier or "free")
    ladder = _upgrade_ladder()
    step = dict(ladder.get(key, ladder["free"]))
    step["current_id"] = key
    if step.get("next_id") == "elite":
        step["href"] = PATH_CREATE_CHECKOUT_SESSION_TIER_ELITE
    elif step.get("next_id") == "quant":
        step["href"] = PATH_CREATE_CHECKOUT_SESSION_TIER_QUANT
    elif step.get("next_id") == "institutional":
        step["href"] = "/data-room"
    elif step.get("next_id") == "pro":
        step["href"] = "/create-checkout-session?tier=pro"
    return step


def signup_plan_cards() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in TIERS:
        out.append(
            {
                "id": t["id"],
                "display": t.get("display", t["id"].upper()),
                "name": t["name"],
                "price_display": t["price_display"],
                "promise": t.get("promise"),
                "popular": bool(t.get("popular")),
                "trial_days": t.get("trial_days"),
                "self_serve": bool(t.get("self_serve")),
            }
        )
    return out


def signup_next_after_register(plan: str) -> dict[str, Any]:
    plan = normalize_signup_plan(plan)
    if plan == "free":
        return {
            "action": "app",
            "href": "/profile?welcome=1&plan=free",
            "start_pro_trial": False,
            "start_paid_trial": False,
            "message": "FREE ready — open your first Proof Card before any upgrade.",
        }
    if plan in SELF_SERVE_PLANS:
        p = plan_def(plan)
        return {
            "action": "paid_trial",
            "href": f"/profile?welcome=1&plan={plan}&trial=1",
            "start_pro_trial": plan == "pro",
            "start_paid_trial": True,
            "trial_days": PAID_TRIAL_DAYS,
            "checkout_tier": plan,
            "message": f"{p['display']} {PAID_TRIAL_DAYS}-day trial started.",
        }
    return {
        "action": "data_room",
        "href": "/data-room?from=signup",
        "start_pro_trial": False,
        "start_paid_trial": False,
        "message": "Account created — continue to INSTITUTIONAL Talk to us.",
    }


def pricing_catalog() -> dict[str, Any]:
    return {
        "product": "BLACKDARK",
        "surface": "trust_os_pricing",
        "currency": "USD",
        "option": PRICING_OPTION,
        "canon": "FREE · PRO · ELITE · QUANT · INSTITUTIONAL — binding commercial ladder",
        "binding": "billing/plan_registry.py · docs/PRICING_TRUST_OS.md",
        "story": PRICING_STORY,
        "value_equation": VALUE_EQUATION,
        "unique_by_tier": UNIQUE_BY_TIER,
        "wow_surfaces_complete": True,
        "tiers": TIERS,
        "signup_plans": signup_plan_cards(),
        "upgrade_ladder": {k: next_upgrade(k) for k in SIGNUP_PLANS},
        "integration_addendum": INTEGRATION_ADDENDUM,
        "honesty": {
            "guaranteed_accuracy_claimed": False,
            "note": "We sell reviewable decisions and proof — not guaranteed returns.",
        },
        "checkout": {
            "pro": "/create-checkout-session?tier=pro",
            "elite": PATH_CREATE_CHECKOUT_SESSION_TIER_ELITE,
            "quant": PATH_CREATE_CHECKOUT_SESSION_TIER_QUANT,
            "whale": PATH_CREATE_CHECKOUT_SESSION_TIER_ELITE,
            "institutional": "/data-room",
        },
        "trial_days_paid": PAID_TRIAL_DAYS,
    }
