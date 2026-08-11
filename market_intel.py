"""
BLACKDARK — Market Intelligence (Week 3).

Open Interest, profit analytics, and whale gravity map data.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.MarketIntel")


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def tracked_asset_list() -> list[str]:
    return config.tracked_asset_list()


async def fetch_open_interest(symbols: list[str] | None = None) -> list[dict[str, Any]]:
    """Binance USDT-M perpetual open interest for tracked assets."""
    assets = symbols or tracked_asset_list()
    results: list[dict[str, Any]] = []
    timeout = aiohttp.ClientTimeout(total=25)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for asset in assets:
            pair = f"{asset}USDT"
            if not pair.isalnum():
                continue
            oi_url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={pair}"
            ticker_url = f"https://fapi.binance.com/fapi/v1/ticker/24hr?symbol={pair}"
            try:
                async with session.get(oi_url) as oi_resp:
                    if oi_resp.status != 200:
                        continue
                    oi_data = await oi_resp.json()
                async with session.get(ticker_url) as t_resp:
                    ticker = await t_resp.json() if t_resp.status == 200 else {}
                funding_url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={pair}"
                async with session.get(funding_url) as f_resp:
                    f_data = await f_resp.json() if f_resp.status == 200 else {}
            except (aiohttp.ClientError, TypeError, ValueError):
                continue

            oi_contracts = float(oi_data.get("openInterest") or 0)
            price = float(ticker.get("lastPrice") or 0)
            oi_usd = oi_contracts * price if price else 0.0
            change = float(ticker.get("priceChangePercent") or 0)
            funding_rate = float(f_data.get("lastFundingRate") or 0)

            if oi_usd > 500_000_000 and change > 2:
                signal = "Long buildup"
            elif oi_usd > 500_000_000 and change < -2:
                signal = "Long unwind"
            elif funding_rate > 0.0003:
                signal = "Crowded longs"
            elif funding_rate < -0.0001:
                signal = "Short squeeze risk"
            else:
                signal = "Neutral"

            results.append(
                {
                    "asset": asset,
                    "open_interest_contracts": round(oi_contracts, 2),
                    "open_interest_usd": round(oi_usd, 0),
                    "price": price,
                    "change_24h": round(change, 2),
                    "funding_rate_pct": round(funding_rate * 100, 4),
                    "signal": signal,
                }
            )

    results.sort(key=lambda x: x["open_interest_usd"], reverse=True)
    return results


async def build_profit_analytics() -> dict[str, Any]:
    from database import (
        fetch_arbitrage_alert_log,
        fetch_oracle_audit_stats,
        fetch_platform_analytics,
        fetch_simulation_logs,
    )

    audit = await fetch_oracle_audit_stats(limit=200)
    alerts = await fetch_arbitrage_alert_log(limit=100)
    sims = await fetch_simulation_logs(limit=50)
    platform = await fetch_platform_analytics()

    profitable_alerts = 0
    for row in alerts:
        try:
            payload = json.loads(row.get("payload_json") or "{}")
            if float(payload.get("net_profit_usdt") or 0) > 0:
                profitable_alerts += 1
        except (TypeError, ValueError):
            pass

    sim_pnl = sum(float(s.get("pnl_usd") or 0) for s in sims)

    return {
        "generated_at": _utcnow_iso(),
        "oracle": {
            "total_predictions": audit.get("total_predictions", 0),
            "average_accuracy_percent": audit.get("average_accuracy_percent", 0),
        },
        "arbitrage": {
            "alerts_logged": len(alerts),
            "profitable_signals": profitable_alerts,
            "hit_rate_percent": round(profitable_alerts / len(alerts) * 100, 1) if alerts else 0.0,
        },
        "simulations": {
            "total_runs": len(sims),
            "aggregate_pnl_usd": round(sim_pnl, 2),
        },
        "platform": {
            "dashboard_views": platform.get("dashboard_views", 0),
            "waitlist": platform.get("waitlist_count", 0),
            "subscribers": platform.get("subscriber_count", 0),
        },
        "summary_narrative": (
            f"Oracle accuracy {audit.get('average_accuracy_percent', 0)}% · "
            f"{profitable_alerts}/{len(alerts)} arb alerts profitable · "
            f"Sim P&L ${sim_pnl:,.2f}"
        ),
    }


def build_whale_gravity_map(
    whale_ctx: dict[str, Any],
    market: list[dict[str, Any]],
    *,
    parse_metadata,
) -> dict[str, Any]:
    """Build bubble map from CVVD whale context + live market prices."""
    price_by_asset = {a["symbol"]: a for a in market}

    nodes: dict[str, dict[str, Any]] = {}

    for alert in whale_ctx.get("whale_alerts") or []:
        asset = str(alert.get("asset") or "").upper()
        if not asset:
            continue
        meta = parse_metadata(alert)
        score = float(meta.get("manipulation_score") or 0)
        nodes.setdefault(
            asset,
            {
                "asset": asset,
                "gravity_score": 0.0,
                "alert_count": 0,
                "net_flow_usd": 0.0,
                "sector": alert.get("sector") or config.SECTOR_MAP.get(asset, "Other"),
            },
        )
        nodes[asset]["gravity_score"] += min(50, score * 0.5)
        nodes[asset]["alert_count"] += 1
        nodes[asset]["net_flow_usd"] += float(meta.get("net_flow_usd") or 0)

    for flow in whale_ctx.get("sector_flows") or []:
        sector = str(flow.get("sector") or "")
        meta = parse_metadata(flow)
        sii = float(meta.get("sii_score") or 0)
        for asset, pdata in price_by_asset.items():
            asset_sector = config.SECTOR_MAP.get(asset, pdata.get("sector", "Other"))
            if asset_sector != sector and pdata.get("sector") != sector:
                continue
            nodes.setdefault(
                asset,
                {
                    "asset": asset,
                    "gravity_score": 0.0,
                    "alert_count": 0,
                    "net_flow_usd": 0.0,
                    "sector": asset_sector,
                },
            )
            nodes[asset]["gravity_score"] += sii * 0.12

    bubbles = []
    for asset, node in nodes.items():
        mkt = price_by_asset.get(asset, {})
        gravity = min(100, round(node["gravity_score"], 1))
        if gravity >= 55:
            label = "High gravity"
        elif gravity >= 28:
            label = "Moderate"
        else:
            label = "Low"
        bubbles.append(
            {
                **node,
                "gravity_score": gravity,
                "price": mkt.get("price"),
                "change_24h": mkt.get("change_24h"),
                "size": max(24, min(100, gravity + node["alert_count"] * 10)),
                "label": label,
            }
        )

    bubbles.sort(key=lambda x: x["gravity_score"], reverse=True)
    return {
        "bubbles": bubbles[:25],
        "total_alerts": len(whale_ctx.get("whale_alerts") or []),
        "data_source": "CVVD + Binance Live",
        "timestamp": _utcnow_iso(),
    }
