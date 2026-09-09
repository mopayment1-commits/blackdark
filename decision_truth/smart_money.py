"""Smart money context without unsupported causality (DTS-031–033)."""

from __future__ import annotations

from typing import Any


def build_smart_money_context(opportunity: dict[str, Any]) -> dict[str, Any]:
    wallet = opportunity.get("whale_wallet") or opportunity.get("smart_money")
    if not wallet and not opportunity.get("whale_flow_usd"):
        return {"status": "unavailable", "context_only": True}

    attribution = {
        "entity": wallet or "unknown_cluster",
        "confidence": float(opportunity.get("attribution_confidence") or 0.5),
        "source": opportunity.get("attribution_source") or "onchain_heuristic",
        "provenance": opportunity.get("attribution_provenance") or "wallet_profiler",
    }
    return {
        "status": "context",
        "attribution": attribution,
        "flow_usd": opportunity.get("whale_flow_usd"),
        "association_note": "Temporal association only — causality not claimed without evidence.",
        "unsupported_causality_blocked": True,
    }


def audit_causality_language(text: str) -> bool:
    """Return True if text avoids unsupported causality."""
    banned = ("caused", "because wallet", "whale x caused", "price rose because")
    lower = (text or "").lower()
    return not any(b in lower for b in banned)
