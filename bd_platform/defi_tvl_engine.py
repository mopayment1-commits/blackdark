"""
DeFi TVL Engine — Feature #702 (Sprint 2 — DeFi Core).

TVL intelligence with explicit double-count policy, versioned methodology,
and source metadata. Displayed in Market Radar as DeFi layer.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DeFiTVL")

_FEATURE_ID = 702
_SEED_PATH = Path("data/defi_tvl_seed.json")
_STORE_PATH = Path("data/defi_tvl_engine.json")
_METHODOLOGY_VERSION = "v2.1"

Category = Literal["lending", "dex", "liquid_staking", "cdp", "bridge", "other"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"methodology": {}, "protocols": [], "chains": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("defi tvl seed load failed: %s", exc)
        return {"methodology": {}, "protocols": [], "chains": []}


def _load_store() -> dict[str, Any]:
    if _STORE_PATH.is_file():
        try:
            return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    store = {**_load_seed(), "updated_at": _utcnow()}
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(store, indent=2), encoding="utf-8")
    return store


def _format_tvl_usd(value: float) -> str:
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.0f}M"
    return f"${value:,.0f}"


def _enrich_protocol(row: dict[str, Any], methodology: dict[str, Any]) -> dict[str, Any]:
    tvl = float(row.get("tvl_usd") or 0)
    return {
        **row,
        "tvl_display": _format_tvl_usd(tvl),
        "methodology_display": (
            f"{methodology.get('version', _METHODOLOGY_VERSION)}: "
            f"{methodology.get('description', '')}"
        ),
        "double_count_policy": methodology.get("double_count_policy"),
        "double_count_display": row.get("double_count_display") or "No exclusions applied",
        "source_line": f"Source: {row.get('source')} | {row.get('source_url', '')}",
        "source_metadata": {
            "primary": row.get("source"),
            "url": row.get("source_url"),
            "methodology_version": row.get("methodology_version") or methodology.get("version"),
        },
        "normalized_tvl_usd": tvl,
        "market_radar_layer": "defi",
    }


def build_tvl_dashboard(
    *,
    chain: str | None = None,
    category: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    store = _load_store()
    methodology = store.get("methodology") or {}
    protocols = [_enrich_protocol(p, methodology) for p in store.get("protocols") or []]

    if chain:
        protocols = [p for p in protocols if str(p.get("chain", "")).lower() == chain.lower()]
    if category:
        protocols = [p for p in protocols if str(p.get("category", "")).lower() == category.lower()]

    protocols.sort(key=lambda p: float(p.get("tvl_usd") or 0), reverse=True)
    chains = store.get("chains") or []
    total_tvl = sum(float(p.get("tvl_usd") or 0) for p in protocols)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "surface": "market_radar_defi_layer",
        "methodology_version": methodology.get("version", _METHODOLOGY_VERSION),
        "methodology_display": (
            f"{methodology.get('version', _METHODOLOGY_VERSION)}: "
            f"{methodology.get('description', '')}"
        ),
        "double_count_policy": methodology.get("double_count_policy"),
        "total_tvl_usd": total_tvl,
        "total_tvl_display": _format_tvl_usd(total_tvl),
        "protocol_count": len(protocols[:limit]),
        "protocols": protocols[:limit],
        "chains": chains,
        "source_primary": methodology.get("source_primary"),
        "timestamp": _utcnow(),
    }


def get_protocol_tvl(protocol_id: str) -> dict[str, Any]:
    store = _load_store()
    methodology = store.get("methodology") or {}
    for row in store.get("protocols") or []:
        if row.get("id") == protocol_id:
            return {
                "ok": True,
                "feature_id": _FEATURE_ID,
                "protocol": _enrich_protocol(row, methodology),
                "timestamp": _utcnow(),
            }
    return {"ok": False, "error": "protocol_not_found"}


def get_methodology() -> dict[str, Any]:
    store = _load_store()
    methodology = store.get("methodology") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "methodology": methodology,
        "version": methodology.get("version", _METHODOLOGY_VERSION),
        "double_count_policy": methodology.get("double_count_policy"),
        "display": (
            f"Methodology {methodology.get('version')}: {methodology.get('description')} | "
            f"Policy: {methodology.get('double_count_policy')}"
        ),
        "timestamp": _utcnow(),
    }


def defi_tvl_engine_status() -> dict[str, Any]:
    store = _load_store()
    protocols = store.get("protocols") or []
    with_exclusions = sum(1 for p in protocols if float(p.get("double_count_excluded_usd") or 0) > 0)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "module": "DeFi TVL Engine",
        "sprint": 2,
        "market_radar_layer": "defi",
        "methodology_versioned": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "double_count_policy_documented": True,
        "source_metadata_required": True,
        "protocol_count": len(protocols),
        "protocols_with_exclusions": with_exclusions,
        "chain_count": len(store.get("chains") or []),
        "timestamp": _utcnow(),
    }
