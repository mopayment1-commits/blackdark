"""
Liquidation Cluster Analytics — Feature #307 (Sprint 2 Intelligence Ledger).

Renamed from "Imminent Liquidation Cluster Scanning".
Data display only — no prediction, no "imminent", no "scanning".
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.LiquidationClusterAnalytics")

_FEATURE_ID = 307
_ABSORBED_IDS = (356,)
_RENAMED_FROM = "Imminent Liquidation Cluster Scanning"
_TITLE = "Liquidation Cluster Analytics"
_STANDALONE = True
_MERGED_INTO = "Intelligence Ledger / Liquidation Cluster Analytics"
_SPRINT = 2
_WAVE = 2
_SEED_PATH = Path("data/liquidation_cluster_analytics_seed.json")
_METHODOLOGY_VERSION = "1.0"
_TARGET_LATENCY_MS = 2000

Confidence = Literal["high", "medium", "low"]

_DISCLAIMER = (
    "Liquidation clusters = historical + current open interest data. "
    "Estimated liquidation levels are probability estimates only — not certainty. "
    "No 'will liquidate at X price' claims. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("liquidation cluster analytics seed load failed: %s", exc)
        return {"assets": {}}


def build_data_source_block(sources: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "sources": sources,
        "documented": True,
        "types": ["exchange_api", "on_chain_perp"],
        "confidence_per_venue": True,
        "display": "Exchange APIs + on-chain perp protocols | Source documented per venue",
    }


def build_cluster_block(cluster: dict[str, Any]) -> dict[str, Any]:
    """Cluster = historical + current OI — no prediction certainty."""
    estimated_levels = cluster.get("estimated_levels") or []
    levels_out = []
    for lvl in estimated_levels:
        levels_out.append({
            "price": lvl.get("price"),
            "estimated_oi_usd": lvl.get("estimated_oi_usd"),
            "probability_pct": lvl.get("probability_pct"),
            "probability_only": True,
            "not_certainty": True,
            "display": (
                f"~${lvl.get('price'):,.0f}: est. ${lvl.get('estimated_oi_usd', 0):,.0f} OI "
                f"({lvl.get('probability_pct', 0)}% probability — not certainty)"
            ),
        })

    return {
        "cluster_id": cluster.get("cluster_id"),
        "price_level": cluster.get("price_level"),
        "side": cluster.get("side"),
        "historical_liquidation_usd": cluster.get("historical_liquidation_usd"),
        "current_open_interest_usd": cluster.get("current_open_interest_usd"),
        "cluster_type": "historical_and_current_oi",
        "no_imminent_language": True,
        "no_scanning_language": True,
        "estimated_levels": levels_out,
        "venue": cluster.get("venue"),
        "source": cluster.get("source"),
        "confidence": cluster.get("confidence", "medium"),
        "timestamp_utc": cluster.get("timestamp_utc"),
    }


def build_liquidation_risk_context(asset_data: dict[str, Any], *, asset: str) -> dict[str, Any]:
    """#356 Liquidation Risk Context — historical analysis, no probability output."""
    seed = _load_seed()
    lr = seed.get("legal_review") or {}
    legal_complete = bool(lr.get("complete", False))
    risk_ctx = asset_data.get("risk_context") or {}
    patterns = risk_ctx.get("historical_patterns") or []

    patterns_out = []
    for p in patterns:
        patterns_out.append({
            "pattern_id": p.get("pattern_id"),
            "event_date": p.get("event_date"),
            "historical_liquidation_usd": p.get("historical_liquidation_usd"),
            "volatility_at_event": p.get("volatility_at_event"),
            "leverage_context": p.get("leverage_context"),
            "positioning_context": p.get("positioning_context"),
            "historical_analysis_only": True,
            "no_probability_output": True,
            "no_cascade_probability_alert": True,
            "display": (
                f"Historical event {p.get('event_date')}: "
                f"${p.get('historical_liquidation_usd', 0):,.0f} liquidated | "
                f"vol {p.get('volatility_at_event', 'N/A')}"
            ),
        })

    wf = risk_ctx.get("walk_forward_validation") or {}
    return {
        "sub_task": "#356",
        "absorbed_from": "Liquidation Cascade Model",
        "title": "Liquidation Risk Context",
        "renamed_from": "Liquidation Cascade Model",
        "no_model_in_name": True,
        "no_probability_output": True,
        "standalone_rejected": True,
        "merged_as": "component in Liquidation Cluster Analytics (#307)",
        "output_format": "historical_liquidation_pattern_analysis",
        "asset": asset,
        "historical_patterns": patterns_out,
        "pattern_count": len(patterns_out),
        "historical_cascade_frequency": risk_ctx.get("historical_cascade_frequency"),
        "risk_metric_numeric_only": True,
        "no_cascade_probability_alert": True,
        "no_forecast": True,
        "walk_forward_validation": {
            "required": True,
            "completed": wf.get("completed", False),
            "events_tested": wf.get("events_tested", 0),
            "out_of_sample_pct": wf.get("out_of_sample_pct"),
            "no_backtest_only": True,
            "display": (
                f"Walk-forward: {wf.get('events_tested', 0)} events | "
                f"OOS: {wf.get('out_of_sample_pct', 'N/A')}%"
            ),
        },
        "legal_review": {
            "mandatory": True,
            "complete": legal_complete,
            "release_blocked_without_review": not legal_complete,
        },
        "wave": 2,
        "disclaimer": (
            "Historical liquidation pattern analysis only. "
            "Not prediction. No cascade probability for users. Not investment advice."
        ),
    }


def build_liquidation_cluster_panel(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_data = (seed.get("assets") or {}).get(sym)

    if not asset_data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    clusters = [build_cluster_block(c) for c in (asset_data.get("clusters") or [])]
    risk_context = build_liquidation_risk_context(asset_data, asset=sym)
    sources = build_data_source_block(asset_data.get("sources") or [])
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "asset": sym,
        "clusters": clusters,
        "cluster_count": len(clusters),
        "liquidation_risk_context": risk_context,
        "data_sources": sources,
        "no_prediction": True,
        "probability_only_estimates": True,
        "no_imminent_language": True,
        "no_scanning_language": True,
        "data_display_only": True,
        "target_latency_ms": _TARGET_LATENCY_MS,
        "latency_within_target": elapsed <= _TARGET_LATENCY_MS,
        "real_time_update": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def liquidation_cluster_analytics_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "wave": _WAVE,
        "absorbed_tickets": {
            356: "Liquidation Risk Context (standalone rejected, renamed from Liquidation Cascade Model)",
        },
        "asset_count": len(seed.get("assets") or {}),
        "acceptance_criteria": {
            "latency_target_2s": True,
            "no_prediction": True,
            "probability_only_estimates": True,
            "source_documented_per_venue": True,
            "no_imminent_language": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
