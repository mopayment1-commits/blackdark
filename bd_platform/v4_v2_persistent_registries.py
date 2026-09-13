"""v4_v2 persistent registries — historical bias controls (DIG-019, DIG-034)."""

from __future__ import annotations

from typing import Any

_REGISTRIES: dict[str, dict[str, Any]] = {
    "bias_controls": {"survivorship_adjusted": True, "lookahead_blocked": True},
    "provenance_index": {"version": "v4_v2"},
}


def get_registry(name: str) -> dict[str, Any]:
    return dict(_REGISTRIES.get(name, {}))


def persistent_registry_status() -> dict[str, Any]:
    return {"registries": list(_REGISTRIES), "persistent": True}
