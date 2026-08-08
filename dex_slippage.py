"""
BLACKDARK — DEX slippage simulation (AMM + liquidity impact).
"""

from __future__ import annotations

from typing import Any


def constant_product_slippage_bps(
    *,
    amount_usd: float,
    liquidity_usd: float,
    fee_bps: float = 30.0,
) -> float:
    """
    x*y=k impact estimate: impact ≈ amount / (2 * liquidity) for small trades.
    Returns total slippage + pool fee in bps.
    """
    if liquidity_usd <= 0 or amount_usd <= 0:
        return 9999.0
    impact_bps = (amount_usd / (2.0 * liquidity_usd)) * 10_000
    return max(0.0, impact_bps + fee_bps)


def simulate_amm_swap(
    *,
    amount_in_usd: float,
    price: float,
    liquidity_usd: float,
    pool_fee_bps: float = 30.0,
) -> dict[str, Any] | None:
    """Simulate swap; None if liquidity insufficient (>25% of pool)."""
    if price <= 0 or liquidity_usd <= 0:
        return None
    if amount_in_usd > liquidity_usd * 0.25:
        return None

    slippage_bps = constant_product_slippage_bps(
        amount_usd=amount_in_usd,
        liquidity_usd=liquidity_usd,
        fee_bps=pool_fee_bps,
    )
    effective_price = price * (1 + slippage_bps / 10_000)
    amount_out_usd = amount_in_usd * (1 - slippage_bps / 10_000)

    return {
        "amount_in_usd": amount_in_usd,
        "amount_out_usd": amount_out_usd,
        "slippage_bps": round(slippage_bps, 2),
        "effective_price": effective_price,
        "executable": slippage_bps < 500,
    }


def dex_execution_feasibility(
    *,
    net_bps: float,
    slippage_bps: float,
    liquidity_usd: float,
    quote_usd: float,
    min_net_bps: float = 8.0,
) -> str:
    if slippage_bps >= 500 or liquidity_usd < quote_usd * 2:
        return "not_executable"
    if net_bps < min_net_bps:
        return "below_threshold"
    if net_bps >= 25 and slippage_bps <= 50:
        return "high"
    if net_bps >= 12:
        return "medium"
    return "partial"
