"""Adaptive Intelligence Experience — institutional router, contracts, and discovery."""

from __future__ import annotations

from bd_platform.adaptive_intelligence.capability_graph import build_capability_graph
from bd_platform.adaptive_intelligence.decision_contract import build_decision_contract
from bd_platform.adaptive_intelligence.intent_search import search_intent
from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request
from bd_platform.adaptive_intelligence.progressive_disclosure import apply_progressive_disclosure

__all__ = [
    "search_intent",
    "route_intelligence_request",
    "build_decision_contract",
    "build_capability_graph",
    "apply_progressive_disclosure",
]
