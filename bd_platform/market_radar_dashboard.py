"""
Market Radar Dashboard — unified surface for #155, #140, #186, #142, #139.

Single entry point for Market Radar: price infrastructure, macro calendar,
event stream, liquidity health, and sentiment intelligence.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.MarketRadarDashboard")

_FEATURE_IDS = (155, 140, 186, 142, 139)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def build_market_radar_dashboard(
    asset: str = "BTC",
    *,
    focus_assets: list[str] | None = None,
    macro_limit: int = 10,
    event_limit: int = 20,
) -> dict[str, Any]:
    """Unified Market Radar dashboard — all intelligence modules in one response."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")
    assets = focus_assets or [sym, "ETH", "SOL"]

    from bd_platform.industry_event_monitor import get_event_feed, industry_event_monitor_status
    from bd_platform.liquidity_health_check import analyze_liquidity_health, liquidity_health_status
    from bd_platform.macro_events_engine import build_macro_events_calendar, macro_events_status
    from bd_platform.market_radar_infrastructure import (
        market_radar_infrastructure_status,
        monitor_multi_asset_prices,
    )
    from bd_platform.sentiment_intelligence import (
        analyze_asset_sentiment,
        sentiment_intelligence_status,
    )
    from bd_platform.premium_intelligence import (
        get_regional_premiums_dashboard,
        premium_intelligence_status,
    )

    prices_task = monitor_multi_asset_prices(assets, max_assets=min(len(assets), 10))
    macro_task = build_macro_events_calendar(limit=macro_limit)
    sentiment_task = analyze_asset_sentiment(sym)
    liquidity_task = analyze_liquidity_health(sym)
    premiums_task = asyncio.to_thread(get_regional_premiums_dashboard, sym)
    from bd_platform.signal_context_layer import build_context_panel, signal_context_layer_status
    from bd_platform.etf_intelligence import build_etf_intelligence_dashboard, etf_intelligence_status
    from bd_platform.cvd_intelligence import build_cvd_analysis, cvd_intelligence_status
    from bd_platform.global_liquidity_intelligence import (
        build_global_liquidity_dashboard,
        global_liquidity_status,
    )
    from bd_platform.macro_intelligence_hub import (
        build_macro_intelligence_hub,
        macro_intelligence_hub_status,
    )

    context_task = build_context_panel(sym, surface="market_radar")
    etf_task = asyncio.to_thread(build_etf_intelligence_dashboard, sym)
    cvd_task = asyncio.to_thread(build_cvd_analysis, sym)
    global_liq_task = asyncio.to_thread(build_global_liquidity_dashboard, sym)
    macro_hub_task = asyncio.to_thread(build_macro_intelligence_hub, sym, tier="pro")

    prices, macro, sentiment, liquidity, premiums, signal_context, etf_intelligence, cvd_intel, global_liquidity, macro_hub = await asyncio.gather(
        prices_task,
        macro_task,
        sentiment_task,
        liquidity_task,
        premiums_task,
        context_task,
        etf_task,
        cvd_task,
        global_liq_task,
        macro_hub_task,
        return_exceptions=True,
    )

    events = get_event_feed(limit=event_limit)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    def _safe(result: Any, fallback: dict[str, Any]) -> dict[str, Any]:
        if isinstance(result, Exception):
            logger.debug("dashboard module failed: %s", result)
            return {**fallback, "ok": False, "error": str(result)}
        return result

    prices_block = _safe(prices, {"feature_id": 155, "matrix": []})
    macro_block = _safe(macro, {"feature_id": 140, "events": []})
    sentiment_block = _safe(sentiment, {"feature_id": 139})
    liquidity_block = _safe(liquidity, {"feature_id": 142})
    premiums_block = _safe(premiums, {"feature_ids": [255, 233], "cards": []})
    signal_context_block = _safe(signal_context, {"feature_id": 330, "three_reasons": []})
    etf_block = _safe(etf_intelligence, {"feature_ids": [210, 240], "rolling_totals": {}})
    cvd_block = _safe(cvd_intel, {"feature_id": 232, "cvd_value_usd": 0})
    global_liq_block = _safe(global_liquidity, {"feature_id": 248, "composite_index": {}})
    macro_hub_block = _safe(macro_hub, {"feature_id": 263, "integrated_modules": []})

    sla_flags = [
        prices_block.get("sla_met", True),
        macro_block.get("sla_met", True),
        sentiment_block.get("sla_met", True),
        liquidity_block.get("sla_met", True),
        premiums_block.get("sla_met", True),
        signal_context_block.get("sla_met", True),
        etf_block.get("ok", True),
        cvd_block.get("ok", True),
        global_liq_block.get("ok", True),
        macro_hub_block.get("ok", True),
    ]

    return {
        "ok": True,
        "surface": "market_radar_dashboard",
        "feature_ids": list(_FEATURE_IDS) + [255, 233, 330, 210, 240, 232, 248, 263],
        "focus_asset": sym,
        "headline": (
            f"Market Radar — {sym}: "
            f"{prices_block.get('assets_with_data', 0)} assets tracked | "
            f"{macro_block.get('high_impact_count', 0)} macro events | "
            f"{events.get('count', 0)} industry events"
        ),
        "prices": prices_block,
        "macro_events": macro_block,
        "event_stream": events,
        "liquidity_health": liquidity_block,
        "sentiment": sentiment_block,
        "regional_premiums": premiums_block,
        "signal_context": signal_context_block,
        "etf_intelligence": etf_block,
        "cvd_intelligence": cvd_block,
        "global_liquidity": global_liq_block,
        "macro_intelligence_hub": macro_hub_block,
        "status": {
            "infrastructure": market_radar_infrastructure_status(),
            "macro": macro_events_status(),
            "events": industry_event_monitor_status(),
            "liquidity": liquidity_health_status(),
            "sentiment": sentiment_intelligence_status(),
            "premium_intelligence": premium_intelligence_status(),
            "signal_context_layer": signal_context_layer_status(),
            "etf_intelligence": etf_intelligence_status(),
            "cvd_intelligence": cvd_intelligence_status(),
            "global_liquidity": global_liquidity_status(),
            "macro_intelligence_hub": macro_intelligence_hub_status(),
        },
        "integrated_features": [
            "#125", "#133", "#137", "#139", "#140", "#142", "#149", "#155", "#186",
            "#210", "#232", "#233", "#240", "#248", "#255", "#263", "#330",
        ],
        "sla_met": elapsed_ms <= 2000 and all(sla_flags),
        "latency_ms": round(elapsed_ms, 1),
        "timestamp": _utcnow(),
    }


def market_radar_dashboard_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "market_radar_dashboard",
        "modules": {
            "155": "price_infrastructure",
            "140": "macro_events_calendar",
            "186": "industry_event_stream",
            "142": "liquidity_health_check",
            "139": "sentiment_intelligence",
            "233": "coinbase_premium",
            "255": "korea_premium",
            "330": "signal_context_layer",
            "210": "etf_intelligence",
            "240": "etf_intelligence",
            "232": "cvd_intelligence",
            "248": "global_liquidity_intelligence",
            "263": "macro_intelligence_hub",
        },
        "endpoint": "/api/platform/market-radar/dashboard",
        "timestamp": _utcnow(),
    }
