"""
BLACKDARK — Sentiment gate for arbitrage execution (Buyer Requirement #6).

Blocks auto-execution during extreme fear spikes from Telegram/Reddit/X.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

logger = logging.getLogger("BLACKDARK.SentimentGate")

_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 60.0


def _fear_threshold() -> float:
    return float(os.getenv("SENTIMENT_FEAR_BLOCK_THRESHOLD", "-0.65"))


def _greed_boost_threshold() -> float:
    return float(os.getenv("SENTIMENT_GREED_BOOST_THRESHOLD", "0.75"))


async def fetch_asset_sentiment(asset: str) -> dict[str, Any]:
    """Get compound sentiment for an asset (cached 60s)."""
    key = asset.upper()
    now = time.time()
    cached = _cache.get(key)
    if cached and now - cached[0] < _CACHE_TTL:
        return cached[1]

    try:
        from database import fetch_rolling_compound_sentiment_index

        row = await fetch_rolling_compound_sentiment_index(key)
        score = float(row.get("compound_score") or 0) if row else 0.0
        payload = {
            "asset": key,
            "compound_score": score,
            "source": "database",
            "fear_threshold": _fear_threshold(),
        }
    except Exception:
        payload = {"asset": key, "compound_score": 0.0, "source": "fallback"}

    _cache[key] = (now, payload)
    return payload


def sentiment_allows_execution(asset: str, *, compound_score: float | None = None) -> bool:
    """Sync gate — pass compound_score if already fetched."""
    if os.getenv("SENTIMENT_GATE_ENABLED", "true").lower() not in {"1", "true", "yes"}:
        return True

    score = compound_score
    if score is None:
        cached = _cache.get(asset.upper())
        if cached:
            score = cached[1].get("compound_score")
        else:
            # Unknown sentiment must not fail-open into auto-exec.
            logger.info("Sentiment gate BLOCKED | asset=%s reason=sentiment_unknown", str(asset).replace("\r", " ").replace("\n", " "))
            return False
    if score is None:
        return False

    if float(score) <= _fear_threshold():
        logger.info("Sentiment gate BLOCKED | asset=%s score=%.3f", str(asset).replace("\r", " ").replace("\n", " "), float(score))
        return False
    return True


async def sentiment_execution_context(asset: str) -> dict[str, Any]:
    sent = await fetch_asset_sentiment(asset)
    allowed = sentiment_allows_execution(asset, compound_score=sent.get("compound_score"))
    return {
        **sent,
        "execution_allowed": allowed,
        "gate_enabled": os.getenv("SENTIMENT_GATE_ENABLED", "true").lower() in {"1", "true", "yes"},
    }
