"""Discovery & Recommendation — separated signals (spec §15, AIE-016/017)."""

from __future__ import annotations

from typing import Any


def score_recommendation(
    *,
    popularity: float = 0.0,
    relevance: float = 0.0,
    trust_quality: float = 0.0,
    personalization: float = 0.0,
    novelty: float = 0.0,
) -> dict[str, Any]:
    """Popularity never becomes trust; personalization never becomes financial truth."""
    return {
        "popularity": popularity,
        "relevance": relevance,
        "trust_quality": trust_quality,
        "personalization": personalization,
        "novelty": novelty,
        "composite_rank": relevance * 0.4 + trust_quality * 0.35 + novelty * 0.1 + popularity * 0.05 + personalization * 0.1,
        "why_recommended": {
            "primary": "relevance_and_trust",
            "factors": {
                "popularity": popularity,
                "relevance": relevance,
                "trust_quality": trust_quality,
                "personalization": personalization,
                "novelty": novelty,
            },
            "financial_ground_truth": False,
        },
    }
