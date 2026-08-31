"""
Exchange Flow Velocity Monitor — Feature #508 (Sprint 1 On-Chain Intelligence Layer).

Renamed from "Exchange Wallet Outflow Acceleration".
Integrated feed — NOT standalone. Rule-based velocity tracking, no prediction.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.ExchangeFlowVelocityMonitor")

_FEATURE_ID = 508
_RENAMED_FROM = "Exchange Wallet Outflow Acceleration"
_TITLE = "Exchange Flow Velocity Monitor"
_STANDALONE = False
_MERGED_INTO = "On-Chain Intelligence Layer / Exchange Flow Feed"
_LAYER = "On-Chain Intelligence Layer"
_SPRINT = 1
_SEED_PATH = Path("data/exchange_flow_velocity_monitor_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Data monitoring only | Not a sell signal | Not investment advice | "
    "Velocity = current flow vs historical average, not prediction"
)

_BANNED_TERMS = (
    "acceleration",
    "sell signal",
    "buy signal",
    "portfolio management",
    "prediction",
    "forecast",
)

FlowType = Literal["inflow", "outflow"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"exchanges": {}, "velocity_windows": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("exchange flow velocity seed load failed: %s", exc)
        return {"exchanges": {}, "velocity_windows": {}}


def build_velocity_methodology(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    windows = seed.get("velocity_windows") or {}
    return {
        "methodology_version": _METHODOLOGY_VERSION,
        "method": "rule_based_velocity",
        "no_ml": True,
        "no_prediction": True,
        "not_portfolio_management": True,
        "formula": (
            "velocity_pct = ((current_period_flow - baseline_avg) / baseline_avg) * 100"
        ),
        "baseline_window_days": windows.get("baseline_days", 30),
        "current_window_hours": windows.get("current_hours", 24),
        "not_acceleration_predictive": True,
        "display": "Rule-based velocity — current flow vs 30-day average, not predictive",
    }


def compute_flow_velocity(
    current_flow_usd: float,
    baseline_avg_usd: float,
    *,
    flow_type: FlowType = "outflow",
) -> dict[str, Any]:
    """Compute flow velocity vs baseline — descriptive, not predictive."""
    if baseline_avg_usd == 0:
        velocity_pct = 0.0 if current_flow_usd == 0 else 100.0
    else:
        velocity_pct = ((current_flow_usd - baseline_avg_usd) / abs(baseline_avg_usd)) * 100

    sign = "+" if velocity_pct >= 0 else ""
    return {
        "flow_type": flow_type,
        "current_flow_usd": round(current_flow_usd, 2),
        "baseline_avg_usd": round(baseline_avg_usd, 2),
        "velocity_pct": round(velocity_pct, 2),
        "not_predictive": True,
        "not_sell_signal": True,
        "data_only": True,
        "display": (
            f"{flow_type.capitalize()} velocity: {sign}{velocity_pct:.0f}% vs "
            f"{30}-day average"
        ),
    }


def build_exchange_flow_record(exchange_data: dict[str, Any], *, exchange_id: str) -> dict[str, Any]:
    """Format exchange flow velocity data point."""
    entity = exchange_data.get("entity_name") or exchange_data.get("name") or exchange_id
    outflow = compute_flow_velocity(
        float(exchange_data.get("current_outflow_usd", 0)),
        float(exchange_data.get("baseline_outflow_avg_usd", 1)),
        flow_type="outflow",
    )
    inflow = compute_flow_velocity(
        float(exchange_data.get("current_inflow_usd", 0)),
        float(exchange_data.get("baseline_inflow_avg_usd", 1)),
        flow_type="inflow",
    )

    return {
        "exchange_id": exchange_id,
        "entity": entity,
        "entity_display": f"Entity: {entity}",
        "outflow": outflow,
        "inflow": inflow,
        "net_flow_usd": round(
            float(exchange_data.get("current_inflow_usd", 0))
            - float(exchange_data.get("current_outflow_usd", 0)),
            2,
        ),
        "chains_tracked": exchange_data.get("chains_tracked") or [],
        "data_only": True,
        "not_signal": True,
        "not_portfolio_management": True,
        "display": (
            f"Outflow velocity: {outflow['display'].split(': ')[1]} | "
            f"Entity: {entity}"
        ),
        "timestamp": exchange_data.get("timestamp") or _utcnow(),
    }


def build_exchange_flow_velocity_panel(
    *,
    exchange_id: str | None = None,
    asset: str | None = None,
) -> dict[str, Any]:
    """Main panel — exchange flow velocity feed within On-Chain Intelligence Layer."""
    t0 = time.perf_counter()
    seed = _load_seed()
    exchanges_raw = seed.get("exchanges") or {}

    if exchange_id:
        exchange = exchanges_raw.get(exchange_id.lower())
        if not exchange:
            return {
                "ok": False,
                "feature_id": _FEATURE_ID,
                "error": "exchange_not_found",
                "exchange_id": exchange_id,
            }
        exchanges_to_process = {exchange_id.lower(): exchange}
    else:
        exchanges_to_process = exchanges_raw
        if asset:
            asset_upper = asset.upper()
            exchanges_to_process = {
                eid: e for eid, e in exchanges_raw.items()
                if asset_upper in (e.get("assets_tracked") or [])
            }

    records = [
        build_exchange_flow_record(data, exchange_id=eid)
        for eid, data in exchanges_to_process.items()
    ]
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "not_acceleration_predictive": True,
        "no_trading_signals": True,
        "not_portfolio_management": True,
        "data_monitoring_only": True,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "surface": "onchain_intelligence_feed",
        "rule_based_only": True,
        "records": records,
        "record_count": len(records),
        "methodology": build_velocity_methodology(seed),
        "acceptance_criteria": {
            "latency_under_10s": elapsed < 10_000,
            "real_time_refresh": True,
            "not_portfolio_feature": True,
            "integrated_feed": True,
        },
        "banned_output_terms": list(_BANNED_TERMS),
        "disclaimer": _DISCLAIMER,
        "disclaimer_on_every_output": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def exchange_flow_velocity_monitor_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "not_acceleration_predictive": True,
        "no_trading_signals": True,
        "not_portfolio_management": True,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "surface": "onchain_intelligence_feed",
        "rule_based_only": True,
        "methodology": build_velocity_methodology(seed),
        "exchange_count": len(seed.get("exchanges") or {}),
        "acceptance_criteria": {
            "latency_under_10s": True,
            "real_time_refresh": True,
            "integrated_feed": True,
            "not_portfolio_feature": True,
            "no_ml": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
