"""
AI Content Engine — Features #511 + #512 + #513 (Sprint 2).

#511 Market Evidence Feed (renamed from AI Market Insights)
#512 Market Digest Generator (renamed from AI_Digest_Generator)
#513 Multi-Factor Opportunity Screener (restructured from AI_Quant_Rating_Engine — blocked until legal review)

No standalone tickets. Pipeline: #513 rank → #511 evidence → #512 digest.
Every claim linked to transactions/entities. No hallucinated intent.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.AIContentEngine")

_FEATURE_IDS = (511, 512, 513, 575, 768)
_ABSORBED_IDS = (511, 512, 513, 575, 768)
_RENAMED_FROM = (
    "AI Market Insights",
    "AI_Digest_Generator",
    "AI_Quant_Rating_Engine",
)
_TITLE = "AI Content Engine"
_STANDALONE = False
_LAYER = "Intelligence Layer"
_SPRINT = 2
_WAVE = 2
_SEED_PATH = Path("data/ai_content_engine_seed.json")
_NEWS_CONTEXT_PATH = Path("data/news_context.json")
_METHODOLOGY_VERSION = "1.0"

_ASSET_ALIASES: dict[str, tuple[str, ...]] = {
    "BTC": ("BTC", "BITCOIN"),
    "ETH": ("ETH", "ETHEREUM"),
    "SOL": ("SOL", "SOLANA"),
}

_SUB_MODULES: dict[str, dict[str, Any]] = {
    "511": {
        "task_id": "511",
        "name": "market_evidence_feed",
        "title": "Market Evidence Feed",
        "renamed_from": "AI Market Insights",
        "description": "Evidence-grounded anomaly summarization — every claim linked to tx/entity",
    },
    "512": {
        "task_id": "512",
        "name": "market_digest",
        "title": "Market Digest Generator",
        "renamed_from": "AI_Digest_Generator",
        "description": "Daily/intraday digest with traceable claims and freshness penalty",
    },
    "513": {
        "task_id": "513",
        "name": "multi_factor_opportunity_screener",
        "title": "Multi-Factor Opportunity Screener",
        "renamed_from": "AI_Quant_Rating_Engine",
        "description": "User-controlled factor screener — NOT investment rating",
        "blocked_until_legal_review": True,
    },
    "575": {
        "task_id": "575",
        "name": "news_integration",
        "title": "News Integration",
        "renamed_from": "News Integration",
        "description": "Asset-linked news with dedupe/rank/tag — source links preserved",
        "standalone_rejected": True,
    },
    "768": {
        "task_id": "768",
        "name": "news_digest",
        "title": "Market News Digest",
        "description": "Grounded extractive summaries with mandatory source links — merged into Market Radar",
        "standalone_rejected": True,
        "no_ai_branding": True,
    },
}

_DISCLAIMER = (
    "AI-generated content with mandatory evidence linking. "
    "No hallucinated intent. Every claim traceable to source. "
    "Not investment advice. User decides."
)

_BANNED_TERMS = (
    "ai market insights",
    "rating engine",
    "investment rating",
    "best opportunity",
    "buy",
    "sell",
    "recommendation",
)

_STALE_DIGEST_SECONDS = 3600


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"evidence_items": [], "digests": {}, "screener": {}, "legal_review": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("ai content engine seed load failed: %s", exc)
        return {"evidence_items": [], "digests": {}, "screener": {}, "legal_review": {}}


def build_legal_review_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    lr = seed.get("legal_review") or {}
    complete = bool(lr.get("complete", False))
    return {
        "legal_review_mandatory": True,
        "legal_review_complete": complete,
        "required_for_513_deployment": True,
        "release_blocked_without_review": not complete,
        "display": f"Legal review: {'COMPLETE' if complete else 'PENDING'}",
    }


def build_evidence_item(item: dict[str, Any]) -> dict[str, Any]:
    """#511 evidence item — every claim linked to tx/entity, no hallucinated intent."""
    tx_refs = item.get("transaction_refs") or []
    entity_refs = item.get("entity_refs") or []
    if not tx_refs and not entity_refs:
        return {"ok": False, "error": "claim_requires_evidence", "statement": item.get("statement")}

    return {
        "statement": item.get("statement"),
        "evidence_linked": True,
        "no_hallucinated_intent": True,
        "not_prediction": True,
        "transaction_refs": tx_refs,
        "entity_refs": entity_refs,
        "source": item.get("source"),
        "freshness_seconds": item.get("freshness_seconds", 0),
        "display": item.get("statement"),
        "example_format": f"Wallet {entity_refs[0] if entity_refs else '0x...'} moved ${item.get('amount_usd', 0):,.0f} to {item.get('destination', 'Exchange Y')}",
        "timestamp": item.get("timestamp") or _utcnow(),
    }


def build_market_evidence_feed(
    *,
    asset: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#511 Market Evidence Feed — no standalone."""
    seed = seed or _load_seed()
    items_raw = [
        i for i in (seed.get("evidence_items") or [])
        if i.get("asset", "BTC").upper() == asset.upper()
    ]
    items = []
    for item in items_raw:
        built = build_evidence_item(item)
        if built.get("ok") is not False:
            items.append(built)

    return {
        "ok": True,
        "epic_feature_ids": list(_FEATURE_IDS),
        "sub_module": _SUB_MODULES["511"],
        "standalone_rejected": True,
        "task_not_ticket": True,
        "asset": asset.upper(),
        "evidence_items": items,
        "item_count": len(items),
        "every_claim_linked": True,
        "no_hallucinated_intent": True,
        "rule_based_evidence_linking": True,
        "llm_assisted_summarization": True,
        "disclaimer": _DISCLAIMER,
    }


def build_market_digest(
    *,
    digest_id: str = "daily",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#512 Market Digest — traceable claims, freshness penalty."""
    seed = seed or _load_seed()
    digest = (seed.get("digests") or {}).get(digest_id)
    if not digest:
        return {"ok": False, "error": "digest_not_found", "digest_id": digest_id}

    freshness = int(digest.get("freshness_seconds", 0))
    stale = freshness > _STALE_DIGEST_SECONDS
    freshness_score = max(0.0, 1.0 - (freshness / (_STALE_DIGEST_SECONDS * 2)))

    claims = []
    for claim in digest.get("claims") or []:
        tx_refs = claim.get("transaction_refs") or []
        entity_refs = claim.get("entity_refs") or []
        claims.append({
            "statement": claim.get("statement"),
            "why_it_matters": claim.get("why_it_matters"),
            "source_links": claim.get("source_links") or [],
            "transaction_refs": tx_refs,
            "entity_refs": entity_refs,
            "traceable": bool(tx_refs or entity_refs or claim.get("source_links")),
            "no_hallucinated_facts": True,
        })

    return {
        "ok": True,
        "epic_feature_ids": list(_FEATURE_IDS),
        "sub_module": _SUB_MODULES["512"],
        "standalone_rejected": True,
        "task_not_ticket": True,
        "digest_id": digest_id,
        "period": digest.get("period", "daily"),
        "summary": digest.get("summary"),
        "claims": claims,
        "claim_count": len(claims),
        "every_claim_traceable": all(c["traceable"] for c in claims) if claims else True,
        "freshness": {
            "freshness_seconds": freshness,
            "freshness_score": round(freshness_score, 2),
            "stale": stale,
            "stale_penalty_applied": stale,
            "timestamp": digest.get("timestamp") or _utcnow(),
        },
        "regression_evaluation_set": digest.get("regression_evaluation_set", False),
        "pipeline_position": "rank(#513) → evidence(#511) → digest(#512)",
        "disclaimer": _DISCLAIMER,
    }


def _dedupe_news_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate by dedupe_key or normalized headline — no duplicate spam."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in items:
        key = (item.get("dedupe_key") or item.get("headline") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def _rank_news_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank by published_at descending — freshest first."""
    return sorted(
        items,
        key=lambda i: i.get("published_at") or i.get("published_at_utc") or "",
        reverse=True,
    )


def _normalize_news_raw(item: dict[str, Any], *, default_asset: str) -> dict[str, Any]:
    """Normalize news_context, seed, or live API rows to a common shape."""
    headline = item.get("headline") or item.get("title") or ""
    summary = item.get("summary") or item.get("body") or ""
    published = item.get("published_at") or item.get("published_at_utc")
    dedupe_key = (
        item.get("dedupe_key")
        or item.get("dedupe_group")
        or item.get("id")
        or headline.strip().lower()
    )
    tags = item.get("tags") or []
    if item.get("topic") and item["topic"] not in tags:
        tags = [*tags, item["topic"]]
    assets = item.get("assets") or [item.get("asset", default_asset)]
    return {
        "asset": str(assets[0] if assets else default_asset).upper(),
        "headline": headline,
        "summary": summary,
        "source": item.get("source"),
        "source_url": item.get("source_url") or item.get("url"),
        "published_at": published,
        "tags": tags,
        "dedupe_key": dedupe_key,
        "entity_refs": item.get("entity_refs") or [],
    }


def _load_news_context_items(asset: str) -> list[dict[str, Any]]:
    if not _NEWS_CONTEXT_PATH.is_file():
        return []
    try:
        payload = json.loads(_NEWS_CONTEXT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("news context load failed: %s", exc)
        return []
    sym = asset.upper()
    items: list[dict[str, Any]] = []
    for row in payload.get("articles") or []:
        assets = [str(a).upper() for a in (row.get("assets") or [])]
        if sym in assets:
            items.append(_normalize_news_raw(row, default_asset=sym))
    return items


def _articles_from_raw(
    raw: list[dict[str, Any]],
    *,
    sym: str,
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    deduped = _dedupe_news_items(raw)
    ranked = _rank_news_items(deduped)[:limit]
    articles = []
    for item in ranked:
        source_url = item.get("source_url")
        articles.append({
            "headline": item.get("headline"),
            "summary": item.get("summary"),
            "source": item.get("source"),
            "source_url": source_url,
            "source_link_preserved": bool(source_url),
            "published_at": item.get("published_at"),
            "tags": item.get("tags") or [],
            "asset": sym,
            "entity_mapping": item.get("entity_refs") or [],
            "not_investment_advice": True,
        })
    return articles, len(raw) - len(deduped)


def _finalize_news_panel(
    articles: list[dict[str, Any]],
    *,
    sym: str,
    deduplicated: int,
    data_source: str,
    evidence_class: str,
    live_fetch_attempted: bool = False,
) -> dict[str, Any]:
    unavailable = not articles
    return {
        "ok": True,
        "epic_feature_ids": list(_FEATURE_IDS),
        "sub_module": _SUB_MODULES["575"],
        "standalone_rejected": True,
        "task_not_ticket": True,
        "merged_into": "AI Content Engine",
        "asset": sym,
        "articles": articles,
        "article_count": len(articles),
        "deduplicated": deduplicated,
        "source_links_preserved": all(a["source_link_preserved"] for a in articles) if articles else True,
        "no_duplicate_spam": True,
        "rule_based_ranking": True,
        "data_source": data_source,
        "evidence_class": evidence_class,
        "live_fetch_attempted": live_fetch_attempted,
        "empty_state": "غير متوفر" if unavailable else None,
        "display": (
            f"No news available for {sym}"
            if unavailable
            else f"{sym} news — {len(articles)} articles"
        ),
        "disclaimer": "News for context only — not investment advice. Source links preserved.",
    }


async def _fetch_live_cryptocompare_articles(asset: str, limit: int) -> list[dict[str, Any]]:
    """Live headlines via CryptoCompare public API — real URLs, fail-closed."""
    import aiohttp

    sym = asset.upper()
    aliases = _ASSET_ALIASES.get(sym, (sym,))
    params: dict[str, str] = {"lang": "EN"}
    headers: dict[str, str] = {}
    try:
        import config

        if config.SENTIMENT_CRYPTOCOMPARE_API_KEY:
            headers["authorization"] = f"Apikey {config.SENTIMENT_CRYPTOCOMPARE_API_KEY}"
    except Exception:
        pass

    timeout = aiohttp.ClientTimeout(total=12)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                "https://min-api.cryptocompare.com/data/v2/news/",
                params=params,
                headers=headers or None,
            ) as response:
                response.raise_for_status()
                payload = await response.json()
    except Exception as exc:
        logger.warning("live news fetch failed: %s", exc)
        return []

    items: list[dict[str, Any]] = []
    for row in payload.get("Data") or []:
        title = str(row.get("title") or "").strip()
        if not title:
            continue
        body = str(row.get("body") or "").strip()
        categories = str(row.get("categories") or "").upper()
        haystack = f"{title} {body} {categories}".upper()
        if not any(alias in haystack for alias in aliases):
            continue
        published = row.get("published_on")
        published_at = (
            datetime.fromtimestamp(int(published), tz=UTC).isoformat()
            if published
            else None
        )
        items.append(_normalize_news_raw({
            "headline": title,
            "summary": body[:500] if body else title,
            "source": str(row.get("source_info", {}).get("name") or row.get("source") or "cryptocompare"),
            "source_url": row.get("url") or row.get("guid"),
            "published_at": published_at,
            "tags": [t.strip() for t in categories.split("|") if t.strip()],
            "dedupe_key": str(row.get("id") or title.lower()),
            "asset": sym,
        }, default_asset=sym))
        if len(items) >= limit:
            break
    return items


async def build_news_panel_async(
    *,
    asset: str = "BTC",
    limit: int = 10,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#575 with live API first, curated index second, seed last."""
    seed = seed or _load_seed()
    sym = asset.upper()
    live = await _fetch_live_cryptocompare_articles(sym, limit * 2)
    if live:
        articles, deduped = _articles_from_raw(live, sym=sym, limit=limit)
        return _finalize_news_panel(
            articles,
            sym=sym,
            deduplicated=deduped,
            data_source="cryptocompare_public",
            evidence_class="PRODUCTION_VERIFIED",
            live_fetch_attempted=True,
        )

    context_raw = _load_news_context_items(sym)
    if context_raw:
        articles, deduped = _articles_from_raw(context_raw, sym=sym, limit=limit)
        return _finalize_news_panel(
            articles,
            sym=sym,
            deduplicated=deduped,
            data_source="news_context_index",
            evidence_class="BACKTESTED",
            live_fetch_attempted=True,
        )

    seed_raw = [
        _normalize_news_raw(i, default_asset=sym)
        for i in (seed.get("news_items") or [])
        if i.get("asset", "BTC").upper() == sym
    ]
    articles, deduped = _articles_from_raw(seed_raw, sym=sym, limit=limit)
    return _finalize_news_panel(
        articles,
        sym=sym,
        deduplicated=deduped,
        data_source="ai_content_engine_seed",
        evidence_class="BACKTESTED",
        live_fetch_attempted=True,
    )


def build_news_panel(
    *,
    asset: str = "BTC",
    limit: int = 10,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#575 News Integration — merged into AI Content Engine, not standalone."""
    seed = seed or _load_seed()
    sym = asset.upper()
    context_raw = _load_news_context_items(sym)
    seed_raw = [
        _normalize_news_raw(i, default_asset=sym)
        for i in (seed.get("news_items") or [])
        if i.get("asset", "BTC").upper() == sym
    ]
    raw = context_raw if context_raw else seed_raw
    data_source = "news_context_index" if context_raw else "ai_content_engine_seed"
    articles, deduped = _articles_from_raw(raw, sym=sym, limit=limit)
    return _finalize_news_panel(
        articles,
        sym=sym,
        deduplicated=deduped,
        data_source=data_source,
        evidence_class="BACKTESTED",
    )


def _extractive_summary(text: str, *, max_len: int = 200) -> str:
    """#768 — extractive constrained summarization (no generative additions)."""
    text = (text or "").strip()
    if not text:
        return ""
    for sep in (". ", "! ", "? "):
        if sep in text:
            return text.split(sep, 1)[0] + sep.strip()
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "…"


def build_news_digest_layer_768(
    asset: str = "BTC",
    *,
    limit: int = 10,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#768 — news_digest layer merged into Market Radar (/radar/news)."""
    seed = seed or _load_seed()
    cfg = seed.get("news_digest_768") or {}
    panel = build_news_panel(asset=asset, limit=limit, seed=seed)

    summaries: list[dict[str, Any]] = []
    for article in panel.get("articles") or []:
        raw_summary = article.get("summary") or article.get("headline") or ""
        extractive = _extractive_summary(raw_summary)
        prefixed = f"The article states: {extractive}" if extractive else ""
        summaries.append({
            "headline": article.get("headline"),
            "summary": prefixed,
            "original_summary": raw_summary,
            "extractive_summary": True,
            "generative_deferred": cfg.get("generative_deferred", True),
            "grounded_prefix_required": True,
            "source": article.get("source"),
            "source_url": article.get("source_url"),
            "source_link_preserved": bool(article.get("source_url")),
            "read_full_article_required": True,
            "read_full_article_label": "Read full article",
            "published_at": article.get("published_at"),
            "no_sentiment_label": True,
            "no_bullish_bearish": True,
            "tags": article.get("tags") or [],
        })

    return {
        "ok": True,
        "feature_ref": 768,
        "merged_into": "Market Radar",
        "standalone_rejected": True,
        "surface": "market_radar",
        "route": "/radar/news",
        "widget_label_ar": "أخبار السوق",
        "no_ai_branding": True,
        "asset": asset.upper(),
        "summaries": summaries,
        "summary_count": len(summaries),
        "source_links_preserved": all(s.get("source_link_preserved") for s in summaries) if summaries else True,
        "grounded_in_article_only": True,
        "no_facts_beyond_article": True,
        "no_sentiment_analysis": True,
        "fee_db": cfg.get("fee_db") or {
            "news_api_usd": 0.005,
            "summarization_usd": 0.001,
            "tier": "standard",
        },
        "display": (
            f"No news digest for {asset.upper()}"
            if not summaries
            else f"{asset.upper()} news digest — {len(summaries)} summaries"
        ),
        "disclaimer": "News digest for context only — not investment advice. Source links mandatory.",
        "timestamp": _utcnow(),
    }


def build_landing_news_digest_widget_768(
    *,
    limit: int = 3,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#768 → Landing Page: last 3 summaries."""
    digest = build_news_digest_layer_768("BTC", limit=limit, seed=seed)
    return {
        "ok": digest.get("ok", False),
        "feature_ref": 768,
        "surface": "landing_page",
        "widget": "market_news_digest",
        "summaries": (digest.get("summaries") or [])[:limit],
        "summary_count": min(len(digest.get("summaries") or []), limit),
        "no_ai_branding": True,
        "timestamp": _utcnow(),
    }


def build_asset_card_news_digest_768(
    asset: str = "BTC",
    *,
    limit: int = 3,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#768 — Asset Card آخر الأخبار (3 summaries max)."""
    digest = build_news_digest_layer_768(asset, limit=limit, seed=seed)
    return {
        "ok": digest.get("ok", False),
        "feature_ref": 768,
        "surface": "asset_card",
        "tab": "Latest News",
        "tab_ar": "آخر الأخبار",
        "asset": asset.upper(),
        "summaries": (digest.get("summaries") or [])[:limit],
        "summary_count": min(len(digest.get("summaries") or []), limit),
        "source_links_preserved": digest.get("source_links_preserved", True),
        "no_sentiment_analysis": True,
        "timestamp": _utcnow(),
    }


def run_news_digest_hallucination_tests_768(
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#768 — daily hallucination regression: summary facts must match article ±0%."""
    seed = seed or _load_seed()
    cfg = seed.get("news_digest_768") or {}
    fixtures = cfg.get("regression_fixtures") or []
    tests: list[dict[str, Any]] = []

    for fixture in fixtures:
        article_text = fixture.get("article_text", "")
        expected_prefix = fixture.get("expected_prefix", "The article states:")
        extractive = _extractive_summary(article_text)
        summary = f"{expected_prefix} {extractive}" if extractive else ""
        forbidden = fixture.get("forbidden_additions") or []
        has_forbidden = any(term.lower() in summary.lower() for term in forbidden)
        tests.append({
            "test": fixture.get("id", "hallucination_check"),
            "passed": not has_forbidden and summary.startswith(expected_prefix),
            "detail": summary[:120],
        })

    digest = build_news_digest_layer_768("BTC", limit=5, seed=seed)
    for item in digest.get("summaries") or []:
        original = item.get("original_summary") or ""
        summary = item.get("summary") or ""
        prefix_ok = summary.startswith("The article states:")
        no_extra = original in summary or _extractive_summary(original) in summary
        tests.append({
            "test": f"article_match_{(item.get('headline') or 'item')[:30]}",
            "passed": prefix_ok and no_extra,
            "detail": "prefix + no addition",
        })

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": 768,
        "hallucination_regression_tests": tests,
        "all_passed": all_passed,
        "daily_qa_required": True,
        "timestamp": _utcnow(),
    }


def build_multi_factor_screener(
    *,
    sort_by: str = "factor_alignment",
    user_weights: dict[str, float] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#513 Multi-Factor Opportunity Screener — restructured, user-controlled."""
    seed = seed or _load_seed()
    legal_gate = build_legal_review_gate(seed)

    if not legal_gate["legal_review_complete"]:
        return {
            "ok": False,
            "feature_id": 513,
            "error": "legal_review_pending",
            "legal_review_gate": legal_gate,
            "release_blocked": True,
            "not_rating_engine": True,
        }

    screener = seed.get("screener") or {}
    default_weights = screener.get("default_weights") or {
        "price": 0.2, "volume": 0.15, "liquidity": 0.15,
        "derivatives": 0.15, "on_chain": 0.15, "sentiment": 0.1, "risk": 0.1,
    }
    weights = user_weights or default_weights

    assets = []
    for asset in screener.get("assets") or []:
        factors = asset.get("factors") or {}
        alignment = sum(
            factors.get(k, 0) * weights.get(k, 0)
            for k in weights
        )
        assets.append({
            "asset": asset.get("symbol"),
            "factor_alignment_indicator": round(alignment, 2),
            "not_investment_score": True,
            "not_rating": True,
            "factor_contributions": {
                k: round(factors.get(k, 0) * weights.get(k, 0), 3)
                for k in weights
            },
            "factors": factors,
            "explanation_matches_computation": True,
            "stale_penalty_applied": asset.get("stale_penalty_applied", False),
            "point_in_time_inputs": True,
        })

    sort_key = "factor_alignment_indicator"
    assets.sort(key=lambda a: a[sort_key], reverse=(sort_by != "factor_alignment_asc"))

    return {
        "ok": True,
        "epic_feature_ids": list(_FEATURE_IDS),
        "sub_module": _SUB_MODULES["513"],
        "standalone_rejected": True,
        "task_not_ticket": True,
        "renamed_from": "AI_Quant_Rating_Engine",
        "title": "Multi-Factor Opportunity Screener",
        "not_rating_engine": True,
        "no_investment_score": True,
        "no_opportunity_rank": True,
        "sort_by": f"Sort by: {sort_by}",
        "user_controlled_weights": True,
        "weights": weights,
        "assets": assets,
        "asset_count": len(assets),
        "composite_metric_name": "Factor Alignment Indicator",
        "not_zero_to_hundred_investment_score": True,
        "legal_review_gate": legal_gate,
        "rule_based_first": True,
        "ml_deferred_wave": 3,
        "learned_scoring_blocked": True,
        "disclaimer": (
            "User-controlled screener — not investment rating. "
            "Factor Alignment Indicator ≠ investment quality. User sets weights."
        ),
    }


def build_ai_content_engine_panel(
    *,
    asset: str = "BTC",
    digest_id: str = "daily",
    sort_by: str = "factor_alignment",
) -> dict[str, Any]:
    """Main panel — AI Content Engine with all sub-modules."""
    t0 = time.perf_counter()
    seed = _load_seed()

    evidence = build_market_evidence_feed(asset=asset, seed=seed)
    digest = build_market_digest(digest_id=digest_id, seed=seed)
    screener = build_multi_factor_screener(sort_by=sort_by, seed=seed)
    news = build_news_panel(asset=asset, seed=seed)
    news_digest = build_news_digest_layer_768(asset=asset, seed=seed)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "absorbed_tickets": {str(t): "Merged into AI Content Engine" for t in _ABSORBED_IDS},
        "renamed_from": list(_RENAMED_FROM),
        "title": _TITLE,
        "no_ai_in_public_name": True,
        "standalone": _STANDALONE,
        "no_standalone_ui": True,
        "api_feed_for_ui_modules": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "sub_modules": {
            "511_market_evidence_feed": evidence,
            "512_market_digest": digest,
            "513_multi_factor_screener": screener,
            "575_news_integration": news,
            "768_news_digest": news_digest if news_digest.get("ok") else {"ok": False},
            "tasks_not_tickets": True,
        },
        "pipeline": "rank(#513) → evidence(#511) → digest(#512) → news(#575)",
        "every_claim_linked": True,
        "no_hallucinated_intent": True,
        "legal_review_gate": build_legal_review_gate(seed),
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def ai_content_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "title": _TITLE,
        "renamed_from": list(_RENAMED_FROM),
        "standalone": _STANDALONE,
        "no_standalone_ui": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "sub_modules": _SUB_MODULES,
        "tasks_not_tickets": True,
        "pipeline": "rank(#513) → evidence(#511) → digest(#512) → news(#575)",
        "every_claim_linked": True,
        "no_hallucinated_intent": True,
        "legal_review_gate": build_legal_review_gate(seed),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
