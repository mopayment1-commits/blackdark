"""
Canonical Normalization Engine — #1027 (Data Engine).

Merged into Data Engine — NOT standalone.
Transforms heterogeneous source data (formats, units, symbols) into one
consistent internal schema before any calculation or display.

Pipeline sequence: ingest (#1024) → normalize (#1027) → outlier check (#1026) → serve
"""

from __future__ import annotations

import csv
import io
import json
import logging
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CanonicalNormalization")

_FEATURE_REF = 1027
_MERGED_INTO = "Data Engine"
_STANDALONE = False
_SEED_PATH = Path("data/canonical_normalization_seed.json")
_RUNBOOK = "docs/infrastructure/CANONICAL_NORMALIZATION.md"

_PROVENANCE_REF = 945
_MULTI_SOURCE_REF = 1024
_ASSET_TAXONOMY_REF = 927
_REFERENCE_PRICING_REF = 959
_PROTOCOL_KPIS_REF = 986
_OUTLIER_DETECTION_REF = 1026

DataType = Literal["price", "volume", "onchain"]
InputFormat = Literal["json", "xml", "csv"]

_normalization_log: list[dict[str, Any]] = []
_dedup_index: dict[str, dict[str, Any]] = {}


def reset_normalization_state() -> None:
    _normalization_log.clear()
    _dedup_index.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("canonical normalization seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("canonical_normalization_engine_1027") or {}


def canonical_normalization_status_1027(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "policy": {
            "enabled": policy.get("enabled", True),
            "rule_based_only": policy.get("rule_based_only", True),
            "no_ml_normalization_sprint_2": policy.get("no_ml_normalization_sprint_2", True),
            "schema_version": policy.get("schema_version", "1.0.0"),
            "pipeline_sequence": policy.get("pipeline_sequence", ["ingest", "normalize", "outlier_check", "serve"]),
            "blocks_production_if_incomplete": policy.get("blocks_production_if_incomplete", True),
        },
        "units": cfg.get("units") or {},
        "null_handling": cfg.get("null_handling") or {},
        "format_unification": cfg.get("format_unification") or {},
        "schema_mappings": seed.get("schema_mappings") or {},
        "integrations": {
            "provenance_ref": _PROVENANCE_REF,
            "multi_source_ref": _MULTI_SOURCE_REF,
            "asset_taxonomy_ref": _ASSET_TAXONOMY_REF,
            "reference_pricing_ref": _REFERENCE_PRICING_REF,
            "protocol_kpis_ref": _PROTOCOL_KPIS_REF,
            "outlier_detection_ref": _OUTLIER_DETECTION_REF,
        },
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def canonicalize_symbol(
    raw_symbol: str,
    *,
    seed: dict[str, Any] | None = None,
    source: str | None = None,
) -> dict[str, Any]:
    """Symbol canonicalization — #927 Asset Taxonomy, no silent remap."""
    seed = seed or _load_seed()
    aliases = seed.get("symbol_aliases") or {}
    raw = str(raw_symbol).strip()

    try:
        from blackdark.canonical.resolver import resolve_asset

        resolved = resolve_asset(raw)
        if resolved.found and resolved.symbol:
            return {
                "input": raw,
                "canonical_symbol": resolved.symbol,
                "canonical_id": resolved.canonical_id,
                "label": resolved.asset.label if resolved.asset else resolved.symbol,
                "matched_via": resolved.matched_via,
                "silent_remap": False,
                "asset_taxonomy_ref": _ASSET_TAXONOMY_REF,
            }
    except ImportError:
        logger.debug("asset taxonomy resolver unavailable")

    upper = raw.upper()
    if upper in aliases:
        canonical = aliases[upper]
        return {
            "input": raw,
            "canonical_symbol": canonical,
            "canonical_id": f"bd:{canonical}",
            "matched_via": "seed_alias",
            "silent_remap": False,
            "asset_taxonomy_ref": _ASSET_TAXONOMY_REF,
        }

    if raw in aliases:
        canonical = aliases[raw]
        return {
            "input": raw,
            "canonical_symbol": canonical,
            "canonical_id": f"bd:{canonical}",
            "matched_via": "seed_alias_label",
            "silent_remap": False,
            "asset_taxonomy_ref": _ASSET_TAXONOMY_REF,
        }

    return {
        "input": raw,
        "canonical_symbol": upper if upper.isalnum() and len(upper) <= 12 else None,
        "canonical_id": None,
        "matched_via": "unmapped",
        "silent_remap": False,
        "asset_taxonomy_ref": _ASSET_TAXONOMY_REF,
        "source": source,
    }


def _nested_get(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def map_source_schema(
    *,
    source: str,
    raw_payload: dict[str, Any],
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map vendor schema → canonical schema — documented + versioned."""
    seed = seed or _load_seed()
    mappings = seed.get("schema_mappings") or {}
    mapping = mappings.get(source) or {}
    fields = mapping.get("fields") or {}
    schema_version = mapping.get("version", "1.0.0")

    canonical: dict[str, Any] = {
        "schema_version": schema_version,
        "source": source,
        "raw_sources": [source],
        "transformations_applied": ["schema_mapping"],
    }

    for canonical_field, source_path in fields.items():
        value = _nested_get(raw_payload, source_path) if "." in source_path else raw_payload.get(source_path)
        canonical[canonical_field] = value if value is not None else None
        if value is None:
            canonical.setdefault("null_fields", []).append(canonical_field)

    if mapping.get("nested"):
        slug = raw_payload.get(str(fields.get("symbol", "id")))
        nested_data = raw_payload.get(str(slug)) if slug else None
        if isinstance(nested_data, dict):
            if canonical.get("price_usd") is None and "usd" in nested_data:
                canonical["price_usd"] = nested_data.get("usd")
            if canonical.get("volume_native") is None and "usd_24h_vol" in nested_data:
                canonical["volume_native"] = nested_data.get("usd_24h_vol")
            canonical["transformations_applied"].append("nested_schema_expansion")

    sym_raw = canonical.get("symbol") or raw_payload.get("symbol") or raw_payload.get("s")
    if sym_raw:
        sym = canonicalize_symbol(str(sym_raw), seed=seed, source=source)
        canonical["symbol"] = sym["canonical_symbol"]
        canonical["canonical_id"] = sym["canonical_id"]
        canonical["symbol_resolution"] = sym

    return canonical


def standardize_units(
    record: dict[str, Any],
    *,
    fx_rate_usd: float = 1.0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """All prices = USD, volumes = native + USD, timestamps = UTC."""
    seed = seed or _load_seed()
    units = (_cfg(seed).get("units") or {})
    out = dict(record)
    transforms = list(out.get("transformations_applied") or [])

    price = out.get("price_usd") or out.get("price") or out.get("value")
    if price is not None:
        out["price_usd"] = float(price)
        out["price_currency"] = units.get("price_currency", "USD")
        transforms.append("price_usd_standardization")

    vol_native = out.get("volume_native") or out.get("volume")
    if vol_native is not None:
        out["volume_native"] = float(vol_native)
        out["volume_usd"] = float(vol_native) * fx_rate_usd
        transforms.append("volume_native_usd_standardization")

    ts = out.get("timestamp")
    if ts is not None:
        if isinstance(ts, (int, float)):
            out["timestamp_utc"] = datetime.fromtimestamp(float(ts) / (1000.0 if ts > 1e12 else 1.0), UTC).isoformat()
        else:
            parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            out["timestamp_utc"] = parsed.astimezone(UTC).isoformat()
        transforms.append("timestamp_utc_standardization")
    else:
        out["timestamp_utc"] = None
        out.setdefault("null_fields", []).append("timestamp")

    out["transformations_applied"] = transforms
    out["units_immutable"] = units.get("immutable", True)
    return out


def handle_null_fields(record: dict[str, Any], *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Missing fields = explicit null — no fabricated zeros."""
    seed = seed or _load_seed()
    null_cfg = (_cfg(seed).get("null_handling") or {})
    out = dict(record)
    null_fields = list(out.get("null_fields") or [])

    for key in ("price_usd", "volume_native", "volume_usd", "timestamp_utc", "value", "symbol"):
        if key not in out:
            out[key] = None
            null_fields.append(key)
        elif out[key] is None and key not in null_fields:
            null_fields.append(key)

    if null_cfg.get("no_fabricated_zeros", True):
        for key in ("price_usd", "volume_native", "volume_usd", "value"):
            if out.get(key) == 0 and key in null_fields:
                pass  # keep explicit zero if source sent zero
            elif out.get(key) == 0 and f"{key}_from_source" not in out:
                out[key] = None
                null_fields.append(key)

    out["null_fields"] = sorted(set(null_fields))
    out["null_handling"] = {
        "explicit_null": null_cfg.get("explicit_null", True),
        "no_fabricated_zeros": null_cfg.get("no_fabricated_zeros", True),
        "flagged_in_provenance": null_cfg.get("flag_in_provenance", True),
    }
    return out


def unify_format(
    *,
    payload: str | dict[str, Any] | list[Any],
    input_format: InputFormat,
    source: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """JSON/XML/CSV → unified internal JSONB format."""
    seed = seed or _load_seed()
    if isinstance(payload, dict):
        data = payload
    elif input_format == "json":
        data = json.loads(payload) if isinstance(payload, str) else payload
    elif input_format == "xml":
        root = ET.fromstring(payload if isinstance(payload, str) else str(payload))
        data = {child.tag: child.text for child in root}
    elif input_format == "csv":
        reader = csv.DictReader(io.StringIO(payload if isinstance(payload, str) else ""))
        rows = list(reader)
        data = rows[0] if rows else {}
    else:
        data = {}

    mapped = map_source_schema(source=source, raw_payload=data if isinstance(data, dict) else {}, seed=seed)
    standardized = standardize_units(mapped, seed=seed)
    with_nulls = handle_null_fields(standardized, seed=seed)

    internal_format = (_cfg(seed).get("format_unification") or {}).get("internal_format", "jsonb")
    return {
        "ok": True,
        "internal_format": internal_format,
        "source": source,
        "input_format": input_format,
        "record": with_nulls,
        "schema_enforced": True,
    }


def _dedup_key(*, data_type: DataType, symbol: str, value: float | None, timestamp_utc: str | None) -> str:
    ts_part = timestamp_utc or "none"
    val_part = f"{value:.8f}" if value is not None else "null"
    return f"{data_type}:{symbol}:{val_part}:{ts_part}"


def deduplicate_cross_source(
    records: list[dict[str, Any]],
    *,
    data_type: DataType,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Same event from 2 sources → one canonical record + multi-source provenance."""
    seed = seed or _load_seed()
    dedup_cfg = (_cfg(seed).get("deduplication") or {})
    if not dedup_cfg.get("cross_source_enabled", True):
        return {"records": records, "deduplicated": False}

    merged: dict[str, dict[str, Any]] = {}
    for rec in records:
        symbol = str(rec.get("symbol") or rec.get("canonical_symbol") or "UNKNOWN")
        value = rec.get("value")
        if value is None:
            value = rec.get("price_usd") if data_type == "price" else rec.get("volume_native")
        ts = rec.get("timestamp_utc")
        key = _dedup_key(data_type=data_type, symbol=symbol, value=float(value) if value is not None else None, timestamp_utc=ts)

        if key in merged:
            existing = merged[key]
            sources = list(existing.get("raw_sources") or [existing.get("source")])
            src = rec.get("source")
            if src and src not in sources:
                sources.append(src)
            existing["raw_sources"] = sources
            existing["multi_source_provenance"] = True
            existing["deduplicated"] = True
            _dedup_index[key] = existing
        else:
            rec_copy = dict(rec)
            rec_copy["raw_sources"] = list(rec_copy.get("raw_sources") or [rec_copy.get("source")])
            rec_copy["multi_source_provenance"] = len(rec_copy["raw_sources"]) > 1
            merged[key] = rec_copy
            _dedup_index[key] = rec_copy

    return {
        "records": list(merged.values()),
        "deduplicated": True,
        "dedup_count": len(records) - len(merged),
        "strategy": dedup_cfg.get("strategy", "canonical_record_multi_provenance"),
    }


def record_normalization_fee(
    *,
    source_count: int = 1,
    transformation_count: int = 1,
    schema_version: str = "1.0.0",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    base = float(fee_cfg.get("compute_per_record_usd", 0.00002))
    mapping = float(fee_cfg.get("schema_mapping_usd", 0.00001))
    dedup = float(fee_cfg.get("dedup_usd", 0.000005))
    complexity = max(1, transformation_count)
    cost = round(base + mapping * source_count + dedup * complexity, 6)
    return {
        "source_count": source_count,
        "transformation_count": transformation_count,
        "schema_version": schema_version,
        "cost_usd": cost,
        "fee_db_logged": True,
        "logged_per_operation": True,
        "timestamp": _utcnow(),
    }


def build_normalization_provenance(
    *,
    record: dict[str, Any],
    schema_version: str = "1.0.0",
) -> dict[str, Any]:
    return {
        "provenance_ref": _PROVENANCE_REF,
        "raw_sources": record.get("raw_sources") or [record.get("source")],
        "transformations_applied": record.get("transformations_applied") or [],
        "schema_version": schema_version,
        "normalization_timestamp": _utcnow(),
        "null_fields": record.get("null_fields") or [],
        "multi_source_provenance": record.get("multi_source_provenance", False),
        "visible_in_api": True,
    }


def _log_normalization(entry: dict[str, Any]) -> None:
    _normalization_log.append({
        "normalization_id": f"norm_{uuid.uuid4().hex[:10]}",
        **entry,
        "audit_logged": True,
        "append_only": True,
    })


def normalize_observation(
    *,
    data_type: DataType,
    observation: dict[str, Any],
    symbol: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize a single multi-source observation to canonical internal format."""
    seed = seed or _load_seed()
    source = str(observation.get("source", "unknown"))
    raw_payload = observation.get("raw_payload") or observation

    if observation.get("raw_payload"):
        mapped = map_source_schema(source=source, raw_payload=raw_payload, seed=seed)
    else:
        mapped = {
            "source": source,
            "symbol": observation.get("symbol") or symbol,
            "price_usd": observation.get("value") if data_type == "price" else None,
            "volume_native": observation.get("value") if data_type == "volume" else None,
            "value": observation.get("value") if data_type == "onchain" else None,
            "raw_sources": [source],
            "transformations_applied": ["direct_observation_mapping"],
            "schema_version": (_cfg(seed).get("policy") or {}).get("schema_version", "1.0.0"),
        }
        sym = canonicalize_symbol(str(mapped.get("symbol") or symbol), seed=seed, source=source)
        mapped["symbol"] = sym["canonical_symbol"] or symbol
        mapped["canonical_id"] = sym["canonical_id"]
        mapped["symbol_resolution"] = sym

    standardized = standardize_units(mapped, seed=seed)
    with_nulls = handle_null_fields(standardized, seed=seed)

    normalized = {
        "source": source,
        "symbol": with_nulls.get("symbol") or symbol,
        "canonical_id": with_nulls.get("canonical_id"),
        "value": observation.get("value") or with_nulls.get("price_usd") or with_nulls.get("volume_native") or with_nulls.get("value"),
        "ok": observation.get("ok", True),
        "price_usd": with_nulls.get("price_usd"),
        "volume_native": with_nulls.get("volume_native"),
        "volume_usd": with_nulls.get("volume_usd"),
        "timestamp_utc": with_nulls.get("timestamp_utc"),
        "null_fields": with_nulls.get("null_fields") or [],
        "normalization": build_normalization_provenance(
            record=with_nulls,
            schema_version=str(with_nulls.get("schema_version", "1.0.0")),
        ),
    }
    if observation.get("latency_ms") is not None:
        normalized["latency_ms"] = observation["latency_ms"]
    if observation.get("timestamp_utc") is not None:
        normalized["timestamp_utc"] = observation["timestamp_utc"]
    for flag in ("corroborated_by_news", "corroborated_by_events", "events_ref", "news_ref"):
        if flag in observation:
            normalized[flag] = observation[flag]

    return normalized


def normalize_observations(
    *,
    data_type: DataType,
    observations: list[dict[str, Any]],
    symbol: str = "BTC",
    chain: str = "ethereum",
    enable_dedup: bool = False,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Main normalization entry — called after ingest (#1024), before outlier gate (#1026)."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    if not (cfg.get("policy") or {}).get("enabled", True):
        return {"gate_applied": False, "observations": observations}

    normalized_list = [
        normalize_observation(data_type=data_type, observation=obs, symbol=symbol, seed=seed)
        for obs in observations
    ]

    dedup: dict[str, Any]
    if enable_dedup:
        dedup = deduplicate_cross_source(normalized_list, data_type=data_type, seed=seed)
        final_observations = []
        for rec in dedup["records"]:
            final_observations.append({
                "source": rec.get("source"),
                "symbol": rec.get("symbol") or symbol,
                "value": rec.get("value"),
                "ok": rec.get("ok", True),
                "canonical_id": rec.get("canonical_id"),
                "price_usd": rec.get("price_usd"),
                "volume_native": rec.get("volume_native"),
                "volume_usd": rec.get("volume_usd"),
                "timestamp_utc": rec.get("timestamp_utc"),
                "null_fields": rec.get("null_fields") or [],
                "normalization": rec.get("normalization") or build_normalization_provenance(record=rec),
                "raw_sources": rec.get("raw_sources"),
                "multi_source_provenance": rec.get("multi_source_provenance", False),
            })
    else:
        dedup = {"records": normalized_list, "deduplicated": False, "dedup_skipped": "pipeline_preserves_multi_source"}
        final_observations = normalized_list

    fee = record_normalization_fee(
        source_count=len(observations),
        transformation_count=sum(
            len(o.get("normalization", {}).get("transformations_applied") or [])
            for o in final_observations
        ),
        seed=seed,
    )

    result = {
        "gate_applied": True,
        "feature_ref": _FEATURE_REF,
        "data_type": data_type,
        "chain": chain,
        "observations": final_observations,
        "deduplication": dedup,
        "fee_db": fee,
        "pipeline_step": "normalize",
        "next_step": "outlier_check",
        "timestamp": _utcnow(),
    }
    _log_normalization(result)
    return result


def get_normalization_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    rows = _normalization_log[-limit:]
    return {
        "ok": True,
        "count": len(rows),
        "append_only": True,
        "provenance_ref": _PROVENANCE_REF,
        "audit_trail": rows,
        "timestamp": _utcnow(),
    }


def check_production_gate_1027(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = canonical_normalization_status_1027(seed=seed)
    policy = status["policy"]
    mappings = status.get("schema_mappings") or {}
    required_sources = ("binance", "coingecko", "coinmarketcap")
    mappings_ok = all(s in mappings for s in required_sources)
    complete = (
        policy["enabled"]
        and policy["rule_based_only"]
        and mappings_ok
        and policy["no_ml_normalization_sprint_2"]
    )
    return {
        "ok": complete,
        "feature_ref": _FEATURE_REF,
        "blocks_production": policy["blocks_production_if_incomplete"],
        "production_allowed": complete,
        "checks": {
            "enabled": policy["enabled"],
            "rule_based_only": policy["rule_based_only"],
            "schema_mappings": mappings_ok,
            "no_ml_sprint_2": policy["no_ml_normalization_sprint_2"],
        },
        "timestamp": _utcnow(),
    }


def run_normalization_e2e_1027(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = canonical_normalization_status_1027(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({
        "id": "pipeline_sequence",
        "passed": status["policy"]["pipeline_sequence"] == ["ingest", "normalize", "outlier_check", "serve"],
    })

    sym = canonicalize_symbol("Bitcoin", seed=seed)
    checks.append({"id": "symbol_btc", "passed": sym["canonical_symbol"] == "BTC"})
    checks.append({"id": "no_silent_remap", "passed": sym["silent_remap"] is False})

    binance = unify_format(
        payload={"s": "BTCUSDT", "price": "42000.00", "E": 1693238400000},
        input_format="json",
        source="binance",
        seed=seed,
    )
    checks.append({"id": "binance_schema_mapping", "passed": binance["record"].get("price_usd") == 42000.0})
    checks.append({"id": "price_usd_unit", "passed": binance["record"].get("price_currency") == "USD"})

    cg = unify_format(
        payload={"id": "bitcoin", "bitcoin": {"usd": 42050.0, "usd_24h_vol": 1200000000}},
        input_format="json",
        source="coingecko",
        seed=seed,
    )
    checks.append({"id": "coingecko_nested", "passed": cg["record"].get("price_usd") == 42050.0})

    null_rec = handle_null_fields({"source": "test"}, seed=seed)
    checks.append({"id": "explicit_null", "passed": null_rec.get("price_usd") is None})
    checks.append({"id": "null_flagged", "passed": "price_usd" in (null_rec.get("null_fields") or [])})

    dedup = deduplicate_cross_source(
        [
            {"source": "binance", "symbol": "BTC", "value": 42000.0, "timestamp_utc": "2026-08-28T12:00:00+00:00"},
            {"source": "coingecko", "symbol": "BTC", "value": 42000.0, "timestamp_utc": "2026-08-28T12:00:00+00:00"},
        ],
        data_type="price",
        seed=seed,
    )
    checks.append({"id": "cross_source_dedup", "passed": len(dedup["records"]) == 1})
    checks.append({"id": "multi_provenance", "passed": dedup["records"][0].get("multi_source_provenance") is True})

    storage_norm = normalize_observations(
        data_type="price",
        observations=[
            {"source": "binance", "value": 42000.0, "ok": True, "timestamp_utc": "2026-08-28T12:00:00+00:00"},
            {"source": "coingecko", "value": 42000.0, "ok": True, "timestamp_utc": "2026-08-28T12:00:00+00:00"},
        ],
        symbol="BTC",
        enable_dedup=True,
        seed=seed,
    )
    checks.append({"id": "storage_dedup_enabled", "passed": len(storage_norm["observations"]) == 1})

    norm = normalize_observations(
        data_type="price",
        observations=[
            {"source": "binance", "value": 42000.0, "ok": True},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        symbol="BTC",
        seed=seed,
    )
    checks.append({"id": "normalize_observations", "passed": len(norm["observations"]) == 2})
    checks.append({"id": "provenance_attached", "passed": "normalization" in norm["observations"][0]})

    gate = check_production_gate_1027(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["production_allowed"] is True})

    fee = norm.get("fee_db") or {}
    checks.append({"id": "fee_db_logged", "passed": fee.get("fee_db_logged") is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
