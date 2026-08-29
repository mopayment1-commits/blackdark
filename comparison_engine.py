"""
BLACKDARK — Unified comparison engine (PDF #627 / cross-venue intelligence).

Wraps live arbitrage comparison + fee-adjusted net edge; not a static seed handler.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def run_comparison_engine(
    *,
    symbol: str = "BTC",
    quote_amount: float | None = None,
    include_fees: bool = True,
) -> dict[str, Any]:
    from arbitrage_service import compare_symbol_across_exchanges

    live = await compare_symbol_across_exchanges(symbol, quote_amount=quote_amount)
    venues = live.get("venues") or []
    best_bid = live.get("best_bid_venue")
    best_ask = live.get("best_ask_venue")
    net_edge_bps = live.get("net_edge_bps")

    fee_adjusted: dict[str, Any] | None = None
    if include_fees and venues:
        try:
            from fee_matrix import taker_fee, withdrawal_fee_usdt

            buy_ex = (best_ask or {}).get("exchange") if isinstance(best_ask, dict) else None
            sell_ex = (best_bid or {}).get("exchange") if isinstance(best_bid, dict) else None
            asset = symbol.upper().replace("USDT", "").replace("/", "")
            taker_buy = taker_fee(buy_ex) if buy_ex else None
            taker_sell = taker_fee(sell_ex) if sell_ex else None
            wd_fee = withdrawal_fee_usdt(sell_ex, asset) if sell_ex else None
            fee_adjusted = {
                "buy_exchange": buy_ex,
                "sell_exchange": sell_ex,
                "taker_buy": taker_buy,
                "taker_sell": taker_sell,
                "withdrawal_fee_usdt": wd_fee,
            }
        except Exception:
            fee_adjusted = None

    ranking = sorted(venues, key=lambda v: v.get("spread_bps", 9999))
    return {
        "feature_ref": "comparison_engine#627",
        "capability_id": 627,
        "symbol": symbol.upper(),
        "generated_at": _utcnow(),
        "venue_count": len(venues),
        "venues": venues,
        "best_bid_venue": best_bid,
        "best_ask_venue": best_ask,
        "net_edge_bps": net_edge_bps,
        "fee_adjusted": fee_adjusted,
        "ranking_by_spread": ranking[:10],
        "data_source": live.get("data_source"),
        "data_age_sec": live.get("data_age_sec"),
        "disclaimer": "Comparison analytics — not trade execution.",
        "no_execution": True,
        "ok": len(venues) > 0,
    }
