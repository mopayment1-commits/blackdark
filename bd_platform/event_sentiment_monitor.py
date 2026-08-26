"""
Event & Sentiment Monitor — Feature #443 (Intelligence Ledger Sprint-2).

Renamed from "Event-Driven Arbitrage" — analytics and monitoring only.
Execution language (buy/sell/automatic/exploit) is banned.

Capabilities:
  - NLP sentiment from Twitter, Reddit, Telegram, News (15-min refresh)
  - Event calendar: hard forks, listings, delistings, regulatory, unlocks
  - Fear/Greed index from unrealized PnL + funding rates + social volume
  - MC/Volume ratio + on-chain total value (asset scoring metrics)
  - #429 integration: sentiment context + event proximity on each signal

Cancelled v1:
  - Google Trends (API limited/unreliable)
  - Auto-trading / execution language
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.EventSentimentMonitor")

_FEATURE_ID = 443
_TITLE = "Event & Sentiment Monitor"
_LEGAL_NAME = "Event & Sentiment Monitor"
_RENAMED_FROM = "Event-Driven Arbitrage"
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Sprint-2 Event & Sentiment Monitor"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/event_sentiment_monitor_seed.json")
_METHODOLOGY_VERSION = "1.0"

_BANNED_TERMS = (
    "buy",
    "sell",
    "automatic",
    "exploit",
    "short",
    "شراء",
    "بيع",
    "آلي",
    "استغلال",
)

_DISCLAIMER = (
    "Event & Sentiment Monitor — sentiment analysis and event timeline only. "
    "NLP sentiment refreshed every 15 minutes from Twitter, Reddit, Telegram, and News. "
    "Event calendar provides alerts for forks, listings, delistings, regulatory actions, "
    "and unlock schedules. Fear/Greed index combines unrealized PnL, funding rates, and "
    "social volume. Monitoring only — no execution, no auto-trading, not investment advice."
)

SentimentLabel = Literal["positive", "neutral", "negative"]
FearGreedLabel = Literal["extreme_fear", "fear", "neutral", "greed", "extreme_greed"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "events": [], "sources": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("event sentiment monitor seed load failed: %s", exc)
        return {"assets": {}, "events": [], "sources": {}}


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _sentiment_label(score: float) -> SentimentLabel:
    if score >= 0.6:
        return "positive"
    if score <= 0.4:
        return "negative"
    return "neutral"


def _fear_greed_label(score: int) -> FearGreedLabel:
    if score <= 20:
        return "extreme_fear"
    if score <= 40:
        return "fear"
    if score <= 60:
        return "neutral"
    if score <= 80:
        return "greed"
    return "extreme_greed"


def _enabled_source_count(seed: dict[str, Any]) -> int:
    sources = seed.get("sources") or {}
    return sum(1 for s in sources.values() if s.get("enabled"))


def compute_nlp_sentiment(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Aggregate NLP sentiment across Twitter/Reddit/Telegram/News."""
    seed = seed or _load_seed()
    asset_data = (seed.get("assets") or {}).get(asset.upper())
    if not asset_data:
        return {"ok": False, "asset": asset, "error": "asset_not_found"}

    source_cfg = seed.get("sources") or {}
    asset_sources = asset_data.get("sources") or {}
    nlp_cfg = seed.get("nlp") or {}

    per_source: list[dict[str, Any]] = []
    weighted_sum = 0.0
    weight_total = 0.0

    for name, cfg in source_cfg.items():
        if name == "economic_calendar" or not cfg.get("enabled"):
            continue
        src = asset_sources.get(name) or {}
        score = float(src.get("sentiment_score", 0.5))
        weight = float(cfg.get("weight", 0.25))
        weighted_sum += score * weight
        weight_total += weight
        per_source.append({
            "source": name,
            "provider": cfg.get("provider"),
            "sentiment_score": round(score, 4),
            "sentiment_label": _sentiment_label(score),
            "volume": src.get("volume"),
            "mentions_24h": src.get("mentions_24h"),
            "weight": weight,
        })

    composite = round(weighted_sum / weight_total, 4) if weight_total > 0 else 0.5
    label = _sentiment_label(composite)
    accuracy = float(nlp_cfg.get("accuracy_pct", 0))

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "asset": asset.upper(),
        "composite_sentiment_score": composite,
        "composite_sentiment_label": label,
        "per_source": per_source,
        "source_count": len(per_source),
        "source_coverage_minimum": seed.get("source_coverage_minimum", 5),
        "nlp_model": nlp_cfg.get("model"),
        "nlp_model_version": nlp_cfg.get("model_version"),
        "nlp_accuracy_pct": accuracy,
        "nlp_accuracy_target_met": accuracy >= float(seed.get("nlp_accuracy_target_pct", 80)),
        "update_interval_minutes": seed.get("update_interval_minutes", 15),
        "google_trends_cancelled_v1": True,
        "monitoring_only": True,
        "display": (
            f"NLP Sentiment: {label} ({composite:.2f}) | "
            f"Sources: {len(per_source)} | Model: {nlp_cfg.get('model')} v{nlp_cfg.get('model_version')} | "
            f"Accuracy: {accuracy}%"
        ),
        "timestamp": _utcnow(),
    }


def compute_fear_greed_index(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fear/Greed from unrealized PnL + funding rates + social volume."""
    seed = seed or _load_seed()
    asset_data = (seed.get("assets") or {}).get(asset.upper())
    if not asset_data:
        return {"ok": False, "asset": asset, "error": "asset_not_found"}

    weights = seed.get("fear_greed_weights") or {}
    w_pnl = float(weights.get("unrealized_pnl", 0.4))
    w_funding = float(weights.get("funding_rates", 0.3))
    w_social = float(weights.get("social_volume", 0.3))

    pnl_ratio = float(asset_data.get("unrealized_pnl_ratio", 0.5))
    pnl_component = round(pnl_ratio * 100, 2)

    funding = float(asset_data.get("funding_rate", 0))
    funding_component = round(50 + funding * 10_000, 2)
    funding_component = max(0.0, min(100.0, funding_component))

    social_vol = float(asset_data.get("social_volume_24h", 0))
    baseline = float(asset_data.get("social_volume_baseline", 1)) or 1.0
    social_ratio = social_vol / baseline
    social_component = round(min(100.0, 50 + (social_ratio - 1) * 25), 2)

    score = round(
        pnl_component * w_pnl + funding_component * w_funding + social_component * w_social,
        1,
    )
    score_int = int(max(0, min(100, round(score))))
    label = _fear_greed_label(score_int)

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "asset": asset.upper(),
        "fear_greed_score": score_int,
        "fear_greed_label": label,
        "components": {
            "unrealized_pnl": {"weight": w_pnl, "value": pnl_component, "ratio": pnl_ratio},
            "funding_rates": {"weight": w_funding, "value": funding_component, "rate": funding},
            "social_volume": {"weight": w_social, "value": social_component, "ratio": round(social_ratio, 3)},
        },
        "display": f"Fear/Greed: {score_int} ({label.replace('_', ' ')})",
        "timestamp": _utcnow(),
    }


def compute_asset_scoring_metrics(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """MC/Volume ratio (P/E-like) and total on-chain value."""
    seed = seed or _load_seed()
    asset_data = (seed.get("assets") or {}).get(asset.upper())
    if not asset_data:
        return {"ok": False, "asset": asset, "error": "asset_not_found"}

    mc = float(asset_data.get("market_cap_usd", 0))
    vol = float(asset_data.get("volume_24h_usd", 0))
    mc_volume_ratio = round(mc / vol, 2) if vol > 0 else None

    supply = float(asset_data.get("on_chain_supply", 0))
    last_price = float(asset_data.get("last_on_chain_price_usd", 0))
    total_on_chain_value = round(supply * last_price, 2)

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "asset": asset.upper(),
        "market_cap_usd": mc,
        "volume_24h_usd": vol,
        "mc_volume_ratio": mc_volume_ratio,
        "mc_volume_label": "market_cap / daily_volume (P/E-like)",
        "on_chain_supply": supply,
        "last_on_chain_price_usd": last_price,
        "total_on_chain_value_usd": total_on_chain_value,
        "total_on_chain_method": "last_on_chain_price × circulating_supply",
        "asset_scoring_ref": "Asset Scoring layer",
        "display": (
            f"MC/Volume: {mc_volume_ratio} | "
            f"On-chain value: ${total_on_chain_value:,.0f}"
        ),
        "timestamp": _utcnow(),
    }


def compute_event_proximity(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Event proximity for an asset — alerts only."""
    seed = seed or _load_seed()
    now = now or datetime.now(UTC)
    asset_upper = asset.upper()
    events = seed.get("events") or []

    upcoming: list[dict[str, Any]] = []
    for ev in events:
        if str(ev.get("asset", "")).upper() != asset_upper:
            continue
        scheduled = _parse_dt(str(ev["scheduled_at_utc"]))
        delta = scheduled - now
        hours_until = round(delta.total_seconds() / 3600, 1)
        days_until = round(delta.total_seconds() / 86400, 2)
        proximity = "past" if hours_until < 0 else ("imminent" if hours_until <= 48 else "upcoming")

        upcoming.append({
            **ev,
            "hours_until": hours_until,
            "days_until": days_until,
            "proximity": proximity,
            "alert_only": True,
            "no_execution_recommendation": True,
        })

    upcoming.sort(key=lambda e: e.get("hours_until", 9999))
    nearest = upcoming[0] if upcoming else None

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "asset": asset_upper,
        "event_count": len(upcoming),
        "nearest_event": nearest,
        "events": upcoming,
        "alert_only": True,
        "display": (
            f"Events: {len(upcoming)} | "
            f"Nearest: {nearest.get('title') if nearest else 'none'} "
            f"({nearest.get('proximity') if nearest else 'n/a'})"
        ),
        "timestamp": _utcnow(),
    }


def build_event_calendar(
    *,
    seed: dict[str, Any] | None = None,
    event_type: str | None = None,
    asset: str | None = None,
) -> dict[str, Any]:
    """Full event calendar — hard forks, listings, delistings, regulatory, unlocks."""
    seed = seed or _load_seed()
    events = list(seed.get("events") or [])
    event_types = seed.get("event_types") or []

    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    if asset:
        events = [e for e in events if str(e.get("asset", "")).upper() == asset.upper()]

    now = datetime.now(UTC)
    enriched = []
    for ev in events:
        scheduled = _parse_dt(str(ev["scheduled_at_utc"]))
        delta = scheduled - now
        enriched.append({
            **ev,
            "hours_until": round(delta.total_seconds() / 3600, 1),
            "days_until": round(delta.total_seconds() / 86400, 2),
            "alert_only": True,
            "no_execution_recommendation": True,
        })

    enriched.sort(key=lambda e: e.get("hours_until", 9999))

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Event Calendar",
        "event_types_supported": event_types,
        "events": enriched,
        "count": len(enriched),
        "alerts_only": True,
        "monitoring_only": True,
        "google_trends_cancelled_v1": True,
        "timestamp": _utcnow(),
    }


def compute_price_sentiment_correlation(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare sentiment composite with recent price movement."""
    seed = seed or _load_seed()
    asset_data = (seed.get("assets") or {}).get(asset.upper())
    if not asset_data:
        return {"ok": False, "asset": asset, "error": "asset_not_found"}

    sentiment = compute_nlp_sentiment(asset, seed=seed)
    score = float(sentiment.get("composite_sentiment_score", 0.5))
    price = float(asset_data.get("price_usd", 0))
    mc = float(asset_data.get("market_cap_usd", 0))

    cfg = seed.get("price_correlation") or {}
    lookback = int(cfg.get("lookback_hours", 24))

    if score >= 0.6:
        alignment = "bullish_sentiment"
    elif score <= 0.4:
        alignment = "bearish_sentiment"
    else:
        alignment = "neutral_sentiment"

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "asset": asset.upper(),
        "price_usd": price,
        "market_cap_usd": mc,
        "sentiment_score": score,
        "sentiment_label": sentiment.get("composite_sentiment_label"),
        "alignment": alignment,
        "lookback_hours": lookback,
        "min_data_points": cfg.get("min_data_points", 96),
        "display": (
            f"Price: ${price:,.2f} | Sentiment: {score:.2f} ({alignment})"
        ),
        "timestamp": _utcnow(),
    }


def analyze_asset(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full per-asset event & sentiment analysis."""
    seed = seed or _load_seed()
    t0 = time.perf_counter()

    sentiment = compute_nlp_sentiment(asset, seed=seed)
    if not sentiment.get("ok"):
        return sentiment

    fear_greed = compute_fear_greed_index(asset, seed=seed)
    scoring = compute_asset_scoring_metrics(asset, seed=seed)
    proximity = compute_event_proximity(asset, seed=seed)
    correlation = compute_price_sentiment_correlation(asset, seed=seed)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": asset.upper(),
        "sentiment": sentiment,
        "fear_greed": fear_greed,
        "asset_scoring_metrics": scoring,
        "event_proximity": proximity,
        "price_sentiment_correlation": correlation,
        "monitoring_only": True,
        "alerts_only": True,
        "no_auto_execution": True,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_alerts(
    *,
    seed: dict[str, Any] | None = None,
    hours_ahead: int = 72,
) -> dict[str, Any]:
    """Generate alert-only notifications for imminent events."""
    seed = seed or _load_seed()
    now = datetime.now(UTC)
    cutoff = now + timedelta(hours=hours_ahead)
    alerts: list[dict[str, Any]] = []

    for ev in seed.get("events") or []:
        scheduled = _parse_dt(str(ev["scheduled_at_utc"]))
        if now <= scheduled <= cutoff:
            hours_until = round((scheduled - now).total_seconds() / 3600, 1)
            alerts.append({
                "alert_id": f"evt_{ev.get('event_id')}",
                "event_id": ev.get("event_id"),
                "asset": ev.get("asset"),
                "event_type": ev.get("event_type"),
                "title": ev.get("title"),
                "impact": ev.get("impact"),
                "hours_until": hours_until,
                "scheduled_at_utc": ev.get("scheduled_at_utc"),
                "alert_only": True,
                "no_execution_recommendation": True,
                "severity": "high" if ev.get("impact") == "high" and hours_until <= 24 else "medium",
                "display": (
                    f"[ALERT] {ev.get('asset')} {ev.get('event_type')}: {ev.get('title')} "
                    f"in {hours_until}h (monitoring only)"
                ),
            })

    alerts.sort(key=lambda a: a.get("hours_until", 9999))
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "alerts": alerts,
        "alert_count": len(alerts),
        "hours_ahead": hours_ahead,
        "alerts_only": True,
        "worth_studying_not_execution": True,
        "timestamp": _utcnow(),
    }


def build_archive_panel(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Archive metadata — ≥1 year retention."""
    seed = seed or _load_seed()
    archive = seed.get("archive") or {}
    retention = int(archive.get("retention_days", 365))

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "retention_days": retention,
        "retention_target_met": retention >= 365,
        "earliest_record": archive.get("earliest_record"),
        "records_count": archive.get("records_count"),
        "update_interval_minutes": archive.get("update_interval_minutes", 15),
        "archive_path": "data/event_sentiment_archive.jsonl",
        "display": (
            f"Archive: {retention} days | "
            f"Records: {archive.get('records_count', 0):,} | "
            f"From: {archive.get('earliest_record', 'n/a')}"
        ),
        "timestamp": _utcnow(),
    }


def build_event_sentiment_panel(
    asset: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()

    if asset:
        analyses = [analyze_asset(asset, seed=seed)]
    else:
        analyses = [analyze_asset(a, seed=seed) for a in (seed.get("assets") or {})]

    calendar = build_event_calendar(seed=seed)
    alerts = build_alerts(seed=seed)
    archive = build_archive_panel(seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "analyses": [a for a in analyses if a.get("ok")],
        "count": sum(1 for a in analyses if a.get("ok")),
        "event_calendar": calendar,
        "alerts": alerts,
        "archive": archive,
        "source_count": _enabled_source_count(seed),
        "source_coverage_minimum": seed.get("source_coverage_minimum", 5),
        "update_interval_minutes": seed.get("update_interval_minutes", 15),
        "nlp_accuracy_target_pct": seed.get("nlp_accuracy_target_pct", 80),
        "cancelled_v1": seed.get("cancelled_v1"),
        "monitoring_only": True,
        "alerts_only": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def enrich_arbitrage_opportunity(
    opportunity: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#429 integration — attach sentiment context + event proximity."""
    seed = seed or _load_seed()
    asset = str(opportunity.get("asset") or "BTC").upper()

    sentiment = compute_nlp_sentiment(asset, seed=seed)
    proximity = compute_event_proximity(asset, seed=seed)
    fear_greed = compute_fear_greed_index(asset, seed=seed)

    nearest = proximity.get("nearest_event")
    context_display = (
        f"Sentiment: {sentiment.get('composite_sentiment_label')} "
        f"({sentiment.get('composite_sentiment_score', 0):.2f}) | "
        f"Fear/Greed: {fear_greed.get('fear_greed_score')} | "
        f"Event proximity: {nearest.get('proximity') if nearest else 'none'}"
    )

    return {
        "feature_ref": _FEATURE_ID,
        "sentiment_context": {
            "composite_score": sentiment.get("composite_sentiment_score"),
            "composite_label": sentiment.get("composite_sentiment_label"),
            "source_count": sentiment.get("source_count"),
            "nlp_accuracy_pct": sentiment.get("nlp_accuracy_pct"),
        },
        "event_proximity": {
            "event_count": proximity.get("event_count"),
            "nearest_event": nearest,
            "alert_only": True,
        },
        "fear_greed": {
            "score": fear_greed.get("fear_greed_score"),
            "label": fear_greed.get("fear_greed_label"),
        },
        "monitoring_only": True,
        "no_auto_execution": True,
        "display": context_display,
        "timestamp": _utcnow(),
    }


def event_sentiment_monitor_status() -> dict[str, Any]:
    seed = _load_seed()
    nlp = seed.get("nlp") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "monitoring_only": True,
        "alerts_only": True,
        "no_auto_execution": True,
        "update_interval_minutes": seed.get("update_interval_minutes", 15),
        "source_count": _enabled_source_count(seed),
        "source_coverage_minimum": seed.get("source_coverage_minimum", 5),
        "nlp_accuracy_pct": nlp.get("accuracy_pct"),
        "nlp_accuracy_target_pct": seed.get("nlp_accuracy_target_pct", 80),
        "archive_retention_days": (seed.get("archive") or {}).get("retention_days", 365),
        "cancelled_v1": seed.get("cancelled_v1"),
        "outputs": [
            "composite_sentiment_score",
            "nlp_per_source",
            "fear_greed_index",
            "event_calendar",
            "event_proximity",
            "mc_volume_ratio",
            "total_on_chain_value",
            "price_sentiment_correlation",
            "alerts",
            "archive",
        ],
        "integrations": {
            "unified_arbitrage_engine_429": True,
            "community_pulse_287": "complementary",
            "asset_scoring": "mc_volume + on_chain_value",
        },
        "banned_language": seed.get("banned_language"),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "ledger merge"})
    checks.append({"id": "renamed_monitor", "passed": "Arbitrage" not in seed.get("legal_name", ""), "detail": seed.get("legal_name")})
    checks.append({"id": "alerts_only", "passed": seed.get("alerts_only") is True, "detail": "no execution"})
    checks.append({"id": "google_trends_cancelled", "passed": (seed.get("cancelled_v1") or {}).get("google_trends") is True, "detail": "v1"})
    checks.append({"id": "source_coverage_5", "passed": _enabled_source_count(seed) >= 5, "detail": f"sources={_enabled_source_count(seed)}"})
    checks.append({"id": "nlp_accuracy_80", "passed": float((seed.get("nlp") or {}).get("accuracy_pct", 0)) >= 80, "detail": "NLP"})
    checks.append({"id": "archive_1yr", "passed": int((seed.get("archive") or {}).get("retention_days", 0)) >= 365, "detail": "archive"})
    checks.append({"id": "update_15min", "passed": seed.get("update_interval_minutes") == 15, "detail": "refresh"})

    btc = analyze_asset("BTC", seed=seed)
    checks.append({"id": "nlp_sentiment", "passed": btc.get("sentiment", {}).get("composite_sentiment_score") is not None, "detail": "sentiment"})
    checks.append({"id": "fear_greed", "passed": btc.get("fear_greed", {}).get("fear_greed_score") is not None, "detail": "fear/greed"})
    checks.append({"id": "mc_volume", "passed": btc.get("asset_scoring_metrics", {}).get("mc_volume_ratio") is not None, "detail": "scoring"})
    checks.append({"id": "on_chain_value", "passed": btc.get("asset_scoring_metrics", {}).get("total_on_chain_value_usd") is not None, "detail": "on-chain"})
    checks.append({"id": "event_proximity", "passed": btc.get("event_proximity", {}).get("event_count", 0) >= 1, "detail": "events"})
    checks.append({"id": "price_correlation", "passed": btc.get("price_sentiment_correlation", {}).get("alignment") is not None, "detail": "correlation"})

    cal = build_event_calendar(seed=seed)
    checks.append({"id": "event_calendar_types", "passed": len(cal.get("event_types_supported") or []) >= 5, "detail": "types"})

    alerts = build_alerts(seed=seed)
    checks.append({"id": "alerts_only_flag", "passed": alerts.get("alerts_only") is True, "detail": f"count={alerts.get('alert_count')}"})

    enrich = enrich_arbitrage_opportunity({"asset": "BTC"}, seed=seed)
    checks.append({"id": "429_integration", "passed": "sentiment_context" in enrich and "event_proximity" in enrich, "detail": "429"})

    display = enrich.get("display", "").lower()
    banned_hit = any(term in display for term in _BANNED_TERMS)
    checks.append({"id": "no_banned_language", "passed": not banned_hit, "detail": "language"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
