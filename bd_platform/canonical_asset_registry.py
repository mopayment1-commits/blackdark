"""
Canonical Asset Registry — Feature #705 merged into #194 Unified Connector (Sprint 1).

Metadata layer — NOT a standalone user-facing feature.
Stable IDs + lifecycle versioning (active, deprecated, dead).
Prevents symbol chaos: ETH = Ethereum everywhere, ETH-OLD = legacy.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CanonicalAssets")

_FEATURE_ID = 705
_MERGED_INTO = "#194 Unified Connector"
_STANDALONE = False
_SEED_PATH = Path("data/canonical_assets_seed.json")
_STORE_PATH = Path("data/canonical_assets.json")

Lifecycle = Literal["active", "deprecated", "dead"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> list[dict[str, Any]]:
    if not _SEED_PATH.is_file():
        return []
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("canonical assets seed load failed: %s", exc)
        return []


def _load_store() -> dict[str, Any]:
    if _STORE_PATH.is_file():
        try:
            return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    assets = {a["stable_id"]: a for a in _load_seed()}
    store = {"assets": assets, "updated_at": _utcnow()}
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    return store


def _enrich_asset(row: dict[str, Any]) -> dict[str, Any]:
    lifecycle = str(row.get("lifecycle") or "active")
    enriched = {
        **row,
        "lifecycle_display": f"Lifecycle: {lifecycle} | Version: {row.get('lifecycle_version', 1)}",
        "canonical_model": True,
        "stable_id_required": True,
        "merged_feature": _MERGED_INTO,
        "display": f"{row.get('symbol')} ({row.get('stable_id')}) — {lifecycle}",
    }
    integrated: list[str] = []
    try:
        from bd_platform.market_cap_supply import get_supply_provenance

        supply = get_supply_provenance(str(row.get("symbol") or ""))
        if supply:
            enriched["supply_provenance"] = supply
            integrated.append("#267")
    except Exception:
        logger.debug("supply provenance enrich failed", exc_info=True)
    try:
        from bd_platform.dev_health_score import get_dev_health_for_asset

        dev_health = get_dev_health_for_asset(str(row.get("symbol") or ""))
        if dev_health:
            enriched["dev_health"] = dev_health
            integrated.append("#238")
    except Exception:
        logger.debug("dev health enrich failed", exc_info=True)
    try:
        from bd_platform.dex_volume_feed import get_dex_volume_for_asset

        dex_volume = get_dex_volume_for_asset(str(row.get("symbol") or ""))
        if dex_volume:
            enriched["dex_volume"] = dex_volume
            integrated.append("#235")
    except Exception:
        logger.debug("dex volume enrich failed", exc_info=True)
    try:
        from bd_platform.futures_volume_intelligence import get_futures_volume_for_asset

        futures_volume = get_futures_volume_for_asset(str(row.get("symbol") or ""))
        if futures_volume:
            enriched["futures_volume"] = futures_volume
            integrated.append("#246")
    except Exception:
        logger.debug("futures volume enrich failed", exc_info=True)
    if integrated:
        enriched["integrated_features"] = integrated
    return enriched


def list_canonical_assets(
    *,
    lifecycle: Lifecycle | None = None,
    chain: str | None = None,
    canonical_only: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    store = _load_store()
    rows = [_enrich_asset(a) for a in store.get("assets", {}).values()]

    if lifecycle:
        rows = [r for r in rows if str(r.get("lifecycle", "")).lower() == lifecycle]
    if chain:
        rows = [r for r in rows if str(r.get("chain", "")).lower() == chain.lower()]
    if canonical_only:
        rows = [r for r in rows if r.get("canonical") is True]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "parent_feature": 194,
        "count": len(rows[:limit]),
        "assets": rows[:limit],
        "stable_ids": True,
        "lifecycle_versioning": True,
        "timestamp": _utcnow(),
    }


def resolve_asset(symbol: str) -> dict[str, Any]:
    """Resolve symbol to canonical stable ID — ETH everywhere, ETH-OLD = legacy."""
    store = _load_store()
    sym = symbol.upper()
    matches: list[dict[str, Any]] = []

    for asset in store.get("assets", {}).values():
        aliases = [a.upper() for a in (asset.get("aliases") or [])]
        if sym == str(asset.get("symbol", "")).upper() or sym in aliases:
            matches.append(_enrich_asset(asset))

    active = [m for m in matches if m.get("lifecycle") == "active" and m.get("canonical")]
    canonical = active[0] if active else (matches[0] if matches else None)

    if not canonical:
        return {"ok": False, "error": "asset_not_found", "symbol": symbol}

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "symbol": symbol.upper(),
        "resolved": canonical,
        "stable_id": canonical.get("stable_id"),
        "lifecycle": canonical.get("lifecycle"),
        "is_deprecated": canonical.get("lifecycle") in ("deprecated", "dead"),
        "timestamp": _utcnow(),
    }


def get_canonical_asset(stable_id: str) -> dict[str, Any]:
    store = _load_store()
    row = store.get("assets", {}).get(stable_id)
    if not row:
        return {"ok": False, "error": "stable_id_not_found"}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": _enrich_asset(row),
        "timestamp": _utcnow(),
    }


def canonical_asset_registry_status() -> dict[str, Any]:
    store = _load_store()
    assets = list(store.get("assets", {}).values())
    lifecycles = {a.get("lifecycle") for a in assets}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "parent_feature": 194,
        "module": "Canonical Asset Registry (metadata layer)",
        "sprint": 1,
        "asset_count": len(assets),
        "lifecycle_states": sorted(lifecycles),
        "stable_ids": True,
        "lifecycle_versioning": True,
        "integrated_with": ["connector_coverage_map", "#194", "#267", "#238", "#235", "#246"],
        "supply_provenance_merged": True,
        "dev_health_merged": True,
        "dex_volume_merged": True,
        "futures_volume_merged": True,
        "timestamp": _utcnow(),
    }
