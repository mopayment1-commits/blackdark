"""
BLACKDARK Trust OS — Pricing catalog (single product, depth ladder).

Option A (binding):
Proof Pass $0 · Decision Pro $29 (7-day trial) · Decision Desk $49 · Institutional from $3,000 → open.
No $15 / Essential mid-tier.
"""

from __future__ import annotations

from typing import Any

# Self-serve SKUs map to auth tiers free/pro/whale (whale = Decision Desk @ $49).
# Institutional is sales-led (not a Stripe SKU).

PRICING_OPTION = "A"
PRICING_STORY = (
    "Proof → daily decision habit → desk packaging → institutional trust room. "
    "One Trust OS. Depth of use is what you pay for — not separate platforms."
)

# Why $29 should feel fair: Free proves the decision; Pro removes the habit ceiling.
VALUE_EQUATION: dict[str, Any] = {
    "principle": (
        "Pay for depth of daily use — not for a different product. "
        "Free must create proof value before money is asked."
    ),
    "why_29_is_fair": [
        "Free already delivers Act/Wait + Why + shareable Proof Card (real value before pay).",
        "Pro removes the 3/day ceiling so the daily habit is not rationed.",
        "Pro removes Free Proof watermark — certificates look professional when shared.",
        "Pro unlocks Portfolio AI, alerts, history, and continuity (Since You Left).",
        "7-day trial lets the user feel unlimited habit before any charge.",
        "At ~$1/day, the bar is: one clear verified decision habit, not a chart zoo.",
    ],
    "anti_waste_rules": [
        "Never charge Free users before first Proof Card aha.",
        "Never promise guaranteed returns at any tier.",
        "Upgrade CTA always points to the next depth only (not a wall of SKUs).",
        "Institutional is Talk to us — no fake self-serve $3000 checkout.",
    ],
}

TIERS: list[dict[str, Any]] = [
    {
        "id": "free",
        "sku": "proof_pass",
        "name": "Proof Pass",
        "price_usd_month": 0,
        "price_display": "$0",
        "cta": "Start free",
        "cta_href": "/login?tab=register&plan=free",
        "signup_plan": "free",
        "self_serve": True,
        "promise": "Take a clear decision… and prove it publicly — before you pay anything.",
        "value_felt": "You get a real Act/Wait + Why + shareable Proof Card. Not a teaser screenshot.",
        "highlights": [
            "OQS Why — understandable bull / bear / neutral reason",
            "Shareable Decision Certificate (Proof Card)",
            "3 certified decisions / day",
            "Unlimited public sharing of your Proof Cards",
            "Live Public Accuracy Ledger",
            "Public Kill-Rate Board + Contradiction Replay + Proof Arena",
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
        "cta_href": "/login?tab=register&plan=pro",
        "signup_plan": "pro",
        "self_serve": True,
        "promise": "Stop rationing decisions — run a daily verified habit.",
        "value_felt": (
            "~$1/day for unlimited certified Oracle decisions, Portfolio AI, alerts, "
            "and certificates without the Free Proof watermark."
        ),
        "highlights": [
            "Everything in Proof Pass",
            "Unlimited certified Oracle decisions (no 3/day ceiling)",
            "7-day trial — feel the habit before you pay",
            "Portfolio AI + full Market Radar",
            "Oracle alerts (Telegram / Email / WhatsApp / in-app) without free caps",
            "Net-Edge Truth Score + Since You Left Top-3 continuity",
            "Personal decision history + accuracy",
            "No Free Proof watermark on certificates",
            "Research Lab + Arbitrage catalog + AI Chat",
        ],
        "trial_days": 7,
        "conversion_from_free": (
            "You already saw the proof on Free. Pro is the same Trust OS without the "
            "daily ceiling — so $29 buys continuity, not a new product."
        ),
    },
    {
        "id": "whale",
        "sku": "decision_desk",
        "name": "Decision Desk",
        "price_usd_month": 49,
        "price_cents": 4900,
        "price_display": "$49",
        "cta": "Upgrade to Decision Desk",
        "cta_href": "/login?tab=register&plan=whale",
        "signup_plan": "whale",
        "self_serve": True,
        "promise": "When you need to convince someone else — edge tools + evidence pack.",
        "value_felt": (
            "+$20 over Pro for whale Signal-to-Noise, Stealth Advisor, B2B/API, "
            "and committee-ready evidence — not a cosmetic rename."
        ),
        "highlights": [
            "Everything in Decision Pro",
            "Whale Signal-to-Noise filtering",
            "Stealth Execution Advisor",
            "B2B feed / API key",
            "Acquirer Evidence Pack",
            "Half-Life Heat Clock + Committee One-Pager + Corpus Passport",
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
        "cta_href": "/login?tab=register&plan=institutional",
        "signup_plan": "institutional",
        "self_serve": False,
        "promise": "Trust system inside the official decision room.",
        "value_felt": "Priced as a room/process system (SLA, roles, Data Room) — not a retail upsell.",
        "highlights": [
            "Everything in Decision Desk",
            "Data Room + SLA / SSO-MFA path",
            "Corpus Passport for acquirers",
            "Committee One-Pager Auto PDF for M&A",
            "Anti-Hype Mode (evidence-only)",
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


UNIQUE_BY_TIER: dict[str, list[str]] = {
    "proof_pass": [
        "Single-Sentence Oracle",
        "Decision Certificate (shareable)",
        "Public Accuracy Ledger",
        "Kill-Rate Board · Contradiction Replay · Proof Arena · Since You Left",
    ],
    "decision_pro": [
        "Unlimited certified decisions",
        "Market Radar + Portfolio AI",
        "Alerts (Telegram / Email / WhatsApp / in-app)",
        "Net-Edge Truth Score",
    ],
    "decision_desk": [
        "Signal vs Noise whale filter",
        "Stealth Execution Advisor",
        "B2B / API key",
        "Evidence Pack + Half-Life Heat Clock + Committee One-Pager",
    ],
    "institutional": [
        "Data Room",
        "SLA + SSO / MFA path",
        "Corpus Passport + Committee PDF",
        "Anti-Hype Mode (evidence-only institutional skin)",
    ],
}

# Sequential upgrade ladder (Option A).
_UPGRADE_NEXT: dict[str, dict[str, Any]] = {
    "free": {
        "next_id": "pro",
        "label": "Decision Pro $29",
        "cta": "Start 7-Day Trial",
        "href": "/create-checkout-session?tier=pro",
        "checkout_tier": "pro",
        "reason": "Remove the 3/day ceiling and Free Proof watermark — keep the same Trust OS.",
    },
    "pro": {
        "next_id": "whale",
        "label": "Decision Desk $49",
        "cta": "Upgrade to Decision Desk",
        "href": "/create-checkout-session?tier=whale",
        "checkout_tier": "whale",
        "reason": "Whale Signal-to-Noise, Stealth Advisor, B2B/API, Evidence Pack.",
    },
    "whale": {
        "next_id": "institutional",
        "label": "Trust OS Institutional",
        "cta": "Talk to us",
        "href": "/data-room",
        "checkout_tier": None,
        "reason": "Data Room, SLA, roles, Integration Addendum — sales-led.",
    },
    "institutional": {
        "next_id": None,
        "label": None,
        "cta": None,
        "href": None,
        "checkout_tier": None,
        "reason": "Top of ladder.",
    },
}

SIGNUP_PLANS = ("free", "pro", "whale", "institutional")


def normalize_signup_plan(plan: str | None) -> str:
    raw = (plan or "free").strip().lower()
    aliases = {
        "proof": "free",
        "proof_pass": "free",
        "decision_pro": "pro",
        "desk": "whale",
        "decision_desk": "whale",
        "inst": "institutional",
        "trust_os_institutional": "institutional",
    }
    raw = aliases.get(raw, raw)
    return raw if raw in SIGNUP_PLANS else "free"


def next_upgrade(tier: str | None) -> dict[str, Any]:
    """Return the single next upgrade step for the current auth tier."""
    key = (tier or "free").strip().lower()
    if key not in _UPGRADE_NEXT:
        key = "free"
    step = dict(_UPGRADE_NEXT[key])
    step["current_id"] = key
    step["has_upgrade"] = bool(step.get("next_id"))
    return step


def signup_plan_cards() -> list[dict[str, Any]]:
    """Compact cards for register UI (4 Option A plans)."""
    out: list[dict[str, Any]] = []
    for t in TIERS:
        out.append(
            {
                "id": t["id"],
                "name": t["name"],
                "price_display": t["price_display"],
                "promise": t["promise"],
                "value_felt": t.get("value_felt"),
                "popular": bool(t.get("popular")),
                "trial_days": t.get("trial_days"),
                "self_serve": bool(t.get("self_serve")),
                "highlights": (t.get("highlights") or [])[:4],
            }
        )
    return out


def signup_next_after_register(plan: str) -> dict[str, Any]:
    """Post-register redirect / trial policy for Option A plan pick."""
    plan = normalize_signup_plan(plan)
    if plan == "free":
        return {
            "action": "app",
            "href": "/profile?welcome=1&plan=free",
            "start_pro_trial": False,
            "message": "Proof Pass ready — open your first Proof Card before any upgrade.",
        }
    if plan == "pro":
        return {
            "action": "pro_trial",
            "href": "/profile?welcome=1&plan=pro&trial=1",
            "start_pro_trial": True,
            "message": "Decision Pro 7-day trial started — unlimited certified decisions.",
        }
    if plan == "whale":
        return {
            "action": "checkout",
            "href": "/create-checkout-session?tier=whale",
            "start_pro_trial": False,
            "checkout_tier": "whale",
            "message": "Account created — continue to Decision Desk checkout ($49).",
        }
    return {
        "action": "data_room",
        "href": "/data-room?from=signup",
        "start_pro_trial": False,
        "message": "Account created — continue to Institutional Talk to us.",
    }


def pricing_catalog() -> dict[str, Any]:
    return {
        "product": "BLACKDARK",
        "surface": "trust_os_pricing",
        "currency": "USD",
        "option": PRICING_OPTION,
        "canon": "1 product · 4 value layers · 6 heroes — Option A depth ladder (no $15)",
        "binding": "docs/MORNING_SESSION_FINAL_BINDING.md · docs/PRICING_TRUST_OS.md",
        "story": PRICING_STORY,
        "value_equation": VALUE_EQUATION,
        "unique_by_tier": UNIQUE_BY_TIER,
        "wow_surfaces_complete": True,
        "tiers": TIERS,
        "signup_plans": signup_plan_cards(),
        "upgrade_ladder": {k: next_upgrade(k) for k in ("free", "pro", "whale", "institutional")},
        "integration_addendum": INTEGRATION_ADDENDUM,
        "honesty": {
            "guaranteed_accuracy_claimed": False,
            "no_fifteen_dollar_tier": True,
            "note": "We sell reviewable decisions and proof — not guaranteed returns.",
        },
        "checkout": {
            "pro": "/create-checkout-session?tier=pro",
            "whale": "/create-checkout-session?tier=whale",
            "institutional": "/data-room",
        },
    }
