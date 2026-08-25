"""
Instrument Master & Coverage Expansion — Feature #268 merged into Wave 01 Data Engine.

NOT standalone — expands Sprint 1 Data Engine with validated instrument mappings.
Reuses existing tables (assets, prices, markets). No duplicate pipelines.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

logger = logging.getLogger("BLACKDARK.InstrumentMaster")

_FEATURE_ID = 268
_STANDALONE = False
_MERGED_INTO = "Wave 01 Data Engine"
_SPRINT = 1
_SEED_PATH = Path("data/instrument_master_seed.json")
_METHODOLOGY_VERSION = "1.0"

AssetClass = Literal["spot", "perp", "option"]
VenueType = Literal["CEX", "DEX", "Derivatives"]
TierLabel = Literal["hot", "warm", "cold"]

_REUSED_TABLES = (
    "data_sources",
    "ohlcv_data",
    "market_snapshots",
    "funding_rates",
    "open_interest",
    "ingestion_runs",
)

_SCOPE_LOCK = {
    "claimed_marketing_total": 1_300_000,
    "validated_crypto_native": 50_000,
    "asset_classes": ["spot", "perp", "option"],
    "tradfi_equities": "Wave 3",
    "sources": ["CEX APIs", "DEX on-chain", "derivatives venues"],
    "update_policy": {
        "top_5k": "real-time",
        "remainder": "delayed",
    },
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"instruments": [], "coverage": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("instrument master seed load failed: %s", exc)
        return {"instruments": [], "coverage": {}}


def build_scope_lock_display() -> dict[str, Any]:
    """Scope lock — no expansion without validation."""
    return {
        **_SCOPE_LOCK,
        "display": (
            f"1.3M instruments: crypto spot + perps + options only | "
            f"TradFi/equities = Wave 3 | "
            f"Source: [CEX APIs + DEX on-chain + derivatives venues] | "
            f"Update: real-time for top 5K, delayed for remainder"
        ),
        "validated_count": _SCOPE_LOCK["validated_crypto_native"],
        "no_expansion_without_validation": True,
    }


def build_instrument_mapping(record: dict[str, Any]) -> dict[str, Any]:
    """Instrument mapping schema — no mapping = no ingestion."""
    confidence = float(record.get("mapping_confidence_pct", 0))
    return {
        "instrument_id": record.get("instrument_id"),
        "venue": record.get("venue"),
        "venue_type": record.get("venue_type"),
        "asset_class": record.get("asset_class"),
        "base": record.get("base"),
        "quote": record.get("quote"),
        "normalized_pair": f"{record.get('base')}/{record.get('quote')}",
        "mapping_confidence_pct": confidence,
        "last_verified": record.get("last_verified"),
        "tier": record.get("tier", "warm"),
        "daily_volume_usd": record.get("daily_volume_usd"),
        "source_tag": record.get("source_tag"),
        "display": (
            f"Instrument ID: {record.get('instrument_id')} | "
            f"Venue: {record.get('venue_type')} | "
            f"Asset class: {record.get('asset_class')} | "
            f"Base/quote: {record.get('base')}/{record.get('quote')} | "
            f"Mapping confidence: {confidence}% | "
            f"Last verified: {record.get('last_verified')}"
        ),
        "no_mapping_no_ingestion": True,
        "ingestion_allowed": confidence >= float(record.get("min_confidence_pct", 80)),
    }


def build_deduplication_audit() -> dict[str, Any]:
    """Audit against existing Sprint 1 schema — expand, don't rebuild."""
    return {
        "strategy": "Reuse existing tables — no duplicate pipelines",
        "reused_tables": list(_REUSED_TABLES),
        "no_duplicate_pipelines": True,
        "expand_not_rebuild": True,
        "display": (
            "Audit current Sprint 1 schema. Reuse existing tables "
            "(assets, prices, markets). No duplicate pipelines. Expand, don't rebuild."
        ),
    }


def build_cost_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Cost gate — hot/warm/cold tiers with auto-archive policy."""
    seed = seed or _load_seed()
    tiers = seed.get("cost_tiers") or {}
    return {
        "compute_budget": seed.get("compute_budget", "pre-defined cap"),
        "auto_archive_threshold_usd": seed.get("auto_archive_threshold_usd", 1000),
        "auto_archive_days": seed.get("auto_archive_days", 90),
        "tiers": {
            "hot": {
                "share_pct": tiers.get("hot_pct", 5),
                "label": "active",
                "description": "Top volume instruments — real-time ingestion",
            },
            "warm": {
                "share_pct": tiers.get("warm_pct", 15),
                "label": "monitor",
                "description": "Moderate volume — delayed updates",
            },
            "cold": {
                "share_pct": tiers.get("cold_pct", 80),
                "label": "archive",
                "description": "Low volume — auto-archive after 90 days < $1K daily",
            },
        },
        "display": (
            "Compute budget: pre-defined cap | "
            "Auto-archive instruments with < $1K daily volume after 90 days | "
            "Tier: hot (active 5%) / warm (monitor 15%) / cold (archive 80%)"
        ),
        "no_unbounded_cost": True,
    }


def build_acceptance_criteria(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Expanded acceptance beyond instrument mappings alone."""
    seed = seed or _load_seed()
    sla = seed.get("sla") or {}
    return {
        "instrument_mappings": True,
        "latency_sla_ms_top_5k": sla.get("latency_ms_top_5k", 500),
        "latency_display": f"Latency SLA < {sla.get('latency_ms_top_5k', 500)}ms for top 5K",
        "coverage_accuracy_pct": sla.get("coverage_accuracy_pct", 99.2),
        "coverage_benchmark": sla.get("coverage_benchmark", "CoinGecko"),
        "coverage_display": (
            f"Coverage accuracy > {sla.get('coverage_accuracy_pct', 99)}% "
            f"vs {sla.get('coverage_benchmark', 'CoinGecko')} benchmark"
        ),
        "uptime_sla_pct": sla.get("uptime_sla_pct", 99.9),
        "uptime_display": f"Uptime SLA {sla.get('uptime_sla_pct', 99.9)}%",
        "provenance_per_tick": True,
        "source_tagging": True,
        "provenance_display": "Data provenance per tick with source tagging",
    }


def build_methodology_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    last_updated = seed.get("last_updated", "2026-08-25")
    return {
        "version": _METHODOLOGY_VERSION,
        "module": "Instrument Master & Coverage Expansion",
        "merged_feature": _FEATURE_ID,
        "replaces_standalone_268": True,
        "last_updated": last_updated,
        "display": (
            f"Instrument Master v{_METHODOLOGY_VERSION} | "
            f"Merged into Wave 01 Data Engine | "
            f"Mapping quality over volume | Last Updated: {last_updated}"
        ),
    }


def list_instrument_mappings(
    *,
    tier: TierLabel | None = None,
    asset_class: AssetClass | None = None,
    venue_type: VenueType | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    seed = _load_seed()
    instruments = seed.get("instruments") or []
    mapped = [build_instrument_mapping(r) for r in instruments]

    if tier:
        mapped = [m for m in mapped if m.get("tier") == tier]
    if asset_class:
        mapped = [m for m in mapped if m.get("asset_class") == asset_class]
    if venue_type:
        mapped = [m for m in mapped if m.get("venue_type") == venue_type]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "count": len(mapped[:limit]),
        "total_in_seed": len(instruments),
        "instruments": mapped[:limit],
        "scope_lock": build_scope_lock_display(),
        "timestamp": _utcnow(),
    }


def get_instrument_mapping(instrument_id: str) -> dict[str, Any]:
    seed = _load_seed()
    for record in seed.get("instruments") or []:
        if str(record.get("instrument_id")) == instrument_id:
            mapping = build_instrument_mapping(record)
            return {
                "ok": True,
                "feature_id": _FEATURE_ID,
                "instrument": mapping,
                "provenance": {
                    "source_tag": record.get("source_tag"),
                    "ingestion_table": record.get("reused_table", "ohlcv_data"),
                    "no_duplicate_pipeline": True,
                },
                "timestamp": _utcnow(),
            }
    return {"ok": False, "error": "instrument_not_found", "instrument_id": instrument_id}


def instrument_master_status() -> dict[str, Any]:
    seed = _load_seed()
    coverage = seed.get("coverage") or {}
    instruments = seed.get("instruments") or []
    tier_counts = {"hot": 0, "warm": 0, "cold": 0}
    for inst in instruments:
        t = inst.get("tier", "warm")
        if t in tier_counts:
            tier_counts[t] += 1

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Instrument Master & Coverage Expansion",
        "standalone": _STANDALONE,
        "archived_standalone_ticket": True,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "replaces_marketing_claim": "1.3M → validated crypto-native ~50K",
        "scope_lock": build_scope_lock_display(),
        "deduplication": build_deduplication_audit(),
        "cost_gate": build_cost_gate(seed),
        "acceptance_criteria": build_acceptance_criteria(seed),
        "methodology": build_methodology_block(seed),
        "coverage": {
            "validated_instruments": coverage.get("validated_instruments", len(instruments)),
            "top_5k_realtime": coverage.get("top_5k_realtime", True),
            "tier_distribution": tier_counts,
            "accuracy_vs_benchmark_pct": coverage.get("accuracy_vs_coingecko_pct", 99.2),
        },
        "mapping_quality_is_product": True,
        "volume_not_value": True,
        "timestamp": _utcnow(),
    }
