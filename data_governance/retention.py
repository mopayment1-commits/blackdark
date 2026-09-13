"""Data retention tiering (DIG-028, DIG-030)."""

from __future__ import annotations

from typing import Any

_RETENTION = {
    "decision": 365,
    "signal": 180,
    "oracle": 365,
    "cap_execute": 90,
    "exposure": 90,
    "failure": 730,
    "market_event": 365,
}


def apply_retention_class(payload: dict[str, Any], *, surface: str) -> dict[str, Any]:
    out = dict(payload)
    out["retention_days"] = _RETENTION.get(surface, 90)
    out["retention_class"] = "material_intelligence"
    return out
