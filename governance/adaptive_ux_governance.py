"""Adaptive Intelligence Experience — runtime bindings (BGS-004)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.heroes import GOVERNANCE_TO_PRODUCT, PRODUCT_HEROES

SIX_HEROES = tuple(GOVERNANCE_TO_PRODUCT.keys())


def adaptive_ux_status() -> dict[str, Any]:
    bindings: dict[str, bool] = {}
    try:
        from api.routers.heroes import router  # noqa: F401

        bindings["heroes_router"] = True
    except Exception:
        bindings["heroes_router"] = False
    try:
        from api.routers.adaptive_intelligence import router  # noqa: F401

        bindings["adaptive_router"] = True
    except Exception:
        bindings["adaptive_router"] = False
    try:
        from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request

        sample = route_intelligence_request(intent_id="decide")
        bindings["router_runtime"] = bool(sample.get("router_stages_completed"))
    except Exception:
        bindings["router_runtime"] = False
    try:
        from bd_platform.adaptive_intelligence.decision_contract import build_adaptive_decision_contract

        bindings["decision_contract"] = callable(build_adaptive_decision_contract)
    except Exception:
        bindings["decision_contract"] = False
    try:
        from trust_pulse import build_trust_pulse  # noqa: F401

        bindings["trust_pulse"] = True
    except Exception:
        bindings["trust_pulse"] = False
    try:
        from bd_platform.adaptive_intelligence.calm_surface import calm_surface_manifest

        bindings["calm_surface"] = bool(calm_surface_manifest().get("surface_budget_enforced"))
    except Exception:
        bindings["calm_surface"] = False

    return {
        "six_heroes": list(SIX_HEROES),
        "product_heroes": list(PRODUCT_HEROES),
        "governance_alias_map": GOVERNANCE_TO_PRODUCT,
        "bindings": bindings,
        "intent_resolver": bindings.get("router_runtime", False),
        "decision_contract_surface": bindings.get("decision_contract", False),
        "heroes_router": bindings.get("heroes_router", False),
        "trust_pulse": bindings.get("trust_pulse", False),
        "calm_surface": bindings.get("calm_surface", False),
        "adaptive_api": bindings.get("adaptive_router", False),
    }
