"""
BLACKDARK Trust OS — UX lenses (Prove / Operate / Desk / Room).

One product. Four memorable lenses. Four primary entries.
Viral atom: shareable Decision Certificate (Proof Card).
Not multi-platform SKUs — depth of the same decision room.
"""

from __future__ import annotations

from typing import Any, Literal

Lens = Literal["prove", "operate", "desk", "room"]

LENSES: list[dict[str, Any]] = [
    {
        "id": "prove",
        "label": "Prove",
        "audience": "retail",
        "tier_hint": "free",
        "promise": "Decide… and prove it.",
        "support": "One clear Act/Wait + Why + shareable Proof Card.",
        "cta_primary": {"label": "Get Decision", "href": "/dashboard?lens=prove#decide"},
        "cta_secondary": {"label": "Verify Ledger", "href": "/oracle-accuracy"},
        "shell": "oracle_first",
        "ux_mode_default": "beginner",
        "show_sections": ["decide", "verify", "certificate", "chart_light"],
        "hide_sections": ["arbitrage", "stealth", "mev", "desk_tools"],
        "soft_sections": ["my_book", "alerts"],  # teaser / upgrade
        "viral_role": "Each Proof Card is an invite — share why this decision was made.",
        "entry_path": "/dashboard?lens=prove",
        "landing_path": "/?lens=prove#oracle",
    },
    {
        "id": "operate",
        "label": "Operate",
        "audience": "pro",
        "tier_hint": "pro",
        "promise": "Make proof a daily habit.",
        "support": "Unlimited decisions, Portfolio AI, Radar, alerts — same room, deeper rhythm.",
        "cta_primary": {"label": "Open Decision Habit", "href": "/dashboard?lens=operate#decide"},
        "cta_secondary": {"label": "Start 7-Day Trial", "href": "/create-checkout-session?tier=pro"},
        "shell": "habit_first",
        "ux_mode_default": "pro",
        "show_sections": [
            "decide",
            "verify",
            "my_book",
            "alerts",
            "radar",
            "certificate",
            "chart",
        ],
        "hide_sections": ["stealth", "mev"],
        "soft_sections": ["arbitrage"],
        "viral_role": "Upgrade path from Free ceiling / watermark — habit without the 3/day cap.",
        "entry_path": "/dashboard?lens=operate",
        "landing_path": "/dashboard?lens=operate",
    },
    {
        "id": "desk",
        "label": "Desk",
        "audience": "whale",
        "tier_hint": "whale",
        "promise": "Convince someone else.",
        "support": "Signal-to-Noise, Stealth views, Evidence pack, API — a decision desk, not more charts.",
        "cta_primary": {"label": "Open Decision Desk", "href": "/dashboard?lens=desk#stealth"},
        "cta_secondary": {"label": "Upgrade Decision Desk", "href": "/create-checkout-session?tier=whale"},
        "shell": "desk_first",
        "ux_mode_default": "pro",
        "show_sections": [
            "decide",
            "verify",
            "my_book",
            "alerts",
            "whales",
            "stealth",
            "mev",
            "arbitrage",
            "certificate",
        ],
        "hide_sections": [],
        "soft_sections": [],
        "viral_role": "Packaging for partners/clients — not a second product.",
        "entry_path": "/dashboard?lens=desk#stealth",
        "landing_path": "/dashboard?lens=desk",
    },
    {
        "id": "room",
        "label": "Room",
        "audience": "fund",
        "tier_hint": "institutional",
        "promise": "Official decision room.",
        "support": "Data Room, Integration Addendum, SSO/MFA/SLA — Talk to us. Not self-serve Checkout.",
        "cta_primary": {"label": "Data Room", "href": "/data-room"},
        "cta_secondary": {"label": "Fund Terminal", "href": "/b2b#fund-terminal"},
        "shell": "room_first",
        "ux_mode_default": "pro",
        "show_sections": ["verify", "evidence", "integration"],
        "hide_sections": ["arbitrage", "stealth", "mev", "my_book"],
        "soft_sections": [],
        "viral_role": "Reverse prestige — same OS funds negotiate lifts Free/Pro trust.",
        "entry_path": "/data-room?lens=room",
        "landing_path": "/b2b?lens=room#fund-terminal",
        "self_serve": False,
    },
]

# Four primary entries — what users memorize.
PRIMARY_ENTRIES: list[dict[str, Any]] = [
    {
        "id": "decide",
        "label": "Decide",
        "path": "/dashboard#decide",
        "action": "oracle",
        "hint": "One symbol → Act/Wait + Why + Proof Card.",
        "lenses": ["prove", "operate", "desk"],
    },
    {
        "id": "verify",
        "label": "Verify",
        "path": "/oracle-accuracy",
        "action": "navigate",
        "hint": "Public Accuracy Ledger — hits and misses.",
        "lenses": ["prove", "operate", "desk", "room"],
    },
    {
        "id": "my_book",
        "label": "My book",
        "path": "/dashboard#portfolio",
        "action": "portfolio",
        "hint": "Portfolio risk in plain language (Operate+).",
        "lenses": ["operate", "desk"],
        "upgrade_from": "prove",
    },
    {
        "id": "alerts",
        "label": "Alerts",
        "path": "/dashboard#alerts",
        "action": "alerts",
        "hint": "Inbox that fires after Truth + Half-Life gates.",
        "lenses": ["operate", "desk"],
        "upgrade_from": "prove",
    },
]

AUDIENCE_TO_LENS = {
    "retail": "prove",
    "pro": "operate",
    "whale": "desk",
    "fund": "room",
    "institutional": "room",
}

TIER_TO_LENS = {
    "free": "prove",
    "pro": "operate",
    "whale": "desk",
}


def normalize_lens(value: str | None) -> Lens:
    raw = (value or "").strip().lower()
    aliases = {
        "prove": "prove",
        "proof": "prove",
        "free": "prove",
        "retail": "prove",
        "operate": "operate",
        "pro": "operate",
        "habit": "operate",
        "desk": "desk",
        "whale": "desk",
        "room": "room",
        "fund": "room",
        "institutional": "room",
        "institution": "room",
    }
    return aliases.get(raw, "prove")  # type: ignore[return-value]


def lens_by_id(lens_id: str | None) -> dict[str, Any]:
    key = normalize_lens(lens_id)
    for row in LENSES:
        if row["id"] == key:
            return dict(row)
    return dict(LENSES[0])


def lens_from_audience(audience: str | None) -> dict[str, Any]:
    from audience_routing import normalize_audience

    aud = normalize_audience(audience)
    return lens_by_id(AUDIENCE_TO_LENS.get(aud, "prove"))


def lens_from_tier(tier: str | None) -> dict[str, Any]:
    return lens_by_id(TIER_TO_LENS.get((tier or "free").strip().lower(), "prove"))


def primary_entries_for_lens(lens_id: str | None) -> list[dict[str, Any]]:
    key = normalize_lens(lens_id)
    out = []
    for entry in PRIMARY_ENTRIES:
        row = dict(entry)
        if key in entry["lenses"]:
            row["available"] = True
        else:
            row["available"] = False
            row["locked"] = entry.get("upgrade_from") == key or key == "prove"
            row["upgrade_hint"] = (
                "Open Operate (Decision Pro) to unlock daily habit depth."
                if key == "prove"
                else None
            )
        out.append(row)
    return out


def lenses_manifest() -> dict[str, Any]:
    return {
        "product": "BLACKDARK Trust OS",
        "canon": "1 product · 4 lenses · 4 entries · 6 heroes — depth ladder, not multi-platform",
        "story": "Prove → Operate → Desk → Room",
        "lenses": LENSES,
        "primary_entries": PRIMARY_ENTRIES,
        "memory_line": "Four words. Four doors. One decision room.",
        "viral_atom": "decision_certificate",
        "honesty": {
            "guaranteed_accuracy": False,
            "note": "We sell reviewable decisions and proof — not guaranteed returns.",
        },
        "competitors_contrast": (
            "They sell data, charts, or opaque scores. "
            "We surface a reviewable decision + shareable Proof Card."
        ),
        "endpoints": {
            "manifest": "/api/lenses",
            "lens": "/api/lenses/{lens}",
            "entries": "/api/lenses/{lens}/entries",
        },
    }


def lens_payload(lens_id: str | None = None, *, audience: str | None = None) -> dict[str, Any]:
    lens = lens_from_audience(audience) if audience and not lens_id else lens_by_id(lens_id)
    return {
        "lens": lens,
        "entries": primary_entries_for_lens(lens["id"]),
        "story": lenses_manifest()["story"],
        "memory_line": lenses_manifest()["memory_line"],
    }
