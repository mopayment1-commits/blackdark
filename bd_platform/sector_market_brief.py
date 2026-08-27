"""
Sector Market Brief — Feature #678 (merged into Market Radar + Daily Brief).

Rule-based sector narrative — NOT ML, NOT buy/sell signals.
Describes market by sector segments: Gaming, AI, RWA, Solana Ecosystem.

Rejected: AI engine template, 100+ features, Sharpe ≥1.5, Win Rate ≥55%.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.SectorMarketBrief")

_FEATURE_ID = 678
_TITLE = "Sector Market Brief"
_LEGAL_NAME = "Sector Market Brief"
_STANDALONE = False
_MERGED_INTO = "Market Radar / Daily Brief"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/sector_market_brief_seed.json")
_METHODOLOGY_VERSION = "1.0"

_SECTOR_IDS = ("gaming", "ai_tokens", "rwa", "solana_ecosystem")

_DISCLAIMER = (
    "Sector Market Brief — rule-based sector narrative from documented data sources. "
    "Purely descriptive — no buy/sell signals, no ML predictions. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"sectors": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("sector market brief seed load failed: %s", exc)
        return {"sectors": {}}


def _evaluate_sector_narrative(sector_id: str, sector: dict[str, Any]) -> dict[str, Any]:
    """Rule-based narrative for one sector — descriptive only."""
    rules = sector.get("rules") or {}
    metrics = sector.get("metrics") or {}
    narrative_ar = None
    narrative_en = None
    signal = "neutral"

    if sector_id == "gaming":
        liq_change = float(metrics.get("dex_volume_change_pct", 0))
        threshold = float(rules.get("liquidity_increase_pct", 5))
        if liq_change >= threshold:
            narrative_ar = f"زيادة سيولة في Gaming (+{liq_change:.0f}%)"
            narrative_en = f"Gaming liquidity increase (+{liq_change:.0f}%)"
            signal = "strength"
    elif sector_id == "ai_tokens":
        index_change = float(metrics.get("sector_index_change_pct", 0))
        threshold = float(rules.get("weakness_decline_pct", -5))
        if index_change <= threshold:
            narrative_ar = f"ضعف في AI Tokens ({index_change:.0f}%)"
            narrative_en = f"AI Tokens weakness ({index_change:.0f}%)"
            signal = "weakness"
    elif sector_id == "rwa":
        inflows = float(metrics.get("institutional_inflows_usd", 0))
        threshold = float(rules.get("strength_inflow_usd", 10_000_000))
        if inflows >= threshold:
            narrative_ar = f"قوة في RWA (+${inflows / 1_000_000:.0f}M inflows)"
            narrative_en = f"RWA strength (+${inflows / 1_000_000:.0f}M inflows)"
            signal = "strength"
    elif sector_id == "solana_ecosystem":
        tx_spike = float(metrics.get("tx_count_spike_pct", 0))
        daa_spike = float(metrics.get("daa_spike_pct", 0))
        funding = float(metrics.get("funding_rate_pct", 0))
        tx_threshold = float(rules.get("abnormal_tx_spike_pct", 25))
        if tx_spike >= tx_threshold or daa_spike >= tx_threshold:
            narrative_ar = "نشاط غير طبيعي في Solana Ecosystem"
            narrative_en = "Abnormal activity in Solana Ecosystem"
            signal = "abnormal"
            metrics = {**metrics, "funding_rate_context_pct": funding}

    return {
        "sector_id": sector_id,
        "sector_name": sector.get("name"),
        "sector_name_ar": sector.get("name_ar"),
        "signal": signal,
        "narrative_ar": narrative_ar,
        "narrative_en": narrative_en,
        "active": narrative_ar is not None,
        "metrics": metrics,
        "data_sources": sector.get("data_sources") or [],
        "evidence_links": sector.get("evidence_links") or [],
        "rule_based_v1": True,
        "no_buy_sell_signal": True,
        "purely_descriptive": True,
    }


def build_sector_pulse_dashboard_678(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#678 — Sector Pulse: 4 cards (Gaming | AI | RWA | Solana) + trend + evidence."""
    seed = seed if seed and seed.get("sectors") else _load_seed()
    sectors_raw = seed.get("sectors") or {}
    cards: list[dict[str, Any]] = []
    narratives: list[str] = []

    for sector_id in _SECTOR_IDS:
        sector = sectors_raw.get(sector_id) or {}
        card = _evaluate_sector_narrative(sector_id, sector)
        card["trend"] = sector.get("trend") or {}
        card["display_backing"] = sector.get("display_backing")
        cards.append(card)
        if card.get("narrative_ar"):
            narratives.append(card["narrative_ar"])

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "merged_into": _MERGED_INTO,
        "standalone": _STANDALONE,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": "Market Radar AI Template (rejected)",
        "route": "/market/sector-pulse",
        "surface": "market_radar",
        "sector_cards": cards,
        "card_count": len(cards),
        "active_narratives": narratives,
        "daily_narrative_ar": "اليوم السوق فيه: " + " • ".join(narratives) if narratives else "لا إشارات قطاعية نشطة",
        "daily_narrative_en": "Today the market shows: " + " | ".join(
            c["narrative_en"] for c in cards if c.get("narrative_en")
        ) if narratives else "No active sector signals",
        "ml_template_rejected": True,
        "no_buy_sell_signals": True,
        "rule_based_v1": True,
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def build_sector_metrics_577(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#678 → #577 — sector metrics for metrics library."""
    seed = seed if seed and seed.get("sectors") else _load_seed()
    sectors = seed.get("sectors") or {}
    gaming = sectors.get("gaming", {}).get("metrics") or {}
    ai = sectors.get("ai_tokens", {}).get("metrics") or {}
    rwa = sectors.get("rwa", {}).get("metrics") or {}
    sol = sectors.get("solana_ecosystem", {}).get("metrics") or {}

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "epic_feature_id": 577,
        "metrics": {
            "gaming_liquidity": {
                "value": gaming.get("dex_volume_usd"),
                "change_pct": gaming.get("dex_volume_change_pct"),
                "unit": "USD",
                "source": "dex_volume + on_chain_transfers",
            },
            "ai_token_index": {
                "value": ai.get("sector_index"),
                "change_pct": ai.get("sector_index_change_pct"),
                "unit": "index",
                "source": "sector_index_decline",
            },
            "rwa_inflows": {
                "value": rwa.get("institutional_inflows_usd"),
                "unit": "USD",
                "source": "stablecoin + institutional_flow",
            },
            "solana_ecosystem_activity": {
                "tx_count_spike_pct": sol.get("tx_count_spike_pct"),
                "daa_spike_pct": sol.get("daa_spike_pct"),
                "funding_rate_pct": sol.get("funding_rate_pct"),
                "source": "tx_count + daa + funding_rate",
            },
        },
        "timestamp": _utcnow(),
    }


def build_sector_pulse_daily_brief_hook_474(*, seed: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """#678 → #474 Daily Brief — sector pulse in daily narrative."""
    pulse = build_sector_pulse_dashboard_678(seed=seed)
    if not pulse.get("ok") or not pulse.get("active_narratives"):
        return None
    sector_data = (seed if seed and seed.get("sectors") else _load_seed()).get("sectors") or {}
    gaming = (sector_data.get("gaming") or {}).get("metrics", {})
    ai = (sector_data.get("ai_tokens") or {}).get("metrics", {})
    rwa = (sector_data.get("rwa") or {}).get("metrics", {})
    mention_ar = (
        f"اليوم: Gaming +{gaming.get('dex_volume_change_pct', 0):.0f}% سيولة، "
        f"AI {ai.get('sector_index_change_pct', 0):.0f}%، "
        f"RWA +${float(rwa.get('institutional_inflows_usd', 0)) / 1_000_000:.0f}M inflows"
    )
    return {
        "integration_474": True,
        "integration_678": True,
        "mention": pulse.get("daily_narrative_ar"),
        "mention_en": pulse.get("daily_narrative_en"),
        "mention_ar": mention_ar,
        "evidence_link": "/api/platform/intelligence-ledger/market-radar/sector-pulse",
        "sector_count": len(pulse.get("active_narratives") or []),
    }


def apply_sector_ranking_boost_429(
    opportunities: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """#678 → #429 — rank opportunities by active sector."""
    sector_seed = seed if seed and seed.get("sectors") else _load_seed()
    pulse = build_sector_pulse_dashboard_678(seed=sector_seed)
    active_sectors = {
        c["sector_id"] for c in (pulse.get("sector_cards") or []) if c.get("active")
    }
    if not active_sectors:
        return opportunities

    sector_tags = sector_seed.get("opportunity_sector_tags") or {}
    boosted: list[dict[str, Any]] = []
    for opp in opportunities:
        opp_copy = dict(opp)
        opp_id = str(opp.get("opportunity_id") or opp.get("loop_id") or "")
        opp_sector = sector_tags.get(opp_id)
        if opp_sector and opp_sector in active_sectors:
            boost = float(sector_seed.get("sector_ranking_boost_pct", 5))
            base_edge = float(opp_copy.get("net_edge_usdt", 0))
            opp_copy["sector_pulse_boost_678"] = boost
            opp_copy["active_sector"] = opp_sector
            opp_copy["net_edge_usdt"] = round(base_edge * (1 + boost / 100), 2)
        boosted.append(opp_copy)

    boosted.sort(key=lambda o: float(o.get("net_edge_usdt", 0)), reverse=True)
    return boosted


def build_market_radar_sector_pulse_widget_678(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#678 → Market Radar widget."""
    pulse = build_sector_pulse_dashboard_678(seed=seed)
    return {
        "ok": pulse.get("ok", False),
        "feature_ref": _FEATURE_ID,
        "surface": "market_radar",
        "widget": "sector_pulse",
        "widget_label": "Sector Market Brief",
        "dashboard": pulse,
        "display": pulse.get("daily_narrative_en"),
        "timestamp": _utcnow(),
    }


def sector_market_brief_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "ml_template_rejected": True,
        "rejected_claims": [
            "AI engine with 100+ features",
            "Sharpe ≥1.5",
            "Win Rate ≥55%",
            "Buy/sell signals",
        ],
        "rule_based_v1": True,
        "sector_count": len(_SECTOR_IDS),
        "sectors_v1": list(_SECTOR_IDS),
        "integrations": {
            "market_radar": True,
            "daily_brief_474": True,
            "onchain_metrics_library_577": True,
            "unified_arbitrage_429": True,
        },
        "route": "/market/sector-pulse",
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": _STANDALONE is False, "detail": "merged"})
    checks.append({"id": "ml_rejected", "passed": seed.get("ml_template_rejected", True) is True, "detail": "no ML"})
    checks.append({"id": "no_buy_sell", "passed": seed.get("no_buy_sell_signals", True) is True, "detail": "descriptive"})

    pulse = build_sector_pulse_dashboard_678(seed=seed)
    checks.append({"id": "four_sector_cards", "passed": pulse.get("card_count") == 4, "detail": "678"})
    checks.append({"id": "active_narratives", "passed": len(pulse.get("active_narratives") or []) >= 1, "detail": "narrative"})
    checks.append({"id": "purely_descriptive", "passed": all(c.get("no_buy_sell_signal") for c in pulse.get("sector_cards") or []), "detail": "no trade"})

    metrics = build_sector_metrics_577(seed=seed)
    checks.append({"id": "sector_metrics_577", "passed": "gaming_liquidity" in (metrics.get("metrics") or {}), "detail": "577"})

    brief = build_sector_pulse_daily_brief_hook_474(seed=seed)
    checks.append({"id": "daily_brief_474", "passed": brief is not None and brief.get("integration_678") is True, "detail": "474"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
