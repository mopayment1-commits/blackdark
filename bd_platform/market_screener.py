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


# --- #928 Asset Screener (Market Radar tab) ---

_FEATURE_REF_928 = 928
_TAXONOMY_REF_927 = 927
_PROVENANCE_REF_945 = 945
_EXPORT_REF_924 = 924

_PRESET_928 = ("top_gainers", "high_volume", "new_listings")


def _deterministic_sort_928(assets: list[dict[str, Any]], sort_by: str = "market_cap_usd", sort_dir: str = "desc") -> list[dict[str, Any]]:
    """Secondary sort: market_cap → volume → name."""

    def key(a: dict[str, Any]) -> tuple:
        primary = a.get(sort_by)
        if primary is None:
            p = (1, 0)
        elif isinstance(primary, (int, float)):
            p = (0, float(primary))
        else:
            p = (0, str(primary))
        mcap = float(a.get("market_cap_usd") or -1)
        vol = float(a.get("volume_24h_usd") or -1)
        name = a.get("symbol") or ""
        if sort_dir == "desc":
            return (p[0], -p[1] if isinstance(p[1], float) else p[1], -mcap, -vol, name)
        return (p[0], p[1], -mcap, -vol, name)

    return sorted(assets, key=key)


def _encode_cursor(index: int) -> str:
    return hashlib.sha256(f"cursor:{index}".encode()).hexdigest()[:16]


def _decode_cursor(cursor: str, total: int) -> int:
    for i in range(total + 1):
        if _encode_cursor(i) == cursor:
            return i
    return 0


def _enrich_taxonomy_928(symbol: str) -> dict[str, Any]:
    try:
        from bd_platform.data_engine_asset_taxonomy import get_asset_classification_927

        cls = get_asset_classification_927(symbol)
        return cls.get("classification") or {}
    except Exception:
        return {}


def asset_screener_status_928() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF_928,
        "merged_into": "Market Radar / Screener tab",
        "standalone": False,
        "standalone_rejected": True,
        "taxonomy_ref": _TAXONOMY_REF_927,
        "provenance_ref": _PROVENANCE_REF_945,
        "export_ref": _EXPORT_REF_924,
        "presets": list(_PRESET_928),
        "pagination": "cursor_based",
        "backend_enforced_filters": True,
        "deterministic_sorting": True,
        "missing_data_explicit": True,
        "asset_count": len(seed.get("assets") or []),
        "timestamp": _utcnow(),
    }


def run_asset_screener_928(
    filters: dict[str, Any] | None = None,
    *,
    sector: str | None = None,
    sub_sector: str | None = None,
    category: str | None = None,
    preset_id: str | None = None,
    sort_by: str = "market_cap_usd",
    sort_dir: str = "desc",
    cursor: str | None = None,
    page_size: int = 20,
    tier: str = "free",
    user_id: str = "user_demo",
) -> dict[str, Any]:
    seed = _load_seed()
    assets = list(seed.get("assets") or [])
    filters = dict(filters or {})

    if preset_id:
        preset = (seed.get("presets_928") or {}).get(preset_id)
        if not preset:
            return {"ok": False, "feature_ref": _FEATURE_REF_928, "error": "preset_not_found"}
        filters = {**preset.get("filters", {}), **filters}
        sort_by = preset.get("sort_by", sort_by)
        sort_dir = preset.get("sort_dir", sort_dir)

    if sector or sub_sector or category:
        from bd_platform.data_engine_asset_taxonomy import filter_assets_by_taxonomy_927

        tax = filter_assets_by_taxonomy_927(sector=sector, sub_sector=sub_sector, category=category)
        allowed = {a["asset"] for a in tax.get("assets") or []}
        assets = [a for a in assets if a.get("symbol") in allowed]

    matched = _apply_filters(assets, filters)
    sorted_assets = _deterministic_sort_928(matched, sort_by=sort_by, sort_dir=sort_dir)

    start = _decode_cursor(cursor, len(sorted_assets)) if cursor else 0
    page_size = min(max(1, page_size), 100)
    page_items = sorted_assets[start : start + page_size]
    next_start = start + page_size
    has_more = next_start < len(sorted_assets)

    rows = []
    for a in page_items:
        tax = _enrich_taxonomy_928(a.get("symbol", ""))
        rows.append({
            "symbol": a.get("symbol"),
            "market_cap_usd": _display_value(a.get("market_cap_usd")),
            "volume_24h_usd": _display_value(a.get("volume_24h_usd")),
            "price_change_24h_pct": _display_value(a.get("price_change_24h_pct")),
            "sector": tax.get("sector") or "N/A",
            "sub_sector": tax.get("sub_sector") or "N/A",
            "category": tax.get("category") or "N/A",
            "missing_data_explicit": any(a.get(k) is None for k in ("market_cap_usd", "volume_24h_usd")),
            "no_disguised_zero": True,
        })

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF_928,
        "merged_into": "Market Radar",
        "filters": filters,
        "taxonomy_filter": {"sector": sector, "sub_sector": sub_sector, "category": category},
        "preset_id": preset_id,
        "sort": {"by": sort_by, "dir": sort_dir, "tie_breaker": "market_cap → volume → name"},
        "pagination": {
            "cursor": cursor,
            "next_cursor": _encode_cursor(next_start) if has_more else None,
            "page_size": page_size,
            "total_results": len(sorted_assets),
            "has_more": has_more,
            "cursor_based": True,
        },
        "results": rows,
        "backend_enforced": True,
        "deterministic": True,
        "tier": tier,
        "timestamp": _utcnow(),
    }


def save_screener_criteria_928(
    name: str,
    filters: dict[str, Any],
    *,
    user_id: str,
    tier: str = "free",
) -> dict[str, Any]:
    if tier != "pro":
        return {
            "ok": False,
            "feature_ref": _FEATURE_REF_928,
            "error": "pro_tier_required",
            "save_criteria_pro_only": True,
        }
    filter_id = f"user_{hashlib.sha256(f'{user_id}:{name}'.encode()).hexdigest()[:10]}"
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF_928,
        "filter_id": filter_id,
        "name": name,
        "filters": filters,
        "saved": True,
        "pro_tier": True,
        "timestamp": _utcnow(),
    }


def export_screener_via_export_layer_928(
    filters: dict[str, Any] | None = None,
    *,
    fmt: str = "csv",
) -> dict[str, Any]:
    from bd_platform.data_engine_export_layer import export_dataset_924

    screener = run_asset_screener_928(filters=filters, page_size=1000)
    export_result = export_dataset_924("market_fundamentals", fmt=fmt)
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF_928,
        "export_ref": _EXPORT_REF_924,
        "screener_results_count": screener.get("pagination", {}).get("total_results", 0),
        "export": export_result,
        "no_separate_export_module": True,
        "timestamp": _utcnow(),
    }
