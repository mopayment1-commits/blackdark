"""
BLACKDARK — Scheduled data ingestion fetchers.

Pulls registered sources into the data lake (SQLite). Rate-limited per source.
"""

from __future__ import annotations

import asyncio
import logging
import os
import defusedxml.ElementTree as ET
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

import config
from data_lake import store_snapshot
from data_sources_registry import Category, DataSourceSpec, sources_by_category
from database import upsert_ingestion_health
from exchange_adapters import TRACKED_PRICE_ASSETS, gateio_currency_pairs, kraken_ticker_pairs, native_symbol


def _take(items, n: int):
    """Safe head slice (never IndexError)."""
    if not items:
        return []
    return list(items)[: max(0, int(n))]


logger = logging.getLogger("BLACKDARK.IngestionFetchers")

FetchResult = dict[str, Any] | list[Any]

_source_locks: dict[str, asyncio.Lock] = {}
_last_fetch_at: dict[str, float] = {}


def _rate_limit_ok(source_id: str, min_interval: int) -> bool:
    import time

    last = _last_fetch_at.get(source_id, 0.0)
    return time.time() - last >= max(min_interval, 1)


def _mark_fetched(source_id: str) -> None:
    import time

    _last_fetch_at[source_id] = time.time()


async def _fetch_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    async with session.get(url, params=params, headers=headers) as response:
        response.raise_for_status()
        return await response.json()


async def _fetch_text(session: aiohttp.ClientSession, url: str) -> str:
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def _parse_rss(payload: str, limit: int = 10) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return items
    geo_kw = ("war", "peace", "fed", "inflation", "sanction", "rate", "crisis")
    for entry in root.findall(".//item")[:limit]:
        title = (entry.findtext("title") or "").strip()
        if not title:
            continue
        lower = title.lower()
        items.append(
            {
                "title": title[:240],
                "published_at": entry.findtext("pubDate"),
                "geopolitical": any(k in lower for k in geo_kw),
            }
        )
    return items


async def _record(
    spec: DataSourceSpec,
    payload: FetchResult,
    *,
    ok: bool = True,
    error: str | None = None,
) -> None:
    if ok and payload is not None:
        await store_snapshot(spec.source_id, spec.category, payload)
    await upsert_ingestion_health(
        spec.source_id,
        spec.category,
        ok=ok,
        error=error,
    )


# ── Handlers ──────────────────────────────────────────────────────────────────

async def _h_binance_spot(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.binance_connector import fetch_binance_spot_ticker

    row = await fetch_binance_spot_ticker("BTC")
    return {
        "symbol": row.get("pair", "BTCUSDT"),
        "price": row.get("price_usd", 0),
        "change_24h_pct": row.get("change_24h_pct", 0),
        "volume": row.get("volume_24h", 0),
        "source": "binance_connector",
        "cache_hit": row.get("cache_hit"),
    }


async def _h_binance_futures(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.binance_connector import fetch_binance_futures_funding

    row = await fetch_binance_futures_funding("BTC")
    return {
        "asset": "BTC",
        "funding_rate": row.get("funding_rate", 0),
        "mark_price": row.get("mark_price", 0),
        "source": "binance_connector",
        "cache_hit": row.get("cache_hit"),
    }


async def _h_coingecko_prices(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_markets, fetch_coingecko_price

    markets = await fetch_coingecko_markets(per_page=50)
    prices = []
    for sym in ("BTC", "ETH", "SOL"):
        row = await fetch_coingecko_price(sym)
        if row.get("ok"):
            prices.append(row)
    return {"markets": markets.get("markets") or [], "prices": prices, "source": "coingecko_connector"}


async def _h_kucoin(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url)
    tickers = (data.get("data") or {}).get("ticker") or []
    tracked: list[dict[str, Any]] = []
    wanted = {native_symbol("kucoin", f"{a}/{config.QUOTE_BASE}", "spot") for a in TRACKED_PRICE_ASSETS}
    for row in tickers:
        sym = str(row.get("symbol") or "")
        if sym not in wanted:
            continue
        asset = sym.split("-")[0].replace("XBT", "BTC")
        last = float(row.get("last") or 0)
        if last <= 0:
            continue
        tracked.append(
            {
                "asset": asset,
                "symbol": sym,
                "price": last,
                "change_24h_pct": float(row.get("changeRate") or 0) * 100,
                "volume_usd": float(row.get("volValue") or 0),
            }
        )
    top = sorted(tickers, key=lambda t: float(t.get("volValue") or 0), reverse=True)[:5]
    return {"exchange": "kucoin", "tracked_quotes": tracked, "top_tickers": top}


async def _h_bybit_spot(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url, params={"category": "spot"})
    rows = (data.get("result") or {}).get("list") or []
    return {"tickers": _take(rows, 5)}


async def _h_bybit_linear(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url, params={"category": "linear"})
    rows = (data.get("result") or {}).get("list") or []
    btc = next((r for r in rows if r.get("symbol") == "BTCUSDT"), {})
    return {"btc_linear": btc}


async def _h_okx(session: aiohttp.ClientSession, spec: DataSourceSpec, inst_type: str) -> FetchResult:
    data = await _fetch_json(session, spec.url, params={"instType": inst_type})
    rows = _take(data.get("data") or [], 5)
    return {"instType": inst_type, "tickers": rows}


async def _h_gateio(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url)
    wanted = set(gateio_currency_pairs())
    tracked: list[dict[str, Any]] = []
    for row in data or []:
        pair = str(row.get("currency_pair") or "")
        if pair not in wanted:
            continue
        asset = pair.split("_")[0]
        last = float(row.get("last") or 0)
        if last <= 0:
            continue
        tracked.append(
            {
                "asset": asset,
                "symbol": pair,
                "price": last,
                "change_24h_pct": float(row.get("change_percentage") or 0),
                "volume_usd": float(row.get("quote_volume") or 0),
            }
        )
    rows = sorted(data or [], key=lambda r: float(r.get("quote_volume") or 0), reverse=True)[:5]
    return {"exchange": "gateio", "tracked_quotes": tracked, "tickers": rows}


async def _h_coinbase(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    tracked: list[dict[str, Any]] = []
    for asset in TRACKED_PRICE_ASSETS:
        product = native_symbol("coinbase", f"{asset}/{config.QUOTE_BASE}", "spot")
        try:
            data = await _fetch_json(
                session,
                f"https://api.exchange.coinbase.com/products/{product}/ticker",
            )
            price = float(data.get("price") or 0)
            if price <= 0:
                continue
            tracked.append(
                {
                    "asset": asset,
                    "symbol": product,
                    "price": price,
                    "volume": float(data.get("volume") or 0),
                }
            )
        except (aiohttp.ClientError, TypeError, ValueError):
            continue
    return {"exchange": "coinbase", "tracked_quotes": tracked}


def _kraken_row(result: dict[str, Any], pair: str) -> Any:
    row = result.get(pair)
    if row:
        return row
    # Kraken may return canonical alt key — match by prefix
    for key, val in result.items():
        if key.upper().startswith(pair[:3]):
            return val
    return None


async def _h_kraken(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url, params={"pair": kraken_ticker_pairs()})
    tracked: list[dict[str, Any]] = []
    for asset in TRACKED_PRICE_ASSETS:
        pair = native_symbol("kraken", f"{asset}/{config.QUOTE_BASE}", "spot")
        row = _kraken_row(data.get("result") or {}, pair)
        if not row:
            continue
        price = float(row.get("c", ["0"])[0])
        if price <= 0:
            continue
        tracked.append(
            {
                "asset": asset,
                "symbol": pair,
                "price": price,
                "volume": float(row.get("v", [0, 0])[1]),
            }
        )
    return {"exchange": "kraken", "tracked_quotes": tracked}


async def _h_coincap(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url, params={"limit": "10"})
    return {"assets": data.get("data") or []}


async def _h_blockchain_com(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url)
    return {
        "market_price_usd": data.get("market_price_usd"),
        "hash_rate": data.get("hash_rate"),
        "n_transactions": data.get("n_transactions"),
    }


async def _h_blockchair(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    key = os.getenv("BLOCKCHAIR_API_KEY")
    params = {"key": key} if key else None
    data = await _fetch_json(session, spec.url, params=params)
    return {"data": data.get("data") or {}}


async def _h_defillama_chains(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    chains = await _fetch_json(session, spec.url)
    total = sum(float(c.get("tvl") or 0) for c in chains or [])
    return {"total_tvl_usd": round(total, 2), "chain_count": len(chains or []), "top": (chains or [])[:5]}


async def _h_defillama_protocols(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    protocols = await _fetch_json(session, spec.url)
    top = sorted(protocols or [], key=lambda p: float(p.get("tvl") or 0), reverse=True)[:10]
    return {"top_protocols": top}


async def _h_defillama_yields(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url)
    pools = (data.get("data") or [])[:10]
    return {"pools": pools}


async def _h_investing_com_rss(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.investing_com_connector import fetch_investing_news_context

    data = await fetch_investing_news_context(limit=20)
    return {
        "articles": (data.get("articles") or [])[:5],
        "high_impact_count": data.get("high_impact_count"),
        "ai_context_line": data.get("ai_context_line"),
        "source": "investing_com_connector",
        "cache_hit": data.get("cache_hit"),
    }


async def _h_theblock_rss(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.theblock_connector import fetch_theblock_research_context

    data = await fetch_theblock_research_context(limit=8)
    return {
        "articles": (data.get("articles") or [])[:5],
        "ai_context_line": data.get("ai_context_line"),
        "source": "theblock_connector",
        "cache_hit": data.get("cache_hit"),
    }


async def _h_dexscreener(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url, params={"q": "BTC"})
    return {"pairs": _take(data.get("pairs") or [], 5)}


async def _h_geckoterminal(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url)
    return {"data": data.get("data") or {}}


async def _h_rss(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    text = await _fetch_text(session, spec.url)
    return {"headlines": _parse_rss(text)}


async def _h_fear_greed(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.alternative_me_connector import fetch_fear_greed_index

    fg = await fetch_fear_greed_index()
    return {
        "value": int(fg.get("value") or 50),
        "label": fg.get("label"),
        "alpha_score": fg.get("alpha_score"),
        "source": "alternative_me_connector",
    }


async def _h_reddit(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(
        session,
        spec.url,
        params={"limit": "8"},
        headers={"User-Agent": "BLACKDARK-Ingestion/1.0"},
    )
    titles = [
        str((c.get("data") or {}).get("title") or "")[:180]
        for c in (data.get("data") or {}).get("children") or []
    ]
    return {"titles": titles}


async def _h_coingecko_trending(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_trending

    data = await fetch_coingecko_trending()
    symbols = [
        str((c.get("item") or {}).get("symbol") or "").upper()
        for c in (data.get("coins") or [])[:7]
    ]
    return {"symbols": [s for s in symbols if s], "source": "coingecko_connector"}


async def _h_stocktwits(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url)
    messages = _take(data.get("messages") or [], 8)
    return {"messages": [m.get("body", "")[:160] for m in messages]}


async def _h_coingecko_global(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.coingecko_connector import fetch_coingecko_global

    data = await fetch_coingecko_global()
    return {"global": data.get("global") or {}, "source": "coingecko_connector"}


async def _h_coingecko_events(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    try:
        data = await _fetch_json(session, spec.url, params={"from_date": "2026-01-01"})
        return {"events": data[:10] if isinstance(data, list) else data}
    except Exception:
        return {"events": []}


async def _h_defillama_airdrops(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    data = await _fetch_json(session, spec.url)
    return {"airdrops": (data or [])[:10]}


async def _h_yahoo_macro(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    symbols = {
        "spx": config.MACRO_YAHOO_SPX_SYMBOL,
        "dxy": config.MACRO_YAHOO_DXY_SYMBOL,
        "vix": config.ORACLE_MACRO_VIX_SYMBOL,
        "us10y": config.ORACLE_MACRO_US10Y_SYMBOL,
        "gold": config.MACRO_YAHOO_GOLD_SYMBOL,
        "oil": config.ORACLE_MACRO_OIL_SYMBOL,
    }
    changes: dict[str, float | None] = {}
    for label, sym in symbols.items():
        try:
            payload = await _fetch_json(
                session,
                f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                params={"interval": "1d", "range": "5d"},
            )
            result = (payload.get("chart") or {}).get("result") or []
            closes = (
                ((result[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
            )
            valid = [float(v) for v in closes if v is not None]
            if len(valid) >= 2 and valid[-2] != 0:
                changes[label] = round((valid[-1] - valid[-2]) / valid[-2], 4)
            else:
                changes[label] = None
        except Exception:
            changes[label] = None
    return {"changes": changes}


async def _h_fred(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    key = os.getenv("FRED_API_KEY")
    if not key:
        raise ValueError("FRED_API_KEY missing")
    data = await _fetch_json(
        session,
        spec.url,
        params={
            "series_id": "FEDFUNDS",
            "api_key": key,
            "file_type": "json",
            "limit": "2",
            "sort_order": "desc",
        },
    )
    return {"observations": _take(data.get("observations") or [], 2)}


async def _h_open_exchange_rates(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    app_id = os.getenv("OPENEXCHANGERATES_APP_ID")
    if not app_id:
        raise ValueError("OPENEXCHANGERATES_APP_ID missing")
    data = await _fetch_json(session, spec.url, params={"app_id": app_id})
    return {"base": data.get("base"), "rates_sample": dict(list((data.get("rates") or {}).items())[:5])}


async def _h_cryptocompare(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    key = os.getenv("SENTIMENT_CRYPTOCOMPARE_API_KEY", "")
    headers = {"authorization": f"Apikey {key}"} if key else None
    data = await _fetch_json(
        session,
        spec.url,
        params={"fsyms": "BTC,ETH,SOL", "tsyms": "USD"},
        headers=headers,
    )
    return {"RAW": data.get("RAW") or {}}


async def _h_coinmarketcap(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    key = os.getenv("COINMARKETCAP_API_KEY")
    if not key:
        raise ValueError("COINMARKETCAP_API_KEY missing")
    data = await _fetch_json(
        session,
        spec.url,
        headers={"X-CMC_PRO_API_KEY": key},
        params={"limit": "10"},
    )
    return {"listings": (data.get("data") or [])[:10]}


async def _h_polygon_io(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.polygon_io_connector import fetch_polygon_macro_context

    row = await fetch_polygon_macro_context()
    return {
        "ticker": row.get("ticker"),
        "change_pct": row.get("change_pct"),
        "headline": row.get("headline"),
        "source": "polygon_io_connector",
        "cache_hit": row.get("cache_hit"),
    }


async def _h_polygonscan(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.polygonscan_connector import fetch_polygon_onchain_health

    row = await fetch_polygon_onchain_health()
    return {
        "chain": row.get("chain"),
        "block_number": row.get("block_number"),
        "gas_gwei": row.get("gas_gwei"),
        "source": row.get("source"),
        "cache_hit": row.get("cache_hit"),
    }


async def _h_tronscan(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from blackdark.ingestion.tronscan_connector import tronscan_connector_status

    return tronscan_connector_status()


async def _h_internal_cvvd(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    from whale_tracker import WhaleTracker

    tracker = WhaleTracker()
    cycle = await tracker.run_cycle()
    return {
        "whale_alerts": _take(cycle.get("whale_alerts") or [], 10),
        "sector_flows": _take(cycle.get("sector_flows") or [], 5),
    }


async def _h_generic_keyed_rest(session: aiohttp.ClientSession, spec: DataSourceSpec) -> FetchResult:
    if not spec.env_key or not os.getenv(spec.env_key):
        raise ValueError(f"{spec.env_key or 'API key'} missing")
    headers = {}
    if spec.env_key == "COINMARKETCAP_API_KEY":
        headers["X-CMC_PRO_API_KEY"] = os.getenv(spec.env_key, "")
    data = await _fetch_json(session, spec.url, headers=headers or None)
    return {"raw": data}


HANDLERS: dict[str, Callable[[aiohttp.ClientSession, DataSourceSpec], Awaitable[FetchResult]]] = {
    "binance_spot": _h_binance_spot,
    "binance_futures": _h_binance_futures,
    "coingecko_prices": _h_coingecko_prices,
    "kucoin_spot": _h_kucoin,
    "bybit_spot": _h_bybit_spot,
    "bybit_linear": _h_bybit_linear,
    "gateio_spot": _h_gateio,
    "kraken_spot": _h_kraken,
    "coinbase_spot": _h_coinbase,
    "coincap": _h_coincap,
    "blockchain_com": _h_blockchain_com,
    "blockchair": _h_blockchair,
    "defillama_tvl": _h_defillama_chains,
    "defillama_protocols": _h_defillama_protocols,
    "defillama_yields": _h_defillama_yields,
    "dexscreener": _h_dexscreener,
    "theblock_rss": _h_theblock_rss,
    "investing_com_rss": _h_investing_com_rss,
    "polygonscan": _h_polygonscan,
    "tronscan": _h_tronscan,
    "polygon_io": _h_polygon_io,
    "geckoterminal": _h_geckoterminal,
    "fear_greed": _h_fear_greed,
    "reddit_crypto": _h_reddit,
    "coingecko_trending": _h_coingecko_trending,
    "stocktwits_btc": _h_stocktwits,
    "coingecko_reports": _h_coingecko_global,
    "coingecko_events": _h_coingecko_events,
    "defillama_airdrops": _h_defillama_airdrops,
    "yahoo_finance": _h_yahoo_macro,
    "fred": _h_fred,
    "open_exchange_rates": _h_open_exchange_rates,
    "cryptocompare_prices": _h_cryptocompare,
    "coinmarketcap": _h_coinmarketcap,
    "internal_cvvd": _h_internal_cvvd,
}


async def fetch_single_source(
    session: aiohttp.ClientSession,
    spec: DataSourceSpec,
) -> bool:
    if spec.fetch_kind == "websocket":
        return False
    if not _rate_limit_ok(spec.source_id, spec.interval_seconds):
        return False

    from blackdark.data import circuit_breaker as cb

    if cb.is_open(spec.source_id):
        await upsert_ingestion_health(
            spec.source_id,
            spec.category,
            ok=False,
            error="circuit_open",
        )
        return False

    lock = _source_locks.setdefault(spec.source_id, asyncio.Lock())
    async with lock:
        if not _rate_limit_ok(spec.source_id, spec.interval_seconds):
            return False
        try:
            if spec.fetch_kind == "rss":
                payload = await _h_rss(session, spec)
            elif spec.source_id == "okx_spot":
                payload = await _h_okx(session, spec, "SPOT")
            elif spec.source_id == "okx_swap":
                payload = await _h_okx(session, spec, "SWAP")
            elif spec.source_id in HANDLERS:
                payload = await HANDLERS[spec.source_id](session, spec)
            elif spec.env_key and not os.getenv(spec.env_key):
                await upsert_ingestion_health(
                    spec.source_id,
                    spec.category,
                    ok=False,
                    error=f"{spec.env_key} not configured",
                )
                return False
            else:
                payload = await _h_generic_keyed_rest(session, spec)

            await _record(spec, payload, ok=True)
            _mark_fetched(spec.source_id)
            cb.record_success(spec.source_id)
            return True
        except Exception as exc:
            logger.warning("Ingestion failed | source=%s error=%s", spec.source_id, exc)
            cb.record_failure(spec.source_id, str(exc)[:200])
            await _record(spec, {}, ok=False, error=str(exc)[:200])
            return False


async def ingest_category(session: aiohttp.ClientSession, category: Category) -> dict[str, int]:
    specs = sources_by_category(category)
    ok = 0
    fail = 0
    skip = 0
    for spec in specs:
        if spec.fetch_kind == "websocket":
            skip += 1
            continue
        if (
            spec.env_key
            and not os.getenv(spec.env_key)
            and spec.source_id not in HANDLERS
            and spec.fetch_kind != "rss"
        ):
            skip += 1
            continue
        success = await fetch_single_source(session, spec)
        if success:
            ok += 1
        else:
            fail += 1
    return {"ok": ok, "fail": fail, "skip": skip, "total": len(specs)}


async def ingest_all_categories() -> dict[str, Any]:
    from blackdark.ingestion.alternative_me_connector import run_alternative_me_ingest
    from blackdark.ingestion.coingecko_connector import run_coingecko_primary_ingest

    timeout = aiohttp.ClientTimeout(total=config.INGESTION_FETCH_TIMEOUT_SECONDS)
    summary: dict[str, Any] = {
        "coingecko_primary": await run_coingecko_primary_ingest(),
        "alternative_me": await run_alternative_me_ingest(),
    }
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for category in (
            "prices", "onchain", "defi", "news", "sentiment",
            "events", "whale", "research", "macro", "regulatory",
        ):
            summary[category] = await ingest_category(session, category)  # type: ignore[arg-type]
    return summary
