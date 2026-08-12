"""
BLACKDARK — AI NLP Sentiment & News Radar (Phase 4 / Data Flywheel Expansion).

Polls multi-source crypto headlines, scores sentiment, persists logs, and
exposes rolling compound indices for opportunity scoring.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
import defusedxml.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp
from pydantic import BaseModel, Field

import config
from database import (
    fetch_all_rolling_compound_sentiment_indices,
    fetch_rolling_compound_sentiment_index,
    fetch_sentiment_logs_for_asset,
    init_db,
    insert_market_sentiment_logs,
)
logger = logging.getLogger("BLACKDARK.SentimentEngine")

NewsSource = Literal[
    "rss",
    "cryptocompare",
    "twitter_mock",
    "telegram_mock",
    "llm_fallback",
    "rules",
]

ASSET_ALIASES: dict[str, tuple[str, ...]] = {
    "BTC": ("BTC", "BITCOIN", "XBT"),
    "ETH": ("ETH", "ETHEREUM", "ETHER"),
    "SOL": ("SOL", "SOLANA"),
    "BNB": ("BNB", "BINANCE COIN"),
    "XRP": ("XRP", "RIPPLE"),
}

FEAR_KEYWORDS = (
    "crash",
    "plunge",
    "dump",
    "panic",
    "sell-off",
    "selloff",
    "hack",
    "exploit",
    "ban",
    "lawsuit",
    "sec sues",
    "liquidation",
    "bear",
    "fear",
    "outflow",
    "collapse",
    "warning",
    "risk-off",
)

GREED_KEYWORDS = (
    "surge",
    "rally",
    "breakout",
    "approval",
    "etf inflow",
    "inflow",
    "all-time high",
    "ath",
    "bull",
    "moon",
    "fomo",
    "accumulation",
    "partnership",
    "upgrade",
    "adoption",
    "greed",
)


class SentimentNewsItem(BaseModel):
    asset: str
    sector: str | None = None
    source: str
    raw_text: str
    published_at: str | None = None


class SentimentAnalysisResult(BaseModel):
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    analyzer: str
    compound_momentum: float = Field(default=0.0, ge=-1.0, le=1.0)


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _sector_for_asset(asset: str) -> str | None:
    return config.SECTOR_MAP.get(asset)


def _normalize_asset(asset: str) -> str:
    return asset.strip().upper()


def _operational_assets() -> list[str]:
    try:
        from liquidity_discovery import load_operational_manifest, operational_assets_from_manifest

        manifest = load_operational_manifest()
        if manifest is not None:
            return operational_assets_from_manifest(manifest)
    except Exception:
        logger.debug("Operational manifest unavailable; using whitelist assets.")
    return sorted(config.WHITELIST_ASSETS)


def _match_assets_in_text(text: str, assets: list[str]) -> list[str]:
    upper_text = text.upper()
    matched: list[str] = []
    for asset in assets:
        aliases = ASSET_ALIASES.get(asset, (asset,))
        if any(re.search(rf"\b{re.escape(alias)}\b", upper_text) for alias in aliases):
            matched.append(asset)
    return matched


def _rules_sentiment(text: str) -> float:
    lower = text.lower()
    fear_hits = sum(1 for word in FEAR_KEYWORDS if word in lower)
    greed_hits = sum(1 for word in GREED_KEYWORDS if word in lower)
    total = fear_hits + greed_hits
    if total == 0:
        return 0.0
    raw = (greed_hits - fear_hits) / total
    return round(max(-1.0, min(1.0, raw)), 4)


def _vader_sentiment(text: str) -> float | None:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        analyzer = SentimentIntensityAnalyzer()
        compound = float(analyzer.polarity_scores(text).get("compound", 0.0))
        return round(max(-1.0, min(1.0, compound)), 4)
    except Exception:
        return None


def _textblob_sentiment(text: str) -> float | None:
    try:
        from textblob import TextBlob

        polarity = float(TextBlob(text).sentiment.polarity)
        return round(max(-1.0, min(1.0, polarity)), 4)
    except Exception:
        return None


async def _llm_sentiment(text: str) -> float | None:
    if not config.SENTIMENT_LLM_FALLBACK:
        return None

    import os

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return None

    prompt = (
        "Score the crypto market sentiment of this headline from -1.0 (extreme fear/panic) "
        "to +1.0 (extreme greed/FOMO). Reply with JSON only: "
        '{"sentiment_score": <float>}.\n\nHeadline: '
        f"{text[:500]}"
    )

    timeout = aiohttp.ClientTimeout(total=config.SENTIMENT_FETCH_TIMEOUT_SECONDS)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.SENTIMENT_OPENAI_MODEL,
                "temperature": 0.0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "You are a financial sentiment scorer."},
                    {"role": "user", "content": prompt},
                ],
            },
        ) as response:
            response.raise_for_status()
            payload = await response.json()
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        score = float(parsed.get("sentiment_score", 0.0))
        return round(max(-1.0, min(1.0, score)), 4)
    except Exception:
        logger.exception("LLM sentiment fallback failed safely.")
        return None


def analyze_sentiment_score(text: str) -> float:
    """
    Score headline text on [-1.0, +1.0] using VADER, TextBlob, then rules.

    For LLM fallback use analyze_sentiment_score_async().
    """
    return analyze_sentiment_score_detailed(text).sentiment_score


def analyze_sentiment_score_detailed(text: str) -> SentimentAnalysisResult:
    cleaned = " ".join(text.split())
    if not cleaned:
        return SentimentAnalysisResult(sentiment_score=0.0, analyzer="empty")

    for analyzer_name, scorer in (
        ("vader", _vader_sentiment),
        ("textblob", _textblob_sentiment),
    ):
        score = scorer(cleaned)
        if score is not None:
            return SentimentAnalysisResult(sentiment_score=score, analyzer=analyzer_name)

    rules_score = _rules_sentiment(cleaned)
    return SentimentAnalysisResult(sentiment_score=rules_score, analyzer="rules")


async def analyze_sentiment_score_async(text: str) -> SentimentAnalysisResult:
    cleaned = " ".join(text.split())
    if not cleaned:
        return SentimentAnalysisResult(sentiment_score=0.0, analyzer="empty")

    for analyzer_name, scorer in (
        ("vader", _vader_sentiment),
        ("textblob", _textblob_sentiment),
    ):
        score = scorer(cleaned)
        if score is not None:
            return SentimentAnalysisResult(sentiment_score=score, analyzer=analyzer_name)

    llm_score = await _llm_sentiment(cleaned)
    if llm_score is not None:
        return SentimentAnalysisResult(sentiment_score=llm_score, analyzer="llm_fallback")

    rules_score = _rules_sentiment(cleaned)
    return SentimentAnalysisResult(sentiment_score=rules_score, analyzer="rules")


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


def _parse_rss_items(payload: str, source_label: str) -> list[SentimentNewsItem]:
    items: list[SentimentNewsItem] = []
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        logger.warning("RSS parse failed | source=%s", str(source_label).replace("\r", " ").replace("\n", " "))
        return items

    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        description = (item.findtext("description") or "").strip()
        text = f"{title}. {description}".strip(". ")
        if not text:
            continue
        pub_date = item.findtext("pubDate")
        for asset in _match_assets_in_text(text, _operational_assets()):
            items.append(
                SentimentNewsItem(
                    asset=asset,
                    sector=_sector_for_asset(asset),
                    source=source_label,
                    raw_text=text[:2000],
                    published_at=pub_date,
                )
            )
    return items


async def _fetch_rss_news(
    session: aiohttp.ClientSession,
    assets: list[str],
) -> list[SentimentNewsItem]:
    if config.SENTIMENT_DATA_SOURCE not in {"rss", "mixed"}:
        return []

    collected: list[SentimentNewsItem] = []
    for feed_url in config.SENTIMENT_RSS_FEEDS:
        try:
            async with session.get(feed_url) as response:
                response.raise_for_status()
                payload = await response.text()
            label = f"rss:{feed_url.split('//')[-1].split('/')[0]}"
            for item in _parse_rss_items(payload, label):
                if item.asset in assets or not assets:
                    collected.append(item)
        except Exception:
            logger.warning("RSS fetch failed safely | feed=%s", str(feed_url).replace("\r", " ").replace("\n", " "))
    return collected


async def _fetch_cryptocompare_news(
    session: aiohttp.ClientSession,
    assets: list[str],
) -> list[SentimentNewsItem]:
    if config.SENTIMENT_DATA_SOURCE not in {"cryptocompare", "mixed"}:
        return []

    params: dict[str, Any] = {"lang": "EN"}
    headers: dict[str, str] = {}
    if config.SENTIMENT_CRYPTOCOMPARE_API_KEY:
        headers["authorization"] = f"Apikey {config.SENTIMENT_CRYPTOCOMPARE_API_KEY}"

    try:
        payload = await _fetch_json(
            session,
            "https://min-api.cryptocompare.com/data/v2/news/",
            params=params,
            headers=headers or None,
        )
    except Exception:
        logger.warning("CryptoCompare news fetch failed safely.")
        return []

    items: list[SentimentNewsItem] = []
    for row in payload.get("Data") or []:
        title = str(row.get("title") or "").strip()
        body = str(row.get("body") or "").strip()
        text = f"{title}. {body}".strip(". ")
        if not text:
            continue
        published = row.get("published_on")
        published_at = (
            datetime.fromtimestamp(int(published), tz=UTC).isoformat()
            if published
            else None
        )
        categories = str(row.get("categories") or "").upper()
        matched = _match_assets_in_text(f"{text} {categories}", assets)
        for asset in matched:
            items.append(
                SentimentNewsItem(
                    asset=asset,
                    sector=_sector_for_asset(asset),
                    source="cryptocompare",
                    raw_text=text[:2000],
                    published_at=published_at,
                )
            )
    return items


def _mock_stream_headline(asset: str, source: str, salt: str) -> str:
    bucket = int(time.time() // config.SENTIMENT_POLL_INTERVAL_SECONDS)
    digest = hashlib.sha256(f"{asset}:{source}:{salt}:{bucket}".encode()).hexdigest()
    polarity = int(digest[:2], 16) / 255.0
    templates_bull = [
        f"{asset} whales accumulate as ETF inflows accelerate",
        f"Analysts see {asset} breakout setup after on-chain accumulation",
        f"{asset} funding turns positive amid broad risk-on sentiment",
    ]
    templates_bear = [
        f"{asset} faces distribution pressure after macro risk-off move",
        f"Traders warn of {asset} liquidation cascade on thin liquidity",
        f"{asset} sentiment cools as outflows hit exchanges",
    ]
    templates = templates_bull if polarity >= 0.5 else templates_bear
    index = int(digest[2:4], 16) % len(templates)
    return templates[index]


async def _fetch_twitter_asset(
    session: aiohttp.ClientSession,
    asset: str,
    headers: dict[str, str],
) -> list[SentimentNewsItem]:
    url = "https://api.twitter.com/2/tweets/search/recent"
    params = {
        "query": f"${asset} OR #{asset} lang:en -is:retweet",
        "max_results": "10",
        "tweet.fields": "created_at,text",
    }
    try:
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError) as exc:
        logger.warning(
            "Twitter API failed | asset=%s err=%s",
            str(asset).replace("\r", " ").replace("\n", " "),
            str(exc).replace("\r", " ").replace("\n", " "),
        )
        return []
    return [
        SentimentNewsItem(
            asset=asset,
            sector=_sector_for_asset(asset),
            source="twitter",
            raw_text=str(tw.get("text") or "")[:500],
            published_at=tw.get("created_at") or _utcnow_iso(),
        )
        for tw in (data.get("data") or [])
        if str(tw.get("text") or "")
    ]


async def _fetch_twitter_real(
    session: aiohttp.ClientSession,
    assets: list[str],
) -> list[SentimentNewsItem]:
    """Fetch via X API v2 (token) or free Reddit/CryptoPanic fallback."""
    token = os.getenv("TWITTER_BEARER_TOKEN", "").strip()
    items: list[SentimentNewsItem] = []

    if token and not config.SENTIMENT_TWITTER_MOCK_ENABLED:
        headers = {"Authorization": f"Bearer {token}"}
        for asset in assets:
            items.extend(await _fetch_twitter_asset(session, asset, headers))
        if items:
            return items

    # Free fallback — no token required (Reddit social proxy)
    return await _fetch_twitter_fallback_reddit(session, assets)


def _reddit_items_from_posts(asset: str, posts: list[dict[str, Any]]) -> list[SentimentNewsItem]:
    items: list[SentimentNewsItem] = []
    for post in posts:
        post_data = post.get("data") or {}
        title = str(post_data.get("title") or "")
        if title and asset.upper() in title.upper():
            items.append(
                SentimentNewsItem(
                    asset=asset,
                    sector=_sector_for_asset(asset),
                    source="social_reddit_live",
                    raw_text=title[:500],
                    published_at=_utcnow_iso(),
                )
            )
    return items


async def _fetch_reddit_asset(
    session: aiohttp.ClientSession,
    *,
    asset: str,
    subreddit: str,
    headers: dict[str, str],
) -> list[SentimentNewsItem]:
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=5"
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return []
            data = await resp.json()
    except (aiohttp.ClientError, TypeError, ValueError):
        return []
    posts = (data.get("data") or {}).get("children") or []
    return _reddit_items_from_posts(asset, posts)


async def _fetch_twitter_fallback_reddit(
    session: aiohttp.ClientSession,
    assets: list[str],
) -> list[SentimentNewsItem]:
    """Live social fallback using Reddit (no Twitter token needed)."""
    if os.getenv("SENTIMENT_TWITTER_FALLBACK", "true").lower() not in {"1", "true", "yes"}:
        return []

    items: list[SentimentNewsItem] = []
    sub_map = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", "BNB": "binance", "XRP": "ripple"}
    headers = {"User-Agent": "BLACKDARK/1.0 sentiment-bot"}

    for asset in assets:
        sub = sub_map.get(asset.upper(), "cryptocurrency")
        items.extend(await _fetch_reddit_asset(session, asset=asset, subreddit=sub, headers=headers))
    return items


def _fetch_mock_social_streams(assets: list[str]) -> list[SentimentNewsItem]:
    items: list[SentimentNewsItem] = []
    # Production / institutional: never inject mock social as live sentiment.
    try:
        from production_guard import is_production

        if is_production() or os.getenv("INSTITUTIONAL_LAUNCH", "").lower() in {"1", "true", "yes"}:
            return items
    except Exception:
        pass
    if config.SENTIMENT_DATA_SOURCE not in {"mock", "mixed"}:
        return items

    for asset in assets:
        if config.SENTIMENT_TWITTER_MOCK_ENABLED:
            items.append(
                SentimentNewsItem(
                    asset=asset,
                    sector=_sector_for_asset(asset),
                    source="twitter_mock",
                    raw_text=_mock_stream_headline(asset, "twitter", "x"),
                    published_at=_utcnow_iso(),
                )
            )
        if config.SENTIMENT_TELEGRAM_MOCK_ENABLED:
            items.append(
                SentimentNewsItem(
                    asset=asset,
                    sector=_sector_for_asset(asset),
                    source="telegram_mock",
                    raw_text=_mock_stream_headline(asset, "telegram", "tg"),
                    published_at=_utcnow_iso(),
                )
            )
    return items


async def fetch_market_sentiment_news(
    assets: list[str] | None = None,
) -> list[SentimentNewsItem]:
    """
    Poll live headlines and micro-blog style items for operational assets.

    Sources are controlled by SENTIMENT_DATA_SOURCE and related env vars.
    """
    target_assets = [_normalize_asset(item) for item in (assets or _operational_assets())]
    timeout = aiohttp.ClientTimeout(total=config.SENTIMENT_FETCH_TIMEOUT_SECONDS)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        rss_task = _fetch_rss_news(session, target_assets)
        cc_task = _fetch_cryptocompare_news(session, target_assets)
        twitter_task = _fetch_twitter_real(session, target_assets)
        mock_task = _fetch_mock_social_streams(target_assets)
        rss_items, cc_items, twitter_items, mock_items = await asyncio.gather(
            rss_task,
            cc_task,
            twitter_task,
            mock_task,
            return_exceptions=True,
        )

    collected: list[SentimentNewsItem] = []
    for batch in (rss_items, cc_items, twitter_items, mock_items):
        if isinstance(batch, Exception):
            logger.warning(
                "Sentiment source batch failed safely: %s",
                str(batch).replace("\r", " ").replace("\n", " "),
            )
            continue
        collected.extend(batch)

    deduped: dict[tuple[str, str, str], SentimentNewsItem] = {}
    for item in collected:
        key = (item.asset, item.source, item.raw_text[:160])
        deduped[key] = item
    return list(deduped.values())


async def _compute_compound_momentum(asset: str, new_score: float) -> float:
    prior_rows = await fetch_sentiment_logs_for_asset(
        asset,
        window_seconds=config.SENTIMENT_ROLLING_WINDOW_SECONDS,
    )
    scores = [float(row.get("sentiment_score") or 0.0) for row in prior_rows]
    scores.append(new_score)
    if not scores:
        return new_score
    return round(max(-1.0, min(1.0, sum(scores) / len(scores))), 4)


async def persist_sentiment_items(items: list[SentimentNewsItem]) -> int:
    if not items:
        return 0

    rows: list[tuple[Any, ...]] = []
    timestamp = _utcnow_iso()
    for item in items:
        try:
            analysis = await analyze_sentiment_score_async(item.raw_text)
            compound = await _compute_compound_momentum(item.asset, analysis.sentiment_score)
            rows.append(
                (
                    timestamp,
                    item.asset,
                    item.sector,
                    item.source,
                    item.raw_text,
                    analysis.sentiment_score,
                    compound,
                )
            )
        except Exception:
            logger.exception(
                "Sentiment persistence skipped for item | asset=%s source=%s",
                str(item.asset).replace("\r", " ").replace("\n", " "),
                str(item.source).replace("\r", " ").replace("\n", " "),
            )

    if rows:
        await insert_market_sentiment_logs(rows)
    return len(rows)


async def get_rolling_compound_sentiment_index(
    asset: str,
    *,
    window_seconds: int | None = None,
) -> float:
    """Export hook: rolling compound sentiment index for one asset."""
    return await fetch_rolling_compound_sentiment_index(
        _normalize_asset(asset),
        window_seconds=window_seconds or config.SENTIMENT_ROLLING_WINDOW_SECONDS,
    )


async def get_all_rolling_compound_sentiment_indices(
    assets: list[str] | None = None,
    *,
    window_seconds: int | None = None,
) -> dict[str, float]:
    """Export hook: rolling compound sentiment indices keyed by asset."""
    target = [_normalize_asset(item) for item in (assets or _operational_assets())]
    return await fetch_all_rolling_compound_sentiment_indices(
        target,
        window_seconds=window_seconds or config.SENTIMENT_ROLLING_WINDOW_SECONDS,
    )


def sentiment_score_adjustment_for_asset(
    asset: str,
    context: dict[str, Any] | None,
) -> float:
    """
    Map rolling compound sentiment [-1, 1] into a bounded oracle score delta.
    """
    if not context:
        return 0.0
    try:
        indices = context.get("sentiment_compound_index") or {}
        compound = float(indices.get(_normalize_asset(asset), 0.0))
        if abs(compound) <= config.SENTIMENT_NEUTRAL_BAND:
            return 0.0
        if compound > 0:
            return round(min(config.SENTIMENT_SCORE_BOOST_MAX, compound * config.SENTIMENT_SCORE_BOOST_MAX), 2)
        return round(max(-config.SENTIMENT_SCORE_PENALTY_MAX, compound * config.SENTIMENT_SCORE_PENALTY_MAX), 2)
    except Exception:
        logger.exception("Sentiment score adjustment failed | asset=%s", str(asset).replace("\r", " ").replace("\n", " "))
        return 0.0


def get_sentiment_index_for_asset(asset: str, context: dict[str, Any]) -> float:
    indices = context.get("sentiment_compound_index") or {}
    return float(indices.get(_normalize_asset(asset), 0.0))


def is_extreme_negative_sentiment(compound_index: float) -> bool:
    return compound_index < config.SENTIMENT_EXTREME_NEGATIVE_THRESHOLD


def sentiment_panic_penalty_for_asset(
    asset: str,
    context: dict[str, Any] | None,
) -> float:
    """
    Return the institutional defensive score penalty when panic/FUD is detected.
    """
    if not context:
        return 0.0
    try:
        compound = get_sentiment_index_for_asset(asset, context)
        if is_extreme_negative_sentiment(compound):
            return config.SENTIMENT_PANIC_SCORE_PENALTY
        return 0.0
    except Exception:
        logger.exception("Sentiment panic penalty lookup failed | asset=%s", str(asset).replace("\r", " ").replace("\n", " "))
        return 0.0


def build_sentiment_panic_warning(asset: str, compound_index: float) -> str:
    return (
        f"INSTITUTIONAL SENTIMENT ALERT: {_normalize_asset(asset)} 5-minute compound "
        f"sentiment at {compound_index:+.2f} signals extreme fear/FUD. "
        f"Opportunity score penalized by {config.SENTIMENT_PANIC_SCORE_PENALTY:.0f} "
        "points to protect fund capital."
    )


async def load_active_sentiment_indices_for_valuation(
    assets: list[str] | None = None,
) -> dict[str, Any]:
    """
    Pull the latest rolling compound sentiment index per asset before valuation.

    Uses get_rolling_compound_sentiment_index() for each operational asset.
    """
    target_assets = [_normalize_asset(item) for item in (assets or _operational_assets())]
    indices: dict[str, float] = {}
    panic_assets: dict[str, float] = {}

    for asset in target_assets:
        try:
            compound = await get_rolling_compound_sentiment_index(
                asset,
                window_seconds=config.SENTIMENT_ROLLING_WINDOW_SECONDS,
            )
            indices[asset] = round(compound, 4)
            if is_extreme_negative_sentiment(compound):
                panic_assets[asset] = indices[asset]
        except Exception:
            logger.warning(
                "Rolling sentiment index unavailable | asset=%s",
                str(asset).replace("\r", " ").replace("\n", " "),
                exc_info=True,
            )
            indices[asset] = 0.0

    valuation_context = {
        "sentiment_compound_index": indices,
        "sentiment_panic_assets": panic_assets,
        "sentiment_score_adjustments": {
            asset: sentiment_score_adjustment_for_asset(
                asset,
                {"sentiment_compound_index": indices},
            )
            for asset in indices
        },
    }
    return valuation_context


async def load_active_sentiment_indices_for_valuation_safe(
    assets: list[str] | None = None,
) -> dict[str, Any]:
    try:
        return await load_active_sentiment_indices_for_valuation(assets)
    except Exception:
        logger.exception(
            "Active sentiment index load failed safely; returning empty valuation context."
        )
        return {
            "sentiment_compound_index": {},
            "sentiment_panic_assets": {},
            "sentiment_score_adjustments": {},
        }


async def build_sentiment_context(
    assets: list[str] | None = None,
) -> dict[str, Any]:
    indices = await get_all_rolling_compound_sentiment_indices(assets)
    adjustments = {
        asset: sentiment_score_adjustment_for_asset(asset, {"sentiment_compound_index": indices})
        for asset in indices
    }
    return {
        "sentiment_compound_index": indices,
        "sentiment_score_adjustments": adjustments,
    }


async def build_sentiment_context_safe(
    assets: list[str] | None = None,
) -> dict[str, Any]:
    try:
        return await build_sentiment_context(assets)
    except Exception:
        logger.exception("Sentiment context build failed safely; returning empty context.")
        return {
            "sentiment_compound_index": {},
            "sentiment_score_adjustments": {},
        }


def merge_sentiment_context(
    base_context: dict[str, Any] | None,
    sentiment_context: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(base_context or {})
    if sentiment_context:
        merged.update(sentiment_context)
    return merged


@dataclass
class SentimentEngine:
    """Async sentiment polling service for the arbitrage engine."""

    _shutdown: asyncio.Event = field(default_factory=asyncio.Event)
    _session: aiohttp.ClientSession | None = None

    async def close(self) -> None:
        self._shutdown.set()
        if self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    async def run_cycle(self, assets: list[str] | None = None) -> dict[str, Any]:
        await init_db()
        news_items = await fetch_market_sentiment_news(assets)
        inserted = await persist_sentiment_items(news_items)
        indices = await get_all_rolling_compound_sentiment_indices(assets)
        logger.info(
            "Sentiment cycle complete | headlines=%d persisted=%d assets=%d",
            len(news_items),
            inserted,
            len(indices),
        )
        return {
            "headlines_fetched": len(news_items),
            "rows_persisted": inserted,
            "sentiment_compound_index": indices,
        }

    async def run_loop(self, assets: list[str] | None = None) -> None:
        logger.info(
            "Sentiment engine loop started | interval=%ss window=%ss",
            config.SENTIMENT_POLL_INTERVAL_SECONDS,
            config.SENTIMENT_ROLLING_WINDOW_SECONDS,
        )
        while not self._shutdown.is_set():
            try:
                await self.run_cycle(assets)
            except Exception:
                logger.exception("Sentiment cycle failed; continuing.")

            try:
                await asyncio.wait_for(
                    self._shutdown.wait(),
                    timeout=config.SENTIMENT_POLL_INTERVAL_SECONDS,
                )
                break
            except TimeoutError:
                continue

        logger.info("Sentiment engine loop stopped.")
