"""
BLACKDARK — Dimension conflict guard (AI multi-modal veto / abstain).

When technical, on-chain, sentiment, and macro dimensions strongly disagree,
forces WAIT / Do Not Touch instead of random or contradictory buy signals.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

import config

logger = logging.getLogger("BLACKDARK.DimensionConflictGuard")

ConflictSeverity = Literal["none", "mild", "severe"]


def _enabled() -> bool:
    return getattr(config, "DIMENSION_CONFLICT_VETO_ENABLED", True)


def severe_score_cap() -> float:
    return float(getattr(config, "DIMENSION_CONFLICT_SEVERE_SCORE_CAP", 49))


def mild_score_cap() -> float:
    return float(getattr(config, "DIMENSION_CONFLICT_MILD_SCORE_CAP", 59))


def min_buy_score() -> float:
    return float(getattr(config, "AI_ORACLE_MIN_SCORE", 65))


def apply_dimension_conflict_guard(
    score: float,
    breakdown: dict[str, Any] | None,
) -> tuple[float, dict[str, Any]]:
    """Cap score and set veto/abstain flags when dimensions conflict."""
    conflicts = (breakdown or {}).get("conflicts") or {}
    severity = str(conflicts.get("severity") or "none")
    meta: dict[str, Any] = {
        "severity": severity,
        "veto": False,
        "abstain": False,
        "message": conflicts.get("message", ""),
        "bullish": conflicts.get("bullish", []),
        "bearish": conflicts.get("bearish", []),
        "confidence_penalty": float(conflicts.get("confidence_penalty") or 0.0),
    }

    if not _enabled() or severity == "none":
        return score, meta

    adjusted = float(score)
    if severity == "severe":
        adjusted = min(adjusted, severe_score_cap())
        meta["veto"] = True
        meta["abstain"] = True
        meta["action"] = "WAIT"
        logger.info(
            "Dimension conflict VETO | bullish=%s bearish=%s score=%.1f→%.1f",
            meta["bullish"],
            meta["bearish"],
            score,
            adjusted,
        )
    elif severity == "mild":
        adjusted = min(adjusted, mild_score_cap())
        meta["abstain"] = True
        meta["action"] = "CAUTION"
        logger.info(
            "Dimension conflict abstain | bullish=%s bearish=%s score=%.1f→%.1f",
            meta["bullish"],
            meta["bearish"],
            score,
            adjusted,
        )

    return adjusted, meta


def arbitrage_verdict_with_conflict(
    score: float,
    confidence: float,
    conflict_meta: dict[str, Any],
) -> str:
    """Arbitrage oracle verdict with conflict veto."""
    if conflict_meta.get("veto") or conflict_meta.get("abstain"):
        return "Do Not Touch"
    if score >= min_buy_score() and confidence >= float(getattr(config, "AI_ORACLE_MIN_CONFIDENCE", 60)):
        return "Buy Now"
    return "Do Not Touch"


def execution_allowed(
    *,
    breakdown: dict[str, Any] | None = None,
    conflict_meta: dict[str, Any] | None = None,
    oracle_verdict: str | None = None,
) -> tuple[bool, str]:
    """Hard gate for auto-execution when dimensions conflict."""
    if not _enabled():
        return True, "guard_disabled"

    meta = conflict_meta or {}
    if not meta and breakdown:
        conflicts = breakdown.get("conflicts") or {}
        meta = {"severity": conflicts.get("severity", "none"), "veto": False, "abstain": False}
        if conflicts.get("severity") == "severe":
            meta["veto"] = True
            meta["abstain"] = True
        elif conflicts.get("severity") == "mild":
            meta["abstain"] = True

    if meta.get("veto"):
        return False, "dimension_conflict_severe"
    if meta.get("abstain") and getattr(config, "DIMENSION_CONFLICT_BLOCK_MILD_EXECUTION", True):
        return False, "dimension_conflict_mild_abstain"

    from regulatory_compliance_guard import is_actionable_bullish

    verdict = str(oracle_verdict or "").strip()
    if verdict and not is_actionable_bullish(verdict):
        return False, "oracle_verdict_blocked"

    return True, "ok"


def llm_verdict_allowed(
    llm_verdict: str,
    score: float,
    conflict_meta: dict[str, Any],
) -> bool:
    """Prevent LLM from overriding conflict veto with bullish analytics."""
    from regulatory_compliance_guard import is_actionable_bullish

    if not is_actionable_bullish(llm_verdict):
        return True
    if conflict_meta.get("veto") or conflict_meta.get("abstain"):
        return False
    return score >= min_buy_score()


def dimension_conflict_status() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "severe_score_cap": severe_score_cap(),
        "mild_score_cap": mild_score_cap(),
        "min_buy_score": min_buy_score(),
        "block_mild_execution": getattr(config, "DIMENSION_CONFLICT_BLOCK_MILD_EXECUTION", True),
        "policy": (
            "Severe conflict (e.g. TA buy vs NLP fear vs whale distribution) → "
            "score capped, verdict WAIT/Do Not Touch, execution blocked."
        ),
        "dimensions": ["technical", "onchain", "sentiment", "macro", "whale"],
    }
