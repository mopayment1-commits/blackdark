"""CAP646 runtime fallbacks — seed live surfaces when WS/Redis paths are cold."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer


async def seed_live_book_from_ticker(symbol: str) -> dict[str, Any] | None:
    """Seed live_book_hub from Binance ticker when WS books are empty."""
    from live_book_hub import get_top_of_book, update_top_of_book
    from market_context import fetch_binance_ticker, normalize_oracle_symbol

    asset, pair = normalize_oracle_symbol(symbol)
    sym = f"{asset}/USDT"
    existing = get_top_of_book("binance", sym) or get_top_of_book(f"{asset}USDT")
    if existing:
        return existing

    ticker = await fetch_binance_ticker(pair)
    price = float((ticker or {}).get("price") or 0)
    if price <= 0:
        return None

    spread_bps = 1.0
    half = price * (spread_bps / 10_000.0) / 2.0
    update_top_of_book(
        "binance",
        sym,
        bid=price - half,
        bid_qty=1.0,
        ask=price + half,
        ask_qty=1.0,
        market_type="spot",
    )
    return get_top_of_book("binance", sym)


async def resolve_order_book(symbol: str) -> dict[str, Any] | None:
    from live_book_hub import get_top_of_book

    book = get_top_of_book(f"{symbol}USDT") or get_top_of_book("binance", f"{symbol}/USDT")
    if book:
        return book
    return await seed_live_book_from_ticker(symbol)


async def resolve_ohlcv_closes(
    symbol: str,
    *,
    interval: str = "1h",
    limit: int = 100,
) -> tuple[list[float], str]:
    from market_context import fetch_binance_klines, fetch_binance_ticker, normalize_oracle_symbol

    asset, pair = normalize_oracle_symbol(symbol)
    closes = await fetch_binance_klines(f"{asset}USDT", interval=interval, limit=limit)
    if closes:
        return closes, "binance_klines"
    ticker = await fetch_binance_ticker(pair)
    price = float((ticker or {}).get("price") or 0)
    if price > 0:
        return [price] * min(limit, 20), "ticker_shadow_bar"
    return [], "none"


async def resolve_dex_volume_snapshot(symbol: str) -> dict[str, Any]:
    from bd_platform.free_market_data import binance_futures_snapshot
    from market_context import fetch_binance_ticker, normalize_oracle_symbol
    from perp_dex_fetcher import PERP_DEX_VENUES, fetch_perp_dex_market

    asset, pair = normalize_oracle_symbol(symbol)
    cex = await binance_futures_snapshot(asset)
    if not cex.get("available"):
        spot = await fetch_binance_ticker(pair)
        if spot:
            cex = {
                "source": "binance_spot_fallback",
                "asset": asset,
                "symbol": f"{asset}USDT",
                "mark_price": float(spot.get("price") or 0),
                "available": True,
            }

    dex_quotes: list[dict[str, Any]] = []
    for venue in sorted(PERP_DEX_VENUES)[:3]:
        try:
            ticker, _book = await fetch_perp_dex_market(None, pair, "perpetual", exchange_id=venue)
            dex_quotes.append({"exchange": venue, "price": ticker.price, "symbol": pair})
        except Exception as exc:
            dex_quotes.append({"exchange": venue, "error": str(exc)})

    ok_quotes = [q for q in dex_quotes if q.get("price")]
    return {
        "cex": cex,
        "dex_quotes": dex_quotes,
        "dex": ok_quotes[0] if ok_quotes else None,
        "success": bool(cex.get("available") or ok_quotes),
    }


async def resolve_gas_usd(chain: str = "ethereum") -> dict[str, Any]:
    from gas_oracle import get_swap_gas_usd, refresh_gas_cache

    await seed_live_book_from_ticker("ETH")
    await refresh_gas_cache(chains=(chain, "ethereum", "bsc", "solana"))
    gas = await get_swap_gas_usd(chain)
    if gas is not None:
        return {"gas_usd": gas, "source": "live_oracle", "success": True}

    return {
        "gas_usd": None,
        "source": "unknown_fail_closed",
        "success": False,
        "note": "Live gas/native USD unavailable — executable DeFi paths remain blocked",
    }


def success_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return ai_compliance_footer({**payload, "success": True})
