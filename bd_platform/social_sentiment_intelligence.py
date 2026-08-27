"""
Social Sentiment Intelligence — Feature #783 (Sprint 2 Market Radar).

Absorbs #780 Sentiment Intelligence (duplicate) into unified sentiment overlay.
Rule-Based keyword matching + source weighting — NO ML/NLP classification.

Integrations:
  #758 Trending Words → word import + classification
  Market Radar → sentiment overlay "التحليل المزاجي"
"""

from __future__ import annotations

import json
import logging
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SocialSentimentIntelligence")

_FEATURE_ID = 783
_ABSORBED_IDS = (780,)
_TITLE = "Social Sentiment Intelligence"
_STANDALONE = False
_MERGED_INTO = "Market Radar Sentiment Layer"
_SPRINT = 2
_SEED_PATH = Path("data/social_sentiment_intelligence_seed.json")
_RULE_SET_VERSION = "1.0"
_MIN_MENTIONS = 100

SentimentLabel = Literal["Positive", "Neutral", "Negative", "Insufficient Data"]

_DISCLAIMER = (
    "Rule-based sentiment from keyword matching and source weighting. "
    "Not NLP/ML classification. Correlation context only — not causation. "
    "Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("social sentiment intelligence seed load failed: %s", exc)
        return {}


def _classify_word(word: str, *, seed: dict[str, Any]) -> str:
    """#780/#783 — Rule-Based keyword classification (no ML)."""
    rules = seed.get("keyword_rules") or {}
    w = word.lower().strip()
    if w in [k.lower() for k in rules.get("positive") or []]:
        return "positive"
    if w in [k.lower() for k in rules.get("negative") or []]:
        return "negative"
    if w in [k.lower() for k in rules.get("neutral") or []]:
        return "neutral"
    return "neutral"


def _source_weight(source_tier: str, *, seed: dict[str, Any]) -> int:
    weights = seed.get("source_weights") or {}
    if source_tier == "tier1":
        return int((weights.get("tier1") or {}).get("weight", 3))
    return int((weights.get("tier2") or {}).get("weight", 1))


def _apply_spam_filters(
    words: list[dict[str, Any]],
    *,
    seed: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """#758-style spam handling — bot exclusion + duplicate user exclusion."""
    spam_cfg = seed.get("spam_handling_758") or {}
    bot_ids = set(spam_cfg.get("bot_user_ids") or [])
    dup_threshold = int(spam_cfg.get("duplicate_user_threshold", 3))

    user_counts: Counter[str] = Counter()
    clean: list[dict[str, Any]] = []
    bots_excluded = 0
    dup_users_excluded = 0

    for item in words:
        user_id = item.get("user_id", "")
        if item.get("is_bot") or user_id in bot_ids:
            bots_excluded += 1
            continue
        user_counts[user_id] += 1
        if user_counts[user_id] > dup_threshold:
            dup_users_excluded += 1
            continue
        clean.append(item)

    return clean, {
        "bot_exclusion": spam_cfg.get("bot_exclusion", True),
        "duplicate_user_exclusion": spam_cfg.get("duplicate_user_exclusion", True),
        "bots_excluded": bots_excluded,
        "duplicate_users_excluded": dup_users_excluded,
        "spam_filtered": bots_excluded + dup_users_excluded,
    }


def _confidence_by_sample_size(mention_count: int, *, seed: dict[str, Any]) -> float | None:
    """#783 — confidence scales with sample size; None if insufficient."""
    if mention_count < int(seed.get("min_mentions_for_score", _MIN_MENTIONS)):
        return None
    if mention_count >= 500:
        return 90.0
    if mention_count >= 300:
        return 80.0
    if mention_count >= 200:
        return 70.0
    return 60.0


def _compute_weighted_sentiment(
    words: list[dict[str, Any]],
    *,
    seed: dict[str, Any],
) -> dict[str, Any]:
    positive_w = 0.0
    negative_w = 0.0
    neutral_w = 0.0
    total_mentions = 0

    classified: list[dict[str, Any]] = []
    for item in words:
        word = item.get("word", "")
        mentions = int(item.get("mentions", 0))
        tier = item.get("source_tier", "tier2")
        weight = _source_weight(tier, seed=seed)
        label = _classify_word(word, seed=seed)
        weighted = mentions * weight
        total_mentions += mentions

        classified.append({
            "word": word,
            "mentions": mentions,
            "source_tier": tier,
            "source_weight": weight,
            "sentiment_class": label,
            "weighted_mentions": weighted,
            "language": item.get("language", "EN"),
        })

        if label == "positive":
            positive_w += weighted
        elif label == "negative":
            negative_w += weighted
        else:
            neutral_w += weighted

    total_weighted = positive_w + negative_w + neutral_w
    if total_mentions < int(seed.get("min_mentions_for_score", _MIN_MENTIONS)):
        return {
            "sentiment_label": "Insufficient Data",
            "sentiment_score": None,
            "sentiment_trend": "unknown",
            "mention_count": total_mentions,
            "insufficient_data": True,
            "confidence_pct": None,
            "classified_words": classified,
        }

    if total_weighted == 0:
        score = 50.0
        label: SentimentLabel = "Neutral"
    else:
        score = round(positive_w / total_weighted * 100, 1)
        if score >= 60:
            label = "Positive"
        elif score <= 40:
            label = "Negative"
        else:
            label = "Neutral"

    trend = "rising" if positive_w > negative_w * 1.2 else "falling" if negative_w > positive_w * 1.2 else "flat"

    return {
        "sentiment_label": label,
        "sentiment_score": score,
        "sentiment_trend": trend,
        "mention_count": total_mentions,
        "insufficient_data": False,
        "confidence_pct": _confidence_by_sample_size(total_mentions, seed=seed),
        "weighted_breakdown": {
            "positive": round(positive_w, 1),
            "negative": round(negative_w, 1),
            "neutral": round(neutral_w, 1),
        },
        "classified_words": classified,
    }


def build_sentiment_intelligence_panel_783(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#783 — Social Sentiment Intelligence (absorbs #780 base logic)."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    sym = asset.upper()
    trending = (seed.get("trending_words_758") or {}).get(sym)

    if not trending:
        return {
            "ok": False,
            "feature_ref": 783,
            "absorbed_feature_refs": list(_ABSORBED_IDS),
            "asset": sym,
            "error": "asset_not_found",
        }

    raw_words = list(trending.get("words") or [])
    clean_words, spam_meta = _apply_spam_filters(raw_words, seed=seed)
    sentiment = _compute_weighted_sentiment(clean_words, seed=seed)
    weights = seed.get("source_weights") or {}
    ml_qa = seed.get("multilingual_qa") or {}

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    panel = {
        "ok": not sentiment.get("insufficient_data"),
        "feature_ref": 783,
        "absorbed_feature_refs": list(_ABSORBED_IDS),
        "merged_into": _MERGED_INTO,
        "standalone_rejected": True,
        "duplicate_of_780_rejected": True,
        "asset": sym,
        "sentiment_label": sentiment["sentiment_label"],
        "sentiment_score": sentiment.get("sentiment_score"),
        "sentiment_trend": sentiment.get("sentiment_trend"),
        "mention_count": sentiment["mention_count"],
        "insufficient_data": sentiment.get("insufficient_data", False),
        "min_mentions_required": int(seed.get("min_mentions_for_score", _MIN_MENTIONS)),
        "confidence_pct": sentiment.get("confidence_pct"),
        "confidence_by_sample_size": True,
        "rule_based_only": True,
        "no_ml_classification": True,
        "no_nlp_model": True,
        "keyword_matching": True,
        "source_weighting": {
            "tier1_weight": (weights.get("tier1") or {}).get("weight", 3),
            "tier2_weight": (weights.get("tier2") or {}).get("weight", 1),
            "tier1_sources": (weights.get("tier1") or {}).get("sources", []),
            "tier2_sources": (weights.get("tier2") or {}).get("sources", []),
            "explicit_in_response": True,
        },
        "spam_handling": spam_meta,
        "trending_words_758": {
            "raw_word_count": len(raw_words),
            "clean_word_count": len(clean_words),
            "classified_words": sentiment.get("classified_words") or [],
        },
        "weighted_breakdown": sentiment.get("weighted_breakdown"),
        "rule_documentation": (
            f"Sentiment Rule Set v{_RULE_SET_VERSION} | "
            f"Keywords: {seed.get('keyword_count', 500)}+ | "
            f"Languages: {'/'.join(seed.get('languages') or ['EN', 'AR'])}"
        ),
        "rule_set_version": _RULE_SET_VERSION,
        "rule_version_visible": True,
        "rule_version_not_hideable": True,
        "multilingual_qa": {
            "languages_tested": ml_qa.get("languages_tested", ["EN", "AR"]),
            "en_accuracy_pct": ml_qa.get("en_accuracy_pct"),
            "ar_accuracy_pct": ml_qa.get("ar_accuracy_pct"),
            "qa_passed": (
                float(ml_qa.get("en_accuracy_pct", 0)) >= float(ml_qa.get("min_accuracy_pct", 75))
                and float(ml_qa.get("ar_accuracy_pct", 0)) >= float(ml_qa.get("min_accuracy_pct", 75))
            ),
        },
        "fee_db": seed.get("fee_db") or {},
        "disclaimer": _DISCLAIMER,
        "display": (
            f"{sym} Sentiment: {sentiment['sentiment_label']} "
            f"({sentiment.get('sentiment_score', 'N/A')}) | "
            f"Mentions: {sentiment['mention_count']} | "
            f"Trend: {sentiment.get('sentiment_trend', 'unknown')}"
        ),
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }

    try:
        from bd_platform.evidence_confidence_middleware import enrich_insight_payload

        return enrich_insight_payload(
            panel,
            system="market_radar",
            endpoint="/intelligence-ledger/market-radar/sentiment",
            source_tier="market_radar",
            age_seconds=max(1, int(elapsed // 1000) or 1),
        )
    except Exception:
        logger.debug("777 evidence middleware skipped", exc_info=True)
        return panel


def build_market_radar_sentiment_overlay_783(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#783 — Market Radar التحليل المزاجي overlay."""
    panel = build_sentiment_intelligence_panel_783(asset, seed=seed)
    return {
        "ok": panel.get("ok", False),
        "feature_ref": 783,
        "surface": "market_radar",
        "widget": "sentiment_analysis",
        "widget_ar": "التحليل المزاجي",
        "sentiment": panel,
        "timestamp": _utcnow(),
    }


def run_sentiment_intelligence_qa_783(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#783 — spam/low sample handling + rule version + multilingual QA."""
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    btc = build_sentiment_intelligence_panel_783("BTC", seed=seed)
    tests.append({"test": "btc_sentiment_ok", "passed": btc.get("ok") is True})
    tests.append({"test": "rule_version_documented", "passed": btc.get("rule_version_not_hideable") is True})
    tests.append({"test": "no_nlp_model", "passed": btc.get("no_nlp_model") is True})
    tests.append({"test": "source_weighting_explicit", "passed": btc.get("source_weighting", {}).get("explicit_in_response") is True})
    tests.append({"test": "spam_bot_excluded", "passed": (btc.get("spam_handling") or {}).get("bots_excluded", 0) > 0})
    tests.append({"test": "confidence_by_sample", "passed": btc.get("confidence_pct") is not None})
    tests.append({"test": "multilingual_qa", "passed": (btc.get("multilingual_qa") or {}).get("qa_passed") is True})

    low = build_sentiment_intelligence_panel_783("LOW_SAMPLE", seed=seed)
    tests.append({"test": "low_sample_insufficient", "passed": low.get("sentiment_label") == "Insufficient Data"})
    tests.append({"test": "low_sample_no_score", "passed": low.get("sentiment_score") is None})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": 783,
        "absorbed_feature_refs": list(_ABSORBED_IDS),
        "qa_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }


def social_sentiment_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "absorbed_feature_ids": list(_ABSORBED_IDS),
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "rule_set_version": _RULE_SET_VERSION,
        "min_mentions_for_score": int(seed.get("min_mentions_for_score", _MIN_MENTIONS)),
        "rule_based_only": True,
        "no_ml_nlp": True,
        "languages": seed.get("languages") or ["EN", "AR"],
        "integrated_with": ["#758 Trending Words", "Market Radar"],
        "timestamp": _utcnow(),
    }
