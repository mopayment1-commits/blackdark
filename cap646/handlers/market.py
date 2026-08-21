"""Market data capabilities — T04 and related."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer, reject_if_stale
from cap646.data_spine import freshness_assurance_report, normalization_report
from data_freshness import attach_oracle_freshness


async def handle_market_capability(
    capability_id: int,
    *,
    params: dict[str, Any],
) -> dict[str, Any]:
    symbol = str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")

    if capability_id == 47:
        from market_context import fetch_binance_market_overview_pack, probe_price_sources

        pack = await fetch_binance_market_overview_pack(limit=int(params.get("limit") or 20))
        probe = await probe_price_sources(symbol)
        payload = attach_oracle_freshness(
            {
                "capability_id": 47,
                "surface": "spot_market_metrics_suite",
                "overview": pack,
                "probe": probe,
                "success": bool(pack),
            }
        )
        ok, payload = reject_if_stale(payload)
        return ai_compliance_footer(payload)

    if capability_id in {267, 483, 508, 509, 510, 537, 538}:
        from live_book_hub import get_top_of_book, hub_stats

        book = get_top_of_book(f"{symbol}USDT")
        depth_level = {508: "L1", 509: "L2", 510: "L3"}.get(capability_id, "standard")
        payload = attach_oracle_freshness(
            {
                "capability_id": capability_id,
                "surface": "order_book_depth",
                "depth_level": depth_level,
                "book": book,
                "hub_stats": hub_stats(),
                "success": bool(book),
            }
        )
        ok, payload = reject_if_stale(payload)
        return ai_compliance_footer(payload)

    if capability_id in {330, 331, 332}:
        from market_context import probe_price_sources

        probe = await probe_price_sources(symbol)
        return ai_compliance_footer(
            {"capability_id": capability_id, "surface": "reference_rates", "probe": probe, "success": bool(probe)}
        )

    if capability_id in {129, 175}:
        from sentiment_engine import build_sentiment_context_safe
        from sentiment_gate import fetch_asset_sentiment

        ctx = await build_sentiment_context_safe(symbol)
        gate = await fetch_asset_sentiment(symbol)
        return ai_compliance_footer(
            {"capability_id": capability_id, "surface": "sentiment_intelligence", "context": ctx, "gate": gate, "success": True}
        )

    if capability_id == 356:
        from bd_platform.free_market_data import binance_futures_snapshot
        from perp_dex_fetcher import fetch_perp_dex_market

        cex = await binance_futures_snapshot(symbol)
        dex = await fetch_perp_dex_market(symbol)
        return ai_compliance_footer(
            {"capability_id": 356, "surface": "dex_volume", "cex": cex, "dex": dex, "success": bool(cex or dex)}
        )

    if capability_id == 507:
        from market_context import fetch_binance_klines

        closes = await fetch_binance_klines(f"{symbol}USDT", interval=str(params.get("interval") or "1h"), limit=100)
        ohlcv = [{"close": c} for c in closes] if closes else []
        return ai_compliance_footer(
            {"capability_id": 507, "surface": "ohlcv", "symbol": symbol, "bars": len(ohlcv), "ohlcv": ohlcv[-10:], "success": bool(ohlcv)}
        )

    if capability_id in {630, 500}:
        fn = freshness_assurance_report if capability_id == 630 else normalization_report
        return await fn(symbol=symbol)

    # Generic market handler
    from market_context import probe_price_sources

    probe = await probe_price_sources(symbol)
    payload = attach_oracle_freshness(
        {"capability_id": capability_id, "surface": "market_data", "probe": probe, "success": bool(probe)}
    )
    return ai_compliance_footer(payload)
