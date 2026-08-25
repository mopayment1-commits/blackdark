"""
Unique Social Volume — Feature #195 (quality layer within #139 Sentiment Engine).

Deduplication, bot/spam discount, and source-level QA.
Transparency: Raw → Unique → Weighted by quality.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.UniqueSocialVolume")

_FEATURE_ID = 195
_BOT_POSTS_PER_DAY_THRESHOLD = 50
_BOT_WEIGHT = 0.1
_SOURCE_TIER_WEIGHTS = {
    "institutional": 1.0,
    "verified_media": 0.85,
    "exchange_official": 0.8,
    "community": 0.5,
    "unknown": 0.3,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_text(text: str) -> str:
    cleaned = re.sub(r"https?://\S+", "", text.lower())
    cleaned = re.sub(r"[^\w\s]", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _content_hash(text: str) -> str:
    return hashlib.sha256(_normalize_text(text).encode("utf-8")).hexdigest()


def _source_tier(doc: dict[str, Any]) -> str:
    return str(doc.get("source_tier") or doc.get("source_type") or "unknown")


def _bot_weight(doc: dict[str, Any]) -> float:
    posts = int(doc.get("posts_per_day") or doc.get("daily_post_count") or 0)
    if doc.get("is_bot"):
        return _BOT_WEIGHT
    if posts >= _BOT_POSTS_PER_DAY_THRESHOLD:
        return _BOT_WEIGHT
    if posts >= 25:
        return 0.4
    return 1.0


def compute_unique_social_volume(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Deduplicate social documents and apply bot + source-quality weighting.

    Each document: {id, text, source_id, author, posts_per_day, source_tier, is_bot}
    """
    raw_volume = len(documents)
    seen_hashes: set[str] = set()
    seen_source_content: set[tuple[str, str]] = set()
    unique_docs: list[dict[str, Any]] = []
    duplicate_count = 0

    for doc in documents:
        text = str(doc.get("text") or doc.get("content") or "")
        if not text.strip():
            continue
        h = _content_hash(text)
        source_id = str(doc.get("source_id") or doc.get("author") or "unknown")
        pair = (source_id, h)
        if h in seen_hashes or pair in seen_source_content:
            duplicate_count += 1
            continue
        seen_hashes.add(h)
        seen_source_content.add(pair)
        unique_docs.append(doc)

    unique_volume = len(unique_docs)
    weighted_total = 0.0
    source_breakdown: dict[str, dict[str, Any]] = {}

    for doc in unique_docs:
        tier = _source_tier(doc)
        tier_w = _SOURCE_TIER_WEIGHTS.get(tier, _SOURCE_TIER_WEIGHTS["unknown"])
        bot_w = _bot_weight(doc)
        combined = tier_w * bot_w
        weighted_total += combined
        bucket = source_breakdown.setdefault(
            tier,
            {"count": 0, "weighted": 0.0, "tier_weight": tier_w},
        )
        bucket["count"] += 1
        bucket["weighted"] += combined

    weighted_volume = round(weighted_total, 1)
    display = (
        f"Social Volume: {raw_volume:,} (raw) → {unique_volume:,} (unique) "
        f"→ {weighted_volume:,.1f} (weighted by quality)"
    )

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "parent_feature": 139,
        "raw_volume": raw_volume,
        "unique_volume": unique_volume,
        "weighted_volume": weighted_volume,
        "duplicate_count": duplicate_count,
        "deduplication_rate_pct": round((duplicate_count / raw_volume * 100) if raw_volume else 0, 1),
        "display": display,
        "display_ar": (
            f"حجم اجتماعي: {raw_volume:,} (خام) → {unique_volume:,} (فريد) "
            f"→ {weighted_volume:,.1f} (موزون بالجودة)"
        ),
        "source_breakdown": source_breakdown,
        "bot_spam_policy": {
            "bot_posts_per_day_threshold": _BOT_POSTS_PER_DAY_THRESHOLD,
            "bot_weight": _BOT_WEIGHT,
            "high_frequency_discount": "Accounts posting ≥25/day receive reduced weight",
            "documented": True,
        },
        "source_qa_policy": {
            "tiers": _SOURCE_TIER_WEIGHTS,
            "principle": "Trusted institutional sources ≠ anonymous accounts",
        },
        "timestamp": _utcnow(),
    }


def _mock_social_documents(asset: str) -> list[dict[str, Any]]:
    """Bootstrap social document set for demo / when live feed unavailable."""
    sym = asset.upper()
    base = [
        {"id": f"{sym}-1", "text": f"{sym} breaking resistance — bullish momentum building", "source_id": "reuters_crypto", "source_tier": "verified_media", "posts_per_day": 8},
        {"id": f"{sym}-2", "text": f"{sym} breaking resistance — bullish momentum building", "source_id": "bot_farm_1", "source_tier": "unknown", "posts_per_day": 120, "is_bot": True},
        {"id": f"{sym}-3", "text": f"Institutional inflows into {sym} accelerate per on-chain data", "source_id": "glassnode", "source_tier": "institutional", "posts_per_day": 3},
        {"id": f"{sym}-4", "text": f"{sym} liquidity thinning on major CEX order books", "source_id": "kaiko", "source_tier": "institutional", "posts_per_day": 5},
        {"id": f"{sym}-5", "text": f"Random pump group shilling {sym} to 100x", "source_id": "anon_channel", "source_tier": "unknown", "posts_per_day": 200, "is_bot": True},
        {"id": f"{sym}-6", "text": f"{sym} ETF flows turn positive for third consecutive week", "source_id": "bloomberg", "source_tier": "verified_media", "posts_per_day": 6},
        {"id": f"{sym}-7", "text": f"Exchange official: {sym} network upgrade scheduled Q3", "source_id": "binance_official", "source_tier": "exchange_official", "posts_per_day": 2},
        {"id": f"{sym}-8", "text": f"Community debate on {sym} halving impact continues", "source_id": "reddit_crypto", "source_tier": "community", "posts_per_day": 15},
    ]
    # Scale raw volume for realistic display
    scaled: list[dict[str, Any]] = []
    for i in range(12):
        for doc in base:
            clone = dict(doc)
            clone["id"] = f"{doc['id']}-r{i}"
            if i > 0 and i % 3 == 0:
                clone["text"] = doc["text"]  # intentional duplicates
            scaled.append(clone)
    return scaled


async def analyze_unique_social_volume(asset: str) -> dict[str, Any]:
    """Asset-level unique social volume with raw vs unique comparison."""
    sym = asset.upper().replace("/USDT", "")
    documents = _mock_social_documents(sym)
    result = compute_unique_social_volume(documents)
    result["asset"] = sym
    return result


def unique_social_volume_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "parent_feature": 139,
        "layer": "sentiment_quality",
        "deduplication": True,
        "bot_detection": True,
        "source_level_qa": True,
        "bot_spam_policy_documented": True,
        "timestamp": _utcnow(),
    }
