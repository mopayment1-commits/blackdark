"""
Arbitrage Scanner — Feature #112 (CEX ↔ DEX with mandatory Net Profit).

Product name: **Arbitrage Scanner** — NOT "استغلال".
Displays full waterfall: Gross Gap → Gas → Slippage → Trading Fees = Net Profit (#113).

Integrates #130 fee database via `net_profit_engine`.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.ArbitrageScanner")

_DISCLAIMER = (
    "Arbitrage Scanner shows cost-adjusted estimates only. Net profit requires complete "
    "fee, gas, and slippage data — incomplete rows are flagged, not hidden. "
    "Not financial advice. Execution requires infrastructure beyond informational scan."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _is_dex_venue(venue: str) -> bool:
    v = (venue or "").lower()
    return v not in {"binance", "okx", "bybit", "kraken", "coinbase", "kucoin", "gateio", "bitget", "mexc"}


def _chain_for_dex(dex_row: dict[str, Any]) -> str:
    chain = str(dex_row.get("chain") or "ethereum").lower()
    mapping = {
        "eth": "ethereum",
        "ethereum": "ethereum",
        "bsc": "bsc",
        "bnb": "bsc",
        "arbitrum": "arbitrum",
        "polygon": "polygon",
        "solana": "solana",
    }
    return mapping.get(chain, "ethereum")


async def _enrich_opportunity(opp: dict[str, Any], quote_usd: float) -> dict[str, Any]:
    from bd_platform.net_profit_engine import attach_net_profit, compute_net_profit_breakdown

    buy_venue = str(opp.get("buy_venue") or "binance")
    sell_venue = str(opp.get("sell_venue") or "okx")
    asset = str(opp.get("asset") or "BTC")
    buy_price = float(opp.get("buy_price") or 0)
    sell_price = float(opp.get("sell_price") or 0)
    if buy_price <= 0 or sell_price <= 0:
        return {**opp, "net_profit_complete": False}

    units = quote_usd / buy_price
    gross_revenue = units * sell_price
    gross_gap_usd = gross_revenue - quote_usd

    chain = "ethereum"
    if _is_dex_venue(buy_venue) or _is_dex_venue(sell_venue):
        chain = _chain_for_dex({"chain": opp.get("dex_chain")})

    breakdown = await compute_net_profit_breakdown(
        gross_gap_usd=gross_gap_usd,
        notional_usd=quote_usd,
        buy_exchange=buy_venue if not _is_dex_venue(buy_venue) else "binance",
        sell_exchange=sell_venue if not _is_dex_venue(sell_venue) else "binance",
        symbol=f"{asset}/USDT",
        chain=chain,
        dex_liquidity_usd=float(opp.get("dex_liquidity_usd") or 0) or None,
        include_withdrawal=_is_dex_venue(buy_venue) or _is_dex_venue(sell_venue),
    )

    row = attach_net_profit(dict(opp), breakdown)
    wf = breakdown.get("waterfall") or {}
    row["spread_bps"] = opp.get("spread_bps")
    row["gross_gap_usd"] = wf.get("gross_gap_usd")
    row["net_spread_bps"] = (
        round((float(wf["net_profit_usd"]) / quote_usd) * 10_000, 2)
        if breakdown.get("ok") and wf.get("net_profit_usd") is not None
        else None
    )
    row["scanner_headline"] = breakdown.get("headline")
    row["executable"] = bool(breakdown.get("ok") and float(wf.get("net_profit_usd") or 0) > 0)
    row["indicative"] = not breakdown.get("ok")
    return row


async def scan_arbitrage(
    *,
    quote_usd: float = 1000.0,
    kind: str = "cex_dex",
) -> dict[str, Any]:
    """
    Arbitrage Scanner — CEX↔DEX with mandatory net profit waterfall (#112 + #113).
    """
    t0 = time.perf_counter()
    from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities

    raw = await scan_cex_dex_opportunities(quote_usd=quote_usd)
    enriched = await asyncio.gather(*[_enrich_opportunity(opp, quote_usd) for opp in raw.get("opportunities") or []])

    enriched.sort(
        key=lambda x: float((x.get("net_profit_breakdown") or {}).get("waterfall", {}).get("net_profit_usd") or -1e9),
        reverse=True,
    )
    net_positive = [o for o in enriched if o.get("net_profit_complete") and float(o.get("net_profit_usd") or 0) > 0]

    return {
        "ok": True,
        "feature_id": 112,
        "surface": "arbitrage_scanner",
        "product_name": "Arbitrage Scanner",
        "kind": kind,
        "quote_usd": quote_usd,
        "count": len(enriched),
        "net_profitable_count": len(net_positive),
        "opportunities": enriched,
        "top": enriched[0] if enriched else None,
        "requires_net_profit": True,
        "integrated_features": [113, 130],
        "disclaimer": _DISCLAIMER,
        "data_sources": raw.get("data_sources"),
        "timestamp": _utcnow(),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
    }


async def arbitrage_scanner_status() -> dict[str, Any]:
    from bd_platform.net_profit_engine import fee_database_status

    fees = await fee_database_status()
    return {
        "ok": True,
        "scanner": "cex_dex",
        "net_profit_required": True,
        "fee_database": fees,
        "timestamp": _utcnow(),
    }
