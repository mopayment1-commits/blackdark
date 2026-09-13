"""BLACKDARK Adaptive Intelligence Experience v4 — canonical integration layer (reuse-before-build)."""

from bd_platform.adaptive_intelligence.calm_surface import calm_surface_manifest
from bd_platform.adaptive_intelligence.decision_boundary import build_boundary
from bd_platform.adaptive_intelligence.decision_contract import build_adaptive_decision_contract
from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request
from bd_platform.adaptive_intelligence.intent_contract import IntentContract, resolve_intent_contract
from bd_platform.adaptive_intelligence.safety_floor import enforce_safety_floor
from bd_platform.adaptive_intelligence.trust_dimensions import TrustDimensionVector
from bd_platform.adaptive_intelligence.universal_command import universal_command_search

__all__ = [
    "IntentContract",
    "TrustDimensionVector",
    "build_adaptive_decision_contract",
    "build_boundary",
    "calm_surface_manifest",
    "enforce_safety_floor",
    "resolve_intent_contract",
    "route_intelligence_request",
    "universal_command_search",
]
