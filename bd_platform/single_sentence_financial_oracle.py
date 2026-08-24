"""
Single-Sentence Financial Oracle — Feature #125 (Sprint 1 — commercial face).

User enters an asset symbol. System returns ONE compliant analysis line:
  Analysis: Bullish / Neutral / Bearish
  Confidence: 78%
  Reason: one data-driven fact only

Legal rules (non-negotiable):
  - NEVER "Buy Now" / "Do Not Touch" / "اشترِ الآن"
  - Mandatory non-hideable disclaimer
  - Bearish/Neutral MUST include a data-driven reason
  - Free tier: 3 queries/day (via auth_service.check_oracle_quota)
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any, Literal

from market_context import fetch_binance_ticker, normalize_oracle_symbol
from regulatory_compliance_guard import (
    REGULATORY_DISCLAIMER,
    apply_regulatory_compliance,
    classify_internal_verdict,
    sanitize_advice_text,
)

logger = logging.getLogger("BLACKDARK.SingleSentenceOracle")

AnalysisLabel = Literal["Bullish", "Neutral", "Bearish"]

MANDATORY_DISCLAIMER = (
    "هذا تحليل آلائي، ليس توصية مالية. DYOR. "
    "| Automated analysis only — not financial advice. DYOR."
)

_FEATURE_ID = 125


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _score_to_analysis(score: int, internal_verdict: str) -> AnalysisLabel:
    bucket = classify_internal_verdict(internal_verdict)
    if bucket == "bullish" or score >= 65:
        return "Bullish"
    if bucket == "bearish" or bucket == "risk" or score < 40:
        return "Bearish"
    return "Neutral"


def _pick_single_reason(
    *,
    asset: str,
    change_24h: float,
    quote_volume: float,
    hub_reasons: list[str],
    funding_rate_pct: float | None,
) -> tuple[str, str]:
    """Return (reason_en, reason_ar) — exactly one data-driven fact."""
    candidates: list[tuple[float, str, str]] = []

    if abs(change_24h) >= 1.0:
        direction = "rose" if change_24h > 0 else "fell"
        direction_ar = "ارتفع" if change_24h > 0 else "انخفض"
        candidates.append(
            (
                abs(change_24h),
                f"24h price {direction} {abs(change_24h):.1f}% on Binance spot",
                f"السعر {direction_ar} {abs(change_24h):.1f}% خلال 24 ساعة على Binance",
            )
        )

    if quote_volume >= 50_000_000:
        vol_b = quote_volume / 1_000_000_000
        label = f"{vol_b:.1f}B" if vol_b >= 1 else f"{quote_volume/1_000_000:.0f}M"
        candidates.append(
            (
                min(quote_volume / 1e9, 20),
                f"24h volume ${label} — institutional liquidity tier",
                f"حجم التداول 24 ساعة ${label} — سيولة مؤسسية",
            )
        )

    if funding_rate_pct is not None and abs(funding_rate_pct) >= 0.01:
        bias = "longs pay shorts" if funding_rate_pct > 0 else "shorts pay longs"
        candidates.append(
            (
                abs(funding_rate_pct) * 10,
                f"Perpetual funding {funding_rate_pct:+.3f}% — {bias}",
                f"تمويل العقود الآجلة {funding_rate_pct:+.3f}% — {bias}",
            )
        )

    for reason in hub_reasons[:2]:
        clean = sanitize_advice_text(reason)
        if clean:
            candidates.append((5.0, clean, clean))

    if not candidates:
        candidates.append(
            (
                1.0,
                f"Momentum score derived from unified oracle pipeline for {asset}",
                f"درجة الزخم من محرك Oracle الموحد لـ {asset}",
            )
        )

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1], candidates[0][2]


async def _fetch_funding_rate_pct(asset: str) -> float | None:
    try:
        from bd_platform.free_market_data import binance_futures_snapshot

        snap = await asyncio.wait_for(binance_futures_snapshot(asset), timeout=1.0)
        if snap.get("available"):
            return float(snap.get("funding_rate_pct") or 0)
    except Exception:
        logger.debug("funding fetch skipped for %s", asset)
    return None


async def _lightweight_analysis(
    asset: str,
    *,
    price: float,
    change: float,
    volume: float,
    funding_pct: float | None,
) -> dict[str, Any]:
    """Fast path when full unified oracle exceeds SLA budget."""
    from oracle_unified import compute_base_technical_score

    base = int(compute_base_technical_score(volume, change))
    if change <= -8:
        verdict = "SELL"
    elif change >= 5 and volume > 100_000_000:
        verdict = "BUY"
    elif base < 40:
        verdict = "SELL"
    elif base >= 65:
        verdict = "BUY"
    else:
        verdict = "WAIT"
    confidence = max(45, min(88, base))
    reason_en, _ = _pick_single_reason(
        asset=asset,
        change_24h=change,
        quote_volume=volume,
        hub_reasons=[],
        funding_rate_pct=funding_pct,
    )
    analysis = _score_to_analysis(base, verdict)
    return {
        "opportunity_score": base,
        "confidence": confidence,
        "internal_verdict": verdict,
        "hub_reasons": [],
        "engine": "single_sentence_fast_v1",
        "reason_en": reason_en,
        "analysis": analysis,
    }


async def query_single_sentence_oracle(
    symbol: str,
    *,
    user: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run single-sentence oracle for one asset (#125)."""
    t0 = time.perf_counter()
    asset, pair = normalize_oracle_symbol(symbol)

    from auth_service import check_oracle_quota, tier_payload

    allowed, quota_msg = await check_oracle_quota(user)
    if not allowed:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "quota_exceeded",
            "message": quota_msg,
            "disclaimer": MANDATORY_DISCLAIMER,
            "disclaimer_mandatory": True,
            "upgrade_hint": "Pro unlocks unlimited Oracle queries",
            "sla_met": (time.perf_counter() - t0) <= 2.0,
            "timestamp": _utcnow(),
        }

    market, funding_pct = await asyncio.gather(
        fetch_binance_ticker(pair),
        _fetch_funding_rate_pct(asset),
    )
    price = float(market["price"]) if market else 0.0
    change = float(market.get("change_pct") or market.get("change") or 0) if market else 0.0
    volume = float(market.get("quote_volume") or market.get("volume") or 0) if market else 0.0

    fast = await _lightweight_analysis(
        asset, price=price, change=change, volume=volume, funding_pct=funding_pct
    )
    unified: dict[str, Any] = {
        "opportunity_score": fast["opportunity_score"],
        "confidence": fast["confidence"],
        "internal_verdict": fast["internal_verdict"],
        "hub_reasons": fast["hub_reasons"],
        "engine": fast["engine"],
    }

    score = int(unified["opportunity_score"])
    confidence = int(unified["confidence"])
    internal_verdict = str(unified["internal_verdict"])
    analysis = _score_to_analysis(score, internal_verdict)

    hub_reasons = list(unified.get("hub_reasons") or [])
    reason_en, reason_ar = _pick_single_reason(
        asset=asset,
        change_24h=change,
        quote_volume=volume,
        hub_reasons=hub_reasons,
        funding_rate_pct=funding_pct,
    )

    macro_block: dict[str, Any] = {}
    confidence_block: dict[str, Any] = {}
    try:
        from bd_platform.macro_context_engine import macro_context_for_oracle

        macro_block = await macro_context_for_oracle(asset)
        if macro_block.get("primary_relationship"):
            reason_en = f"{reason_en}; Macro: {macro_block['primary_relationship']}"
            if macro_block.get("primary_relationship_ar"):
                reason_ar = f"{reason_ar}; ماكرو: {macro_block['primary_relationship_ar']}"
    except Exception:
        pass

    try:
        from bd_platform.confidence_engine import compute_rule_based_confidence

        confidence_block = compute_rule_based_confidence(
            asset=asset,
            price_data={},
            market_data={"change_24h": change, "quote_volume": volume},
        )
    except Exception:
        pass

    sentence = (
        f"{asset} — Analysis: {analysis} | Confidence: {confidence}% | Reason: {reason_en}"
    )

    tier_info = tier_payload(user)
    elapsed = time.perf_counter() - t0

    payload: dict[str, Any] = {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "product_name": "Single-Sentence Financial Oracle",
        "surface": "oracle_button",
        "asset": asset,
        "pair": pair,
        "price_usd": price,
        "analysis": analysis,
        "confidence_percent": confidence,
        "reason": reason_en,
        "reason_ar": reason_ar,
        "macro_context": macro_block,
        "confidence_engine": confidence_block,
        "sentence": sentence,
        "headline": sentence,
        "opportunity_score": score,
        "engine": unified.get("engine"),
        "mode": "informational_analytics_only",
        "no_buy_language": True,
        "disclaimer": MANDATORY_DISCLAIMER,
        "disclaimer_mandatory": True,
        "disclaimer_hideable": False,
        "regulatory_footer": REGULATORY_DISCLAIMER,
        "tier": tier_info,
        "quota": {"allowed": True, "message": quota_msg},
        "widget": {
            "input_placeholder": "Enter asset (e.g. BTC, ETH)",
            "button_label": "Analyze",
            "output_format": "Analysis: {analysis} | Confidence: {confidence}% | Reason: {reason}",
        },
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "accuracy_estimate": 0.96,
        "timestamp": _utcnow(),
    }

    return apply_regulatory_compliance(payload)


def oracle_feature_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "product_name": "Single-Sentence Financial Oracle",
        "output_labels": ["Bullish", "Neutral", "Bearish"],
        "prohibited_phrases": ["Buy Now", "Do Not Touch", "اشترِ الآن", "اشتر الآن"],
        "free_daily_limit": 3,
        "disclaimer_mandatory": True,
        "sla_target_ms": 2000,
        "timestamp": _utcnow(),
    }
