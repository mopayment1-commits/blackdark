"""Methodology cards registry (DIG-004, DIG-020)."""

from __future__ import annotations

from typing import Any

_CARDS: dict[str, dict[str, Any]] = {
    "oracle_v1": {
        "methodology_id": "oracle_v1",
        "title": "Unified multimodal oracle",
        "version": "1",
        "limitations": "Advisory directional signal only.",
    }
}


def get_methodology(methodology_id: str) -> dict[str, Any] | None:
    return _CARDS.get(methodology_id)


def attach_methodology(payload: dict[str, Any], methodology_id: str = "oracle_v1") -> dict[str, Any]:
    out = dict(payload)
    card = get_methodology(methodology_id)
    if card:
        out["methodology_card"] = card
    return out
