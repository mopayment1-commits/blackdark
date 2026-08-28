"""
Shared portfolio risk inputs — returns series from holdings (#907/#959/#967).

Used by VaR (#1021), CVaR (#1022), Correlation (#1049), Stress Testing (#1006).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from money_decimal import d, money


def proxy_asset_returns(*, beta: float, lookback_days: int) -> list[float]:
    """Deterministic proxy daily returns (beta-scaled) until live historical feed wired."""
    return [beta * 0.02 * ((i % 7) - 3) / 3 for i in range(lookback_days)]


def build_portfolio_risk_context(
    holdings: list[dict[str, Any]],
    *,
    lookback_days: int = 90,
) -> dict[str, Any]:
    """Build total value, weighted portfolio returns, and per-asset return series."""
    total_value = Decimal("0")
    for h in holdings:
        total_value += d(h.get("value_usd") or 0)

    if total_value <= 0:
        return {"ok": False, "error": "empty_portfolio"}

    asset_returns: dict[str, list[float]] = {}
    weighted_returns: list[float] = []

    for h in holdings:
        symbol = str(h.get("symbol") or "UNKNOWN")
        value = d(h.get("value_usd") or 0)
        if value <= 0:
            continue
        beta = float(h.get("btc_beta") or 1.0)
        series = proxy_asset_returns(beta=beta, lookback_days=lookback_days)
        asset_returns[symbol] = series
        weight = float(value / total_value)
        if not weighted_returns:
            weighted_returns = [r * weight for r in series]
        else:
            weighted_returns = [a + r * weight for a, r in zip(weighted_returns, series)]

    return {
        "ok": True,
        "total_value_usd": money(total_value),
        "holdings_count": len(holdings),
        "lookback_days": lookback_days,
        "weighted_returns": weighted_returns,
        "asset_returns": asset_returns,
        "symbols": list(asset_returns.keys()),
    }
