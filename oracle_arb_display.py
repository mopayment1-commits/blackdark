"""Read-only cross-exchange arb snippets for Oracle / Trust Pulse (paid)."""

from __future__ import annotations

import logging
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.OracleArb")

MAX_OPPORTUNITIES = 5

_EXCHANGE_TRADE_URL: dict[str, str] = {
    "binance": "https://www.binance.com/en/trade/{asset}_USDT?type=spot",
    "okx": "https://www.okx.com/trade-spot/{asset_lower}-usdt",
    "bybit": "https://www.bybit.com/en/trade/spot/{asset}/USDT",
    "kucoin": "https://www.kucoin.com/trade/{asset}-USDT",
    "gate": "https://www.gate.io/trade/{asset}_USDT",
    "mexc": "https://www.mexc.com/exchange/{asset}_USDT",
    "bitget": "https://www.bitget.com/spot/{asset}USDT",
    "htx": "https://www.htx.com/trade/{asset_lower}_usdt",
    "huobi": "https://www.htx.com/trade/{asset_lower}_usdt",
}


def _trade_url(exchange_id: str, asset: str) -> str:
    key = (exchange_id or "").strip().lower()
    template = _EXCHANGE_TRADE_URL.get(key) or "https://www.google.com/search?q={exchange}+{asset}+USDT+spot"
    asset_u = asset.upper()
    return template.format(
        asset=asset_u,
        asset_lower=asset_u.lower(),
        exchange=key,
    )


def _simple_from_cross(row: dict[str, Any], asset: str) -> dict[str, Any]:
    buy = str(row.get("buy_exchange") or "")
    sell = str(row.get("sell_exchange") or "")
    pct = float(row.get("net_profit_percent") or 0)
    if row.get("gross_spread_bps") is not None:
        pct = max(pct, float(row["gross_spread_bps"]) / 100.0)
    return {
        "exchange_1": buy,
        "exchange_2": sell,
        "price_diff_percent": round(pct, 4),
        "link_exchange_1": _trade_url(buy, asset),
        "link_exchange_2": _trade_url(sell, asset),
        "note": "Buy lower / sell higher — display only, no platform execution",
    }


def _pairwise_from_compare(compare: dict[str, Any], asset: str, limit: int) -> list[dict[str, Any]]:
    venues = list(compare.get("venues") or [])
    pairs: list[dict[str, Any]] = []
    for i, a in enumerate(venues):
        for b in venues[i + 1 :]:
            ex_a = str(a.get("exchange") or "")
            ex_b = str(b.get("exchange") or "")
            ask_a = float(a.get("best_ask") or 0)
            bid_b = float(b.get("best_bid") or 0)
            if ask_a <= 0:
                continue
            diff = (bid_b - ask_a) / ask_a * 100.0
            if diff <= 0:
                ask_b = float(b.get("best_ask") or 0)
                bid_a = float(a.get("best_bid") or 0)
                if ask_b > 0:
                    diff_rev = (bid_a - ask_b) / ask_b * 100.0
                    if diff_rev > diff:
                        diff = diff_rev
                        ex_a, ex_b = ex_b, ex_a
            if diff <= 0:
                continue
            pairs.append(
                {
                    "exchange_1": ex_a,
                    "exchange_2": ex_b,
                    "price_diff_percent": round(diff, 4),
                    "link_exchange_1": _trade_url(ex_a, asset),
                    "link_exchange_2": _trade_url(ex_b, asset),
                    "note": "Cross-venue quote spread — display only",
                }
            )
    pairs.sort(key=lambda x: float(x["price_diff_percent"]), reverse=True)
    return pairs[:limit]


async def fetch_display_arb_opportunities(symbol: str, *, limit: int = MAX_OPPORTUNITIES) -> dict[str, Any]:
    """Up to 5 read-only arb rows for one asset."""
    cleaned = (symbol or "BTC").upper().replace("/", "").replace("-", "")
    asset = cleaned.removesuffix("USDT") or "BTC"
    limit = max(1, min(int(limit), MAX_OPPORTUNITIES))

    from arbitrage_service import compare_symbol_across_exchanges, scan_arbitrage_opportunities

    rows: list[dict[str, Any]] = []
    try:
        scan = await scan_arbitrage_opportunities(
            prefer_live=not getattr(config, "PRICE_FEED_WS_ONLY", False),
            force_rest=False,
        )
        for item in scan.get("opportunities") or []:
            if str(item.get("kind") or "") != "cross_exchange":
                continue
            if str(item.get("asset") or "").upper() != asset:
                continue
            rows.append(_simple_from_cross(item, asset))
            if len(rows) >= limit:
                break
    except Exception:
        logger.exception("Oracle arb scan slice failed asset=%s", asset)

    if len(rows) < limit:
        try:
            compare = await compare_symbol_across_exchanges(asset)
            extra = _pairwise_from_compare(compare, asset, limit - len(rows))
            seen = {(r["exchange_1"], r["exchange_2"]) for r in rows}
            for e in extra:
                key = (e["exchange_1"], e["exchange_2"])
                if key in seen:
                    continue
                rows.append(e)
                seen.add(key)
                if len(rows) >= limit:
                    break
        except Exception:
            logger.exception("Oracle arb compare failed asset=%s", asset)

    return {
        "asset": asset,
        "symbol": f"{asset}/USDT",
        "opportunities": rows[:limit],
        "max_shown": MAX_OPPORTUNITIES,
        "display_only": True,
        "disclaimer": "Research display only — no auto-trade or execution on BLACKDARK.",
    }


_LEDGER_ARB_ASSETS = ("BTC", "ETH", "SOL", "BNB", "XRP")


async def fetch_public_ledger_arb_opportunities(
    *,
    per_asset: int = 2,
    total_limit: int = 8,
) -> dict[str, Any]:
    """Aggregate read-only spreads for the public /oracle-accuracy ledger."""
    per_asset = max(1, min(int(per_asset), MAX_OPPORTUNITIES))
    total_limit = max(1, min(int(total_limit), 12))
    combined: list[dict[str, Any]] = []
    for asset in _LEDGER_ARB_ASSETS:
        try:
            blob = await fetch_display_arb_opportunities(asset, limit=per_asset)
        except Exception:
            logger.debug("public ledger arb slice failed asset=%s", asset, exc_info=True)
            continue
        for row in blob.get("opportunities") or []:
            combined.append({**row, "asset": asset, "symbol": f"{asset}/USDT"})
    combined.sort(key=lambda r: float(r.get("price_diff_percent") or 0), reverse=True)
    opportunities = combined[:total_limit]
    return {
        "opportunities": opportunities,
        "count": len(opportunities),
        "display_only": True,
        "disclaimer": "Research display only — no auto-trade or execution on BLACKDARK.",
    }
