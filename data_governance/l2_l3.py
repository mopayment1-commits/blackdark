"""L1/L2/L3 selective policy (DIG-015)."""

from __future__ import annotations

from typing import Any


def l2_l3_policy(symbol: str) -> dict[str, Any]:
    return {"symbol": symbol.upper(), "l2_enabled": True, "l3_enabled": False, "policy": "selective"}
