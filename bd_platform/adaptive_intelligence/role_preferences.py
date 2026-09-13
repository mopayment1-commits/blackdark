"""Role-based experience — preference not restriction (spec §14)."""

from __future__ import annotations

from typing import Any

_DEFAULTS: dict[str, dict[str, Any]] = {
    "retail": {"terminology": "plain", "depth": "summary", "default_surfaces": ["six_heroes", "today_focus"]},
    "pro": {"terminology": "desk", "depth": "standard", "default_surfaces": ["six_heroes", "today_focus", "explorer"]},
    "institutional": {"terminology": "institutional", "depth": "deep", "default_surfaces": ["data_room", "workspaces"]},
}


def get_role_preferences(role: str | None = None) -> dict[str, Any]:
    key = (role or "retail").strip().lower()
    prefs = dict(_DEFAULTS.get(key, _DEFAULTS["retail"]))
    return {
        "role": key,
        "preferences": prefs,
        "restricts_capabilities": False,
        "overridable": True,
        "preference_not_financial_truth": True,
    }
