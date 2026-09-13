"""My Stack — favorites/recent/playbooks (spec §13, AIE-015)."""

from __future__ import annotations

from typing import Any

_STACK: dict[str, dict[str, list[str]]] = {}


def get_stack(user_id: str) -> dict[str, Any]:
    return _STACK.get(user_id) or {
        "favorites": [],
        "recent": [],
        "saved_searches": [],
        "playbooks": [],
        "alerts": [],
    }


def add_favorite(user_id: str, capability_id: str) -> dict[str, Any]:
    stack = get_stack(user_id)
    favs = stack.setdefault("favorites", [])
    if capability_id not in favs:
        favs.append(capability_id)
    _STACK[user_id] = stack
    return stack
