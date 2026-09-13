"""Contextual capability placement — same canonical semantics (spec §16)."""

from __future__ import annotations

from typing import Any

_CONTEXT_MAP: dict[str, list[str]] = {
    "asset": ["single_sentence_oracle", "opportunity_score_explainability"],
    "position": ["portfolio_ai"],
    "wallet": ["whale_signal_vs_noise"],
    "opportunity": ["opportunity_score_explainability"],
    "risk": ["portfolio_ai", "whale_signal_vs_noise"],
}


def contextual_capabilities(context: str) -> dict[str, Any]:
    key = (context or "").strip().lower()
    caps = _CONTEXT_MAP.get(key, [])
    return {
        "context": key,
        "capabilities": caps,
        "canonical_semantics_unchanged": True,
        "entitlement_authority": "cap646/entitlements.py",
        "surface_only": True,
    }
