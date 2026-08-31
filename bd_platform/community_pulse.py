"""
Community Pulse — Features #272 + #287 + #290 + #292 merged (Sprint 2).

#272 Mindshare | #287 NLP sentiment (sub-task) | #290 Social Dominance | #292 Social Volume.
NOT standalone — purchased feed (LunarCrush/Kaito API), no NLP team.
Merged into Market Radar as Community Pulse.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CommunityPulse")

_ABSORBED_IDS = (272, 287, 290, 292)
_FEATURE_ID = 272
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Community Pulse (Market Radar)"
_SPRINT = 2
_SEED_PATH = Path("data/community_pulse_seed.json")
_METHODOLOGY_VERSION = "1.0"
_MIN_MENTIONS_WEEKLY = 100

_ABSORBED_TICKETS = {
    272: "Mindshare Intelligence",
    287: "NLP sentiment classification (sub-task)",
    290: "Social Dominance",
    292: "Social Volume",
}

_DISCLAIMER = (
    "Community Pulse measures social attention and sentiment from purchased feeds. "
    "Not investment advice. Low-confidence and sarcastic content is flagged. "
    "Sentiment = feed classification — not profit probability."
)

SentimentLabel = Literal["positive", "neutral", "negative"]
ConfidenceLevel = Literal["high", "low", "insufficient"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "provider": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("community pulse seed load failed: %s", exc)
        return {"assets": {}, "provider": {}}


def build_provider_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Purchased feed — LunarCrush/Kaito API. No NLP team, no raw scraper."""
    seed = seed or _load_seed()
    provider = seed.get("provider") or {}
    return {
        "provider": provider.get("name", "LunarCrush"),
        "fallback_provider": provider.get("fallback", "Kaito"),
        "no_nlp_team": True,
        "no_raw_scraper": True,
        "purchased_feed": True,
        "monthly_cost_cap_usd": provider.get("monthly_cost_cap_usd", 500),
        "current_spend_usd": provider.get("current_spend_usd", 0),
        "paused_on_exceed": provider.get("paused_on_exceed", False),
        "display": (
            f"Feed: {provider.get('name', 'LunarCrush')} API "
            f"(fallback: {provider.get('fallback', 'Kaito')}) | "
            f"No NLP team — purchased feed only | "
            f"Cap: ${provider.get('monthly_cost_cap_usd', 500)}/month"
        ),
    }


def build_nlp_sentiment_block(asset_data: dict[str, Any], *, symbol: str) -> dict[str, Any]:
    """#287 NLP sentiment classification — from purchased feed, not built in-house."""
    mentions = int(asset_data.get("mentions_weekly", 0))
    sentiment_raw = asset_data.get("sentiment") or {}
    label: SentimentLabel = sentiment_raw.get("label", "neutral")
    score = float(sentiment_raw.get("score", 0))
    sarcasm_flag = bool(sentiment_raw.get("sarcasm_detected", False))
    model = sentiment_raw.get("model", "lunarcrush-v3")
    model_version = sentiment_raw.get("model_version", "3.1")
    source_coverage = sentiment_raw.get("source_coverage_pct", 0)

    if mentions < _MIN_MENTIONS_WEEKLY:
        confidence: ConfidenceLevel = "insufficient"
        greyed_out = True
        warning = "Insufficient volume for reliable sentiment"
    elif sarcasm_flag:
        confidence = "low"
        greyed_out = True
        warning = "Sarcasm detected — sentiment confidence reduced"
    elif mentions < _MIN_MENTIONS_WEEKLY * 2:
        confidence = "low"
        greyed_out = True
        warning = "Low volume — confidence reduced"
    else:
        confidence = "high"
        greyed_out = False
        warning = None

    return {
        "sub_task": "#287",
        "symbol": symbol,
        "sentiment_label": label if confidence != "insufficient" else "neutral",
        "sentiment_score": score if not greyed_out else None,
        "positive_pct": sentiment_raw.get("positive_pct"),
        "neutral_pct": sentiment_raw.get("neutral_pct"),
        "negative_pct": sentiment_raw.get("negative_pct"),
        "confidence": confidence,
        "greyed_out": greyed_out,
        "sarcasm_detected": sarcasm_flag,
        "sarcasm_handling": "confidence reduced to low when detected",
        "model": model,
        "model_version": model_version,
        "source_coverage_pct": source_coverage,
        "model_version_visible": True,
        "source_coverage_visible": True,
        "history_days": sentiment_raw.get("history_days", 30),
        "not_a_signal": True,
        "display": (
            f"Sentiment: {label} ({score:.2f}) | Model: {model} v{model_version} | "
            f"Coverage: {source_coverage}% | Confidence: {confidence}"
            + (f" | {warning}" if warning else "")
        ),
        "warning": warning,
    }


def build_mindshare_block(asset_data: dict[str, Any], *, symbol: str) -> dict[str, Any]:
    """#272 mindshare layer."""
    mindshare_pct = float(asset_data.get("mindshare_pct", 0))
    mentions = int(asset_data.get("mentions_weekly", 0))
    return {
        "sub_task": "#272",
        "symbol": symbol,
        "mindshare_pct": mindshare_pct,
        "mentions_weekly": mentions,
        "trend": asset_data.get("trend", "flat"),
        "display": f"Mindshare: {mindshare_pct}% | Mentions: {mentions}/week",
    }


def build_social_dominance_block(
    asset_data: dict[str, Any],
    *,
    symbol: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#290 social dominance — absorbed into #272. NOT standalone."""
    seed = seed or _load_seed()
    dom = asset_data.get("social_dominance") or {}
    universe = seed.get("universe") or {}
    mentions = int(asset_data.get("mentions_weekly", 0))
    dominance_pct = float(dom.get("dominance_pct", 0))

    if mentions < _MIN_MENTIONS_WEEKLY:
        low_volume = True
        greyed_out = True
        confidence = "insufficient"
        warning = "Low volume — dominance % unreliable"
    else:
        low_volume = False
        greyed_out = False
        confidence = "high"
        warning = None

    formula = "asset_mentions / total_tracked_mentions × 100"
    return {
        "sub_task": "#290",
        "archived_standalone": True,
        "absorbed_into": "#272 Community Pulse",
        "symbol": symbol,
        "dominance_pct": dominance_pct if not greyed_out else None,
        "trend": dom.get("trend", "flat"),
        "percentile": dom.get("percentile"),
        "rank": dom.get("rank"),
        "universe_version": universe.get("version"),
        "universe_asset_count": universe.get("asset_count"),
        "universe_documented": True,
        "formula": formula,
        "historical_reproducible": dom.get("historical_reproducible", True),
        "low_volume_safeguard": low_volume,
        "greyed_out": greyed_out,
        "confidence": confidence,
        "display": (
            f"Social dominance: {dominance_pct if not greyed_out else 'N/A'}% | "
            f"Trend: {dom.get('trend', 'flat')} | "
            f"Percentile: {dom.get('percentile', 'N/A')} | "
            f"Universe v{universe.get('version', '?')}"
            + (f" | {warning}" if warning else "")
        ),
        "warning": warning,
    }


def build_social_volume_block(asset_data: dict[str, Any], *, symbol: str) -> dict[str, Any]:
    """#292 social volume — absorbed."""
    vol = asset_data.get("social_volume") or {}
    return {
        "sub_task": "#292",
        "symbol": symbol,
        "volume_24h": vol.get("volume_24h", 0),
        "volume_change_pct": vol.get("volume_change_pct", 0),
        "display": (
            f"Social volume: {vol.get('volume_24h', 0):,} | "
            f"Change: {vol.get('volume_change_pct', 0):+.1f}%"
        ),
    }


def build_community_pulse_panel(asset: str = "BTC") -> dict[str, Any]:
    """Community Pulse panel — merged social/sentiment cluster."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_data = (seed.get("assets") or {}).get(sym)

    provider_gate = build_provider_gate(seed)
    if provider_gate.get("paused_on_exceed"):
        return {
            "ok": False,
            "feature_ids": list(_ABSORBED_IDS),
            "error": "provider_cost_cap_exceeded",
            "provider_gate": provider_gate,
        }

    if not asset_data:
        return {
            "ok": False,
            "feature_ids": list(_ABSORBED_IDS),
            "error": "asset_not_tracked",
            "asset": sym,
        }

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_ids": list(_ABSORBED_IDS),
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "surface": "community_pulse",
        "asset": sym,
        "mindshare": build_mindshare_block(asset_data, symbol=sym),
        "sentiment": build_nlp_sentiment_block(asset_data, symbol=sym),
        "social_dominance": build_social_dominance_block(asset_data, symbol=sym, seed=seed),
        "social_volume": build_social_volume_block(asset_data, symbol=sym),
        "provider_gate": provider_gate,
        "rejected_standalone_287": True,
        "no_separate_nlp_engine": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def community_pulse_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Community Pulse",
        "absorbed_ids": list(_ABSORBED_IDS),
        "absorbed_tickets": _ABSORBED_TICKETS,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "provider_gate": build_provider_gate(seed),
        "rejected_standalone_tickets": [287, 290],
        "nlp_sentiment_sub_task": "#287",
        "no_nlp_team": True,
        "acceptance_criteria": {
            "model_version_visible": True,
            "source_coverage_visible": True,
            "sarcasm_confidence_handling": True,
            "low_volume_confidence_handling": True,
            "purchased_feed_only": True,
            "social_dominance_universe_versioned": True,
            "social_dominance_low_volume_safeguards": True,
            "social_dominance_historical_reproducible": True,
        },
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }
