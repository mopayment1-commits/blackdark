"""Intelligence Router — deterministic-first orchestration with abstain/stop controls."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.decision_contract import build_decision_contract
from bd_platform.adaptive_intelligence.intent_search import search_intent


def route_intelligence_request(
    *,
    goal: str,
    symbol: str = "BTC",
    tier: str = "free",
    max_candidates: int = 3,
) -> dict[str, Any]:
    discovery = search_intent(goal, limit=max_candidates)
    if discovery.get("abstain"):
        return {
            "ok": False,
            "abstain": True,
            "reason": discovery.get("reason"),
            "discovery": discovery,
        }
    candidates = discovery["matches"][:max_candidates]
    contract = build_decision_contract(
        goal=goal,
        symbol=symbol,
        candidates=candidates,
        tier=tier,
    )
    return {
        "ok": True,
        "abstain": contract.get("abstain", False),
        "discovery": discovery,
        "decision_contract": contract,
        "doctrine": "deterministic_first_evidence_first_shadow_first",
    }
