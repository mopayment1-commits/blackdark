"""
Feed Latency Intelligence — Feature #111 (Market Radar / Pro Tier).

Informational layer comparing data freshness between fast (WebSocket) and slow
(REST-polled) exchange feeds. NOT execution advice — no profit promises.

Product naming: "Data Freshness" / "Feed Latency" (never "استغلال").
Example headline: "Price on Gate.io is 0.3% behind live data".
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp

from data_freshness import freshness_chip

logger = logging.getLogger("BLACKDARK.FeedLatency")

_CACHE_PATH = Path("data/feed_latency_cache.json")
_DISCLAIMER = (
    "Feed latency data is informational only — not trading advice or a profit "
    "guarantee. Execution based on feed speed differences requires infrastructure "
    "beyond this MVP. Prices may diverge for reasons other than update lag."
)

# Typical feed intervals (ms) — informational baseline when live age unavailable.
FEED_PROFILES: dict[str, dict[str, Any]] = {
    "binance": {"tier": "fast", "typical_interval_ms": 100, "transport": "websocket"},
    "okx": {"tier": "fast", "typical_interval_ms": 150, "transport": "websocket"},
    "bybit": {"tier": "fast", "typical_interval_ms": 120, "transport": "websocket"},
    "kraken": {"tier": "fast", "typical_interval_ms": 200, "transport": "websocket"},
    "coinbase": {"tier": "slow", "typical_interval_ms": 1000, "transport": "rest"},
    "gateio": {"tier": "slow", "typical_interval_ms": 3000, "transport": "rest"},
    "kucoin": {"tier": "slow", "typical_interval_ms": 2000, "transport": "rest"},
    "bitfinex": {"tier": "slow", "typical_interval_ms": 2500, "transport": "rest"},
    "mexc": {"tier": "slow", "typical_interval_ms": 5000, "transport": "rest"},
}

_FAST_EXCHANGES = tuple(k for k, v in FEED_PROFILES.items() if v["tier"] == "fast")
_SLOW_EXCHANGES = tuple(k for k, v in FEED_PROFILES.items() if v["tier"] == "slow")

_CACHE_TTL_HOT_SEC = 60
_CACHE_TTL_WARM_SEC = 3600
_CACHE_TTL_COLD_SEC = 86400
_RATE_LIMIT_SEC = 1.0

_memory_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_rate_limit_ts: dict[str, float] = {}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _norm_asset(symbol: str) -> str:
    s = symbol.upper().strip().replace("/", "").replace("-", "")
    return s.replace("USDT", "") if s.endswith("USDT") else s


def _pair_usdt(asset: str) -> str:
    return f"{asset}/USDT"


def _rate_limited(domain: str) -> bool:
    now = time.monotonic()
    last = _rate_limit_ts.get(domain, 0.0)
    if now - last < _RATE_LIMIT_SEC:
        return True
    _rate_limit_ts[domain] = now
    return False


def _cache_get(key: str) -> dict[str, Any] | None:
    now = time.time()
    mem = _memory_cache.get(key)
    if mem and mem[0] > now:
        return mem[1]

    if _CACHE_PATH.exists():
        try:
            blob = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
            row = blob.get(key)
            if row and float(row.get("expires_at", 0)) > now:
                payload = row.get("payload") or {}
                _memory_cache[key] = (float(row["expires_at"]), payload)
                return payload
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return None


def _cache_set(key: str, payload: dict[str, Any], *, ttl_sec: int) -> None:
    expires = time.time() + ttl_sec
    _memory_cache[key] = (expires, payload)
    try:
        blob: dict[str, Any] = {}
        if _CACHE_PATH.exists():
            blob = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        blob[key] = {"expires_at": expires, "payload": payload, "cached_at": _utcnow()}
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(json.dumps(blob, indent=2), encoding="utf-8")
    except OSError:
        logger.debug("feed latency disk cache write failed")


async def _fetch_binance_rest(asset: str) -> dict[str, Any] | None:
    if _rate_limited("binance"):
        return None
    sym = f"{asset}USDT"
    if not sym.isalnum():
        return None
    timeout = aiohttp.ClientTimeout(total=2.5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.binance.com/api/v3/ticker/bookTicker", params={"symbol": sym}
            ) as resp:
                if resp.status != 200:
                    return None
                row = await resp.json()
                bid = float(row.get("bidPrice") or 0)
                ask = float(row.get("askPrice") or 0)
                if bid <= 0 or ask <= 0:
                    return None
                return {
                    "exchange": "binance",
                    "mid": (bid + ask) / 2.0,
                    "bid": bid,
                    "ask": ask,
                    "source": "binance_rest",
                    "fetched_at": _utcnow(),
                }
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        return None


async def _fetch_coinbase(asset: str) -> dict[str, Any] | None:
    if _rate_limited("coinbase"):
        return None
    product = f"{asset}-USD"
    timeout = aiohttp.ClientTimeout(total=2.5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                f"https://api.exchange.coinbase.com/products/{product}/ticker"
            ) as resp:
                if resp.status != 200:
                    return None
                row = await resp.json()
                price = float(row.get("price") or 0)
                if price <= 0:
                    return None
                return {
                    "exchange": "coinbase",
                    "mid": price,
                    "source": "coinbase_rest",
                    "fetched_at": _utcnow(),
                }
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        return None


async def _fetch_gateio(asset: str) -> dict[str, Any] | None:
    if _rate_limited("gateio"):
        return None
    pair = f"{asset}_USDT"
    timeout = aiohttp.ClientTimeout(total=2.5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.gateio.ws/api/v4/spot/tickers",
                params={"currency_pair": pair},
            ) as resp:
                if resp.status != 200:
                    return None
                rows = await resp.json()
                if not rows:
                    return None
                row = rows[0]
                last = float(row.get("last") or 0)
                if last <= 0:
                    return None
                return {
                    "exchange": "gateio",
                    "mid": last,
                    "source": "gateio_rest",
                    "fetched_at": _utcnow(),
                }
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        return None


async def _fetch_kucoin(asset: str) -> dict[str, Any] | None:
    if _rate_limited("kucoin"):
        return None
    sym = f"{asset}-USDT"
    timeout = aiohttp.ClientTimeout(total=2.5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://api.kucoin.com/api/v1/market/orderbook/level1",
                params={"symbol": sym},
            ) as resp:
                if resp.status != 200:
                    return None
                body = await resp.json()
                data = body.get("data") or {}
                bid = float(data.get("bestBid") or 0)
                ask = float(data.get("bestAsk") or 0)
                if bid <= 0 or ask <= 0:
                    return None
                return {
                    "exchange": "kucoin",
                    "mid": (bid + ask) / 2.0,
                    "source": "kucoin_rest",
                    "fetched_at": _utcnow(),
                }
    except (aiohttp.ClientError, asyncio.TimeoutError, TimeoutError, ValueError):
        return None


async def _fetch_coingecko_fallback(asset: str) -> dict[str, Any] | None:
    try:
        from blackdark.ingestion.coingecko_connector import fetch_coingecko_price

        cg = await fetch_coingecko_price(asset)
        if cg.get("ok") and float(cg.get("price_usd") or 0) > 0:
            return {
                "exchange": "coingecko",
                "mid": float(cg["price_usd"]),
                "source": "coingecko_fallback",
                "fetched_at": _utcnow(),
            }
    except (ImportError, asyncio.TimeoutError, TimeoutError, ValueError, TypeError):
        pass
    return None


def _live_reference(asset: str) -> dict[str, Any] | None:
    """Fast feed from in-memory WebSocket hub."""
    try:
        from live_book_hub import get_best_price, get_quote_age_ms

        pair = _pair_usdt(asset)
        for ex in _FAST_EXCHANGES:
            quote = get_best_price(ex, pair)
            age_ms = get_quote_age_ms(ex, pair)
            if quote and quote.get("mid", 0) > 0:
                profile = FEED_PROFILES.get(ex, {})
                return {
                    "exchange": ex,
                    "mid": float(quote["mid"]),
                    "bid": float(quote.get("bid") or 0),
                    "ask": float(quote.get("ask") or 0),
                    "source": f"{ex}_websocket",
                    "feed_age_ms": age_ms,
                    "typical_interval_ms": profile.get("typical_interval_ms"),
                    "tier": "fast",
                    "fetched_at": _utcnow(),
                }
    except ImportError:
        pass
    return None


def _headline(exchange: str, lag_pct: float, *, feed_age_ms: float | None) -> str:
    ex_name = exchange.replace("_", ".").title()
    if abs(lag_pct) < 0.05:
        age_part = f" (feed ~{feed_age_ms:.0f}ms old)" if feed_age_ms is not None else ""
        return f"{ex_name} price aligned with live data{age_part}"
    direction = "behind" if lag_pct < 0 else "ahead of"
    return f"Price on {ex_name} is {abs(lag_pct):.2f}% {direction} live data"


def _build_venue_row(
    *,
    exchange: str,
    mid: float,
    ref_mid: float,
    source: str,
    feed_age_ms: float | None = None,
    typical_interval_ms: int | None = None,
    tier: str | None = None,
) -> dict[str, Any]:
    lag_pct = ((mid - ref_mid) / ref_mid * 100.0) if ref_mid > 0 else 0.0
    profile = FEED_PROFILES.get(exchange, {})
    tier = tier or profile.get("tier", "unknown")
    typical = typical_interval_ms or profile.get("typical_interval_ms")
    chip = freshness_chip(freshness_ms=feed_age_ms) if feed_age_ms is not None else freshness_chip()

    alert_level = "low"
    if abs(lag_pct) >= 0.5 or (feed_age_ms and feed_age_ms > 5000):
        alert_level = "high"
    elif abs(lag_pct) >= 0.15 or (feed_age_ms and feed_age_ms > 2000):
        alert_level = "medium"

    return {
        "exchange": exchange,
        "tier": tier,
        "transport": profile.get("transport", "unknown"),
        "typical_interval_ms": typical,
        "mid_price": round(mid, 8),
        "reference_mid": round(ref_mid, 8),
        "lag_pct": round(lag_pct, 4),
        "lag_bps": round(lag_pct * 100, 2),
        "feed_age_ms": round(feed_age_ms, 1) if feed_age_ms is not None else None,
        "data_freshness": chip,
        "headline": _headline(exchange, lag_pct, feed_age_ms=feed_age_ms),
        "source": source,
        "alert_level": alert_level,
        "informational_only": True,
    }


async def _resolve_reference(asset: str) -> tuple[dict[str, Any], str]:
    live = _live_reference(asset)
    if live:
        return live, "live_book_hub"

    rest = await _fetch_binance_rest(asset)
    if rest:
        rest["tier"] = "fast"
        rest["typical_interval_ms"] = FEED_PROFILES["binance"]["typical_interval_ms"]
        return rest, "binance_rest_fallback"

    cg = await _fetch_coingecko_fallback(asset)
    if cg:
        cg["tier"] = "fallback"
        return cg, "coingecko_fallback"

    return {"exchange": "unknown", "mid": 0.0, "source": "unavailable"}, "unavailable"


async def compare_feed_latency(
    symbol: str = "BTC",
    *,
    exchanges: list[str] | None = None,
) -> dict[str, Any]:
    """
    Compare slow vs fast feed prices for one asset.
    Informational Market Radar layer — Feature #111.
    """
    t0 = time.perf_counter()
    asset = _norm_asset(symbol)
    cache_key = f"feed_latency:{asset}:{','.join(exchanges or [])}"
    cached = _cache_get(cache_key)
    if cached:
        cached = dict(cached)
        cached["cache_hit"] = True
        cached["sla_met"] = (time.perf_counter() - t0) <= 3.0
        return cached

    ref, ref_source = await _resolve_reference(asset)
    ref_mid = float(ref.get("mid") or 0)
    if ref_mid <= 0:
        return {
            "ok": False,
            "feature_id": 111,
            "surface": "feed_latency",
            "product_name": "Data Freshness / Feed Latency",
            "symbol": asset,
            "error": "reference_price_unavailable",
            "disclaimer": _DISCLAIMER,
            "sla_met": (time.perf_counter() - t0) <= 3.0,
        }

    target_exchanges = exchanges or list(_SLOW_EXCHANGES) + [e for e in _FAST_EXCHANGES if e != ref.get("exchange")]

    fetchers = {
        "coinbase": _fetch_coinbase,
        "gateio": _fetch_gateio,
        "kucoin": _fetch_kucoin,
        "binance": _fetch_binance_rest,
    }

    venues: list[dict[str, Any]] = []

    # Reference row
    ref_age = ref.get("feed_age_ms")
    venues.append(
        _build_venue_row(
            exchange=str(ref.get("exchange") or "binance"),
            mid=ref_mid,
            ref_mid=ref_mid,
            source=str(ref.get("source") or ref_source),
            feed_age_ms=float(ref_age) if ref_age is not None else None,
            tier=str(ref.get("tier") or "fast"),
        )
    )
    venues[0]["role"] = "live_reference"
    venues[0]["headline"] = f"Live reference — {venues[0]['exchange']} ({ref_source})"

    tasks: list[tuple[str, Any]] = []
    for ex in target_exchanges:
        ex_l = ex.lower()
        if ex_l == str(ref.get("exchange") or "").lower():
            continue
        if ex_l in _FAST_EXCHANGES:
            try:
                from live_book_hub import get_best_price, get_quote_age_ms

                quote = get_best_price(ex_l, _pair_usdt(asset))
                age = get_quote_age_ms(ex_l, _pair_usdt(asset))
                if quote and quote.get("mid", 0) > 0:
                    venues.append(
                        _build_venue_row(
                            exchange=ex_l,
                            mid=float(quote["mid"]),
                            ref_mid=ref_mid,
                            source=f"{ex_l}_websocket",
                            feed_age_ms=age,
                        )
                    )
                    continue
            except ImportError:
                pass
        fn = fetchers.get(ex_l)
        if fn:
            tasks.append((ex_l, fn(asset)))

    if tasks:
        results = await asyncio.gather(*[t[1] for t in tasks], return_exceptions=True)
        for (ex_l, _), result in zip(tasks, results):
            if isinstance(result, Exception) or not result:
                venues.append({
                    "exchange": ex_l,
                    "tier": FEED_PROFILES.get(ex_l, {}).get("tier", "slow"),
                    "error": "fetch_failed",
                    "headline": f"{ex_l.title()} feed unavailable — rate limit or upstream error",
                    "informational_only": True,
                })
                continue
            profile = FEED_PROFILES.get(ex_l, {})
            venues.append(
                _build_venue_row(
                    exchange=ex_l,
                    mid=float(result["mid"]),
                    ref_mid=ref_mid,
                    source=str(result.get("source") or "rest"),
                    feed_age_ms=float(profile.get("typical_interval_ms", 2000)),
                    typical_interval_ms=int(profile.get("typical_interval_ms", 2000)),
                )
            )

    venues.sort(key=lambda v: abs(float(v.get("lag_pct") or 0)), reverse=True)
    slow_venues = [v for v in venues if v.get("tier") == "slow" and not v.get("error")]
    max_lag = max((abs(float(v.get("lag_pct") or 0)) for v in slow_venues), default=0.0)
    summary = "All monitored feeds aligned with live reference"
    if slow_venues:
        top = slow_venues[0]
        summary = top.get("headline") or summary

    alerts = [
        {
            "level": v.get("alert_level", "low"),
            "exchange": v.get("exchange"),
            "message": v.get("headline"),
            "lag_pct": v.get("lag_pct"),
        }
        for v in venues
        if v.get("alert_level") in {"medium", "high"} and v.get("role") != "live_reference"
    ]

    out = {
        "ok": True,
        "feature_id": 111,
        "surface": "feed_latency",
        "product_name": "Data Freshness / Feed Latency",
        "former_catalog_name": "Fast vs slow feed latency",
        "symbol": asset,
        "reference": {
            "exchange": ref.get("exchange"),
            "mid_price": round(ref_mid, 8),
            "source": ref_source,
            "feed_age_ms": ref.get("feed_age_ms"),
        },
        "summary": summary,
        "venue_count": len(venues),
        "max_lag_pct": round(max_lag, 4),
        "venues": venues,
        "alerts": alerts[:8],
        "feed_profiles": {k: FEED_PROFILES[k] for k in sorted(set(list(_FAST_EXCHANGES) + list(_SLOW_EXCHANGES)))},
        "cache_ttl_sec": {"hot": _CACHE_TTL_HOT_SEC, "warm": _CACHE_TTL_WARM_SEC, "cold": _CACHE_TTL_COLD_SEC},
        "rate_limit_handling": True,
        "fallback_chain": ["live_book_hub", "binance_rest", "coingecko"],
        "disclaimer": _DISCLAIMER,
        "mode": "informational_only",
        "market_radar": True,
        "tier_required": "pro",
        "cache_hit": False,
        "timestamp": _utcnow(),
        "sla_met": (time.perf_counter() - t0) <= 3.0,
    }

    ttl = _CACHE_TTL_HOT_SEC if ref_source == "live_book_hub" else _CACHE_TTL_WARM_SEC
    _cache_set(cache_key, out, ttl_sec=ttl)
    return out


async def feed_latency_overview(symbols: list[str] | None = None) -> dict[str, Any]:
    """Multi-asset feed latency snapshot for Market Radar dashboard."""
    t0 = time.perf_counter()
    assets = symbols or ["BTC", "ETH", "SOL"]
    results = await asyncio.gather(*[compare_feed_latency(a) for a in assets])
    rows = [r for r in results if r.get("ok")]
    headlines = [r.get("summary") for r in rows if r.get("summary")]

    return {
        "ok": True,
        "feature_id": 111,
        "surface": "feed_latency_overview",
        "product_name": "Data Freshness / Feed Latency",
        "assets": assets,
        "snapshots": rows,
        "headlines": headlines,
        "disclaimer": _DISCLAIMER,
        "mode": "informational_only",
        "sla_met": (time.perf_counter() - t0) <= 3.0,
        "timestamp": _utcnow(),
    }


def enrich_market_radar(payload: dict[str, Any], feed_snapshot: dict[str, Any]) -> dict[str, Any]:
    """Attach feed latency block to Market Radar narrative."""
    out = dict(payload)
    out["feed_latency"] = {
        "enabled": feed_snapshot.get("ok", False),
        "summary": feed_snapshot.get("summary"),
        "max_lag_pct": feed_snapshot.get("max_lag_pct"),
        "alerts": feed_snapshot.get("alerts", [])[:5],
        "disclaimer": _DISCLAIMER,
    }
    return out
