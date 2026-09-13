"""Calm Surface manifest — spec §3 (AIE-003)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.heroes import heroes_manifest
from bd_platform.adaptive_intelligence.today_focus import build_today_focus


def calm_surface_manifest() -> dict[str, Any]:
    heroes = heroes_manifest()
    focus = build_today_focus()
    return {
        "surface_budget_enforced": True,
        "primary_surfaces": [
            "six_heroes",
            "today_focus",
            "top_opportunity",
            "key_risk",
            "what_changed",
            "universal_command",
            "my_stack_summary",
        ],
        "six_heroes": heroes["product_heroes"],
        "today_focus": focus,
        "capability_library_hidden_on_home": True,
        "complexity_on_demand": True,
    }
