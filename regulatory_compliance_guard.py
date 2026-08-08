"""
BLACKDARK — Regulatory compliance guard (unlicensed investment advice mitigation).

Transforms direct buy/sell oracle language into informational analytics labels
required for SEC/MiFID-style "not investment advice" posture.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.RegulatoryCompliance")

from legal_shield import (
    MANDATORY_DISCLAIMER_PREFIX,
    ORACLE_CLASSIFICATION_LABEL,
    STRICT_DISCLAIMER,
    apply_legal_shield,
    get_disclaimer,
    get_mandatory_prefix,
    prefix_disclaimer,
)

# Back-compat aliases (Layer 1 source of truth = legal_shield.py)
REGULATORY_DISCLAIMER = STRICT_DISCLAIMER

PUBLIC_VERDICT_BULLISH = "BULLISH_ANALYTICS"
PUBLIC_VERDICT_BEARISH = "BEARISH_ANALYTICS"
PUBLIC_VERDICT_NEUTRAL = "NEUTRAL_OBSERVE"
PUBLIC_VERDICT_RISK = "ELEVATED_RISK"

_INTERNAL_BULLISH = frozenset({"BUY", "Buy Now", "BULLISH", PUBLIC_VERDICT_BULLISH})
_INTERNAL_BEARISH = frozenset({"SELL", "BEARISH", PUBLIC_VERDICT_BEARISH})
_INTERNAL_NEUTRAL = frozenset({"WAIT", "HOLD", "NEUTRAL", PUBLIC_VERDICT_NEUTRAL})
_INTERNAL_RISK = frozenset({"CAUTION", "Do Not Touch", "AVOID", PUBLIC_VERDICT_RISK})

_ADVICE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bBuy Now\b", re.I), "Analytics indicate positive momentum"),
    (re.compile(r"\bDo Not Touch\b", re.I), "Analytics indicate elevated risk"),
    (re.compile(r"\bStrong buy signal\b", re.I), "Strong bullish analytics signal"),
    (re.compile(r"\bbuy signal\b", re.I), "Bullish analytics signal"),
    (re.compile(r"\bsell signal\b", re.I), "Bearish analytics signal"),
    (re.compile(r"\bBuy now at\b", re.I), "Observed price near"),
    (re.compile(r"\bConsider buying\b", re.I), "Analytics suggest monitoring entry near"),
    (re.compile(r"\bConsider exiting\b", re.I), "Analytics suggest monitoring exit levels for"),
    (re.compile(r"\bSell with stop-loss\b", re.I), "Risk analytics reference resistance near"),
    (re.compile(r"\bACTION:\s*", re.I), "Analytics summary:"),
    (re.compile(r"\byou should buy\b", re.I), "metrics show positive momentum for"),
    (re.compile(r"\byou should sell\b", re.I), "metrics show negative momentum for"),
)


def _enabled() -> bool:
    return getattr(config, "REGULATORY_COMPLIANCE_ENABLED", True)


def classify_internal_verdict(verdict: str) -> str:
    v = (verdict or "").strip()
    if v in _INTERNAL_BULLISH or v.upper() == "BUY":
        return "bullish"
    if v in _INTERNAL_BEARISH or v.upper() == "SELL":
        return "bearish"
    if v in _INTERNAL_RISK or v == "Do Not Touch":
        return "risk"
    return "neutral"


def to_public_verdict(verdict: str) -> str:
    """Map legacy/direct verdicts to compliant public labels."""
    if not _enabled():
        return verdict
    bucket = classify_internal_verdict(verdict)
    if bucket == "bullish":
        return PUBLIC_VERDICT_BULLISH
    if bucket == "bearish":
        return PUBLIC_VERDICT_BEARISH
    if bucket == "risk":
        return PUBLIC_VERDICT_RISK
    return PUBLIC_VERDICT_NEUTRAL


def to_internal_action_verdict(verdict: str) -> str:
    """Normalize for execution/audit pipelines that expect legacy buckets."""
    bucket = classify_internal_verdict(verdict)
    if bucket == "bullish":
        return "Buy Now"
    if bucket == "bearish":
        return "SELL"
    if bucket == "risk":
        return "Do Not Touch"
    return "WAIT"


def is_actionable_bullish(verdict: str) -> bool:
    return classify_internal_verdict(verdict) == "bullish"


def sanitize_advice_text(text: str) -> str:
    if not _enabled() or not text:
        return text
    out = text
    for pattern, replacement in _ADVICE_PATTERNS:
        out = pattern.sub(replacement, out)
    return out.strip()


def compliant_oracle_sentence(asset: str, verdict: str, reason: str) -> str:
    """Build a single-sentence oracle line without imperative buy/sell advice."""
    public = to_public_verdict(verdict)
    clean_reason = sanitize_advice_text(reason)
    templates = {
        PUBLIC_VERDICT_BULLISH: (
            f"{asset} — {public}: {clean_reason} "
            f"(informational analytics; not a recommendation to buy or sell)."
        ),
        PUBLIC_VERDICT_BEARISH: (
            f"{asset} — {public}: {clean_reason} "
            f"(informational analytics; not a recommendation to buy or sell)."
        ),
        PUBLIC_VERDICT_RISK: (
            f"{asset} — {public}: {clean_reason} "
            f"(informational risk analytics only)."
        ),
        PUBLIC_VERDICT_NEUTRAL: (
            f"{asset} — {public}: {clean_reason} "
            f"(monitoring signal; not investment advice)."
        ),
    }
    return templates.get(public, f"{asset} — {public}: {clean_reason}")


def compliant_action_text(score: int, price: float, support: float, resistance: float) -> str:
    """Non-imperative analytics phrasing (replaces 'Buy now at...')."""
    if score >= 70:
        return (
            f"Analytics: momentum score elevated — observed ${price:,.0f}; "
            f"support zone ~${support:,.0f}; resistance ~${resistance:,.0f}"
        )
    if score >= 55:
        return (
            f"Analytics: moderate momentum — price ${price:,.0f}; "
            f"support zone ~${support:,.0f}"
        )
    if score >= 40:
        return (
            f"Analytics: neutral momentum — monitoring range "
            f"${support:,.0f}–${resistance:,.0f}"
        )
    return (
        f"Analytics: weak momentum — resistance ~${resistance:,.0f}; "
        f"elevated downside risk metrics"
    )


def compliant_verdict_description(asset: str, score: int, price: float, verdict: str) -> str:
    public = to_public_verdict(verdict)
    return (
        f"{public} for {asset} at ${price:,.0f} "
        f"(Opportunity Analytics Score: {score}/100 — informational only)"
    )


def llm_oracle_system_prompt() -> str:
    return (
        "You are a crypto market analytics engine for BLACKDARK. "
        "Return ONE sentence of informational analytics only. "
        "NEVER tell the user to buy, sell, or trade. "
        "NEVER use 'Buy Now', 'Sell Now', or 'Do Not Touch'. "
        "Start with one of: 'Bullish analytics —', 'Bearish analytics —', "
        "'Elevated risk —', or 'Neutral observe —'. "
        "End with '(informational only; not investment advice)'."
    )


def apply_regulatory_compliance(payload: dict[str, Any]) -> dict[str, Any]:
    """Transform oracle API payload to compliant public form."""
    if not _enabled():
        return payload

    out = dict(payload)
    raw_verdict = str(out.get("verdict") or out.get("oracle_verdict") or "")
    if raw_verdict:
        out.setdefault("oracle_internal_verdict", to_internal_action_verdict(raw_verdict))
        out["verdict"] = to_public_verdict(raw_verdict)
        if "oracle_verdict" in out:
            out["oracle_verdict"] = out["verdict"]

    for field in ("oracle", "narrative", "action", "explanation"):
        if isinstance(out.get(field), str):
            out[field] = sanitize_advice_text(str(out[field]))

    if isinstance(out.get("explanation"), dict):
        exp = dict(out["explanation"])
        for key in ("summary", "narrative", "text"):
            if isinstance(exp.get(key), str):
                exp[key] = sanitize_advice_text(str(exp[key]))
        out["explanation"] = exp

    sentence = out.get("sentence") or out.get("oracle")
    if isinstance(sentence, str) and raw_verdict:
        out["oracle"] = sanitize_advice_text(sentence)
        if "sentence" in out:
            out["sentence"] = out["oracle"]

    out["regulatory_classification"] = "informational_analytics_only"
    out["compliance_engine"] = "regulatory_compliance_guard_v3+legal_shield"
    # Layer 1+2: mandatory prefix + classification (non-removable)
    out = apply_legal_shield(out)
    return out


def regulatory_compliance_status() -> dict[str, Any]:
    return {
        "enabled": _enabled(),
        "classification": "informational_analytics_only",
        "classification_label": ORACLE_CLASSIFICATION_LABEL,
        "public_verdicts": {
            "bullish": PUBLIC_VERDICT_BULLISH,
            "bearish": PUBLIC_VERDICT_BEARISH,
            "neutral": PUBLIC_VERDICT_NEUTRAL,
            "elevated_risk": PUBLIC_VERDICT_RISK,
        },
        "prohibited_public_phrases": [
            "Buy Now",
            "Sell Now",
            "Do Not Touch",
            "you should buy",
            "you should sell",
        ],
        "disclaimer": get_disclaimer(),
        "policy": (
            "Oracle outputs are analytics labels, not investment recommendations. "
            "Users must acknowledge Terms/Disclaimer before Oracle use. "
            "Live execution uses separate user-controlled API keys and risk gates."
        ),
    }
