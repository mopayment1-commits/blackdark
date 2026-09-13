"""Bridge SQL systems API material writes through central governance runtime."""

from __future__ import annotations

from typing import Any

_SURFACE_MAP = {
    "signal": "signal",
    "decision": "decision",
    "prediction": "oracle",
    "market_event": "market_event",
    "failure": "failure",
    "evidence": "ledger_write",
    "outcome": "ledger_write",
}


def govern_sql_write(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    from blackdark.data_governance.runtime import enforce_material_write

    mapped = _SURFACE_MAP.get(surface, "ledger_write")
    body = dict(payload)
    body.setdefault("source", "data_engine_systems_api")
    body.setdefault("purpose", "analytics")
    return enforce_material_write(mapped, body)
