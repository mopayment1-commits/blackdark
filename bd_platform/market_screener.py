"""
Smart Screener — Feature #742 (Sprint 1 Core UX / Market Radar).

Deterministic filters. Missing data explicit (N/A). Saved filters supported.
Unique BLACKDARK filters: Bot Activity (#721), Exchange Quality (#132), On-Chain Signal.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.MarketScreener")

_FEATURE_ID = 742
_FEE_DB_FEATURE_ID = 130
_BOT_ACTIVITY_FEATURE_ID = 721
_EXCHANGE_QUALITY_FEATURE_ID = 132
_STANDALONE = False
_MERGED_INTO = "Market Radar / Smart Screener"
_SPRINT = 1
_SEED_PATH = Path("data/market_screener_seed.json")
_METHODOLOGY_VERSION = "1.0"

_FREE_MAX_LATENCY_S = 3.0
_PRO_MAX_LATENCY_S = 1.0

_UNIQUE_FILTERS = [
    {"id": "bot_activity_score", "feature_id": _BOT_ACTIVITY_FEATURE_ID, "label": "Bot Activity Score"},
    {"id": "exchange_quality", "feature_id": _EXCHANGE_QUALITY_FEATURE_ID, "label": "Exchange Quality"},
    {"id": "onchain_signal", "feature_id": 737, "label": "On-Chain Signal"},
]

_DISCLAIMER = (
    "Assets matching your criteria — not investment recommendations. "
    "Missing data shown as N/A."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": [], "saved_filters": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("market screener seed load failed: %s", exc)
        return {"assets": [], "saved_filters": {}}


def _display_value(value: Any) -> Any:
    if value is None:
        return "N/A"
    return value


def _apply_filters(assets: list[dict[str, Any]], filters: dict[str, Any]) -> list[dict[str, Any]]:
    field_map = {
        "yield_min": "yield_pct",
        "profit_min": "yield_pct",
    }
    result = []
    for asset in assets:
        match = True
        for key, spec in filters.items():
            field = field_map.get(key, key)
            val = asset.get(field)
            if val is None:
                if spec.get("require_present"):
                    match = False
                    break
                continue
            if "min" in spec and float(val) < float(spec["min"]):
                match = False
                break
            if "max" in spec and float(val) > float(spec["max"]):
                match = False
                break
        if match:
            result.append(asset)
    result.sort(key=lambda a: (a.get("symbol") or ""))
    return result


def _deterministic_checksum(assets: list[dict[str, Any]], filters: dict[str, Any]) -> str:
    payload = json.dumps({"filters": filters, "symbols": [a.get("symbol") for a in assets]}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def run_screener(
    filters: dict[str, Any] | None = None,
    *,
    tier: str = "free",
    saved_filter_id: str | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    assets = seed.get("assets") or []

    if saved_filter_id:
        saved = (seed.get("saved_filters") or {}).get(saved_filter_id)
        if not saved:
            return {"ok": False, "feature_id": _FEATURE_ID, "error": "saved_filter_not_found"}
        filters = saved.get("filters") or {}
    filters = filters or {}

    if filters.get("yield_min") is not None or filters.get("profit_min") is not None:
        fee_db_required = True
    else:
        fee_db_required = False

    matched = _apply_filters(assets, filters)
    rows = []
    for a in matched:
        rows.append({
            "symbol": a.get("symbol"),
            "market_cap_usd": _display_value(a.get("market_cap_usd")),
            "volume_24h_usd": _display_value(a.get("volume_24h_usd")),
            "bot_activity_score": _display_value(a.get("bot_activity_score")),
            "exchange_quality_score": _display_value(a.get("exchange_quality_score")),
            "onchain_signal": _display_value(a.get("onchain_signal")),
            "yield_pct": _display_value(a.get("yield_pct")),
            "missing_data_explicit": any(
                a.get(k) is None for k in ("market_cap_usd", "volume_24h_usd", "bot_activity_score")
            ),
        })

    elapsed_s = time.perf_counter() - t0
    max_latency = _PRO_MAX_LATENCY_S if tier == "pro" else _FREE_MAX_LATENCY_S

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "tier": tier,
        "filters": filters,
        "saved_filter_id": saved_filter_id,
        "assets_matching_criteria": len(rows),
        "display": f"Assets matching your criteria: {len(rows)}",
        "not_opportunities_language": True,
        "results": rows,
        "deterministic": True,
        "result_checksum": _deterministic_checksum(matched, filters),
        "unique_filters": _UNIQUE_FILTERS,
        "fee_db_required": fee_db_required,
        "fee_db_feature_id": _FEE_DB_FEATURE_ID if fee_db_required else None,
        "latency_seconds": round(elapsed_s, 3),
        "latency_within_tier": elapsed_s <= max_latency,
        "max_latency_seconds": max_latency,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def list_saved_filters() -> dict[str, Any]:
    seed = _load_seed()
    saved = seed.get("saved_filters") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "saved_filters": [
            {"filter_id": fid, "name": f.get("name"), "shareable": f.get("shareable", True)}
            for fid, f in saved.items()
        ],
        "count": len(saved),
        "timestamp": _utcnow(),
    }


def market_screener_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Smart Screener (Market Radar)",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "unique_filters": _UNIQUE_FILTERS,
        "asset_count": len(seed.get("assets") or []),
        "saved_filter_count": len(seed.get("saved_filters") or {}),
        "acceptance_criteria": {
            "deterministic": True,
            "missing_data_explicit": True,
            "saved_filters": True,
            "fee_db_for_yield": True,
            "free_tier_max_3s": True,
            "pro_tier_sub_second": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
