"""Today's Decision Surface + user-facing provenance (DIG-035, DIG-051, DIG-058)."""

from __future__ import annotations

from typing import Any


def build_decision_surface(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": payload.get("symbol") or payload.get("asset"),
        "provenance": payload.get("provenance_chain"),
        "receipt": (payload.get("intelligence_receipt") or {}).get("receipt_hash"),
        "evidence_class": payload.get("evidence_class"),
        "disclosure": "Advisory intelligence — not executable profit claim.",
    }
