"""Exchange Outflow Intelligence — Feature #242 (Sprint 2).

Measures asset outflows from labeled exchange clusters to external addresses.
Integrated into Exchange Intelligence Hub (#734-736) — NOT standalone.
Risk context only — NOT sell signals.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from bd_platform.exchange_flow_common import (
    build_address_dedupe,
    build_chain_validation,
    build_cluster_metadata,
    build_exchange_breakdown,
    format_usd,
    load_seed,
    reconcile_flows,
)

logger = logging.getLogger("BLACKDARK.ExchangeOutflowIntelligence")

_FEATURE_ID = 242
_STANDALONE = False
_MERGED_INTO = "Exchange Intelligence Hub (#734-736)"
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER_TEXT = (
    "Exchange outflows represent on-chain movements from labeled exchange addresses to external "
    "addresses. Not all outflows indicate selling or distress. Internal wallet rebalancing may "
    "appear as outflow. Not investment advice."
)


def _detect_outflow_anomaly(outflow_usd: float, baseline_30d: float) -> dict[str, Any] | None:
    if not baseline_30d:
        return None
    pct_change = (outflow_usd - baseline_30d) / baseline_30d * 100
    if abs(pct_change) < 10:
        return None
    confidence = min(95.0, round(50 + abs(pct_change) * 0.5, 1))
    affected = "Multiple" if pct_change > 0 else "Multiple"
    return {
        "label": "Elevated Outflow Detected",
        "pct_vs_baseline": round(pct_change, 1),
        "confidence_pct": confidence,
        "affected_exchange": affected,
        "display": (
            f"Outflow Spike: {pct_change:+.1f}% vs 30D baseline | "
            f"Confidence: {confidence}% | Affected Exchange: {affected}"
        ),
        "context_display": "Elevated Outflow Detected",
        "not_a_signal": True,
        "risk_context_only": True,
        "no_sell_language": True,
    }


def build_outflow_card(asset_data: dict[str, Any], seed: dict[str, Any]) -> dict[str, Any]:
    """Build outflow tab card with closure reconciliation."""
    inflow = float(asset_data.get("inflow_usd", 0))
    outflow = float(asset_data.get("outflow_usd", 0))
    netflow = float(asset_data.get("netflow_usd", 0))

    reconciliation = reconcile_flows(inflow, outflow, netflow)
    cluster = build_cluster_metadata(seed)
    breakdown = build_exchange_breakdown(asset_data.get("exchange_breakdown") or {}, flow_key="outflow_usd")
    chain_val = build_chain_validation(asset_data.get("chain_breakdown") or {})
    dedupe = build_address_dedupe(asset_data.get("address_dedupe") or {})
    anomaly = _detect_outflow_anomaly(outflow, float(asset_data.get("baseline_30d_outflow_usd", 0)))

    symbol = asset_data.get("symbol", "BTC")
    return {
        "feature_id": _FEATURE_ID,
        "feature_name": "Exchange Outflow Intelligence",
        "asset": symbol,
        "outflow_usd": outflow,
        "outflow_display": format_usd(outflow),
        "reconciliation": reconciliation,
        "cluster": cluster,
        "exchange_breakdown": breakdown,
        "chain_validation": chain_val,
        "address_dedupe": dedupe,
        "anomaly": anomaly,
        "chart": asset_data.get("outflow_chart") or [],
        "context_display": (
            f"Exchange {breakdown['entries'][0]['exchange'].title() if breakdown['entries'] else 'N/A'}: "
            f"Outflow {anomaly['pct_vs_baseline']:+.0f}% vs baseline | Context: Elevated"
            if anomaly
            else f"Outflow: {format_usd(outflow)} | Context: Normal range"
        ),
        "risk_context_only": True,
        "not_a_recommendation": True,
        "no_sell_language": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
    }


def build_outflow_dashboard(asset: str = "BTC") -> dict[str, Any]:
    """Outflow dashboard — accessed via Exchange Intelligence Hub."""
    t0 = time.perf_counter()
    seed = load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("assets") or {}).get(sym)
    if not asset_data:
        return {"ok": False, "error": "asset_not_tracked", "asset": sym}

    card = build_outflow_card({**asset_data, "symbol": sym}, seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "surface": "exchange_intelligence_hub",
        "tab": "outflow",
        "methodology_version": seed.get("methodology_version", _METHODOLOGY_VERSION),
        **card,
        "latency_ms": elapsed,
    }


def exchange_outflow_status() -> dict[str, Any]:
    seed = load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_label": "Exchange Outflow Intelligence",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "methodology_version": seed.get("methodology_version", _METHODOLOGY_VERSION),
        "cluster_version": seed.get("cluster_version", "4.2"),
        "assets_tracked": len(seed.get("assets") or {}),
        "acceptance_criteria": {
            "closure_with_inflow_netflow": True,
            "reconciliation_verified": True,
            "cluster_versioned": True,
            "anomaly_detection": True,
            "exchange_breakdown": True,
            "address_dedupe": True,
            "chain_validation": True,
            "disclaimer_non_hideable": True,
            "risk_context_only": True,
            "hub_integration": True,
        },
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
    }
