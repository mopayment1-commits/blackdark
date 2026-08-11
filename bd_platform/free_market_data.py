"""Free public market data — Binance Futures + CoinGecko (no paid API keys)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp

logger = logging.getLogger("BLACKDARK.FreeMarketData")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _get_json(url: str, *, params: dict | None = None) -> Any:
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url, params=params) as resp:
        if resp.status != 200:
            return None
        return await resp.json()


async def binance_futures_snapshot(asset: str = "BTC") -> dict[str, Any]:
    """Funding, mark price, OI, long/short ratio from Binance public REST."""
    symbol = f"{asset.upper()}USDT"
    if not symbol.isalnum():
        return {
            "source": "binance_futures_public",
            "asset": asset.upper(),
            "symbol": symbol,
            "timestamp": _utcnow(),
            "mark_price": 0.0,
            "funding_rate": 0.0,
            "funding_rate_pct": 0.0,
            "open_interest_contracts": 0.0,
            "open_interest_usd": 0.0,
            "change_24h_pct": 0.0,
            "long_short_ratio": 0.0,
            "long_account_pct": 0.0,
            "short_account_pct": 0.0,
            "taker_buy_sell_ratio": 0.0,
            "available": False,
        }
    premium = await _get_json("https://fapi.binance.com/fapi/v1/premiumIndex", params={"symbol": symbol})
    oi = await _get_json("https://fapi.binance.com/fapi/v1/openInterest", params={"symbol": symbol})
    ticker = await _get_json("https://fapi.binance.com/fapi/v1/ticker/24hr", params={"symbol": symbol})
    ls_ratio = await _get_json(
        "https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
        params={"symbol": symbol, "period": "1h", "limit": 1},
    )
    taker = await _get_json(
        "https://fapi.binance.com/futures/data/takerlongshortRatio",
        params={"symbol": symbol, "period": "1h", "limit": 1},
    )

    funding_rate = float((premium or {}).get("lastFundingRate") or 0)
    mark_price = float((premium or {}).get("markPrice") or 0)
    oi_contracts = float((oi or {}).get("openInterest") or 0)
    oi_usd = oi_contracts * mark_price if mark_price else 0
    change_24h = float((ticker or {}).get("priceChangePercent") or 0)
    ls_row = (ls_ratio or [{}])[0] if isinstance(ls_ratio, list) and ls_ratio else {}
    taker_row = (taker or [{}])[0] if isinstance(taker, list) and taker else {}

    return {
        "source": "binance_futures_public",
        "asset": asset.upper(),
        "symbol": symbol,
        "timestamp": _utcnow(),
        "mark_price": mark_price,
        "funding_rate": funding_rate,
        "funding_rate_pct": round(funding_rate * 100, 4),
        "open_interest_contracts": oi_contracts,
        "open_interest_usd": round(oi_usd, 0),
        "change_24h_pct": round(change_24h, 2),
        "long_short_ratio": float(ls_row.get("longShortRatio") or 0),
        "long_account_pct": float(ls_row.get("longAccount") or 0),
        "short_account_pct": float(ls_row.get("shortAccount") or 0),
        "taker_buy_sell_ratio": float(taker_row.get("buySellRatio") or 0),
        "available": bool(premium),
    }


async def binance_liquidation_risk(asset: str = "BTC") -> dict[str, Any]:
    """Cascade risk heuristics from free Binance futures metrics."""
    snap = await binance_futures_snapshot(asset)
    if not snap.get("available"):
        return {"asset": asset.upper(), "available": False, "alerts": []}

    alerts: list[dict[str, Any]] = []
    fr = float(snap.get("funding_rate") or 0)
    ls = float(snap.get("long_short_ratio") or 1)
    oi_usd = float(snap.get("open_interest_usd") or 0)
    chg = float(snap.get("change_24h_pct") or 0)
    taker = float(snap.get("taker_buy_sell_ratio") or 1)

    if abs(fr) > 0.0005:
        alerts.append({
            "type": "funding_extreme",
            "severity": "high",
            "detail": f"Funding {fr*100:.4f}% — crowded side liquidation risk",
            "source": "binance_futures",
        })
    if ls > 1.8:
        alerts.append({
            "type": "long_crowding",
            "severity": "medium",
            "detail": f"Long/short ratio {ls:.2f} — long squeeze watch",
            "source": "binance_futures",
        })
    elif ls < 0.6:
        alerts.append({
            "type": "short_crowding",
            "severity": "medium",
            "detail": f"Long/short ratio {ls:.2f} — short squeeze watch",
            "source": "binance_futures",
        })
    if oi_usd > 1_000_000_000 and chg < -3:
        alerts.append({
            "type": "oi_unwind",
            "severity": "high",
            "detail": f"OI ${oi_usd/1e9:.1f}B with {chg:.1f}% drop — long liquidation cascade",
            "source": "binance_futures",
        })
    if taker < 0.85 and chg < -2:
        alerts.append({
            "type": "taker_sell_pressure",
            "severity": "medium",
            "detail": "Taker sell ratio elevated during drawdown",
            "source": "binance_futures",
        })
    if not alerts:
        alerts.append({
            "type": "equilibrium",
            "severity": "low",
            "detail": "No extreme liquidation cluster signals",
            "source": "binance_futures",
        })

    return {
        "asset": asset.upper(),
        "timestamp": _utcnow(),
        "available": True,
        "alerts": alerts,
        "metrics": snap,
        "data_source": "binance_futures_public",
    }


async def coindesk_rss(limit: int = 15) -> list[dict[str, Any]]:
    """Parse CoinDesk public RSS feed."""
    import xml.etree.ElementTree as ET

    url = "https://www.coindesk.com/arc/outboundfeeds/rss/"
    timeout = aiohttp.ClientTimeout(total=12)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session, session.get(url) as resp:
            if resp.status != 200:
                return []
            text = await resp.text()
    except aiohttp.ClientError:
        return []

    items: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(text)
        for item in root.findall(".//item")[:limit]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            desc = (item.findtext("description") or "")[:300]
            items.append({"title": title, "link": link, "published": pub, "summary": desc, "source": "coindesk"})
    except ET.ParseError:
        logger.debug("CoinDesk RSS parse failed")
    return items
