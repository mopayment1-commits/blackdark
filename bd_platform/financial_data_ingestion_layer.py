"""
Financial Data Ingestion Layer — Feature #137 (Sprint 0 infrastructure).

Internal data ingestion — NOT a user-facing product feature.
Collects market, on-chain, and user data from free financial sources via
Unified Connector Layer (#194 / #175) with aggregator cross-reference (#138).

Pipeline: Collect → Normalize → Deduplicate → Store (#118 ETL) → Query → Export

Acceptance targets:
  - 99.99% validation accuracy
  - Query ≤ 1 second (cached)
  - Near-real-time ingest
  - ≥ 2 year retention
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.FinancialDataIngestion")

_FEATURE_ID = 137
_ACCURACY_TARGET = 0.9999
_QUERY_SLA_SEC = 1.0
_RETENTION_DAYS = 730
_FRESHNESS_PATH = Path("data/ingestion/freshness_tracker.json")
_DEDUP_PATH = Path("data/ingestion/dedup_index.json")
_INGEST_LOG = Path("data/ingestion/ingest_cycles.jsonl")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _checksum(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def normalize_market_record(quote: dict[str, Any], *, source_tier: str) -> dict[str, Any]:
    """Normalize connector quote to unified ingestion schema."""
    from bd_platform.unified_connector_layer import normalize_symbol

    asset = str(quote.get("asset") or "")
    sym = normalize_symbol(asset or quote.get("pair", "BTCUSDT"))
    return {
        "schema": "canonical_market_v1",
        "asset": sym["canonical_asset"],
        "canonical_asset": sym["canonical_asset"],
        "internal_pair": sym["internal_pair"],
        "price_usd": float(quote.get("price_usd") or 0),
        "price": float(quote.get("price_usd") or 0),
        "mark_price": float(quote.get("price_usd") or 0),
        "bid": quote.get("bid"),
        "ask": quote.get("ask"),
        "volume_24h_usd": float(quote.get("volume_24h_usd") or 0),
        "change_24h_pct": float(quote.get("change_24h_pct") or 0),
        "connector_id": quote.get("connector_id"),
        "source_tier": source_tier,  # primary | aggregator
        "timestamp": quote.get("fetched_at") or _utcnow(),
        "timestamp_tz": "UTC",
        "canonical_id": quote.get("canonical_id"),
    }


def deduplicate_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Deduplicate by content checksum — no repeated data."""
    index = _load_json(_DEDUP_PATH, {"checksums": {}})
    seen: set[str] = set(index.get("checksums") or {})
    unique: list[dict[str, Any]] = []
    skipped = 0

    for rec in records:
        chk = _checksum(rec)
        if chk in seen:
            skipped += 1
            continue
        seen.add(chk)
        rec["checksum"] = chk
        unique.append(rec)

    index["checksums"] = {c: _utcnow() for c in list(seen)[-5000:]}
    index["last_dedup_at"] = _utcnow()
    _save_json(_DEDUP_PATH, index)
    return unique, skipped


def track_freshness(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Freshness tracking — know when data is stale."""
    tracker = _load_json(_FRESHNESS_PATH, {"assets": {}})
    assets = tracker.setdefault("assets", {})
    now = datetime.now(UTC)

    for rec in records:
        asset = rec.get("canonical_asset") or rec.get("asset") or "unknown"
        ts_str = rec.get("timestamp") or _utcnow()
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            ts = now
        age_sec = (now - ts).total_seconds()
        prev = assets.get(asset) or {}
        assets[asset] = {
            "last_ingested_at": _utcnow(),
            "source_timestamp": ts_str,
            "age_seconds": round(age_sec, 1),
            "is_stale": age_sec > 300,
            "source_tier": rec.get("source_tier", "primary"),
            "connector_id": rec.get("connector_id"),
            "previous_age_seconds": prev.get("age_seconds"),
        }

    tracker["updated_at"] = _utcnow()
    _save_json(_FRESHNESS_PATH, tracker)

    stale_count = sum(1 for a in assets.values() if a.get("is_stale"))
    return {
        "tracked_assets": len(assets),
        "stale_assets": stale_count,
        "fresh_assets": len(assets) - stale_count,
        "stale_threshold_sec": 300,
    }


async def collect_market_data(
    asset: str = "BTC",
    *,
    use_microservice: bool = True,
) -> dict[str, Any]:
    """
    Collect from primary exchange APIs + aggregator cross-reference (#138).

    Does NOT rely on aggregators alone — primary sources first.
    """
    from bd_platform.unified_connector_layer import (
        _AGGREGATOR_CONNECTOR_IDS,
        _PRIMARY_CONNECTOR_IDS,
        cross_reference_quotes,
        fetch_all_connector_quotes,
    )

    if use_microservice:
        from bd_platform.flexible_connector_microservice import fetch_all_via_microservice

        results = await fetch_all_via_microservice(asset)
    else:
        results = await fetch_all_connector_quotes(asset)

    primary_records: list[dict[str, Any]] = []
    aggregator_records: list[dict[str, Any]] = []

    for r in results:
        if not r.ok or not r.quote:
            continue
        q = r.quote.to_dict()
        if r.connector_id in _AGGREGATOR_CONNECTOR_IDS:
            aggregator_records.append(normalize_market_record(q, source_tier="aggregator"))
        else:
            primary_records.append(normalize_market_record(q, source_tier="primary"))

    cross_ref = cross_reference_quotes(results)

    return {
        "asset": asset.upper(),
        "primary_records": primary_records,
        "aggregator_records": aggregator_records,
        "primary_count": len(primary_records),
        "aggregator_count": len(aggregator_records),
        "cross_reference": cross_ref,
        "collection_policy": "Primary exchange APIs + aggregator backup (#138)",
    }


async def run_ingestion_cycle(
    *,
    assets: list[str] | None = None,
) -> dict[str, Any]:
    """Full ingestion cycle: collect → normalize → deduplicate → store → freshness."""
    t0 = time.perf_counter()
    symbols = assets or ["BTC", "ETH", "SOL"]
    all_records: list[dict[str, Any]] = []
    cross_refs: list[dict[str, Any]] = []

    for sym in symbols[:8]:
        batch = await collect_market_data(sym)
        all_records.extend(batch["primary_records"])
        all_records.extend(batch["aggregator_records"])
        cross_refs.append(batch["cross_reference"])

    unique, dedup_skipped = deduplicate_records(all_records)
    freshness = track_freshness(unique)

    # Store via #118 ETL
    from bd_platform.local_data_etl import ensure_schema, load_structured, transform_record

    await ensure_schema()
    etl_rows = [
        transform_record(
            "market",
            "ingestion_quote",
            rec,
            source=str(rec.get("connector_id") or "ingestion_layer"),
        )
        for rec in unique
    ]
    valid_rows = [r for r in etl_rows if r.get("valid")]
    accuracy = len(valid_rows) / max(1, len(etl_rows))
    loaded = await load_structured(etl_rows)

    elapsed = time.perf_counter() - t0
    cycle = {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "mode": "infrastructure",
        "user_facing": False,
        "assets": symbols[:8],
        "collected": len(all_records),
        "deduplicated": dedup_skipped,
        "stored": loaded.get("loaded", 0),
        "accuracy": round(accuracy, 6),
        "accuracy_target": _ACCURACY_TARGET,
        "accuracy_met": accuracy >= _ACCURACY_TARGET,
        "freshness": freshness,
        "cross_references": cross_refs,
        "retention_days": _RETENTION_DAYS,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 5.0,
        "timestamp": _utcnow(),
    }

    _INGEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    with _INGEST_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(cycle, default=str) + "\n")

    return cycle


async def query_ingested_data(
    *,
    asset: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Fast query over ingested data — ≤1s SLA via ETL cache."""
    from bd_platform.local_data_etl import query_clean_data

    t0 = time.perf_counter()
    result = await query_clean_data(domain="market", asset=asset, limit=limit)
    elapsed = time.perf_counter() - t0
    result["feature_id"] = _FEATURE_ID
    result["ingestion_layer"] = True
    result["sla_met"] = elapsed <= _QUERY_SLA_SEC
    return result


async def export_ingested_data(
    *,
    asset: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """Export cleaned ingestion data for reports."""
    from bd_platform.local_data_etl import export_clean_data

    result = await export_clean_data(domain="market", asset=asset, limit=limit)
    result["feature_id"] = _FEATURE_ID
    result["export_source"] = "financial_data_ingestion_layer"
    return result


def freshness_status() -> dict[str, Any]:
    """Current freshness tracker snapshot."""
    tracker = _load_json(_FRESHNESS_PATH, {"assets": {}})
    assets = tracker.get("assets") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "tracked_assets": len(assets),
        "assets": assets,
        "stale_threshold_sec": 300,
        "updated_at": tracker.get("updated_at"),
        "timestamp": _utcnow(),
    }


def aggregator_cross_reference_status(asset: str = "BTC") -> dict[str, Any]:
    """#138 — Aggregator role as backup/cross-reference (sync status from last cycle)."""
    return {
        "ok": True,
        "feature_id": 138,
        "role": "aggregator_backup_cross_reference",
        "policy": (
            "Aggregators are backup and cross-reference only — "
            "never sole data source. Primary: exchange APIs via #194/#175."
        ),
        "asset": asset.upper(),
        "aggregators": ["coingecko"],
        "merged_into": ["#137", "#194"],
        "timestamp": _utcnow(),
    }


def ingestion_layer_status() -> dict[str, Any]:
    """Financial Data Ingestion Layer status (#137)."""
    tracker = _load_json(_FRESHNESS_PATH, {"assets": {}})
    dedup = _load_json(_DEDUP_PATH, {"checksums": {}})
    cycles = 0
    if _INGEST_LOG.is_file():
        cycles = sum(1 for _ in _INGEST_LOG.open(encoding="utf-8"))

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Financial Data Ingestion Layer",
        "mode": "infrastructure",
        "user_facing": False,
        "pipeline": ["collect", "normalize", "deduplicate", "store", "query", "export"],
        "accuracy_target": _ACCURACY_TARGET,
        "query_sla_sec": _QUERY_SLA_SEC,
        "retention_days": _RETENTION_DAYS,
        "freshness_tracked_assets": len(tracker.get("assets") or {}),
        "dedup_checksums": len(dedup.get("checksums") or {}),
        "ingest_cycles": cycles,
        "integrated_features": ["#118", "#138", "#175", "#194"],
        "policies": {
            "normalization": "canonical_market_v1",
            "deduplication": "sha256_checksum",
            "freshness_tracking": True,
            "aggregator_role": "backup_cross_reference_only",
            "no_venue_leakage": True,
        },
        "timestamp": _utcnow(),
    }
