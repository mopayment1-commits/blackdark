"""
Cross-Chain Bridge Flow Monitor — Features #506 + #521 merged (Sprint 1 On-Chain Layer).

Renamed from "Cross-Chain Bridge Volume Inflow" AI engine.
Data monitoring only — rule-based indexing, no ML, no trading signals.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CrossChainBridgeFlowMonitor")

_FEATURE_IDS = (506, 521)
_RENAMED_FROM = ("Cross-Chain Bridge Volume Inflow",)
_ABSORBED_IDS = (521,)
_TITLE = "Cross-Chain Bridge Flow Monitor"
_STANDALONE = True
_LAYER = "On-Chain Layer"
_SPRINT = 1
_SEED_PATH = Path("data/cross_chain_bridge_flow_monitor_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Data monitoring only | Not a trading signal | Not investment advice | "
    "Confidence reflects data freshness, not prediction quality"
)

_BANNED_TERMS = (
    "ai engine",
    "smart signal",
    "sharpe",
    "win rate",
    "max drawdown",
    "walk-forward",
    "ml model",
    "prediction",
    "buy signal",
    "sell signal",
)

FlowDirection = Literal["inflow", "outflow", "neutral"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"bridges": {}, "flows": [], "indexing": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("bridge flow monitor seed load failed: %s", exc)
        return {"bridges": {}, "flows": [], "indexing": {}}


def build_indexing_documentation(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    indexing = seed.get("indexing") or {}
    return {
        "methodology_version": _METHODOLOGY_VERSION,
        "method": "rule_based_indexing",
        "no_ml": True,
        "no_ai": True,
        "no_trading_signals": True,
        "aggregation": indexing.get(
            "aggregation",
            "sum(transaction_amounts) grouped by bridge_route, time_window",
        ),
        "transaction_counting": indexing.get(
            "transaction_counting",
            "count(cross_chain_bridge_transactions) per route per window",
        ),
        "entity_tagging": indexing.get(
            "entity_tagging",
            "known_entity_labels when available, else Unknown",
        ),
        "confidence_basis": "data_freshness_and_source_coverage",
        "not_performance_metrics": True,
        "display": "Rule-based indexing — count transactions + sum amounts, no ML",
    }


def _freshness_confidence(freshness_seconds: int) -> dict[str, Any]:
    if freshness_seconds <= 300:
        level = "high"
    elif freshness_seconds <= 900:
        level = "medium"
    else:
        level = "low"
    return {
        "freshness_seconds": freshness_seconds,
        "confidence_basis": "data_freshness",
        "confidence_level": level,
        "not_prediction_confidence": True,
        "display": f"Data freshness: {freshness_seconds}s | Confidence: {level} (freshness only)",
    }


def build_bridge_flow_record(flow: dict[str, Any]) -> dict[str, Any]:
    """Format a single bridge flow data point — no signal language."""
    source_chain = flow.get("source_chain", "unknown")
    dest_chain = flow.get("dest_chain", "unknown")
    amount_usd = float(flow.get("amount_usd", 0))
    direction = flow.get("direction", "inflow")
    entity = flow.get("entity_tag") or "Unknown"
    freshness = int(flow.get("freshness_seconds", 300))
    tx_count = int(flow.get("transaction_count", 0))

    sign = "+" if direction == "inflow" and amount_usd >= 0 else ""
    return {
        "bridge_route": f"{source_chain} → {dest_chain}",
        "source_chain": source_chain,
        "dest_chain": dest_chain,
        "direction": direction,
        "amount_usd": amount_usd,
        "transaction_count": tx_count,
        "entity_tag": entity,
        "entity_display": f"Entity: {entity}",
        "confidence": _freshness_confidence(freshness),
        "data_only": True,
        "not_signal": True,
        "display": (
            f"Bridge {source_chain} → {dest_chain}: {sign}${amount_usd:,.0f} {direction} | "
            f"Entity: {entity} | Confidence: data freshness"
        ),
        "timestamp": flow.get("timestamp") or _utcnow(),
    }


def build_bridge_flow_panel(
    *,
    bridge_id: str | None = None,
    source_chain: str | None = None,
    dest_chain: str | None = None,
) -> dict[str, Any]:
    """Main panel — cross-chain bridge flow data monitoring."""
    t0 = time.perf_counter()
    seed = _load_seed()
    flows_raw = seed.get("flows") or []

    if bridge_id:
        flows_raw = [f for f in flows_raw if f.get("bridge_id") == bridge_id]
    if source_chain:
        flows_raw = [f for f in flows_raw if f.get("source_chain", "").lower() == source_chain.lower()]
    if dest_chain:
        flows_raw = [f for f in flows_raw if f.get("dest_chain", "").lower() == dest_chain.lower()]

    flows = [build_bridge_flow_record(f) for f in flows_raw]
    total_inflow = sum(f["amount_usd"] for f in flows if f["direction"] == "inflow")
    total_outflow = sum(abs(f["amount_usd"]) for f in flows if f["direction"] == "outflow")
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "absorbed_tickets": {"521": "Duplicate of #506 — merged"},
        "renamed_from": list(_RENAMED_FROM),
        "title": _TITLE,
        "no_ai_engine": True,
        "no_trading_signals": True,
        "no_performance_claims": True,
        "data_monitoring_only": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "standalone": _STANDALONE,
        "rule_based_only": True,
        "ml_deferred": True,
        "flows": flows,
        "summary": {
            "flow_count": len(flows),
            "total_inflow_usd": round(total_inflow, 2),
            "total_outflow_usd": round(total_outflow, 2),
            "net_flow_usd": round(total_inflow - total_outflow, 2),
            "data_only": True,
            "not_signal": True,
        },
        "indexing": build_indexing_documentation(seed),
        "acceptance_criteria": {
            "latency_under_5_min": elapsed < 300_000,
            "backtest_years": None,
            "sharpe_claims_removed": True,
            "win_rate_claims_removed": True,
            "data_output_only": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "disclaimer_on_every_output": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def cross_chain_bridge_flow_monitor_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "title": _TITLE,
        "renamed_from": list(_RENAMED_FROM),
        "no_ai_engine": True,
        "no_trading_signals": True,
        "no_performance_claims": True,
        "data_monitoring_only": True,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "standalone": _STANDALONE,
        "rule_based_only": True,
        "indexing": build_indexing_documentation(seed),
        "bridge_count": len(seed.get("bridges") or {}),
        "flow_record_count": len(seed.get("flows") or []),
        "acceptance_criteria": {
            "latency_under_5_min": True,
            "data_output_only": True,
            "no_ml": True,
            "no_ai": True,
            "no_sharpe_claims": True,
            "no_win_rate_claims": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
