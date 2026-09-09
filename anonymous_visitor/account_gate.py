"""Account gate policy — AV §8 persistence/personalization boundary."""

from __future__ import annotations

from typing import Any

PERSISTENCE_ACTIONS = frozenset(
    {
        "save_asset",
        "create_watchlist",
        "create_alert",
        "follow_decision",
        "save_layout",
        "sync_devices",
        "portfolio_ai",
        "extended_history",
        "private_workspace",
        "proprietary_depth",
        "export",
        "api_credentials",
    }
)


def evaluate_account_gate(action: str, *, auth_state: str) -> dict[str, Any]:
    act = (action or "").strip().lower()
    if act not in PERSISTENCE_ACTIONS:
        return {"ok": True, "gate_required": False, "action": act}
    if auth_state == "ANONYMOUS":
        return {
            "ok": False,
            "gate_required": True,
            "action": act,
            "cta": "Create Free Account",
            "reason": "persistence_personalization_depth_boundary",
        }
    return {"ok": True, "gate_required": False, "action": act, "auth_state": auth_state}


def account_gate_status() -> dict[str, Any]:
    return {
        "registration_not_required_for_basic_public_value": True,
        "gate_at_persistence_boundary": True,
        "persistence_actions": sorted(PERSISTENCE_ACTIONS),
        "preferred_cta": "Create Free Account",
    }
