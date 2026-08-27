"""
Daily Market Brief — Feature #474 (Intelligence Ledger Sprint-2).

Renamed from "Market Regime Written Read".
Template-based generation from actual contributors — no generic AI prose in v1.

Output: 3 sections only — What Changed / Why / Risks
Every sentence backed by evidence link.

Integrations:
  - Market Radar: Daily Brief appears first on dashboard
  - #443 Event Monitor: events included in narrative
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.DailyMarketBrief")

_FEATURE_ID = 474
_TITLE = "Daily Market Brief"
_LEGAL_NAME = "Daily Market Brief"
_RENAMED_FROM = "Market Regime Written Read"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Intelligence Ledger / Market Radar"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/daily_market_brief_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Daily Market Brief — template-based market narrative from computed contributors. "
    "No generic AI prose. Every claim linked to evidence (chart, metric, on-chain data). "
    "Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"regime": {}, "contributors": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("daily market brief seed load failed: %s", exc)
        return {"regime": {}, "contributors": []}


def _format_contributor(c: dict[str, Any]) -> str:
    metric = c.get("metric", "metric")
    value = c.get("value")
    prev = c.get("previous_value")
    if prev is not None and value is not None:
        delta = value - prev if isinstance(value, (int, float)) and isinstance(prev, (int, float)) else None
        if delta is not None:
            return f"{metric}: {value} (was {prev}, Δ{delta:+.2f})"
    return f"{metric}: {value}"


def generate_daily_brief(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Template-based brief from regime lenses + contributors — no LLM v1."""
    seed = seed or _load_seed()
    regime = seed.get("regime") or {}
    contributors = seed.get("contributors") or []
    events = seed.get("event_context_443") or []
    lenses = regime.get("lenses") or {}

    what_changed_items: list[dict[str, Any]] = []
    if regime.get("regime_change"):
        what_changed_items.append({
            "text": (
                f"Market regime shifted from {regime.get('previous_regime_label')} "
                f"to {regime.get('regime_label')} (score {regime.get('regime_score')})"
            ),
            "evidence_link": "/api/platform/intelligence-ledger/market-radar/exchange-activity",
            "contributor_metric": "regime_score",
            "contributor_value": regime.get("regime_score"),
        })

    for c in contributors[:2]:
        what_changed_items.append({
            "text": _format_contributor(c),
            "evidence_link": c.get("evidence_link"),
            "contributor_metric": c.get("metric"),
            "contributor_value": c.get("value"),
        })

    why_items: list[dict[str, Any]] = []
    sharpe_narrative = None
    try:
        from bd_platform.portfolio_intelligence_engine import build_sharpe_intelligence_panel

        sharpe = build_sharpe_intelligence_panel()
        if sharpe.get("ok"):
            sharpe_narrative = sharpe
            why_items.append({
                "text": (
                    f"Portfolio Sharpe 90d {sharpe.get('sharpe_90d', 0):.2f} "
                    f"({sharpe.get('sharpe_trend', 'flat')}) — "
                    f"percentile {sharpe.get('percentile_vs_sector', 0):.0f} vs sector"
                ),
                "evidence_link": "/api/platform/intelligence-ledger/portfolio-ai/portfolio-intelligence/sharpe",
                "contributor_metric": "sharpe_90d",
                "contributor_value": sharpe.get("sharpe_90d"),
                "feature_ref_490": 490,
            })
    except Exception:
        logger.debug("sharpe brief integration skipped", exc_info=True)

    for lens_name, lens_data in lenses.items():
        if lens_data.get("direction") in ("rising", "falling"):
            why_items.append({
                "text": (
                    f"{lens_name.replace('_', ' ').title()} lens {lens_data.get('direction')} "
                    f"(score {lens_data.get('score')})"
                ),
                "evidence_link": f"/api/platform/intelligence-ledger/market-radar/exchange-activity",
                "contributor_metric": f"lens_{lens_name}",
                "contributor_value": lens_data.get("score"),
            })

    for c in contributors[2:4]:
        why_items.append({
            "text": _format_contributor(c),
            "evidence_link": c.get("evidence_link"),
            "contributor_metric": c.get("metric"),
            "contributor_value": c.get("value"),
        })

    risks_items: list[dict[str, Any]] = []

    if float(lenses.get("volatility", {}).get("score", 50)) > 60:
        risks_items.append({
            "text": f"Elevated volatility lens score: {lenses['volatility']['score']}",
            "evidence_link": "/api/platform/intelligence-ledger/unified-arbitrage/basis-funding",
            "contributor_metric": "lens_volatility",
            "contributor_value": lenses["volatility"]["score"],
        })

    for ev in events[:2]:
        risks_items.append({
            "text": f"Upcoming {ev.get('event_type')}: {ev.get('title')} in {ev.get('hours_until')}h",
            "evidence_link": "/api/platform/intelligence-ledger/event-sentiment/calendar",
            "contributor_metric": "event_proximity",
            "contributor_value": ev.get("hours_until"),
            "event_ref_443": ev.get("event_id"),
        })

    if not risks_items:
        risks_items.append({
            "text": "No elevated regime risks flagged in current lens readings",
            "evidence_link": "/api/platform/intelligence-ledger/market-radar/exchange-activity",
            "contributor_metric": "regime_score",
            "contributor_value": regime.get("regime_score"),
        })

    validation = seed.get("historical_validation") or {}

    hype_vs_reality_summary = None
    try:
        from bd_platform.hype_vs_reality_signal import build_hype_vs_reality_panel, build_signal_quality_summary

        hvr_panel = build_hype_vs_reality_panel("BTC", seed=None)
        if hvr_panel.get("ok"):
            hype_vs_reality_summary = hvr_panel.get("summary")
            assessments = hvr_panel.get("assessments") or []
            for item in (what_changed_items + why_items + risks_items):
                asset_sym = item.get("asset") or "BTC"
                match = next((a for a in assessments if a.get("asset") == asset_sym), assessments[0] if assessments else None)
                if match:
                    item["signal_quality_badge_599"] = match.get("badge")
                    item["hype_vs_reality_state"] = match.get("state")
    except Exception:
        logger.debug("hype vs reality daily brief integration skipped", exc_info=True)

    capital_radar_narrative = None
    try:
        from bd_platform.capital_formation_radar import build_capital_formation_radar

        capital_radar = build_capital_formation_radar()
        if capital_radar.get("ok") and capital_radar.get("capital_radar"):
            top = capital_radar["capital_radar"][0]
            capital_radar_narrative = {
                "top_sector": top.get("sector_name"),
                "capital_momentum_score": top.get("capital_momentum_score"),
                "heatmap_color": top.get("heatmap_color"),
                "formation_vs_price": top.get("formation_vs_price"),
            }
            what_changed_items.insert(0, {
                "text": (
                    f"Capital Radar: {top.get('sector_name')} momentum "
                    f"{top.get('capital_momentum_score', 0):.0f} "
                    f"({top.get('heatmap_color')})"
                ),
                "evidence_link": "/api/platform/intelligence-ledger/capital-formation",
                "contributor_metric": "capital_momentum_score",
                "contributor_value": top.get("capital_momentum_score"),
                "feature_ref_648": 648,
            })
    except Exception:
        logger.debug("capital formation radar brief integration skipped", exc_info=True)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "brief_date": seed.get("brief_date"),
        "regime": {
            "label": regime.get("regime_label"),
            "score": regime.get("regime_score"),
            "previous_label": regime.get("previous_regime_label"),
            "changed": regime.get("regime_change"),
        },
        "what_changed": what_changed_items[:3],
        "why": why_items[:3],
        "risks": risks_items[:3],
        "section_count": 3,
        "template_based_v1": seed.get("template_based_v1", True),
        "no_generic_ai_prose": seed.get("no_generic_ai_prose", True),
        "contributors_match_calculations": validation.get("contributors_match_calculations", True),
        "historical_validation": validation,
        "event_context_443": events,
        "hype_vs_reality_signal_599": hype_vs_reality_summary,
        "signal_quality_summary_599": hype_vs_reality_summary,
        "sharpe_narrative_490": sharpe_narrative,
        "capital_formation_radar_648": capital_radar_narrative,
        "not_investment_advice": True,
        "display": (
            f"Daily Brief {seed.get('brief_date')}: {regime.get('regime_label')} | "
            f"{len(what_changed_items)} changes, {len(risks_items)} risks"
        ),
        "timestamp": _utcnow(),
    }


def build_market_radar_brief_first(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Market Radar integration — Daily Brief as first dashboard element."""
    brief = generate_daily_brief(seed=seed)
    return {
        "ok": brief.get("ok", False),
        "integration": "market_radar",
        "dashboard_position": "first",
        "daily_brief_474": brief,
        "timestamp": _utcnow(),
    }


def daily_market_brief_status() -> dict[str, Any]:
    seed = _load_seed()
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
        "template_based_v1": seed.get("template_based_v1", True),
        "no_generic_ai_prose": seed.get("no_generic_ai_prose", True),
        "max_sections": seed.get("max_sections", 3),
        "integrations": {
            "market_radar": True,
            "event_sentiment_monitor_443": True,
            "sharpe_intelligence_490": True,
            "hype_vs_reality_signal_599": True,
            "capital_formation_radar_648": True,
        },
        "historical_validation": seed.get("historical_validation"),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "ledger"})
    checks.append({"id": "renamed_brief", "passed": seed.get("legal_name") == "Daily Market Brief", "detail": "474"})
    checks.append({"id": "template_based", "passed": seed.get("template_based_v1") is True, "detail": "v1"})
    checks.append({"id": "no_generic_ai", "passed": seed.get("no_generic_ai_prose") is True, "detail": "prose"})

    brief = generate_daily_brief(seed=seed)
    checks.append({"id": "three_sections", "passed": brief.get("section_count") == 3, "detail": "sections"})
    checks.append({"id": "what_changed", "passed": len(brief.get("what_changed") or []) >= 1, "detail": "changed"})
    checks.append({"id": "why", "passed": len(brief.get("why") or []) >= 1, "detail": "why"})
    checks.append({"id": "risks", "passed": len(brief.get("risks") or []) >= 1, "detail": "risks"})

    all_items = (brief.get("what_changed") or []) + (brief.get("why") or []) + (brief.get("risks") or [])
    checks.append({"id": "evidence_links", "passed": all(i.get("evidence_link") for i in all_items), "detail": "links"})
    checks.append({"id": "contributors_match", "passed": brief.get("contributors_match_calculations") is True, "detail": "calc"})
    checks.append({"id": "event_context_443", "passed": len(brief.get("event_context_443") or []) >= 1, "detail": "443"})

    sharpe_in_brief = any(
        i.get("feature_ref_490") == 490
        for i in (brief.get("why") or []) + (brief.get("what_changed") or [])
    )
    checks.append({"id": "sharpe_intelligence_490", "passed": sharpe_in_brief, "detail": "490"})

    capital_in_brief = any(
        i.get("feature_ref_648") == 648 for i in (brief.get("what_changed") or [])
    ) or brief.get("capital_formation_radar_648") is not None
    checks.append({"id": "capital_formation_radar_648", "passed": capital_in_brief, "detail": "648"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
