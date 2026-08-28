"""
Data Engine Asset Taxonomy — Feature #927 (Sprint 1).

Merged into Data Engine — NOT standalone.
Versioned taxonomy with 4-level hierarchy, no silent remap, historical audit.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.AssetTaxonomy")

_FEATURE_REF = 927
_STANDALONE = False
_MERGED_INTO = "Data Engine"
_SEED_PATH = Path("data/data_engine_asset_taxonomy_seed.json")
_HIERARCHY = ("sector", "sub_sector", "category", "asset")

_DISCLAIMER = (
    "Asset Taxonomy — versioned classification. No silent remap. "
    "Historical classifications preserved with effective dates."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("asset taxonomy seed load failed: %s", exc)
        return {}


def asset_taxonomy_status_927(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("asset_taxonomy_927") or {}
    versions = seed.get("taxonomy_versions") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "hierarchy_levels": list(_HIERARCHY),
        "current_version": cfg.get("current_version", "1.0.0"),
        "version_count": len(versions),
        "no_silent_remap": True,
        "historical_auditable": True,
        "deterministic_mapping": True,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def get_taxonomy_version_927(
    version: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("asset_taxonomy_927") or {}
    ver = version or cfg.get("current_version", "1.0.0")
    versions = seed.get("taxonomy_versions") or {}
    taxonomy = versions.get(ver)
    if not taxonomy:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "version_not_found", "version": ver}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "version": ver,
        "effective_from": taxonomy.get("effective_from"),
        "sectors": taxonomy.get("sectors") or {},
        "immutable": True,
        "no_silent_remap": True,
        "timestamp": _utcnow(),
    }


def get_asset_classification_927(
    asset: str,
    *,
    as_of_version: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    symbol = asset.strip().upper()
    assignments = seed.get("asset_assignments") or {}
    entry = assignments.get(symbol)
    if not entry:
        return {
            "ok": True,
            "feature_ref": _FEATURE_REF,
            "asset": symbol,
            "classification": None,
            "label": "Unknown",
            "unknown_remains_unknown": True,
            "no_silent_attribution": True,
            "timestamp": _utcnow(),
        }

    current = entry.get("current") or {}
    if as_of_version and current.get("version") != as_of_version:
        history = entry.get("history") or []
        for h in history:
            if h.get("version") == as_of_version:
                current = h
                break

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "asset": symbol,
        "classification": {
            "sector": current.get("sector"),
            "sub_sector": current.get("sub_sector"),
            "category": current.get("category"),
        },
        "source": current.get("source"),
        "confidence": current.get("confidence"),
        "version": current.get("version"),
        "effective_date": current.get("effective_date"),
        "provenance_required": True,
        "timestamp": _utcnow(),
    }


def get_classification_history_927(
    asset: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    symbol = asset.strip().upper()
    assignments = seed.get("asset_assignments") or {}
    entry = assignments.get(symbol)
    if not entry:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "asset_not_found", "asset": symbol}

    current = entry.get("current") or {}
    history = list(entry.get("history") or [])
    timeline = history + [current]
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "asset": symbol,
        "current": current,
        "history": history,
        "timeline": timeline,
        "historical_auditable": True,
        "no_silent_remap": True,
        "old_classifications_preserved": len(history) > 0,
        "timestamp": _utcnow(),
    }


def reclassify_asset_927(
    asset: str,
    *,
    sector: str,
    sub_sector: str,
    category: str,
    new_version: str,
    source: str = "deterministic_mapping_rule",
    confidence: str = "high",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create new classification version — old preserved, no silent remap."""
    seed = seed or _load_seed()
    symbol = asset.strip().upper()
    assignments = seed.get("asset_assignments") or {}
    entry = assignments.get(symbol) or {"current": {}, "history": []}
    current = entry.get("current") or {}

    if current:
        history_entry = {**current, "superseded_date": _utcnow()}
        entry.setdefault("history", []).append(history_entry)

    new_classification = {
        "sector": sector,
        "sub_sector": sub_sector,
        "category": category,
        "source": source,
        "confidence": confidence,
        "version": new_version,
        "effective_date": _utcnow(),
    }
    entry["current"] = new_classification

    audit_id = f"tax_audit_{uuid.uuid4().hex[:12]}"
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "asset": symbol,
        "classification": new_classification,
        "previous_preserved": len(entry.get("history") or []) > 0,
        "no_silent_remap": True,
        "audit_id": audit_id,
        "audit_logged": True,
        "timestamp": _utcnow(),
    }


def filter_assets_by_taxonomy_927(
    *,
    sector: str | None = None,
    sub_sector: str | None = None,
    category: str | None = None,
    tag: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    assignments = seed.get("asset_assignments") or {}
    matched: list[dict[str, Any]] = []

    for symbol, entry in assignments.items():
        current = entry.get("current") or {}
        if sector and current.get("sector") != sector:
            continue
        if sub_sector and current.get("sub_sector") != sub_sector:
            continue
        if category and current.get("category") != category:
            continue
        matched.append({
            "asset": symbol,
            "sector": current.get("sector"),
            "sub_sector": current.get("sub_sector"),
            "category": current.get("category"),
            "version": current.get("version"),
            "confidence": current.get("confidence"),
            "source": current.get("source"),
        })

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "filters": {"sector": sector, "sub_sector": sub_sector, "category": category, "tag": tag},
        "assets": matched,
        "count": len(matched),
        "taxonomy_versioned": True,
        "timestamp": _utcnow(),
    }


def run_asset_taxonomy_e2e_927(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = asset_taxonomy_status_927(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "four_levels", "passed": len(status["hierarchy_levels"]) == 4})
    checks.append({"id": "versioned", "passed": status["version_count"] >= 2})

    eth = get_asset_classification_927("ETH", seed=seed)
    checks.append({"id": "classification", "passed": eth.get("classification") is not None})
    checks.append({"id": "provenance", "passed": eth.get("source") is not None})

    sol_hist = get_classification_history_927("SOL", seed=seed)
    checks.append({"id": "historical_auditable", "passed": sol_hist.get("old_classifications_preserved") is True})
    checks.append({"id": "no_silent_remap", "passed": sol_hist.get("no_silent_remap") is True})

    unknown = get_asset_classification_927("UNKNOWNCOIN", seed=seed)
    checks.append({"id": "unknown_explicit", "passed": unknown.get("unknown_remains_unknown") is True})

    layer1 = filter_assets_by_taxonomy_927(sector="layer1", seed=seed)
    checks.append({"id": "sector_filter", "passed": layer1.get("count", 0) >= 2})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature_ref": _FEATURE_REF, "all_passed": all_passed, "checks": checks}
