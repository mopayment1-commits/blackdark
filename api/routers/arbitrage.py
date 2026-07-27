"""Arbitrage API router."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends

import config
from api.deps import optional_user, record_behavior, require_feature

router = APIRouter(prefix="/api/arbitrage", tags=["arbitrage"])


@router.get("/defi/scan")
async def arbitrage_defi_scan(quote_usd: float = 1000):
    from defi_arbitrage_engine import scan_all_defi_strategies

    return await scan_all_defi_strategies(quote_usd=quote_usd)


@router.get("/engine/status")
async def arbitrage_engine_status():
    from defi_arbitrage_engine import defi_engine_stats
    from fee_matrix import matrix_stats
    from flywheel_saturation_guard import flywheel_saturation_status
    from gas_oracle import oracle_stats
    from slippage_guard import guard_stats

    return {
        "cross_exchange": {"status": "live", "depth_walk": True, "fee_matrix": True},
        "triangular": {"status": "live", "depth_walk": True, "per_venue_fees": True},
        "defi": defi_engine_stats(),
        "gas_oracle": oracle_stats(),
        "fee_matrix": matrix_stats(),
        "slippage_guard": guard_stats(),
        "flywheel_saturation_guard": flywheel_saturation_status(),
    }


@router.get("/opportunities")
async def arbitrage_opportunities(
    quote_amount: float | None = None,
    live: bool = False,
    min_profit: float = 0.0,
    _user: dict | None = Depends(require_feature("arbitrage")),
):
    from arbitrage_service import process_arbitrage_alerts, scan_arbitrage_opportunities

    result = await scan_arbitrage_opportunities(
        quote_amount=quote_amount,
        prefer_live=live and not config.PRICE_FEED_WS_ONLY,
        force_rest=False,
        min_profit_usdt=min_profit,
    )
    alerts = await process_arbitrage_alerts(result)
    result["alerts_triggered"] = alerts
    return result


@router.post("/scan")
async def arbitrage_scan(
    background_tasks: BackgroundTasks,
    quote_amount: float | None = None,
    user: dict | None = Depends(require_feature("arbitrage")),
):
    from arbitrage_service import process_arbitrage_alerts, scan_arbitrage_opportunities

    result = await scan_arbitrage_opportunities(
        quote_amount=quote_amount,
        prefer_live=not config.PRICE_FEED_WS_ONLY,
        force_rest=not config.PRICE_FEED_WS_ONLY,
    )
    alerts = await process_arbitrage_alerts(result)
    result["alerts_triggered"] = alerts
    background_tasks.add_task(
        record_behavior,
        "arbitrage_scan",
        user=user,
        payload={
            "opportunity_count": len(result.get("opportunities") or []),
            "profitable_count": result.get("profitable_count"),
        },
    )
    try:
        from observability import increment_metric

        increment_metric("arbitrage_scans_total")
    except Exception:
        pass
    return result


@router.get("/compare/{symbol}")
async def arbitrage_compare(
    symbol: str,
    quote_amount: float | None = None,
    _user: dict | None = Depends(require_feature("arbitrage")),
):
    from arbitrage_service import compare_symbol_across_exchanges

    return await compare_symbol_across_exchanges(symbol, quote_amount=quote_amount)


@router.get("/feed-lag/{symbol}")
async def arbitrage_feed_lag(symbol: str):
    from arbitrage_service import compare_symbol_across_exchanges

    compare = await compare_symbol_across_exchanges(symbol)
    return compare.get("feed_lag") or {"opportunities": [], "symbol": symbol}


@router.get("/durations")
async def arbitrage_durations(limit: int = 20):
    from opportunity_tracker import export_state

    state = export_state()
    state["active"] = state.get("active", [])[:limit]
    return state


@router.get("/alerts")
async def arbitrage_alerts(limit: int = 20):
    from database import fetch_arbitrage_alert_log

    rows = await fetch_arbitrage_alert_log(limit=limit)
    return {
        "alerts": rows,
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
        "email_configured": bool(os.getenv("SMTP_HOST")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/catalog")
async def arbitrage_catalog(category: str | None = None, status: str | None = None):
    from arbitrage_catalog import get_catalog

    return get_catalog(category=category, status=status)


@router.get("/catalog/scan")
async def arbitrage_catalog_scan(
    quote_amount: float | None = None,
    min_score: float = 0.0,
    _user: dict | None = Depends(require_feature("arbitrage_catalog")),
):
    from arbitrage_catalog import scan_arbitrage_catalog

    return await scan_arbitrage_catalog(quote_amount=quote_amount, min_score=min_score)


@router.get("/pricing-errors/{symbol}")
async def arbitrage_pricing_errors(symbol: str):
    from arbitrage_service import compare_symbol_across_exchanges

    compare = await compare_symbol_across_exchanges(symbol)
    return compare.get("pricing_errors") or {"opportunities": [], "symbol": symbol}


@router.get("/saturation-guard")
async def api_flywheel_saturation_guard():
    from flywheel_saturation_guard import flywheel_saturation_status

    return flywheel_saturation_status()
