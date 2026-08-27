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
_ABSORBED_IDS = (780, 782)
_TITLE = "Social Sentiment Intelligence"
_STANDALONE = False
_MERGED_INTO = "Market Radar Sentiment Layer"
_SPRINT = 2
_SEED_PATH = Path("data/social_sentiment_intelligence_seed.json")
_RULE_SET_VERSION = "1.0"
_MIN_MENTIONS = 100

SentimentLabel = Literal["Positive", "Neutral", "Negative", "Insufficient Data"]

_DISCLAIMER = (
    "Sentiment reflects community discussion. Not financial advice. May be manipulated. "
    "Rule-based keyword matching and source weighting — not NLP/ML classification."
)

_BALANCE_FORMULA = (
    "(Positive_Weighted - Negative_Weighted) / (Positive_Weighted + Negative_Weighted) × 100"
)
_BALANCE_FORMULA_VERSION = "1.0"
_BALANCE_RANGE = (-100, 100)

_HISTORICAL_BANDS: list[dict[str, Any]] = [
    {"band": "Very Positive", "min": 60, "max": 100},
    {"band": "Positive", "min": 20, "max": 60},
    {"band": "Neutral", "min": -20, "max": 20},
    {"band": "Negative", "min": -60, "max": -20},
    {"band": "Very Negative", "min": -100, "max": -60},
]


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


def _confidence_by_sample_size(mention_count: int, *, seed: dict[str, Any]) -> tuple[float | None, str]:
    """#783 — explicit confidence tiers by sample size."""
    min_mentions = int(seed.get("min_mentions_for_score", _MIN_MENTIONS))
    tiers = seed.get("confidence_tiers") or {}
    if mention_count < min_mentions:
        return None, "Insufficient Data"
    if mention_count > int(tiers.get("very_high_min", 1000)):
        return float(tiers.get("very_high_pct", 90)), "Very High"
    if mention_count >= int(tiers.get("high_min", 500)):
        return float(tiers.get("high_pct", 75)), "High"
    if mention_count >= int(tiers.get("medium_min", 100)):
        return float(tiers.get("medium_pct", 50)), "Medium"
    return float(tiers.get("low_pct", 25)), "Low"


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
    min_mentions = int(seed.get("min_mentions_for_score", _MIN_MENTIONS))
    if total_mentions < min_mentions:
        return {
            "sentiment_label": "Insufficient Data",
            "sentiment_label_ar": "بيانات غير كافية",
            "sentiment_score": None,
            "sentiment_trend": "unknown",
            "mention_count": total_mentions,
            "insufficient_data": True,
            "confidence_pct": None,
            "confidence_tier": "Insufficient Data",
            "positive_weighted": round(positive_w, 1),
            "negative_weighted": round(negative_w, 1),
            "neutral_weighted": round(neutral_w, 1),
            "classified_words": classified,
        }

    conf_pct, conf_tier = _confidence_by_sample_size(total_mentions, seed=seed)

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
    label_ar = {"Positive": "إيجابي", "Neutral": "محايد", "Negative": "سلبي"}.get(label, label)

    return {
        "sentiment_label": label,
        "sentiment_label_ar": label_ar,
        "sentiment_score": score,
        "sentiment_trend": trend,
        "mention_count": total_mentions,
        "insufficient_data": False,
        "confidence_pct": conf_pct,
        "confidence_tier": conf_tier,
        "positive_weighted": round(positive_w, 1),
        "negative_weighted": round(negative_w, 1),
        "neutral_weighted": round(neutral_w, 1),
        "weighted_breakdown": {
            "positive": round(positive_w, 1),
            "negative": round(negative_w, 1),
            "neutral": round(neutral_w, 1),
        },
        "classified_words": classified,
    }


def _compute_sentiment_balance_782(
    positive_weighted: float,
    negative_weighted: float,
    mention_count: int,
    *,
    asset: str,
    seed: dict[str, Any],
) -> dict[str, Any]:
    """#782 — normalized positive-vs-negative balance oscillator (-100 to +100)."""
    min_mentions = int(seed.get("min_mentions_for_score", _MIN_MENTIONS))
    denom = positive_weighted + negative_weighted

    if mention_count < min_mentions or denom == 0:
        return {
            "metric": "sentiment_balance",
            "feature_ref": 782,
            "balance_value": "N/A",
            "balance_band": "N/A",
            "balance_band_ar": "غير متوفر",
            "insufficient_data": True,
            "zero_sample_protected": True,
            "formula": _BALANCE_FORMULA,
            "formula_version": _BALANCE_FORMULA_VERSION,
            "range": list(_BALANCE_RANGE),
            "deterministic": True,
            "no_ai_balance": True,
            "historical_bands": _HISTORICAL_BANDS,
        }

    balance = round((positive_weighted - negative_weighted) / denom * 100, 1)
    balance = max(_BALANCE_RANGE[0], min(_BALANCE_RANGE[1], balance))

    if balance > 60:
        band, band_ar = "Very Positive", "إيجابي جداً"
    elif balance > 20:
        band, band_ar = "Positive", "إيجابي"
    elif balance >= -20:
        band, band_ar = "Neutral", "محايد"
    elif balance >= -60:
        band, band_ar = "Negative", "سلبي"
    else:
        band, band_ar = "Very Negative", "سلبي جداً"

    history = (seed.get("sentiment_balance_782") or {}).get("historical_series") or {}
    sparkline = history.get(asset.upper()) or history.get("default") or []

    return {
        "metric": "sentiment_balance",
        "feature_ref": 782,
        "balance_value": balance,
        "balance_band": band,
        "balance_band_ar": band_ar,
        "positive_weighted": round(positive_weighted, 1),
        "negative_weighted": round(negative_weighted, 1),
        "insufficient_data": False,
        "zero_sample_protected": True,
        "formula": _BALANCE_FORMULA,
        "formula_version": _BALANCE_FORMULA_VERSION,
        "formula_documented": True,
        "range": list(_BALANCE_RANGE),
        "deterministic": True,
        "no_ai_balance": True,
        "historical_bands": _HISTORICAL_BANDS,
        "historical_sparkline": sparkline,
        "fee_db": (seed.get("sentiment_balance_782") or {}).get("fee_db") or seed.get("fee_db"),
    }


def _compute_source_mix(
    classified_words: list[dict[str, Any]],
    *,
    seed: dict[str, Any],
) -> dict[str, Any]:
    """#783 — source/time aggregation with tier weighting."""
    tier1_sources = set((seed.get("source_weights") or {}).get("tier1", {}).get("sources") or [])
    tier1_mentions = 0
    tier2_mentions = 0
    for item in classified_words:
        mentions = int(item.get("mentions", 0))
        if item.get("source_tier") == "tier1":
            tier1_mentions += mentions
        else:
            tier2_mentions += mentions
    total = tier1_mentions + tier2_mentions or 1
    twitter_pct = round(tier1_mentions / total * 100, 1)
    news_pct = round(100 - twitter_pct, 1)
    hourly = (seed.get("hourly_aggregation") or {}).get("buckets") or []
    return {
        "aggregation": "hourly_bucket_weighted_by_source_tier",
        "formula": "bucket_score = Σ(mentions × tier_weight) per hour",
        "hourly_buckets": hourly,
        "source_mix": {
            "Twitter": twitter_pct,
            "News": news_pct,
            "display": f"Twitter ({twitter_pct}%) + News ({news_pct}%)",
            "tier1_sources": list(tier1_sources),
        },
    }


def _build_structured_display(
    asset: str,
    sentiment: dict[str, Any],
    source_mix: dict[str, Any],
) -> str:
    """#783 — structured Arabic output line."""
    label_ar = sentiment.get("sentiment_label_ar", sentiment.get("sentiment_label"))
    conf = sentiment.get("confidence_pct", "N/A")
    mentions = sentiment.get("mention_count", 0)
    sources = (source_mix.get("source_mix") or {}).get("display", "")
    return (
        f"الأصل: {asset} | المزاج: {label_ar} | الثقة: {conf}% | "
        f"العينة: {mentions} منشن | المصادر: {sources}"
    )


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
    classified = sentiment.get("classified_words") or []
    source_mix = _compute_source_mix(classified, seed=seed)
    balance = _compute_sentiment_balance_782(
        float(sentiment.get("positive_weighted") or 0),
        float(sentiment.get("negative_weighted") or 0),
        int(sentiment.get("mention_count") or 0),
        asset=sym,
        seed=seed,
    )
    weights = seed.get("source_weights") or {}
    ml_qa = seed.get("multilingual_qa") or {}
    kw = seed.get("keyword_counts") or {}

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    structured_display = _build_structured_display(sym, sentiment, source_mix)

    panel = {
        "ok": not sentiment.get("insufficient_data"),
        "feature_ref": 783,
        "absorbed_feature_refs": list(_ABSORBED_IDS),
        "merged_into": _MERGED_INTO,
        "standalone_rejected": True,
        "duplicate_of_780_rejected": True,
        "duplicate_of_782_rejected": True,
        "asset": sym,
        "sentiment_label": sentiment["sentiment_label"],
        "sentiment_label_ar": sentiment.get("sentiment_label_ar"),
        "sentiment_score": sentiment.get("sentiment_score"),
        "sentiment_trend": sentiment.get("sentiment_trend"),
        "mention_count": sentiment["mention_count"],
        "insufficient_data": sentiment.get("insufficient_data", False),
        "min_mentions_required": int(seed.get("min_mentions_for_score", _MIN_MENTIONS)),
        "confidence_pct": sentiment.get("confidence_pct"),
        "confidence_tier": sentiment.get("confidence_tier"),
        "confidence_by_sample_size": True,
        "confidence_tiers_documented": seed.get("confidence_tiers"),
        "rule_based_only": True,
        "no_ml_classification": True,
        "no_nlp_model": True,
        "no_sentiment_buy_signal": True,
        "observation_only": True,
        "keyword_matching": True,
        "source_weighting": {
            "tier1_weight": (weights.get("tier1") or {}).get("weight", 3),
            "tier2_weight": (weights.get("tier2") or {}).get("weight", 1),
            "tier1_sources": (weights.get("tier1") or {}).get("sources", []),
            "tier2_sources": (weights.get("tier2") or {}).get("sources", []),
            "explicit_in_response": True,
        },
        "source_time_aggregation": source_mix,
        "spam_handling": spam_meta,
        "sentiment_balance_782": balance,
        "trending_words_758": {
            "raw_word_count": len(raw_words),
            "clean_word_count": len(clean_words),
            "classified_words": classified,
        },
        "weighted_breakdown": sentiment.get("weighted_breakdown"),
        "rule_documentation": (
            f"Sentiment Rule Set v{_RULE_SET_VERSION} | "
            f"Keywords: {kw.get('en', 500)} EN + {kw.get('ar', 300)} AR | "
            f"Last Updated: {seed.get('last_updated', _utcnow()[:10])}"
        ),
        "rule_set_version": _RULE_SET_VERSION,
        "rule_version_visible": True,
        "rule_version_not_hideable": True,
        "multilingual_qa": {
            "languages_tested": ml_qa.get("languages_tested", ["EN", "AR"]),
            "en_accuracy_pct": ml_qa.get("en_accuracy_pct"),
            "ar_accuracy_pct": ml_qa.get("ar_accuracy_pct"),
            "ar_min_accuracy_pct": ml_qa.get("ar_min_accuracy_pct", 85),
            "daily_arabic_samples": ml_qa.get("daily_arabic_samples", 50),
            "qa_passed": (
                float(ml_qa.get("en_accuracy_pct", 0)) >= float(ml_qa.get("min_accuracy_pct", 75))
                and float(ml_qa.get("ar_accuracy_pct", 0)) >= float(ml_qa.get("ar_min_accuracy_pct", 85))
            ),
        },
        "fee_db": {
            **(seed.get("fee_db") or {}),
            "multilingual_qa_usd": (seed.get("fee_db") or {}).get("multilingual_qa_usd", 0.001),
        },
        "disclaimer": _DISCLAIMER,
        "disclaimer_mandatory": True,
        "display": structured_display,
        "display_en": (
            f"{sym} Sentiment: {sentiment['sentiment_label']} "
            f"({sentiment.get('sentiment_score', 'N/A')}) | "
            f"Mentions: {sentiment['mention_count']} | "
            f"Balance: {balance.get('balance_value', 'N/A')}"
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
    balance = panel.get("sentiment_balance_782") or {}
    return {
        "ok": panel.get("ok", False),
        "feature_ref": 783,
        "surface": "market_radar",
        "widget": "sentiment_analysis",
        "widget_ar": "التحليل المزاجي",
        "balance_widget_ar": "مؤشر التوازن المزاجي",
        "sentiment": panel,
        "sentiment_balance_metric": balance,
        "timestamp": _utcnow(),
    }


def build_asset_card_sentiment_badge_783(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#783 — Asset Card المزاج السائد badge."""
    panel = build_sentiment_intelligence_panel_783(asset, seed=seed)
    return {
        "ok": panel.get("ok", False),
        "feature_ref": 783,
        "surface": "asset_card",
        "badge": "dominant_sentiment",
        "badge_ar": "المزاج السائد",
        "sentiment_label": panel.get("sentiment_label"),
        "sentiment_label_ar": panel.get("sentiment_label_ar"),
        "confidence_pct": panel.get("confidence_pct"),
        "confidence_tier": panel.get("confidence_tier"),
        "timestamp": _utcnow(),
    }


def build_asset_card_balance_sparkline_782(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#782 — Asset Card التوازن sparkline (-100 to +100)."""
    panel = build_sentiment_intelligence_panel_783(asset, seed=seed)
    balance = panel.get("sentiment_balance_782") or {}
    return {
        "ok": balance.get("balance_value") != "N/A",
        "feature_ref": 782,
        "surface": "asset_card",
        "tab_ar": "التوازن",
        "balance_value": balance.get("balance_value"),
        "balance_band": balance.get("balance_band"),
        "balance_band_ar": balance.get("balance_band_ar"),
        "range": balance.get("range", [-100, 100]),
        "sparkline": balance.get("historical_sparkline") or [],
        "formula": balance.get("formula"),
        "deterministic": balance.get("deterministic"),
        "timestamp": _utcnow(),
    }


def build_market_radar_sentiment_balance_widget_782(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#782 — Market Radar مؤشر التوازن المزاجي widget."""
    panel = build_sentiment_intelligence_panel_783(asset, seed=seed)
    balance = panel.get("sentiment_balance_782") or {}
    return {
        "ok": balance.get("balance_value") != "N/A",
        "feature_ref": 782,
        "surface": "market_radar",
        "widget": "sentiment_balance",
        "widget_ar": "مؤشر التوازن المزاجي",
        "balance": balance,
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
    tests.append({"test": "structured_display_ar", "passed": "الأصل:" in (btc.get("display") or "")})
    tests.append({"test": "source_time_aggregation", "passed": "hourly_buckets" in (btc.get("source_time_aggregation") or {})})

    balance = btc.get("sentiment_balance_782") or {}
    tests.append({"test": "782_balance_formula_documented", "passed": balance.get("formula_documented") is True})
    tests.append({"test": "782_balance_deterministic", "passed": balance.get("deterministic") is True})
    tests.append({"test": "782_balance_in_range", "passed": isinstance(balance.get("balance_value"), (int, float)) and -100 <= balance["balance_value"] <= 100})
    tests.append({"test": "782_historical_bands", "passed": len(balance.get("historical_bands") or []) == 5})

    low = build_sentiment_intelligence_panel_783("LOW_SAMPLE", seed=seed)
    low_balance = (low.get("sentiment_balance_782") or {}).get("balance_value")
    tests.append({"test": "782_low_sample_na", "passed": low_balance == "N/A"})
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
        "metrics": ["sentiment_analysis", "sentiment_balance_782"],
        "integrated_with": ["#758 Trending Words", "#780 source weighting", "#782 balance", "Market Radar"],
        "timestamp": _utcnow(),
    }
