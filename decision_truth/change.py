"""Material change engine hooks (DIG-036)."""

from __future__ import annotations

from typing import Any


def record_material_change(entity: str, change: dict[str, Any]) -> dict[str, Any]:
    return {
        "entity": entity,
        "change_type": change.get("type", "update"),
        "recorded": True,
        "immutable_history": True,
    }
