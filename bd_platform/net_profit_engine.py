"""
Net Profit Engine — Features #113 + #130 (foundational layer).

Every profit/opportunity display MUST flow through this breakdown:
  Gross Gap → minus Gas → minus Slippage → minus Trading Fees → minus Withdrawal = Net Profit

Uses internal fee database (`fee_matrix`) + gas oracle + slippage models.
Fail-closed when fee cells are unknown — never invent optimistic zeros.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.NetProfitEngine")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _symbol_base(symbol: str) -> str:
    s = symbol.upper().strip().replace("/", "")
    if s.endswith("USDT"):
        return s[:-4]
    return s.split("/")[0]


async def compute_net_profit_breakdown(
    *,
    gross_gap_usd: float,
    notional_usd: float,
    buy_exchange: str,
    sell_exchange: str,
    symbol: str = "BTC/USDT",
    chain: str = "ethereum",
    slippage_bps: float | None = None,
    dex_liquidity_usd: float | None = None,
    include_withdrawal: bool = True,
    include_deposit: bool = False,
) -> dict[str, Any]:
    """
    Full cost waterfall for any arbitrage/opportunity surface (#113).
    """
    t0 = time.perf_counter()
    from fee_matrix import (
        deposit_fee_usdt,
        matrix_stats,
        taker_fee,
        trading_fees_usdt,
        withdrawal_fee_usdt,
    )

    base = _symbol_base(symbol)
    pair = f"{base}/USDT"

    buy_taker = taker_fee(buy_exchange)
    sell_taker = taker_fee(sell_exchange)
    buy_fee_usd = trading_fees_usdt(buy_exchange, notional_usd) if buy_taker is not None else None
    sell_fee_usd = trading_fees_usdt(sell_exchange, notional_usd) if sell_taker is not None else None

    trading_fees_total: float | None = None
    if buy_fee_usd is not None and sell_fee_usd is not None:
        trading_fees_total = buy_fee_usd + sell_fee_usd

    withdrawal_usd: float | None = None
    deposit_usd: float | None = None
    if include_withdrawal and buy_exchange.lower() != sell_exchange.lower():
        withdrawal_usd = withdrawal_fee_usdt(sell_exchange, pair)
    if include_deposit:
        deposit_usd = deposit_fee_usdt(buy_exchange, pair)

    # Slippage — explicit bps or estimate from DEX liquidity
    slip_bps = slippage_bps
    slippage_usd: float | None = None
    if slip_bps is not None:
        slippage_usd = notional_usd * (float(slip_bps) / 10_000.0)
    elif dex_liquidity_usd and dex_liquidity_usd > 0:
        from dex_slippage import constant_product_slippage_bps

        slip_bps = constant_product_slippage_bps(
            amount_usd=notional_usd, liquidity_usd=float(dex_liquidity_usd)
        )
        slippage_usd = notional_usd * (slip_bps / 10_000.0)

    gas_usd: float | None = None
    gas_bps: float | None = None
    try:
        from gas_oracle import gas_cost_bps

        gas_bps = await gas_cost_bps(chain, notional_usd, hops=1)
        if gas_bps is not None:
            gas_usd = notional_usd * (gas_bps / 10_000.0)
    except Exception:
        logger.debug("gas oracle unavailable", exc_info=True)

    missing: list[str] = []
    if trading_fees_total is None:
        missing.append("trading_fees")
    if slippage_usd is None:
        missing.append("slippage")
    if gas_usd is None:
        missing.append("gas")
    if include_withdrawal and buy_exchange.lower() != sell_exchange.lower() and withdrawal_usd is None:
        missing.append("withdrawal_fee")

    net_profit_usd: float | None = None
    complete = not missing
    if complete:
        total_costs = (trading_fees_total or 0) + (slippage_usd or 0) + (gas_usd or 0)
        if withdrawal_usd is not None:
            total_costs += withdrawal_usd
        if deposit_usd is not None:
            total_costs += deposit_usd
        net_profit_usd = gross_gap_usd - total_costs

    return {
        "ok": complete,
        "feature_ids": [113, 130],
        "surface": "net_profit_engine",
        "timestamp": _utcnow(),
        "symbol": pair,
        "notional_usd": round(notional_usd, 2),
        "waterfall": {
            "gross_gap_usd": round(gross_gap_usd, 4),
            "trading_fees_usd": round(trading_fees_total, 4) if trading_fees_total is not None else None,
            "slippage_usd": round(slippage_usd, 4) if slippage_usd is not None else None,
            "slippage_bps": round(slip_bps, 2) if slip_bps is not None else None,
            "gas_usd": round(gas_usd, 4) if gas_usd is not None else None,
            "gas_bps": round(gas_bps, 2) if gas_bps is not None else None,
            "withdrawal_fee_usd": round(withdrawal_usd, 4) if withdrawal_usd is not None else None,
            "deposit_fee_usd": round(deposit_usd, 4) if deposit_usd is not None else None,
            "net_profit_usd": round(net_profit_usd, 4) if net_profit_usd is not None else None,
        },
        "fee_detail": {
            "buy_exchange": buy_exchange,
            "sell_exchange": sell_exchange,
            "buy_taker_rate": buy_taker,
            "sell_taker_rate": sell_taker,
            "buy_fee_usd": round(buy_fee_usd, 4) if buy_fee_usd is not None else None,
            "sell_fee_usd": round(sell_fee_usd, 4) if sell_fee_usd is not None else None,
            "chain": chain,
            "fee_matrix": matrix_stats(),
        },
        "missing_fields": missing,
        "headline": _headline(gross_gap_usd, net_profit_usd, missing),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }


def _headline(gross: float, net: float | None, missing: list[str]) -> str:
    if missing:
        return f"Gross gap ${gross:.2f} — net profit incomplete (missing: {', '.join(missing)})"
    if net is None:
        return f"Gross gap ${gross:.2f} — net profit unavailable"
    if net <= 0:
        return f"Gross gap ${gross:.2f} → Net ${net:.2f} after all costs (not profitable)"
    return f"Gross gap ${gross:.2f} → Net ${net:.2f} after gas, slippage, and fees"


def attach_net_profit(payload: dict[str, Any], breakdown: dict[str, Any]) -> dict[str, Any]:
    """Attach net profit layer to any opportunity payload (#113 requirement)."""
    out = dict(payload)
    out["net_profit_breakdown"] = breakdown
    wf = breakdown.get("waterfall") or {}
    out["gross_gap_usd"] = wf.get("gross_gap_usd")
    out["net_profit_usd"] = wf.get("net_profit_usd")
    out["net_profit_complete"] = breakdown.get("ok", False)
    if breakdown.get("ok"):
        out["profitable"] = float(wf.get("net_profit_usd") or 0) > 0
    return out


async def fee_database_status() -> dict[str, Any]:
    """#130 — trading fee identification surface."""
    from fee_matrix import matrix_stats

    stats = matrix_stats()
    return {
        "ok": True,
        "feature_id": 130,
        "surface": "trading_fee_database",
        "exchanges_tracked": stats.get("exchanges", 0),
        "refresh_interval_sec": stats.get("refresh_interval_sec"),
        "last_refresh": stats.get("last_refresh"),
        "sample": stats.get("sample"),
        "includes": ["taker", "maker", "withdrawal", "deposit", "gas_oracle"],
        "timestamp": _utcnow(),
    }
