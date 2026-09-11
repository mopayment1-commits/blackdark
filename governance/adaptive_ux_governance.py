"""Adaptive Intelligence Experience — Six Heroes router (BGS-004)."""

from __future__ import annotations

from typing import Any

SIX_HEROES = (
    "market_pulse",
    "opportunity_radar",
    "risk_shield",
    "execution_desk",
    "evidence_room",
    "institutional_lens",
)


def adaptive_ux_status() -> dict[str, Any]:
    router_ok = False
    trust_pulse = False
    try:
        from api.routers.heroes import router  # noqa: F401

        router_ok = True
    except Exception:
        pass
    try:
        from trust_pulse import build_trust_pulse  # noqa: F401

        trust_pulse = True
    except Exception:
        pass

    return {
        "six_heroes": list(SIX_HEROES),
        "heroes_router": router_ok,
        "trust_pulse": trust_pulse,
        "intent_resolver": router_ok,
        "decision_contract_surface": True,
        "calm_surface": True,
    }
