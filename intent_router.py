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

# Honest intents → existing surfaces only.
INTENTS: list[dict[str, Any]] = [
    {
        "id": "get_decision",
        "label": "Get a clear Act / Wait decision",
        "outcome": "make_decision",
        "hero": "single_sentence_oracle",
        "path": "/dashboard#oracle",
        "action": "oracle",
        "hint": "One symbol → one sentence. Analytical tool — not advice.",
    },
    {
        "id": "verify_accuracy",
        "label": "Verify public accuracy (including misses)",
        "outcome": "make_decision",
        "hero": "public_accuracy_ledger",
        "path": "/oracle-accuracy",
        "action": "navigate",
        "hint": "Don't trust us. Verify the ledger.",
    },
    {
        "id": "track_whale",
        "label": "Track whale Signal vs Noise",
        "outcome": "reduce_risk",
        "hero": "whale_intelligence_radar",
        "path": "/dashboard#whales",
        "action": "whales",
        "hint": "Transfers ≠ trades. One plain sentence.",
    },
    {
        "id": "portfolio_risk",
        "label": "Check portfolio risk in plain language",
        "outcome": "reduce_risk",
        "hero": "portfolio_ai",
        "path": "/dashboard#portfolio",
        "action": "portfolio",
        "hint": "Risk level + BTC-drop scenario — private holdings stay local.",
    },
    {
        "id": "find_arb",
        "label": "Scan net-edge arbitrage (after fees)",
        "outcome": "discover_opportunities",
        "hero": "opportunity_score_explainability",
        "path": "/dashboard#arbitrage",
        "action": "arbitrage",
        "hint": "Net edge only — not gross spread theater.",
    },
    {
        "id": "fund_terminal",
        "label": "Open Emerging Fund Terminal",
        "outcome": "save_time",
        "hero": "public_accuracy_ledger",
        "path": "/b2b#fund-terminal",
        "action": "navigate",
        "hint": "Sub-$50M fund packaging — not Kaiko-class theater.",
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
    return {
        "question": "What do you want to do today?",
        "principle": "Results over features — route to six heroes only",
        "outcomes": OUTCOMES,
        "intents": INTENTS,
        "rejected_intents": REJECTED_INTENTS,
        "ui_language": "en",
        "note": "Display routing layer. Engines stay quiet behind heroes.",
    }


def resolve_intent(intent_id: str) -> dict[str, Any]:
    for row in INTENTS:
        if row["id"] == intent_id:
            return {"ok": True, "intent": row}
    for row in REJECTED_INTENTS:
        if row["id"] == intent_id:
            return {"ok": False, "rejected": True, "intent_id": intent_id, "reason": row["reason"]}
    return {"ok": False, "rejected": False, "intent_id": intent_id, "reason": "unknown_intent"}
