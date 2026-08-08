"""
BLACKDARK — Intent router (results over features).

Display-layer only: "What do you want to do today?" maps to existing heroes.
Does NOT invent Predict / Build Strategy / Arena product surfaces.
"""

from __future__ import annotations

from typing import Any

# Five outcomes from the strategic correction (not a feature dump).
OUTCOMES: list[dict[str, str]] = [
    {
        "id": "discover_opportunities",
        "label": "Discover opportunities",
        "maps_to": "opportunity_score + arb gates",
    },
    {
        "id": "make_decision",
        "label": "Make a decision",
        "maps_to": "single_sentence_oracle",
    },
    {
        "id": "reduce_risk",
        "label": "Reduce risk",
        "maps_to": "portfolio_ai + whale_signal_vs_noise",
    },
    {
        "id": "save_time",
        "label": "Save time",
        "maps_to": "intent_router + act_wait + inbox",
    },
    {
        "id": "execution_quality",
        "label": "Improve execution quality",
        "maps_to": "net_edge_truth + half_life + stealth_advisor",
    },
]

# Primary four entries (memorable) + secondary desk intents.
INTENTS: list[dict[str, Any]] = [
    {
        "id": "decide",
        "label": "Decide",
        "outcome": "make_decision",
        "hero": "single_sentence_oracle",
        "path": "/dashboard#decide",
        "action": "oracle",
        "hint": "One symbol → Act/Wait + Why + Proof Card.",
        "primary": True,
        "entry": "decide",
    },
    {
        "id": "verify",
        "label": "Verify",
        "outcome": "make_decision",
        "hero": "public_accuracy_ledger",
        "path": "/oracle-accuracy",
        "action": "navigate",
        "hint": "Public Accuracy Ledger — hits and misses.",
        "primary": True,
        "entry": "verify",
    },
    {
        "id": "my_book",
        "label": "My book",
        "outcome": "reduce_risk",
        "hero": "portfolio_ai",
        "path": "/dashboard#portfolio",
        "action": "portfolio",
        "hint": "Portfolio risk in plain language — Operate+.",
        "primary": True,
        "entry": "my_book",
    },
    {
        "id": "alerts",
        "label": "Alerts",
        "outcome": "save_time",
        "hero": "single_sentence_oracle",
        "path": "/dashboard#alerts",
        "action": "alerts",
        "hint": "Inbox after Truth + Half-Life gates.",
        "primary": True,
        "entry": "alerts",
    },
    {
        "id": "track_whale",
        "label": "Whale Signal vs Noise",
        "outcome": "reduce_risk",
        "hero": "whale_intelligence_radar",
        "path": "/dashboard#whales",
        "action": "whales",
        "hint": "Transfers ≠ trades. Desk lens.",
        "primary": False,
        "lens": "desk",
    },
    {
        "id": "find_arb",
        "label": "Net-edge arbitrage",
        "outcome": "discover_opportunities",
        "hero": "opportunity_score_explainability",
        "path": "/dashboard#arbitrage",
        "action": "arbitrage",
        "hint": "Net edge only — Operate/Desk.",
        "primary": False,
        "lens": "operate",
    },
    {
        "id": "fund_terminal",
        "label": "Fund Room",
        "outcome": "save_time",
        "hero": "public_accuracy_ledger",
        "path": "/b2b#fund-terminal",
        "action": "navigate",
        "hint": "Institutional Room — Talk to us / Data Room.",
        "primary": False,
        "lens": "room",
    },
]

# Explicitly rejected intents from inflated strategy pastes.
REJECTED_INTENTS: list[dict[str, str]] = [
    {"id": "predict_guaranteed", "reason": "No guaranteed prediction product surface"},
    {"id": "build_strategy_studio", "reason": "Not a seventh button / strategy IDE"},
    {"id": "blackdark_arena", "reason": "Viral Arena not building — use Certificate share + Glass Box"},
    {"id": "neuro_canvas", "reason": "Neuro-Design Canvas OS not a product surface"},
]


def intent_router_manifest() -> dict[str, Any]:
    primary = [i for i in INTENTS if i.get("primary")]
    secondary = [i for i in INTENTS if not i.get("primary")]
    return {
        "question": "What do you need?",
        "principle": "Four doors — Decide · Verify · My book · Alerts — over six heroes",
        "memory_line": "Prove → Operate → Desk → Room",
        "outcomes": OUTCOMES,
        "intents": INTENTS,
        "primary_entries": primary,
        "secondary_intents": secondary,
        "rejected_intents": REJECTED_INTENTS,
        "ui_language": "en",
        "note": "Lens UX routing. Engines stay quiet behind heroes.",
        "lenses_api": "/api/lenses",
    }


def resolve_intent(intent_id: str) -> dict[str, Any]:
    for row in INTENTS:
        if row["id"] == intent_id:
            return {"ok": True, "intent": row}
    for row in REJECTED_INTENTS:
        if row["id"] == intent_id:
            return {"ok": False, "rejected": True, "intent_id": intent_id, "reason": row["reason"]}
    return {"ok": False, "rejected": False, "intent_id": intent_id, "reason": "unknown_intent"}
