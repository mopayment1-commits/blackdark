"""Universal Intelligence Command / Intent Search — spec §6 (AIE-004)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.intent_contract import resolve_intent_contract
from bd_platform.adaptive_intelligence.intelligence_router import route_intelligence_request


def universal_command_search(
    *,
    query: str,
    asset: str | None = None,
    horizon: str | None = None,
) -> dict[str, Any]:
    intent = resolve_intent_contract(query=query, asset=asset, horizon=horizon)
    routed = route_intelligence_request(query=query, asset=asset, horizon=horizon)
    return {
        "query": query,
        "intent_contract": intent.to_dict(),
        "router_result": routed,
        "keyboard_shortcut": "cmd_or_ctrl_k",
        "shortcut_conflict_safe": True,
        "discoverable_alternative": "/api/adaptive/command",
    }
