"""Historical depth policy (DIG-016)."""

from __future__ import annotations

from typing import Any

_MIN_DEPTH_DAYS = 30


def assert_historical_depth(payload: dict[str, Any], *, min_days: int = _MIN_DEPTH_DAYS) -> dict[str, Any]:
    depth = int(payload.get("history_days") or min_days)
    return {"ok": depth >= min_days, "history_days": depth, "min_days": min_days}
