"""
BLACKDARK — Oracle Data Hub (free-tier intelligence mesh).

Unifies six free data pillars for the AI Oracle:
1. Free LLM providers (Ollama, Groq, Gemini, OpenRouter, HuggingFace)
2. Global economic / geopolitical news (RSS)
3. Sentiment indices (Fear & Greed, CoinGecko trending, Reddit)
4. On-chain + derivatives (DeFiLlama, exchange public APIs)
5. Macro traditional markets (Yahoo Finance extended)
6. Market aggregators (CoinGecko global, CoinCap)
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp

import config
from log_safety import sanitize_asset, sanitize_log_value

logger = logging.getLogger("BLACKDARK.OracleDataHub")

GEOPOLITICAL_KEYWORDS = (
    "war",
    "conflict",
    "ceasefire",
    "peace",
    "sanction",
    "inflation",
    "recession",
    "fed",
    "rate hike",
    "rate cut",
    "tariff",
    "election",
    "crisis",
    "default",
    "oil",
    "energy",
    "central bank",
    "gdp",
    "unemployment",
    "geopolit",
    "nato",
    "missile",
    "invasion",
)

RiskTone = Literal["risk_on", "risk_off", "neutral"]


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _hub_enabled() -> bool:
    return os.getenv("ORACLE_DATA_HUB_ENABLED", "true").lower() in {"1", "true", "yes"}


class _TTLCache:
    def __init__(self, ttl_seconds: int = 90) -> None:
        self.ttl = ttl_seconds
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        row = self._store.get(key)
        if not row:
            return None
        ts, value = row
        if time.time() - ts > self.ttl:
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)


_CACHE = _TTLCache(int(os.getenv("ORACLE_HUB_CACHE_SECONDS", "90")))


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


async def _fetch_text(
    session: aiohttp.ClientSession,
    url: str,
    *,
    headers: dict[str, str] | None = None,
) -> str:
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        return await response.text()


def _parse_rss_headlines(payload: str, source: str, limit: int = 12) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return items

    for entry in root.findall(".//item")[:limit]:
        title = (entry.findtext("title") or "").strip()
        if not title:
            continue
        lower = title.lower()
        geo_hit = any(kw in lower for kw in GEOPOLITICAL_KEYWORDS)
        items.append(
            {
                "title": title[:240],
                "source": source,
                "published_at": entry.findtext("pubDate"),
                "geopolitical": geo_hit,
            }
        )
    return items


async def fetch_global_economic_news(session: aiohttp.ClientSession) -> dict[str, Any]:
    cached = _CACHE.get("geo_news")
    if cached is not None:
        return cached

    headlines: list[dict[str, Any]] = []
    for feed_url in config.ORACLE_GEO_NEWS_RSS_FEEDS:
        label = feed_url.split("//")[-1].split("/")[0]
        try:
            payload = await _fetch_text(session, feed_url)
            headlines.extend(_parse_rss_headlines(payload, label))
        except Exception:
            logger.warning("Geo news RSS failed | feed=%s", sanitize_log_value(feed_url, max_len=120))

    geo_count = sum(1 for row in headlines if row.get("geopolitical"))
    tone: RiskTone = "neutral"
    if geo_count >= 4:
        tone = "risk_off"
    elif geo_count <= 1 and headlines:
        tone = "risk_on"

    result = {
        "headlines": headlines[:20],
        "geopolitical_headline_count": geo_count,
        "macro_news_tone": tone,
        "sources": len(config.ORACLE_GEO_NEWS_RSS_FEEDS),
    }
    _CACHE.set("geo_news", result)
    return result


async def fetch_sentiment_mesh(session: aiohttp.ClientSession) -> dict[str, Any]:
    cached = _CACHE.get("sentiment_mesh")
    if cached is not None:
        return cached

    fear_greed_value = 50
    fear_greed_label = "Neutral"
    trending: list[str] = []
    reddit_hot: list[str] = []

    try:
        fng = await _fetch_json(session, "https://api.alternative.me/fng/", params={"limit": "1"})
        row = (fng.get("data") or [{}])[0]
        fear_greed_value = int(row.get("value") or 50)
        fear_greed_label = str(row.get("value_classification") or "Neutral")
    except Exception:
        logger.warning("Fear & Greed index fetch failed.")

    try:
        trending_payload = await _fetch_json(
            session,
            "https://api.coingecko.com/api/v3/search/trending",
        )
        for coin in (trending_payload.get("coins") or [])[:7]:
            item = coin.get("item") or {}
            symbol = str(item.get("symbol") or "").upper()
            if symbol:
                trending.append(symbol)
    except Exception:
        logger.warning("CoinGecko trending fetch failed.")

    try:
        reddit_headers = {"User-Agent": "BLACKDARK-Oracle/1.0"}
        reddit = await _fetch_json(
            session,
            "https://www.reddit.com/r/CryptoCurrency/hot.json",
            params={"limit": "8"},
            headers=reddit_headers,
        )
        for child in (reddit.get("data") or {}).get("children") or []:
            title = str((child.get("data") or {}).get("title") or "").strip()
            if title:
                reddit_hot.append(title[:180])
    except Exception:
        logger.warning("Reddit sentiment fetch failed.")

    compound = _clamp((fear_greed_value - 50) / 50.0)
    result = {
        "fear_greed_index": fear_greed_value,
        "fear_greed_label": fear_greed_label,
        "coingecko_trending": trending,
        "reddit_hot_titles": reddit_hot,
        "sentiment_compound_proxy": round(compound, 3),
    }
    _CACHE.set("sentiment_mesh", result)
    return result


async def fetch_onchain_derivatives_mesh(
    session: aiohttp.ClientSession,
    asset: str = "BTC",
) -> dict[str, Any]:
    cache_key = f"onchain_deriv_{asset}"
    cached = _CACHE.get(cache_key)
    if cached is not None:
        return cached

    symbol = asset.upper()
    binance_symbol = f"{symbol}USDT"
    if not binance_symbol.isalnum():
        return {
            "asset": symbol,
            "defi_tvl_usd": 0.0,
            "defi_chain_count": 0,
            "funding_rate": None,
            "open_interest_usd": None,
            "long_short_ratio": None,
            "derivatives_bias": "neutral",
            "sources": [],
        }

    tvl_total_usd = 0.0
    chain_count = 0
    funding_rate = None
    open_interest_usd = None
    long_short_ratio = None

    try:
        chains = await _fetch_json(session, "https://api.llama.fi/v2/chains")
        chain_count = len(chains or [])
        tvl_total_usd = sum(float(row.get("tvl") or 0) for row in chains or [])
    except Exception:
        logger.warning("DeFiLlama chains fetch failed.")

    try:
        funding = await _fetch_json(
            session,
            "https://fapi.binance.com/fapi/v1/premiumIndex",
            params={"symbol": binance_symbol},
        )
        funding_rate = float(funding.get("lastFundingRate") or 0)
    except Exception:
        logger.warning("Binance funding fetch failed | asset=%s", sanitize_asset(symbol))

    try:
        oi = await _fetch_json(
            session,
            "https://fapi.binance.com/fapi/v1/openInterest",
            params={"symbol": binance_symbol},
        )
        oi_qty = float(oi.get("openInterest") or 0)
        if funding_rate is not None:
            mark = await _fetch_json(
                session,
                "https://fapi.binance.com/fapi/v1/ticker/price",
                params={"symbol": binance_symbol},
            )
            price = float(mark.get("price") or 0)
            open_interest_usd = round(oi_qty * price, 2)
    except Exception:
        logger.warning("Binance OI fetch failed | asset=%s", sanitize_asset(symbol))

    try:
        ls = await _fetch_json(
            session,
            "https://fapi.binance.com/futures/data/globalLongShortAccountRatio",
            params={"symbol": binance_symbol, "period": "1h", "limit": "1"},
        )
        if ls:
            long_short_ratio = float(ls[0].get("longShortRatio") or 1.0)
    except Exception:
        logger.warning("Binance long/short ratio fetch failed | asset=%s", sanitize_asset(symbol))

    deriv_bias = "neutral"
    if funding_rate is not None:
        if funding_rate > 0.0003:
            deriv_bias = "overheated_longs"
        elif funding_rate < -0.0001:
            deriv_bias = "short_crowded"

    result = {
        "asset": symbol,
        "defi_tvl_usd": round(tvl_total_usd, 2),
        "defi_chain_count": chain_count,
        "funding_rate": funding_rate,
        "open_interest_usd": open_interest_usd,
        "long_short_ratio": long_short_ratio,
        "derivatives_bias": deriv_bias,
        "sources": ["DeFiLlama", "Binance Futures Public API"],
    }
    _CACHE.set(cache_key, result)
    return result


async def fetch_macro_mesh(session: aiohttp.ClientSession) -> dict[str, Any]:
    cached = _CACHE.get("macro_mesh")
    if cached is not None:
        return cached

    symbols = {
        "dxy": config.MACRO_YAHOO_DXY_SYMBOL,
        "spx": config.MACRO_YAHOO_SPX_SYMBOL,
        "vix": config.ORACLE_MACRO_VIX_SYMBOL,
        "us10y": config.ORACLE_MACRO_US10Y_SYMBOL,
        "nasdaq": config.ORACLE_MACRO_NASDAQ_SYMBOL,
        "gold": config.MACRO_YAHOO_GOLD_SYMBOL,
        "oil": config.ORACLE_MACRO_OIL_SYMBOL,
    }

    async def _yahoo_change(sym: str) -> float | None:
        try:
            payload = await _fetch_json(
                session,
                f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}",
                params={"interval": "1d", "range": "5d"},
            )
            result = (payload.get("chart") or {}).get("result") or []
            if not result:
                return None
            closes = (
                ((result[0].get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
            )
            valid = [float(v) for v in closes if v is not None]
            if len(valid) < 2 or valid[-2] == 0:
                return None
            return round((valid[-1] - valid[-2]) / valid[-2], 4)
        except Exception:
            return None

    changes: dict[str, float | None] = {}
    for label, sym in symbols.items():
        changes[label] = await _yahoo_change(sym)

    vix = changes.get("vix") or 0.0
    dxy = changes.get("dxy") or 0.0
    spx = changes.get("spx") or 0.0

    regime: RiskTone = "neutral"
    if vix > 0.08 or dxy > 0.002 or spx < -0.01:
        regime = "risk_off"
    elif vix < -0.03 and spx > 0.005 and dxy < 0:
        regime = "risk_on"

    result = {
        "changes_1d_pct": changes,
        "macro_regime_proxy": regime,
        "sources": ["Yahoo Finance (free chart API)"],
    }
    _CACHE.set("macro_mesh", result)
    return result


async def fetch_aggregator_mesh(session: aiohttp.ClientSession) -> dict[str, Any]:
    cached = _CACHE.get("aggregator_mesh")
    if cached is not None:
        return cached

    global_data: dict[str, Any] = {}
    top_assets: list[dict[str, Any]] = []

    try:
        gecko = await _fetch_json(session, "https://api.coingecko.com/api/v3/global")
        data = gecko.get("data") or {}
        global_data = {
            "total_market_cap_usd": data.get("total_market_cap", {}).get("usd"),
            "total_volume_usd": data.get("total_volume", {}).get("usd"),
            "btc_dominance_pct": data.get("market_cap_percentage", {}).get("btc"),
            "market_cap_change_24h_pct": data.get("market_cap_change_percentage_24h_usd"),
        }
    except Exception:
        logger.warning("CoinGecko global fetch failed.")

    try:
        coincap = await _fetch_json(session, "https://api.coincap.io/v2/assets", params={"limit": "10"})
        for row in coincap.get("data") or []:
            top_assets.append(
                {
                    "symbol": str(row.get("symbol") or "").upper(),
                    "price_usd": float(row.get("priceUsd") or 0),
                    "change_24h_pct": float(row.get("changePercent24Hr") or 0),
                }
            )
    except Exception:
        logger.warning("CoinCap fetch failed.")

    result = {
        "coingecko_global": global_data,
        "coincap_top10": top_assets,
        "sources": ["CoinGecko", "CoinCap"],
    }
    _CACHE.set("aggregator_mesh", result)
    return result


async def _ollama_sentence(prompt: str) -> str | None:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    try:
        timeout = aiohttp.ClientTimeout(total=18)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
        ) as response:
            response.raise_for_status()
            data = await response.json()
        text = str(data.get("response") or "").strip().split("\n")[0]
        return text or None
    except Exception:
        return None


async def _groq_sentence(prompt: str) -> str | None:
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        return None
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply with one sentence only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 80,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        timeout = aiohttp.ClientTimeout(total=18)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()
        return str(data["choices"][0]["message"]["content"]).strip() or None
    except Exception:
        return None


async def _gemini_sentence(prompt: str) -> str | None:
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        timeout = aiohttp.ClientTimeout(total=18)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
            url,
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        ) as response:
            response.raise_for_status()
            data = await response.json()
        parts = (
            ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [{}]
        )
        text = str(parts[0].get("text") or "").strip()
        return text.split("\n")[0] or None
    except Exception:
        return None


async def _openrouter_sentence(prompt: str) -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        return None
    model = os.getenv("OPENROUTER_MODEL", "google/gemma-2-9b-it:free")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Reply with one sentence only."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 80,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://blackdark.app",
    }
    try:
        timeout = aiohttp.ClientTimeout(total=18)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            data = await response.json()
        return str(data["choices"][0]["message"]["content"]).strip() or None
    except Exception:
        return None


async def synthesize_with_free_llm_chain(
    asset: str,
    opportunity_score: float,
    summary: str,
    hub_context: dict[str, Any],
) -> str | None:
    """Try free LLM providers in order until one responds."""
    macro = hub_context.get("macro") or {}
    sentiment = hub_context.get("sentiment") or {}
    geo = hub_context.get("geo_news") or {}

    prompt = (
        "You are a crypto oracle. Return ONE sentence starting with 'Buy Now' or 'Do Not Touch', "
        "then em dash, then reason. Consider war/peace news, macro, fear/greed, derivatives.\n"
        f"Asset={asset}, score={opportunity_score}, summary={summary}\n"
        f"Macro regime={macro.get('macro_regime_proxy')}, "
        f"FearGreed={sentiment.get('fear_greed_index')}, "
        f"Geo headlines={geo.get('geopolitical_headline_count')}"
    )

    chain = os.getenv(
        "ORACLE_FREE_LLM_CHAIN",
        "groq,gemini,openrouter,ollama",
    ).split(",")

    handlers = {
        "ollama": _ollama_sentence,
        "groq": _groq_sentence,
        "gemini": _gemini_sentence,
        "openrouter": _openrouter_sentence,
    }

    for name in chain:
        handler = handlers.get(name.strip().lower())
        if handler is None:
            continue
        sentence = await handler(prompt)
        if sentence and ("Buy Now" in sentence or "Do Not Touch" in sentence):
            return sentence
    return None


def hub_score_adjustment(asset: str, hub_context: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    """Return score delta, reasons, risks from hub context."""
    delta = 0.0
    reasons: list[str] = []
    risks: list[str] = []

    sentiment = hub_context.get("sentiment") or {}
    fg = int(sentiment.get("fear_greed_index") or 50)
    if fg >= 75:
        delta += 2.0
        reasons.append(f"Market greed index elevated ({fg}) — momentum tailwind.")
    elif fg <= 25:
        delta -= 3.0
        risks.append(f"Extreme fear index ({fg}) — capitulation risk.")

    geo = hub_context.get("geo_news") or {}
    geo_count = int(geo.get("geopolitical_headline_count") or 0)
    if geo_count >= 3:
        delta -= 4.0
        risks.append(
            f"{geo_count} geopolitical/macro headlines — war/peace/policy shock risk."
        )
    elif geo.get("macro_news_tone") == "risk_on":
        delta += 1.5
        reasons.append("Global headline tone supportive — reduced macro shock risk.")

    macro = hub_context.get("macro") or {}
    if macro.get("macro_regime_proxy") == "risk_off":
        delta -= 3.0
        risks.append("Macro mesh risk-off (VIX/DXY/SPX stress).")
    elif macro.get("macro_regime_proxy") == "risk_on":
        delta += 2.0
        reasons.append("Macro mesh risk-on — traditional markets supportive.")

    deriv = hub_context.get("derivatives") or {}
    bias = str(deriv.get("derivatives_bias") or "neutral")
    if bias == "overheated_longs":
        delta -= 2.0
        risks.append("Derivatives overheated — crowded long funding.")
    elif bias == "short_crowded":
        delta += 1.5
        reasons.append("Derivatives short-crowded — squeeze potential.")

    agg = hub_context.get("aggregators") or {}
    mc_change = (agg.get("coingecko_global") or {}).get("market_cap_change_24h_pct")
    if mc_change is not None:
        try:
            mc_val = float(mc_change)
            if mc_val >= 2.0:
                delta += 1.0
                reasons.append(f"Total crypto market cap +{mc_val:.1f}% 24h.")
            elif mc_val <= -2.0:
                delta -= 2.0
                risks.append(f"Total crypto market cap {mc_val:.1f}% 24h — broad risk-off.")
        except (TypeError, ValueError):
            pass

    if asset.upper() in (sentiment.get("coingecko_trending") or []):
        delta += 1.0
        reasons.append(f"{asset.upper()} trending on CoinGecko — social attention.")

    delta = max(-12.0, min(12.0, delta))
    return round(delta, 2), reasons, risks


async def build_oracle_data_hub_context(asset: str | None = None) -> dict[str, Any]:
    """
    Build oracle context from data lake first (architecture: scheduler → lake → oracle).
    Falls back to live API fetch only when lake is empty (cold start).
    """
    if not _hub_enabled():
        return {"enabled": False}

    symbol = (asset or "BTC").upper()

    from data_lake import build_lake_context_for_oracle

    lake_ctx = await build_lake_context_for_oracle(symbol)
    loaded = lake_ctx.get("lake_categories_loaded") or []
    if lake_ctx.get("enabled") and len(loaded) >= 2:
        lake_ctx["data_source"] = "data_lake"
        lake_ctx["free_llm_providers"] = [
            name.strip()
            for name in os.getenv(
                "ORACLE_FREE_LLM_CHAIN",
                "groq,gemini,openrouter,ollama",
            ).split(",")
            if name.strip()
        ]
        lake_ctx["pillars"] = [*loaded, "free_llm_chain"]
        return lake_ctx

    timeout = aiohttp.ClientTimeout(total=config.ORACLE_HUB_FETCH_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        geo, sentiment, derivatives, macro, aggregators = await asyncio.gather(
            fetch_global_economic_news(session),
            fetch_sentiment_mesh(session),
            fetch_onchain_derivatives_mesh(session, symbol),
            fetch_macro_mesh(session),
            fetch_aggregator_mesh(session),
            return_exceptions=True,
        )

    def _safe(value: Any, fallback: dict[str, Any]) -> dict[str, Any]:
        return value if isinstance(value, dict) else fallback

    return {
        "enabled": True,
        "data_source": "live_fallback",
        "asset": symbol,
        "timestamp": _utcnow_iso(),
        "geo_news": _safe(geo, {}),
        "sentiment": _safe(sentiment, {}),
        "derivatives": _safe(derivatives, {}),
        "macro": _safe(macro, {}),
        "aggregators": _safe(aggregators, {}),
        "free_llm_providers": [
            name.strip()
            for name in os.getenv(
                "ORACLE_FREE_LLM_CHAIN",
                "groq,gemini,openrouter,ollama",
            ).split(",")
            if name.strip()
        ],
        "pillars": [
            "free_llm_chain",
            "global_economic_news",
            "sentiment_mesh",
            "onchain_derivatives",
            "macro_traditional",
            "market_aggregators",
        ],
    }


def merge_hub_context(base: dict[str, Any] | None, hub: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base or {})
    merged["oracle_data_hub"] = hub
    return merged


async def build_hub_context_safe(asset: str | None = None) -> dict[str, Any]:
    try:
        return await build_oracle_data_hub_context(asset)
    except Exception:
        logger.exception("Oracle data hub build failed.")
        return {"enabled": False, "error": "hub_fetch_failed"}
