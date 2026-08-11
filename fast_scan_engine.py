"""
BLACKDARK — Millisecond fast-scan path (Buyer Requirement #2).

Reads ONLY from in-memory live_book_hub — target <50ms warm, <5ms book read.
"""

from __future__ import annotations

import time
from typing import Any

import config
from live_book_hub import get_best_price, hub_stats


def _cross_exchange_spread(asset: str) -> dict[str, Any] | None:
    symbol = f"{asset}/USDT" if not asset.endswith("/USDT") else asset
    base = symbol.replace("/USDT", "")
    prices: dict[str, dict[str, float]] = {}

    for exchange in ("binance", "okx", "bybit", "kraken"):
        row = get_best_price(exchange, f"{base}/USDT")
        if row and row.get("bid") and row.get("ask"):
            prices[exchange] = {"bid": float(row["bid"]), "ask": float(row["ask"]), "mid": float(row["mid"])}

    if len(prices) < 2:
        return None

    best_bid_ex = max(prices, key=lambda e: prices[e]["bid"])
    best_ask_ex = min(prices, key=lambda e: prices[e]["ask"])
    if best_bid_ex == best_ask_ex:
        return None

    buy_ask = prices[best_ask_ex]["ask"]
    sell_bid = prices[best_bid_ex]["bid"]
    if sell_bid <= buy_ask:
        return None

    spread_bps = ((sell_bid - buy_ask) / buy_ask) * 10_000
    # Fee authority: fee_matrix only. Unknown venue fees → omit net claim (fail-closed).
    from fee_matrix import taker_fee as _venue_taker

    buy_rate = _venue_taker(best_ask_ex)
    sell_rate = _venue_taker(best_bid_ex)
    fee_bps = None
    net_bps = None
    if buy_rate is not None and sell_rate is not None:
        fee_bps = (buy_rate + sell_rate) * 10_000
        net_bps = spread_bps - fee_bps

    # Top-of-book only — NEVER claim profitable/executable without depth rewalk.
    from executable_edge_truth import mark_indicative_only

    payload = {
        "asset": base,
        "buy_exchange": best_ask_ex,
        "sell_exchange": best_bid_ex,
        "buy_price": buy_ask,
        "sell_price": sell_bid,
        "spread_bps": round(spread_bps, 2),
        "kind": "fast_cross",
    }
    if fee_bps is not None and net_bps is not None:
        payload["fee_bps"] = round(fee_bps, 2)
        payload["net_spread_bps"] = round(net_bps, 2)
        payload["topline_positive"] = net_bps > 0
    else:
        payload["fee_bps"] = None
        payload["net_spread_bps"] = None
        payload["topline_positive"] = False
        payload["fee_unknown"] = True

    return mark_indicative_only(
        payload,
        reason="top_of_book_only_no_depth",
    )


def run_fast_scan(*, quote_usd: float = 100.0) -> dict[str, Any]:
    """Sub-second scan using in-memory books only."""
    t0 = time.perf_counter()
    t_book = time.perf_counter()

    assets = list(getattr(config, "WHITELIST_ASSETS", ("BTC", "ETH", "SOL")))[:15]
    opportunities: list[dict[str, Any]] = []

    for asset in assets:
        opp = _cross_exchange_spread(asset)
        if opp and opp.get("topline_positive"):
            net_usdt = quote_usd * (float(opp.get("net_spread_bps") or 0) / 10_000)
            opportunities.append(
                {
                    **opp,
                    "indicative_net_profit_usdt": round(net_usdt, 4),
                    "net_profit_usdt": None,
                    "kind": "fast_cross",
                }
            )

    book_read_ms = (time.perf_counter() - t_book) * 1000
    total_ms = (time.perf_counter() - t0) * 1000

    if total_ms < 50:
        latency_tier = "millisecond"
    elif total_ms < 500:
        latency_tier = "sub_second"
    else:
        latency_tier = "slow"

    return {
        "engine": "fast_scan_in_memory",
        "latency_ms": round(total_ms, 3),
        "book_read_ms": round(book_read_ms, 3),
        "latency_tier": latency_tier,
        "opportunities": sorted(
            opportunities,
            key=lambda x: float(x.get("net_profit_usdt") or 0),
            reverse=True,
        ),
        "books": hub_stats(),
        "assets_scanned": len(assets),
        "ws_required": hub_stats().get("symbol_count", 0) == 0,
        "note": (
            "Start dashboard with EXCHANGE_WS_ENABLED=true for live bookTicker feeds."
            if hub_stats().get("symbol_count", 0) == 0
            else None
        ),
    }
