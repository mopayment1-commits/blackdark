"""Portfolio rebalancing — target weights + trade suggestions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def suggest_rebalance(
    holdings: dict[str, float],
    *,
    target_weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """holdings: {asset: usd_value}. target_weights must sum ~1.0."""
    total = sum(float(v) for v in holdings.values())
    if total <= 0:
        return {"error": "empty_portfolio"}

    if not target_weights:
        n = max(len(holdings), 1)
        target_weights = {k: 1.0 / n for k in holdings}

    tw_sum = sum(float(v) for v in target_weights.values()) or 1.0
    target_weights = {k: float(v) / tw_sum for k, v in target_weights.items()}

    trades: list[dict[str, Any]] = []
    for asset, usd in holdings.items():
        current_w = float(usd) / total
        target_w = target_weights.get(asset, 0.0)
        delta_usd = (target_w - current_w) * total
        if abs(delta_usd) < 1.0:
            continue
        trades.append(
            {
                "asset": asset,
                "side": "buy" if delta_usd > 0 else "sell",
                "amount_usd": round(abs(delta_usd), 2),
                "current_weight_pct": round(current_w * 100, 2),
                "target_weight_pct": round(target_w * 100, 2),
            }
        )

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "portfolio_total_usd": round(total, 2),
        "target_weights": target_weights,
        "trades": trades,
        "mode": "suggestion_only",
        "note": "Connect exchange keys for automated rebalance execution",
    }
