"""
BLACKDARK — Data Lake (local warehouse layer).

SQLite ingestion_snapshots = structured lake for news, macro, on-chain, etc.
hot_spool (existing) = time-series ticks/order books from aggregator/WebSockets.

Oracle and AI modules read from here — never direct API at request time.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import config
from data_sources_registry import Category, registry_summary
from database import (
    fetch_ingestion_health_summary,
    fetch_latest_ingestion_by_category,
    insert_ingestion_snapshot,
    prune_ingestion_snapshots,
)

logger = logging.getLogger("BLACKDARK.DataLake")

ALL_CATEGORIES: tuple[Category, ...] = (
    "prices",
    "onchain",
    "defi",
    "news",
    "sentiment",
    "events",
    "whale",
    "research",
    "macro",
    "regulatory",
)


async def store_snapshot(
    source_id: str,
    category: Category,
    payload: dict[str, Any] | list[Any],
    *,
    status: str = "ok",
) -> None:
    await insert_ingestion_snapshot(source_id, category, payload, status=status)


async def get_category_bundle(
    category: Category,
    *,
    max_age_seconds: int | None = None,
) -> list[dict[str, Any]]:
    age = max_age_seconds or config.INGESTION_LAKE_MAX_AGE_SECONDS
    return await fetch_latest_ingestion_by_category(category, max_age_seconds=age, limit=100)


async def _load_category_bundles() -> tuple[dict[str, Any], str | None]:
    bundles: dict[str, Any] = {}
    latest_ts: str | None = None

    for category in ALL_CATEGORIES:
        rows = await get_category_bundle(category)
        if not rows:
            continue
        bundles[category] = {
            "count": len(rows),
            "sources": [row["source_id"] for row in rows],
            "items": rows,
        }
        for row in rows:
            ts = row.get("fetched_at")
            if ts and (latest_ts is None or ts > latest_ts):
                latest_ts = ts
    return bundles, latest_ts


def _sentiment_from_bundles(bundles: dict[str, Any]) -> tuple[Any, list[str]]:
    sentiment_rows = bundles.get("sentiment", {}).get("items") or []
    fear_greed = None
    trending: list[str] = []
    for row in sentiment_rows:
        payload = row.get("payload") or {}
        if row.get("source_id") == "fear_greed":
            fear_greed = payload.get("value")
        if row.get("source_id") == "coingecko_trending":
            trending = payload.get("symbols") or []
    return fear_greed, trending


def _news_from_bundles(bundles: dict[str, Any]) -> list[dict[str, Any]]:
    news_items: list[dict[str, Any]] = []
    for row in bundles.get("news", {}).get("items") or []:
        headlines = (row.get("payload") or {}).get("headlines") or []
        news_items.extend(headlines[:5])
    return news_items


def _macro_changes_from_bundles(bundles: dict[str, Any]) -> dict[str, Any]:
    macro_items = bundles.get("macro", {}).get("items") or []
    macro_changes: dict[str, Any] = {}
    for row in macro_items:
        if row.get("source_id") == "yahoo_finance":
            macro_changes = (row.get("payload") or {}).get("changes") or {}
    return macro_changes


def _defi_tvl_from_bundles(bundles: dict[str, Any]) -> Any:
    defi_items = bundles.get("defi", {}).get("items") or []
    tvl_usd = None
    for row in defi_items:
        if row.get("source_id") == "defillama_tvl":
            tvl_usd = (row.get("payload") or {}).get("total_tvl_usd")
    return tvl_usd


def _price_quotes_from_bundles(bundles: dict[str, Any]) -> list[dict[str, Any]]:
    price_items = bundles.get("prices", {}).get("items") or []
    price_quotes: list[dict[str, Any]] = []
    for row in price_items[:15]:
        payload = row.get("payload") or {}
        if payload.get("symbol") and payload.get("price"):
            price_quotes.append(payload)
    return price_quotes


def _btc_stats_from_bundles(bundles: dict[str, Any]) -> dict[str, Any]:
    onchain_items = bundles.get("onchain", {}).get("items") or []
    btc_stats: dict[str, Any] = {}
    for row in onchain_items:
        if row.get("source_id") == "blockchain_com":
            btc_stats = row.get("payload") or {}
    return btc_stats


async def build_lake_context_for_oracle(asset: str = "BTC") -> dict[str, Any]:
    """Merge all category snapshots into oracle-ready context."""
    bundles, latest_ts = await _load_category_bundles()
    fear_greed, trending = _sentiment_from_bundles(bundles)
    news_items = _news_from_bundles(bundles)
    macro_changes = _macro_changes_from_bundles(bundles)
    tvl_usd = _defi_tvl_from_bundles(bundles)
    price_items = bundles.get("prices", {}).get("items") or []
    price_quotes = _price_quotes_from_bundles(bundles)
    btc_stats = _btc_stats_from_bundles(bundles)

    return {
        "enabled": bool(bundles),
        "architecture": "scheduler → data_lake (SQLite) → oracle",
        "asset": asset.upper(),
        "timestamp": latest_ts or datetime.now(UTC).isoformat(),
        "registry": registry_summary(),
        "lake_categories_loaded": list(bundles.keys()),
        "sentiment": {
            "fear_greed_index": fear_greed,
            "coingecko_trending": trending,
        },
        "geo_news": {
            "headlines": news_items[:20],
            "geopolitical_headline_count": sum(
                1 for h in news_items if h.get("geopolitical")
            ),
        },
        "macro": {
            "changes_1d_pct": macro_changes,
            "macro_regime_proxy": _macro_regime_from_changes(macro_changes),
        },
        "derivatives": _derivatives_from_prices(price_items, asset),
        "aggregators": {
            "defi_tvl_usd": tvl_usd,
            "price_quotes": price_quotes[:10],
        },
        "onchain": {"btc_network": btc_stats},
        "bundles": bundles,
        "pillars": list(bundles.keys()),
    }


def _macro_regime_from_changes(changes: dict[str, Any]) -> str:
    vix = float(changes.get("vix") or 0)
    spx = float(changes.get("spx") or 0)
    if vix > 0.08 or spx < -0.01:
        return "risk_off"
    if spx > 0.005:
        return "risk_on"
    return "neutral"


def _derivatives_from_prices(price_items: list[dict[str, Any]], asset: str) -> dict[str, Any]:
    symbol = asset.upper()
    funding = None
    for row in price_items:
        payload = row.get("payload") or {}
        if row.get("source_id") == "binance_futures" and payload.get("asset") == symbol:
            funding = payload.get("funding_rate")
    if funding and funding > 0.0003:
        derivatives_bias = "overheated_longs"
    elif funding and funding < -0.0001:
        derivatives_bias = "short_crowded"
    else:
        derivatives_bias = "neutral"

    return {
        "asset": symbol,
        "funding_rate": funding,
        "derivatives_bias": derivatives_bias,
    }


async def lake_status() -> dict[str, Any]:
    health = await fetch_ingestion_health_summary()
    ok_sources = sum(1 for row in health if row.get("last_ok_at"))
    return {
        "registry": registry_summary(),
        "sources_tracked": len(health),
        "sources_ok": ok_sources,
        "health": health,
    }


async def maintenance_prune() -> int:
    return await prune_ingestion_snapshots(config.INGESTION_LAKE_MAX_ROWS)
