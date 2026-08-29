"""
BLACKDARK — Safe analytical oracle language (generation-time compliance).

All oracle/LLM prompts and rule outputs use probabilistic analytics vocabulary.
Banned at every stage: Buy Now, Do Not Touch, sell/buy imperatives.
"""

from __future__ import annotations

import re
from typing import Literal

SAFE_VERDICT_BULLISH = "BULLISH_ANALYTICS"
SAFE_VERDICT_RISK = "ELEVATED_RISK"
SAFE_VERDICT_NEUTRAL = "NEUTRAL_OBSERVE"

SafeOracleVerdict = Literal["BULLISH_ANALYTICS", "ELEVATED_RISK", "NEUTRAL_OBSERVE"]

_BANNED_PHRASES = (
    "buy now",
    "do not touch",
    "sell now",
    "you should buy",
    "you should sell",
    "strong buy",
    "strong sell",
)

_ANALYTICAL_MARKERS = ("probability", "analytics", "informational", "observed", "metrics")

_SYSTEM_INSTRUCTION = (
    "You are a quantitative crypto analytics assistant. "
    "Return exactly ONE sentence using probabilistic, non-imperative language. "
    "Format: '{PROBABILITY}% probability of favorable conditions — {ASSET}: {REASON}. "
    "Informational analytics only; not investment advice.' "
    "NEVER use buy/sell commands, imperative trading language, or direct trade recommendations."
)


def build_analytical_prompt(
    *,
    asset: str,
    score: float,
    summary: str,
    reasons: str = "",
    risks: str = "",
    extra_context: str = "",
) -> str:
    parts = [
        _SYSTEM_INSTRUCTION,
        f"Asset: {asset}",
        f"Analytics score: {score}",
        f"Summary: {summary}",
    ]
    if reasons:
        parts.append(f"Supporting factors: {reasons}")
    if risks:
        parts.append(f"Risk factors: {risks}")
    if extra_context:
        parts.append(extra_context)
    return "\n".join(parts)


def build_hub_llm_prompt(
    asset: str,
    opportunity_score: float,
    summary: str,
    hub_context: dict,
) -> str:
    macro = hub_context.get("macro") or {}
    sentiment = hub_context.get("sentiment") or {}
    geo = hub_context.get("geo_news") or {}
    extra = (
        f"Macro regime={macro.get('macro_regime_proxy')}, "
        f"FearGreed={sentiment.get('fear_greed_index')}, "
        f"Geo headlines={geo.get('geopolitical_headline_count')}"
    )
    return build_analytical_prompt(
        asset=asset,
        score=opportunity_score,
        summary=summary,
        extra_context=extra,
    )


def contains_banned_advice_language(text: str) -> bool:
    lower = (text or "").lower()
    return any(phrase in lower for phrase in _BANNED_PHRASES)


def accepted_analytical_sentence(sentence: str | None) -> bool:
    if not sentence or not sentence.strip():
        return False
    if contains_banned_advice_language(sentence):
        return False
    lower = sentence.lower()
    return any(marker in lower for marker in _ANALYTICAL_MARKERS)


def probability_from_score(score: float) -> int:
    return max(5, min(95, int(round(score))))


def verdict_from_analytics(score: float, confidence: float, *, min_score: float, min_confidence: float) -> SafeOracleVerdict:
    if score >= min_score and confidence >= min_confidence:
        return SAFE_VERDICT_BULLISH
    if score >= min_score * 0.6:
        return SAFE_VERDICT_NEUTRAL
    return SAFE_VERDICT_RISK


def format_analytical_sentence(
    asset: str,
    *,
    probability: int,
    reason: str,
    verdict: SafeOracleVerdict | None = None,
) -> str:
    if verdict == SAFE_VERDICT_RISK:
        lead = f"{probability}% probability of elevated risk"
    elif verdict == SAFE_VERDICT_NEUTRAL:
        lead = f"{probability}% probability of neutral conditions"
    else:
        lead = f"{probability}% probability of favorable conditions"
    clean_reason = reason.strip().rstrip(".")
    return (
        f"{lead} — {asset}: {clean_reason}. "
        "Informational analytics only; not investment advice."
    )


def parse_verdict_from_sentence(sentence: str) -> SafeOracleVerdict:
    lower = sentence.lower()
    if "elevated risk" in lower or "unfavorable" in lower:
        return SAFE_VERDICT_RISK
    if "neutral" in lower:
        return SAFE_VERDICT_NEUTRAL
    return SAFE_VERDICT_BULLISH


def normalize_llm_sentence(sentence: str, *, asset: str, score: float) -> tuple[SafeOracleVerdict, str]:
    """Coerce LLM output into safe analytical format; reject banned phrases."""
    raw = (sentence or "").strip().split("\n")[0].strip()
    if contains_banned_advice_language(raw):
        prob = probability_from_score(score)
        verdict = SAFE_VERDICT_RISK if score < 50 else SAFE_VERDICT_NEUTRAL
        return verdict, format_analytical_sentence(
            asset,
            probability=prob,
            reason="Model output contained non-compliant phrasing; abstaining to analytics-only summary",
            verdict=verdict,
        )
    if accepted_analytical_sentence(raw):
        return parse_verdict_from_sentence(raw), raw
    prob = probability_from_score(score)
    verdict = verdict_from_analytics(score, score, min_score=65, min_confidence=60)
    return verdict, format_analytical_sentence(asset, probability=prob, reason=raw[:200], verdict=verdict)


_PROB_RE = re.compile(r"(\d{1,3})\s*%\s*probability", re.IGNORECASE)


def extract_probability(sentence: str, *, fallback_score: float) -> int:
    m = _PROB_RE.search(sentence or "")
    if m:
        return max(1, min(99, int(m.group(1))))
    return probability_from_score(fallback_score)
