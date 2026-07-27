"""
BLACKDARK — Sentiment manipulation guard (NLP pump-dump / fake news resistance).

Protects oracle and execution from spoofed Twitter/Telegram/Reddit hype:
- Source credibility weights (editorial > authenticated social > mock)
- Pump-and-dump phrase detection
- Coordinated burst / near-duplicate filtering
- Extreme greed blocking (symmetric to fear gate)
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.SentimentManipulationGuard")

# Pump-and-dump / scam phrasing commonly used by bot farms
PUMP_DUMP_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\b100x\b",
        r"\b1000x\b",
        r"\bguaranteed\b",
        r"\binsider\b",
        r"\bpump\b",
        r"\bmoon\s*shot\b",
        r"\bairdrop\s*now\b",
        r"\bfree\s*tokens?\b",
        r"\bnot\s*financial\s*advice\b.*\bbuy\b",
        r"\bwhales?\s*accumulating\b.*\bnow\b",
        r"\blast\s*chance\b",
        r"\bdon'?t\s*miss\b",
        r"\bto\s*the\s*moon\b",
        r"\bgem\s*alert\b",
        r"\bstealth\s*launch\b",
    )
)

MOCK_SOURCES = frozenset({"twitter_mock", "telegram_mock"})
LOW_TRUST_SOURCES = frozenset(
    {
        "twitter",
        "twitter_mock",
        "telegram_mock",
        "social_reddit_live",
        "reddit",
    }
)

_recent_fingerprints: dict[str, list[tuple[float, str]]] = defaultdict(list)
_rejected_total = 0
_pump_hits_total = 0
_burst_hits_total = 0


def _enabled() -> bool:
    return getattr(config, "SENTIMENT_MANIPULATION_GUARD_ENABLED", True)


def source_trust_weight(source: str) -> float:
    """Editorial sources weigh more; mock/social weigh less."""
    src = (source or "").lower()
    if not _enabled():
        return 1.0
    weights = {
        "rss": float(getattr(config, "SENTIMENT_TRUST_WEIGHT_RSS", 1.0)),
        "cryptocompare": float(getattr(config, "SENTIMENT_TRUST_WEIGHT_EDITORIAL", 1.0)),
        "twitter": float(getattr(config, "SENTIMENT_TRUST_WEIGHT_TWITTER", 0.15)),
        "social_reddit_live": float(getattr(config, "SENTIMENT_TRUST_WEIGHT_REDDIT", 0.20)),
        "reddit": float(getattr(config, "SENTIMENT_TRUST_WEIGHT_REDDIT", 0.20)),
        "twitter_mock": float(getattr(config, "SENTIMENT_TRUST_WEIGHT_MOCK", 0.0)),
        "telegram_mock": float(getattr(config, "SENTIMENT_TRUST_WEIGHT_MOCK", 0.0)),
    }
    for key, weight in weights.items():
        if key in src:
            return weight
    if src.startswith("rss"):
        return float(getattr(config, "SENTIMENT_TRUST_WEIGHT_RSS", 1.0))
    return float(getattr(config, "SENTIMENT_TRUST_WEIGHT_DEFAULT", 0.5))


def _text_fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", (text or "").lower().strip())[:240]
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def detect_pump_dump_phrases(text: str) -> list[str]:
    hits: list[str] = []
    for pattern in PUMP_DUMP_PATTERNS:
        if pattern.search(text or ""):
            hits.append(pattern.pattern)
    return hits


def _burst_window_sec() -> float:
    return float(getattr(config, "SENTIMENT_BURST_WINDOW_SEC", 120))


def _burst_max_similar() -> int:
    return int(getattr(config, "SENTIMENT_BURST_MAX_SIMILAR", 3))


def is_coordinated_burst(asset: str, text: str) -> bool:
    """Detect bot-farm style repeated narratives within a short window."""
    if not _enabled():
        return False
    fp = _text_fingerprint(text)
    now = time.monotonic()
    window = _burst_window_sec()
    max_similar = _burst_max_similar()
    key = asset.upper()

    bucket = _recent_fingerprints[key]
    bucket[:] = [(ts, f) for ts, f in bucket if now - ts <= window]
    similar = sum(1 for _, f in bucket if f == fp)
    bucket.append((now, fp))
    return similar >= max_similar


@dataclass
class SentimentItemAssessment:
    asset: str
    source: str
    accepted: bool
    trust_weight: float = 1.0
    rejected_reason: str = ""
    pump_phrases: list[str] = field(default_factory=list)
    manipulation_flags: list[str] = field(default_factory=list)


def assess_sentiment_item(asset: str, source: str, raw_text: str) -> SentimentItemAssessment:
    """Score trust and reject obvious pump-dump / bot-coordination items."""
    global _rejected_total, _pump_hits_total, _burst_hits_total

    weight = source_trust_weight(source)
    assessment = SentimentItemAssessment(
        asset=asset.upper(),
        source=source,
        accepted=True,
        trust_weight=weight,
    )

    if not _enabled():
        return assessment

    if source.lower() in MOCK_SOURCES and not getattr(config, "SENTIMENT_ALLOW_MOCK_IN_SCORING", False):
        assessment.accepted = False
        assessment.rejected_reason = "mock_source_disabled"
        assessment.trust_weight = 0.0
        _rejected_total += 1
        return assessment

    pump_hits = detect_pump_dump_phrases(raw_text)
    if pump_hits:
        assessment.pump_phrases = pump_hits
        assessment.manipulation_flags.append("pump_dump_phrase")
        assessment.accepted = False
        assessment.rejected_reason = "pump_dump_phrase"
        assessment.trust_weight = 0.0
        _pump_hits_total += 1
        _rejected_total += 1
        logger.info(
            "Sentiment item rejected (pump phrase) | asset=%s source=%s phrases=%d",
            asset,
            source,
            len(pump_hits),
        )
        return assessment

    if is_coordinated_burst(asset, raw_text):
        assessment.manipulation_flags.append("coordinated_burst")
        assessment.accepted = False
        assessment.rejected_reason = "coordinated_burst"
        assessment.trust_weight = 0.0
        _burst_hits_total += 1
        _rejected_total += 1
        logger.info(
            "Sentiment item rejected (burst) | asset=%s source=%s",
            asset,
            source,
        )
        return assessment

    if weight <= 0.0:
        assessment.accepted = False
        assessment.rejected_reason = "untrusted_source"
        _rejected_total += 1

    return assessment


def filter_sentiment_items(items: list[Any]) -> tuple[list[Any], dict[str, Any]]:
    """Filter a batch of SentimentNewsItem objects before scoring."""
    accepted: list[Any] = []
    rejected = 0
    reasons: dict[str, int] = defaultdict(int)

    for item in items:
        assessment = assess_sentiment_item(
            getattr(item, "asset", ""),
            getattr(item, "source", ""),
            getattr(item, "raw_text", ""),
        )
        if assessment.accepted and assessment.trust_weight > 0:
            accepted.append(item)
        else:
            rejected += 1
            reasons[assessment.rejected_reason or "unknown"] += 1

    return accepted, {
        "input": len(items),
        "accepted": len(accepted),
        "rejected": rejected,
        "reasons": dict(reasons),
    }


def apply_trust_weight_to_score(raw_score: float, source: str) -> float:
    return round(max(-1.0, min(1.0, raw_score * source_trust_weight(source))), 4)


def is_extreme_positive_sentiment(compound_index: float) -> bool:
    threshold = float(getattr(config, "SENTIMENT_EXTREME_POSITIVE_THRESHOLD", 0.75))
    return compound_index >= threshold


def greed_pump_penalty_for_asset(asset: str, context: dict[str, Any] | None) -> float:
    """Penalize oracle score when NLP reads coordinated greed (pump risk)."""
    if not context or not _enabled():
        return 0.0
    compound = float((context.get("sentiment_compound_index") or {}).get(asset.upper(), 0.0))
    if is_extreme_positive_sentiment(compound):
        return float(getattr(config, "SENTIMENT_GREED_SCORE_PENALTY", 20))
    pump_assets = context.get("sentiment_pump_risk_assets") or {}
    if asset.upper() in pump_assets:
        return float(getattr(config, "SENTIMENT_PUMP_RISK_PENALTY", 15))
    return 0.0


def sentiment_manipulation_status() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "mock_scoring_allowed": getattr(config, "SENTIMENT_ALLOW_MOCK_IN_SCORING", False),
        "source_weights": {
            "rss": source_trust_weight("rss"),
            "cryptocompare": source_trust_weight("cryptocompare"),
            "twitter": source_trust_weight("twitter"),
            "reddit": source_trust_weight("social_reddit_live"),
            "mock": source_trust_weight("telegram_mock"),
        },
        "extreme_positive_threshold": float(
            getattr(config, "SENTIMENT_EXTREME_POSITIVE_THRESHOLD", 0.75)
        ),
        "greed_execution_block": getattr(config, "SENTIMENT_GREED_BLOCK_ENABLED", True),
        "pump_phrase_patterns": len(PUMP_DUMP_PATTERNS),
        "burst_window_sec": _burst_window_sec(),
        "burst_max_similar": _burst_max_similar(),
        "stats": {
            "rejected_total": _rejected_total,
            "pump_hits_total": _pump_hits_total,
            "burst_hits_total": _burst_hits_total,
        },
        "policy": (
            "Mock Telegram/Twitter excluded from scoring by default. "
            "Pump phrases and coordinated bursts rejected. "
            "Extreme greed blocks execution symmetrically to fear."
        ),
    }
