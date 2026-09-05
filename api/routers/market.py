"""Market overview API router."""

from __future__ import annotations

from datetime import UTC, datetime

import aiohttp
from fastapi import APIRouter, HTTPException, Query

import config
from market_context import (
    fetch_binance_market_overview,
    fetch_binance_market_overview_pack,
    fetch_cvvd_whale_context,
    parse_alert_metadata,
)

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/api/market", tags=["market"], responses=COMMON_ERROR_RESPONSES)

_ALLOWED_INTERVALS = {
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
}


def _sector_for_asset(asset: str) -> str:
    return config.SECTOR_MAP.get(asset.upper(), "Other")


@router.get("/overview")
async def market_overview():
    pack = await fetch_binance_market_overview_pack()
    assets = list(pack.get("assets") or [])
    sectors: dict[str, list] = {}
    for asset in assets:
        sector = asset.get("sector") or _sector_for_asset(asset["symbol"])
        sectors.setdefault(sector, []).append(asset)
    return {
        "assets": assets,
        "sectors": sectors,
        "tracked_count": len(config.EXTENDED_TRACKED_ASSETS),
        "resolved_count": len(assets),
        "top_gainers": sorted(assets, key=lambda x: x["change_24h"], reverse=True)[:3],
        "top_losers": sorted(assets, key=lambda x: x["change_24h"])[:3],
        "market_status": "active" if assets else "degraded",
        "data_source": pack.get("data_source") or "unavailable",
        "source_host": pack.get("source_host"),
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/open-interest")
async def market_open_interest():
    from market_intel import fetch_open_interest

    rows = await fetch_open_interest()
    return {
        "assets": rows,
        "count": len(rows),
        "data_source": "Binance Futures API",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/sectors")
async def market_sectors():
    try:
        pack = await fetch_binance_market_overview_pack()
    except Exception:
        pack = {"assets": [], "data_source": "unavailable", "source_host": None}
    assets = list(pack.get("assets") or [])
    try:
        whale_ctx = await fetch_cvvd_whale_context(refresh=False)
    except Exception:
        whale_ctx = {}
    sii_by_sector: dict[str, float] = {}
    for row in whale_ctx.get("sector_flows", []):
        meta = parse_alert_metadata(row)
        sector_name = str(row.get("sector") or "")
        if sector_name:
            sii_by_sector[sector_name] = float(meta.get("sii_score") or 0)

    sector_assets: dict[str, list] = {}
    for asset in assets:
        sector = asset.get("sector") or _sector_for_asset(asset["symbol"])
        sector_assets.setdefault(sector, []).append(asset)

    sectors_out = []
    for sector_name, sector_list in sector_assets.items():
        avg_change = sum(a["change_24h"] for a in sector_list) / len(sector_list)
        avg_score = sum(a["score"] for a in sector_list) / len(sector_list)
        if avg_change > 2 or sii_by_sector.get(sector_name, 0) > 25:
            heat_label = "Hot"
        elif avg_change < -2:
            heat_label = "Cool"
        else:
            heat_label = "Neutral"
        sectors_out.append(
            {
                "sector": sector_name,
                "sii_score": round(sii_by_sector.get(sector_name, 0.0), 2),
                "asset_count": len(sector_list),
                "avg_change_24h": round(avg_change, 2),
                "avg_opportunity_score": round(avg_score, 1),
                "heat_label": heat_label,
                "top_assets": sorted(sector_list, key=lambda x: x["score"], reverse=True)[:3],
            }
        )

    sectors_out.sort(key=lambda x: x["sii_score"], reverse=True)
    source = pack.get("data_source") or "unavailable"
    return {
        "sectors": sectors_out,
        "data_source": source,
        "source_host": pack.get("source_host"),
        "market_status": "active" if assets else "degraded",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/radar-narrative")
async def market_radar_narrative_api():
    from plan_audit import market_radar_narrative

    return await market_radar_narrative()


@router.get("/klines", responses=COMMON_ERROR_RESPONSES)
async def market_klines(
    symbol: str = Query("BTCUSDT", min_length=3, max_length=20),
    interval: str = Query("1h"),
    limit: int = Query(100, ge=1, le=500),
):
    """Server-side klines — unified OHLCV spine with Binance failover."""
    sym = "".join(ch for ch in symbol.upper() if ch.isalnum())
    if not sym.endswith("USDT"):
        sym = f"{sym}USDT"
    if not sym.isalnum() or len(sym) < 5 or len(sym) > 20:
        raise HTTPException(status_code=400, detail="Invalid symbol")
    if interval not in _ALLOWED_INTERVALS:
        raise HTTPException(status_code=400, detail="Invalid interval")

    from ohlcv_spine import fetch_ohlcv_candles

    pack = await fetch_ohlcv_candles(sym, interval=interval, limit=int(limit))
    candles = pack.get("candles") or []
    if candles:
        rows = [
            [
                int(c["t"]),
                str(c["o"]),
                str(c["h"]),
                str(c["l"]),
                str(c["c"]),
                str(c.get("v") or 0),
                int(c.get("n") or 0),
            ]
            for c in candles
        ]
        return {
            "symbol": sym,
            "interval": interval,
            "klines": rows,
            "source": pack.get("source") or "ohlcv_spine",
            "gaps_filled": pack.get("gaps_filled", 0),
            "timestamp": datetime.now(UTC).isoformat(),
        }

    safe_interval = interval
    safe_limit = int(limit)
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.binance.com/api/v3/klines",
                params={"symbol": sym, "interval": safe_interval, "limit": safe_limit},
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(status_code=502, detail="Upstream klines unavailable")
                rows = await resp.json()
    except HTTPException:
        raise
    except (aiohttp.ClientError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Klines fetch failed") from exc

    return {
        "symbol": sym,
        "interval": interval,
        "klines": rows if isinstance(rows, list) else [],
        "source": "binance",
        "timestamp": datetime.now(UTC).isoformat(),
    }
