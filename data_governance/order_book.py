"""Order book governance policy (DIG-015)."""

from __future__ import annotations

from typing import Any


def order_book_policy(depth_levels: int = 20) -> dict[str, Any]:
    return {"depth_levels": depth_levels, "snapshot_only": True, "live_trading_blocked": True}
