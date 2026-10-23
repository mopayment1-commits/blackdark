"""
Central on-demand data mesh — OpenBB, Frankfurter, Marketaux, NewsData, SEC EDGAR,
CoinStats (optional), UN Comtrade (low priority).

Keys only from environment. Per-source timeout + explicit fallback payloads.
Cached per source — not fetched on every Oracle request unless stale.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import UTC, datetime
from typing import Any

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.CentralDataMesh")

MESH_ENABLED = os.getenv("CENTRAL_DATA_MESH_ENABLED", "true").lower() in {"1", "true", "yes"}
MESH_CACHE_SECONDS = int(os.getenv("CENTRAL_DATA_MESH_CACHE_SECONDS", "120"))
MESH_TIMEOUT_SECONDS = float(os.getenv("CENTRAL_DATA_MESH_TIMEOUT_SECONDS", "8"))

_SEC_USER_AGENT = os.getenv(
    "SEC_EDGAR_USER_AGENT",
    os.getenv("BLACKDARK_CONTACT_EMAIL", "research@blackdark.io"),
)
if _SEC_USER_AGENT and not _SEC_USER_AGENT.startswith("("):
    _SEC_USER_AGENT = f"BLACKDARK/1.0 ({_SEC_USER_AGENT})"


class _TTLCache:
    def __init__(self, ttl: int) -> None:
        self.ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        row = self._store.get(key)
        if not row:
            return None
        ts, val = row
        if time.time() - ts > self.ttl:
            return None
        return val

    def set(self, key: str, val: Any) -> None:
        self._store[key] = (time.time(), val)


_CACHE = _TTLCache(MESH_CACHE_SECONDS)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _fallback(source: str, reason: str = "unavailable") -> dict[str, Any]:
    return {"ok": False, "source": source, "fallback": reason, "fetched_at": _utcnow()}


async def _get_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    async with session.get(url, params=params, headers=headers) as resp:
        resp.raise_for_status()
        return await resp.json()


# ── 1) OpenBB Platform (optional HTTP gateway or local SDK) ───────────────────


async def fetch_openbb_snapshot(
    session: aiohttp.ClientSession,
    *,
    symbol: str = "BTC",
) -> dict[str, Any]:
    cache_key = f"openbb:{symbol}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    base = (os.getenv("OPENBB_API_BASE") or "").strip().rstrip("/")
    token = (os.getenv("OPENBB_API_KEY") or os.getenv("OPENBB_TOKEN") or "").strip()
    if base:
        try:
            headers = {"Authorization": f"Bearer {token}"} if token else None
            data = await _get_json(
                session,
                f"{base}/v1/equity/price/quote",
                params={"symbol": "SPY"},
                headers=headers,
            )
            row = {
                "ok": True,
                "source": "openbb_http",
                "macro_proxy": data,
                "fetched_at": _utcnow(),
            }
            _CACHE.set(cache_key, row)
            return row
        except Exception as exc:
            logger.debug("openbb http failed: %s", exc)
            return _fallback("openbb", "http_error")

    if os.getenv("OPENBB_SDK_ENABLED", "").lower() in {"1", "true", "yes"}:
        try:
            payload = await asyncio.wait_for(_openbb_sdk_snapshot(symbol), timeout=MESH_TIMEOUT_SECONDS)
            _CACHE.set(cache_key, payload)
            return payload
        except Exception as exc:
            logger.debug("openbb sdk failed: %s", exc)
            return _fallback("openbb", "sdk_error")

    return _fallback("openbb", "not_configured")


async def _openbb_sdk_snapshot(symbol: str) -> dict[str, Any]:
    def _run() -> dict[str, Any]:
        from openbb import obb  # type: ignore[import-not-found]

        eq = obb.equity.price.quote(symbol="SPY")
        return {
            "ok": True,
            "source": "openbb_sdk",
            "macro_proxy": eq.to_dict() if hasattr(eq, "to_dict") else str(eq),
            "asset_hint": symbol.upper(),
            "fetched_at": _utcnow(),
        }

    return await asyncio.to_thread(_run)


# ── 2) Frankfurter (ECB reference FX, no key) ─────────────────────────────────


async def fetch_frankfurter_fx(session: aiohttp.ClientSession) -> dict[str, Any]:
    cache_key = "frankfurter:usd"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        data = await _get_json(
            session,
            "https://api.frankfurter.app/latest",
            params={"from": "USD", "to": "EUR,GBP,JPY,CHF,CAD,AUD"},
        )
        rates = data.get("rates") or {}
        eur = float(rates.get("EUR") or 0)
        usd_strength = "neutral"
        if eur > 0:
            if eur < 0.9:
                usd_strength = "strong"
            elif eur > 1.05:
                usd_strength = "weak"
        row = {
            "ok": True,
            "source": "frankfurter",
            "base": "USD",
            "rates": rates,
            "date": data.get("date"),
            "usd_strength_proxy": usd_strength,
            "fetched_at": _utcnow(),
        }
        _CACHE.set(cache_key, row)
        return row
    except Exception as exc:
        logger.debug("frankfurter failed: %s", exc)
        return _fallback("frankfurter", "fetch_error")


# ── 3) Marketaux (news + sentiment) ───────────────────────────────────────────


async def fetch_marketaux_news(
    session: aiohttp.ClientSession,
    *,
    symbol: str = "BTC",
) -> dict[str, Any]:
    key = (os.getenv("MARKETAUX_API_KEY") or "").strip()
    if not key:
        return _fallback("marketaux", "missing_api_key")
    cache_key = f"marketaux:{symbol}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        data = await _get_json(
            session,
            "https://api.marketaux.com/v1/news/all",
            params={
                "api_token": key,
                "symbols": f"{symbol}-USD",
                "filter_entities": "true",
                "language": "en",
                "limit": 5,
            },
        )
        articles = data.get("data") or []
        scores = [float(a.get("sentiment") or 0) for a in articles if a.get("sentiment") is not None]
        avg_sent = sum(scores) / len(scores) if scores else None
        row = {
            "ok": True,
            "source": "marketaux",
            "headline_count": len(articles),
            "avg_sentiment": avg_sent,
            "headlines": [a.get("title") for a in articles[:3] if a.get("title")],
            "fetched_at": _utcnow(),
        }
        _CACHE.set(cache_key, row)
        return row
    except Exception as exc:
        logger.debug("marketaux failed: %s", exc)
        return _fallback("marketaux", "fetch_error")


# ── 4) NewsData.io ────────────────────────────────────────────────────────────


async def fetch_newsdata_headlines(session: aiohttp.ClientSession) -> dict[str, Any]:
    key = (os.getenv("NEWSDATA_API_KEY") or "").strip()
    if not key:
        return _fallback("newsdata", "missing_api_key")
    cache_key = "newsdata:business"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        data = await _get_json(
            session,
            "https://newsdata.io/api/1/news",
            params={"apikey": key, "category": "business", "language": "en", "size": 5},
        )
        results = data.get("results") or []
        row = {
            "ok": True,
            "source": "newsdata",
            "headline_count": len(results),
            "headlines": [r.get("title") for r in results[:5] if r.get("title")],
            "fetched_at": _utcnow(),
        }
        _CACHE.set(cache_key, row)
        return row
    except Exception as exc:
        logger.debug("newsdata failed: %s", exc)
        return _fallback("newsdata", "fetch_error")


# ── 5) SEC EDGAR (public filings feed) ────────────────────────────────────────


async def fetch_sec_edgar_pulse(session: aiohttp.ClientSession) -> dict[str, Any]:
    cache_key = "sec_edgar:current"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    headers = {"User-Agent": _SEC_USER_AGENT, "Accept": "application/json"}
    try:
        data = await _get_json(
            session,
            "https://www.sec.gov/files/company_tickers.json",
            headers=headers,
        )
        entries = list(data.values()) if isinstance(data, dict) else []
        row = {
            "ok": True,
            "source": "sec_edgar",
            "listed_companies_sample": len(entries),
            "attribution": "U.S. SEC EDGAR",
            "fetched_at": _utcnow(),
        }
        _CACHE.set(cache_key, row)
        return row
    except Exception as exc:
        logger.debug("sec edgar failed: %s", exc)
        return _fallback("sec_edgar", "fetch_error")


# ── 6) CoinStats (optional) ─────────────────────────────────────────────────


async def fetch_coinstats_market(
    session: aiohttp.ClientSession,
    *,
    asset: str = "BTC",
) -> dict[str, Any]:
    key = (os.getenv("COINSTATS_API_KEY") or "").strip()
    slug = {"BTC": "bitcoin", "ETH": "ethereum"}.get(asset.upper(), asset.lower())
    cache_key = f"coinstats:{slug}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    headers = {"X-API-KEY": key} if key else {}
    try:
        data = await _get_json(
            session,
            f"https://openapiv1.coinstats.app/coins/{slug}",
            headers=headers or None,
        )
        coin = data.get("coin") or data
        row = {
            "ok": True,
            "source": "coinstats",
            "symbol": asset.upper(),
            "price_usd": coin.get("price"),
            "market_cap": coin.get("marketCap"),
            "volume_24h": coin.get("volume"),
            "api_key_used": bool(key),
            "fetched_at": _utcnow(),
        }
        _CACHE.set(cache_key, row)
        return row
    except Exception as exc:
        logger.debug("coinstats failed: %s", exc)
        return _fallback("coinstats", "fetch_error")


# ── 7) UN Comtrade (supplementary, low priority) ────────────────────────────


async def fetch_un_comtrade_hint(session: aiohttp.ClientSession) -> dict[str, Any]:
    if os.getenv("UN_COMTRADE_ENABLED", "").lower() not in {"1", "true", "yes"}:
        return _fallback("un_comtrade", "disabled")
    key = (os.getenv("UN_COMTRADE_API_KEY") or os.getenv("COMTRADE_API_KEY") or "").strip()
    if not key:
        return _fallback("un_comtrade", "missing_api_key")
    cache_key = "un_comtrade:hint"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached
    try:
        data = await _get_json(
            session,
            "https://comtradeapi.un.org/data/v1/get/C/A/HS",
            params={
                "subscription-key": key,
                "reporterCode": "842",
                "period": "2023",
                "partnerCode": "0",
                "flowCode": "X",
                "breakdownMode": "classic",
                "countCode": "ALL",
            },
        )
        row = {
            "ok": True,
            "source": "un_comtrade",
            "records": len(data.get("data") or data.get("dataset") or []),
            "supplementary": True,
            "fetched_at": _utcnow(),
        }
        _CACHE.set(cache_key, row)
        return row
    except Exception as exc:
        logger.debug("un comtrade failed: %s", exc)
        return _fallback("un_comtrade", "fetch_error")


async def build_central_mesh_context(
    asset: str = "BTC",
    *,
    profile: str = "oracle",
) -> dict[str, Any]:
    """
    Fetch only what the profile needs (oracle: FX + news/regulatory + optional keys).
    """
    if not MESH_ENABLED:
        return {"enabled": False, "sources_active": [], "sources": {}}

    symbol = (asset or "BTC").upper()
    timeout = aiohttp.ClientTimeout(total=MESH_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        if profile == "minimal":
            task_names = ("frankfurter", "sec_edgar")
            coros = (
                fetch_frankfurter_fx(session),
                fetch_sec_edgar_pulse(session),
            )
        else:
            task_names = (
                "frankfurter",
                "sec_edgar",
                "openbb",
                "marketaux",
                "newsdata",
                "coinstats",
                "un_comtrade",
            )
            coros = (
                fetch_frankfurter_fx(session),
                fetch_sec_edgar_pulse(session),
                fetch_openbb_snapshot(session, symbol=symbol),
                fetch_marketaux_news(session, symbol=symbol),
                fetch_newsdata_headlines(session),
                fetch_coinstats_market(session, asset=symbol),
                fetch_un_comtrade_hint(session),
            )

        keys = list(task_names)
        results = await asyncio.gather(*coros, return_exceptions=True)
        sources: dict[str, Any] = {}
        active: list[str] = []
        for name, result in zip(keys, results, strict=True):
            if isinstance(result, Exception):
                sources[name] = _fallback(name, "exception")
            else:
                sources[name] = result
            if isinstance(sources[name], dict) and sources[name].get("ok"):
                active.append(name)

    return {
        "enabled": True,
        "asset": symbol,
        "profile": profile,
        "timestamp": _utcnow(),
        "sources": sources,
        "sources_active": active,
        "cache_ttl_seconds": MESH_CACHE_SECONDS,
    }


def merge_mesh_into_hub(hub: dict[str, Any], mesh: dict[str, Any]) -> dict[str, Any]:
    if not mesh.get("enabled"):
        return hub
    out = dict(hub)
    out["central_data_mesh"] = mesh
    pillars = list(out.get("pillars") or [])
    for src in mesh.get("sources_active") or []:
        tag = f"mesh_{src}"
        if tag not in pillars:
            pillars.append(tag)
    out["pillars"] = pillars
    fx = (mesh.get("sources") or {}).get("frankfurter") or {}
    if fx.get("ok"):
        macro = dict(out.get("macro") or {})
        macro["fx_usd_rates"] = fx.get("rates")
        macro["usd_strength_proxy"] = fx.get("usd_strength_proxy")
        out["macro"] = macro
    ma = (mesh.get("sources") or {}).get("marketaux") or {}
    nd = (mesh.get("sources") or {}).get("newsdata") or {}
    if ma.get("ok") or nd.get("ok"):
        sentiment = dict(out.get("sentiment") or {})
        if ma.get("ok"):
            sentiment["marketaux_avg_sentiment"] = ma.get("avg_sentiment")
            sentiment["marketaux_headlines"] = ma.get("headlines")
        if nd.get("ok"):
            sentiment["newsdata_headlines"] = nd.get("headlines")
        out["sentiment"] = sentiment
    sec = (mesh.get("sources") or {}).get("sec_edgar") or {}
    if sec.get("ok"):
        geo = dict(out.get("geo_news") or {})
        geo["sec_edgar_companies_indexed"] = sec.get("listed_companies_sample")
        out["geo_news"] = geo
    cs = (mesh.get("sources") or {}).get("coinstats") or {}
    if cs.get("ok"):
        agg = dict(out.get("aggregators") or {})
        agg["coinstats_price_usd"] = cs.get("price_usd")
        agg["coinstats_volume_24h"] = cs.get("volume_24h")
        out["aggregators"] = agg
    return out


async def attach_mesh_to_oracle_payload(payload: dict[str, Any], asset: str) -> None:
    """Non-blocking enrichment for /oracle/quick responses (metadata only)."""
    try:
        mesh = await build_central_mesh_context(asset, profile="minimal")
        if mesh.get("enabled"):
            payload["central_data_mesh"] = {
                "sources_active": mesh.get("sources_active"),
                "sources": mesh.get("sources"),
            }
    except Exception:
        logger.debug("mesh attach to oracle quick failed", exc_info=True)


async def enrich_hub_with_central_mesh(hub: dict[str, Any], asset: str | None) -> dict[str, Any]:
    symbol = (asset or hub.get("asset") or "BTC").upper()
    mesh = await build_central_mesh_context(symbol, profile="oracle")
    return merge_mesh_into_hub(hub, mesh)
