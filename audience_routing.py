"""
BLACKDARK — Audience entry routing (Section H, mandatory).

Same six heroes; first-screen emphasis differs by audience.
"""

from __future__ import annotations

from typing import Any, Literal

Audience = Literal["retail", "pro", "whale", "fund"]

_AUDIENCES = {
    "retail": {
        "audience": "retail",
        "first_screen": "single_sentence_oracle",
        "heroes": ["single_sentence_oracle", "decision_certificate"],
        "cta": "Get one clear Act / Wait decision — no dashboard tourism.",
        "entry_path": "/?audience=retail",
        "ux_mode_default": "beginner",
        "progressive_disclosure": {
            "emphasize": ["oracle", "certificate", "ledger"],
            "defer": ["stealth", "fund_terminal", "radar_depth", "arb_desk"],
            "shell": "oracle_first",
        },
    },
    "pro": {
        "audience": "pro",
        "first_screen": "opportunity_score_explainability",
        "heroes": ["opportunity_score", "whale_intelligence"],
        "cta": "Full Opportunity Score, Truth gates, and Whale Radar.",
        "entry_path": "/dashboard?audience=pro",
        "ux_mode_default": "pro",
        "progressive_disclosure": {
            "emphasize": ["radar", "opportunity_score", "oracle", "half_life"],
            "defer": ["fund_terminal", "stealth_deep"],
            "shell": "radar_first",
        },
    },
    "whale": {
        "audience": "whale",
        "first_screen": "stealth_execution_advisor",
        "heroes": ["portfolio_ai", "opportunity_half_life", "stealth_execution_advisor"],
        "cta": "Stealth Advisor + Half-Life + MEV report before size hits the book.",
        "entry_path": "/dashboard?audience=whale#stealth",
        "ux_mode_default": "pro",
        "progressive_disclosure": {
            "emphasize": ["stealth", "half_life", "portfolio", "execution_risk"],
            "defer": ["retail_tour", "fund_packaging"],
            "shell": "stealth_first",
        },
    },
    "fund": {
        "audience": "fund",
        "first_screen": "emerging_fund_terminal",
        "heroes": ["public_accuracy_ledger", "evidence_pack"],
        "cta": "Emerging Fund Terminal — DD-ready Ledger + Evidence Pack.",
        "entry_path": "/b2b?audience=fund#fund-terminal",
        "ux_mode_default": "pro",
        "progressive_disclosure": {
            "emphasize": ["ledger", "evidence_pack", "compliance", "fund_terminal"],
            "defer": ["retail_tour", "stealth_deep"],
            "shell": "dd_first",
        },
    },
}


def normalize_audience(value: str | None) -> Audience:
    raw = (value or "retail").strip().lower()
    if raw in {"pro", "professional", "trader"}:
        return "pro"
    if raw in {"whale", "execution"}:
        return "whale"
    if raw in {"fund", "institution", "institutional", "allocator"}:
        return "fund"
    return "retail"


_LENS_ID_BY_AUDIENCE: dict[Audience, str] = {
    "retail": "prove",
    "pro": "operate",
    "whale": "desk",
    "fund": "room",
}

_LENS_LABEL_FALLBACK: dict[str, str] = {
    "prove": "Prove",
    "operate": "Operate",
    "desk": "Desk",
    "room": "Room",
}

_LENS_PROMISE_FALLBACK: dict[str, str] = {
    "prove": "Decide… and prove it.",
    "operate": "Make proof a daily habit.",
    "desk": "Convince someone else.",
    "room": "Official decision room.",
}


def audience_entry(value: str | None = None) -> dict[str, Any]:
    key = normalize_audience(value)
    row = dict(_AUDIENCES[key])
    lens_id = _LENS_ID_BY_AUDIENCE.get(key, "prove")
    row["lens"] = lens_id
    try:
        from trust_os_lenses import AUDIENCE_TO_LENS, lens_by_id, primary_entries_for_lens

        lens_id = AUDIENCE_TO_LENS.get(key, lens_id)
        row["lens"] = lens_id
        lens = lens_by_id(lens_id)
        row["lens_label"] = lens.get("label")
        row["lens_promise"] = lens.get("promise")
        row["primary_entries"] = primary_entries_for_lens(lens_id)
        if lens.get("entry_path"):
            row["entry_path"] = lens["entry_path"]
        if lens.get("ux_mode_default"):
            row["ux_mode_default"] = lens["ux_mode_default"]
    except Exception:
        pass
    if not row.get("lens_label"):
        row["lens_label"] = _LENS_LABEL_FALLBACK.get(lens_id, "Prove")
    if not row.get("lens_promise"):
        row["lens_promise"] = _LENS_PROMISE_FALLBACK.get(lens_id, "")
    row.setdefault("cta", row.get("cta") or "")
    return row


def all_audiences() -> list[dict[str, Any]]:
    return [audience_entry(k) for k in _AUDIENCES]
