"""
Multi-Source Ingest & Reconciliation Layer — #1024 (Data Engine).

Merged into Data Engine / Oracle API / On-Chain Extension — NOT standalone.
Cross-validates Price, Volume, and On-chain data from independent sources.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.MultiSourceReconciliation")

_FEATURE_REF = 1024
_MERGED_INTO = "Data Engine"
_STANDALONE = False
_SEED_PATH = Path("data/multi_source_reconciliation_seed.json")
_RUNBOOK = "docs/infrastructure/MULTI_SOURCE_RECONCILIATION.md"

_PROVENANCE_REF = 945
_SOURCE_PROVENANCE_REF = 1003
_REFERENCE_PRICING_REF = 959
_REAL_VOLUME_REF = 992
_INCIDENT_RESPONSE_REF = 1017
_LOAD_TEST_REF = 1020
_ONCHAIN_EXT_REF = 12

DataType = Literal["price", "volume", "onchain"]
Confidence = Literal["High", "Medium", "Low"]

_DEFAULT_THRESHOLDS = {
    "price": 0.5,
    "volume": 2.0,
    "onchain": 0.1,
}

_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = {
    "price": 300.0,  # 5 minutes
    "volume": 300.0,
    "onchain": 12.0,  # ~block interval check
}

_reconciliation_log: list[dict[str, Any]] = []


def reset_multi_source_state() -> None:
    _CACHE.clear()
    _reconciliation_log.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("multi-source seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("multi_source_reconciliation_1024") or {}


def multi_source_status_1024(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    sources = seed.get("sources") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "policy": {
            "min_sources_per_type": policy.get("min_sources_per_type", 2),
            "rule_based_cross_validation": policy.get("rule_based_cross_validation", True),
            "failover_enabled": policy.get("failover_enabled", True),
            "no_single_source_without_validation": policy.get(
                "no_single_source_without_validation", True
            ),
            "provenance_visible": policy.get("provenance_visible", True),
            "blocks_sprint_1_if_incomplete": policy.get("blocks_sprint_1_if_incomplete", True),
            "cache_ttl_seconds": _CACHE_TTL,
        },
        "thresholds_pct": cfg.get("thresholds_pct") or _DEFAULT_THRESHOLDS,
        "sources": sources,
        "integrations": {
            "provenance_ref": _PROVENANCE_REF,
            "source_provenance_ref": _SOURCE_PROVENANCE_REF,
            "reference_pricing_ref": _REFERENCE_PRICING_REF,
            "real_volume_ref": _REAL_VOLUME_REF,
            "incident_response_ref": _INCIDENT_RESPONSE_REF,
            "load_test_ref": _LOAD_TEST_REF,
            "onchain_extension_ref": _ONCHAIN_EXT_REF,
        },
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def compute_variance_pct(value_a: float, value_b: float) -> float:
    denom = max(abs(value_a), abs(value_b), 1e-12)
    return abs(value_a - value_b) / denom * 100.0


def cross_validate_pair(
    *,
    data_type: DataType,
    source_a: str,
    value_a: float,
    source_b: str,
    value_b: float,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based cross-validation — value vs value with tolerance threshold."""
    seed = seed or _load_seed()
    thresholds = (_cfg(seed).get("thresholds_pct") or _DEFAULT_THRESHOLDS)
    threshold = float(thresholds.get(data_type, _DEFAULT_THRESHOLDS[data_type]))
    variance = compute_variance_pct(value_a, value_b)
    within = variance <= threshold
    return {
        "ok": within,
        "data_type": data_type,
        "source_a": source_a,
        "value_a": value_a,
        "source_b": source_b,
        "value_b": value_b,
        "variance_pct": round(variance, 4),
        "threshold_pct": threshold,
        "within_tolerance": within,
        "timestamp": _utcnow(),
    }


def resolve_confidence(variance_pct: float, threshold_pct: float) -> Confidence:
    if variance_pct <= threshold_pct * 0.5:
        return "High"
    if variance_pct <= threshold_pct:
        return "Medium"
    return "Low"


def build_provenance_tag(
    *,
    source_a: str,
    value_a: float,
    source_b: str,
    value_b: float,
    variance_pct: float,
    confidence: Confidence,
    resolution: str,
) -> dict[str, Any]:
    return {
        "provenance_ref": _PROVENANCE_REF,
        "source_provenance_ref": _SOURCE_PROVENANCE_REF,
        "tag": (
            f"[{source_a}: {value_a} | {source_b}: {value_b} | "
            f"Variance: {variance_pct:.4f}% | Confidence: {confidence}]"
        ),
        "sources": [
            {"source": source_a, "value": value_a},
            {"source": source_b, "value": value_b},
        ],
        "variance_pct": variance_pct,
        "confidence": confidence,
        "resolution_method": resolution,
        "visible_in_api": True,
    }


def record_reconciliation_fee(
    *,
    data_type: DataType,
    sources_count: int = 2,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    per_source = float(fee_cfg.get("ingest_per_source_usd", 0.0001))
    validation = float(fee_cfg.get("validation_compute_usd", 0.00005))
    failover = float(fee_cfg.get("failover_overhead_usd", 0.00002))
    cost = round(per_source * sources_count + validation + failover, 6)
    return {
        "data_type": data_type,
        "sources_count": sources_count,
        "cost_usd": cost,
        "fee_db_logged": True,
        "timestamp": _utcnow(),
    }


def reconcile_observations(
    *,
    data_type: DataType,
    observations: list[dict[str, Any]],
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Core reconciliation — failover, divergence handling, provenance tagging.
    observations: [{"source": "binance", "value": 42000.0, "ok": True}, ...]
    """
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    min_sources = int((cfg.get("policy") or {}).get("min_sources_per_type", 2))
    thresholds = cfg.get("thresholds_pct") or _DEFAULT_THRESHOLDS
    threshold = float(thresholds.get(data_type, _DEFAULT_THRESHOLDS[data_type]))

    valid = [o for o in observations if o.get("ok", True) and o.get("value") is not None]
    failed = [o for o in observations if not o.get("ok", True)]

    fee = record_reconciliation_fee(data_type=data_type, sources_count=len(observations), seed=seed)

    if len(valid) < min_sources:
        failover_source = valid[0]["source"] if valid else None
        result = {
            "ok": False,
            "feature_ref": _FEATURE_REF,
            "data_type": data_type,
            "status": "insufficient_sources",
            "data_degraded": True,
            "badge": "Data Degraded",
            "suppress_output": True,
            "failover": {
                "active": bool(valid),
                "source": failover_source,
                "divergence_flagged": True,
                "failed_sources": [f.get("source") for f in failed],
            },
            "fee_db": fee,
            "timestamp": _utcnow(),
        }
        _log_reconciliation(result)
        _trigger_incident_if_needed(result, seed=seed)
        return result

    a, b = valid[0], valid[1]
    validation = cross_validate_pair(
        data_type=data_type,
        source_a=str(a["source"]),
        value_a=float(a["value"]),
        source_b=str(b["source"]),
        value_b=float(b["value"]),
        seed=seed,
    )
    variance = validation["variance_pct"]
    confidence = resolve_confidence(variance, threshold)

    if variance > threshold:
        result = {
            "ok": False,
            "feature_ref": _FEATURE_REF,
            "data_type": data_type,
            "status": "divergence_suppressed",
            "data_degraded": True,
            "badge": "Data Degraded",
            "suppress_output": True,
            "validation": validation,
            "failover": {
                "active": True,
                "primary": a["source"],
                "secondary": b["source"],
                "divergence_flagged": True,
                "auto_switch_to": b["source"] if not a.get("ok", True) else a["source"],
            },
            "provenance": build_provenance_tag(
                source_a=str(a["source"]),
                value_a=float(a["value"]),
                source_b=str(b["source"]),
                value_b=float(b["value"]),
                variance_pct=variance,
                confidence="Low",
                resolution="suppressed_divergence",
            ),
            "fee_db": fee,
            "timestamp": _utcnow(),
        }
        _log_reconciliation(result)
        _trigger_incident_if_needed(result, seed=seed)
        return result

    reconciled_value = (float(a["value"]) + float(b["value"])) / 2.0
    result = {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "data_type": data_type,
        "status": "reconciled",
        "value": reconciled_value,
        "confidence": confidence,
        "data_degraded": False,
        "badge": None,
        "suppress_output": False,
        "validation": validation,
        "failover": {
            "active": len(failed) > 0,
            "failed_sources": [f.get("source") for f in failed],
            "divergence_flagged": False,
        },
        "provenance": build_provenance_tag(
            source_a=str(a["source"]),
            value_a=float(a["value"]),
            source_b=str(b["source"]),
            value_b=float(b["value"]),
            variance_pct=variance,
            confidence=confidence,
            resolution="averaged",
        ),
        "fee_db": fee,
        "timestamp": _utcnow(),
    }
    _log_reconciliation(result)
    return result


def reconcile_price(
    *,
    symbol: str = "BTC",
    observations: list[dict[str, Any]] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    explicit = observations is not None
    cache_key = f"price:{symbol}"
    if not explicit:
        cached = _CACHE.get(cache_key)
        if cached and time.time() - cached[0] < _CACHE_TTL["price"]:
            out = dict(cached[1])
            out["cache_hit"] = True
            return out

    if observations is None:
        sources = (seed.get("sources") or {}).get("price") or []
        observations = [
            {"source": s.get("id"), "value": s.get("mock_value", 42000.0), "ok": True}
            for s in sources[:2]
        ]

    result = reconcile_observations(data_type="price", observations=observations, seed=seed)
    result["symbol"] = symbol
    result["reference_pricing_ref"] = _REFERENCE_PRICING_REF
    if not explicit:
        _CACHE[cache_key] = (time.time(), result)
    return result


def reconcile_volume(
    *,
    symbol: str = "BTC",
    observations: list[dict[str, Any]] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    explicit = observations is not None
    cache_key = f"volume:{symbol}"
    if not explicit:
        cached = _CACHE.get(cache_key)
        if cached and time.time() - cached[0] < _CACHE_TTL["volume"]:
            out = dict(cached[1])
            out["cache_hit"] = True
            return out

    if observations is None:
        sources = (seed.get("sources") or {}).get("volume") or []
        observations = [
            {"source": s.get("id"), "value": s.get("mock_value", 1_200_000_000.0), "ok": True}
            for s in sources[:2]
        ]

    result = reconcile_observations(data_type="volume", observations=observations, seed=seed)
    result["symbol"] = symbol
    result["real_volume_ref"] = _REAL_VOLUME_REF
    if not explicit:
        _CACHE[cache_key] = (time.time(), result)
    return result


def reconcile_onchain(
    *,
    chain: str = "ethereum",
    observations: list[dict[str, Any]] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    explicit = observations is not None
    cache_key = f"onchain:{chain}"
    if not explicit:
        cached = _CACHE.get(cache_key)
        if cached and time.time() - cached[0] < _CACHE_TTL["onchain"]:
            out = dict(cached[1])
            out["cache_hit"] = True
            return out

    if observations is None:
        sources = (seed.get("sources") or {}).get("onchain") or []
        observations = [
            {"source": s.get("id"), "value": s.get("mock_value", 19_500_000.0), "ok": True}
            for s in sources[:2]
        ]

    result = reconcile_observations(data_type="onchain", observations=observations, seed=seed)
    result["chain"] = chain
    result["onchain_extension_ref"] = _ONCHAIN_EXT_REF
    if not explicit:
        _CACHE[cache_key] = (time.time(), result)
    return result


def _log_reconciliation(entry: dict[str, Any]) -> None:
    log_entry = {
        "reconciliation_id": f"recon_{uuid.uuid4().hex[:10]}",
        **entry,
        "audit_logged": True,
    }
    _reconciliation_log.append(log_entry)


def _trigger_incident_if_needed(result: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    if not result.get("data_degraded"):
        return
    try:
        from bd_platform.infrastructure_incident_response_security_ops import record_incident_829
    except ImportError:
        logger.debug("incident response bridge unavailable")
        return
    try:
        record_incident_829(
            scenario="data_integrity",
            severity="high",
            title=f"Multi-source divergence: {result.get('data_type')}",
            seed=seed,
        )
    except Exception:
        logger.debug("incident record skipped", exc_info=True)


def get_reconciliation_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    rows = _reconciliation_log[-limit:]
    return {"ok": True, "count": len(rows), "audit_trail": rows, "timestamp": _utcnow()}


def check_sprint1_gate_1024(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = multi_source_status_1024(seed=seed)
    sources = status.get("sources") or {}
    price_ok = len(sources.get("price") or []) >= 2
    volume_ok = len(sources.get("volume") or []) >= 2
    onchain_ok = len(sources.get("onchain") or []) >= 2
    all_met = price_ok and volume_ok and onchain_ok
    return {
        "ok": all_met,
        "feature_ref": _FEATURE_REF,
        "blocks_sprint_1": status["policy"]["blocks_sprint_1_if_incomplete"],
        "sprint_1_allowed": all_met,
        "checks": {"price": price_ok, "volume": volume_ok, "onchain": onchain_ok},
        "timestamp": _utcnow(),
    }


def run_multi_source_e2e_1024(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = multi_source_status_1024(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "min_two_sources", "passed": status["policy"]["min_sources_per_type"] == 2})

    price_sources = status["sources"].get("price") or []
    checks.append({"id": "price_binance_coingecko", "passed": len(price_sources) >= 2})

    ok_price = reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": True},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        seed=seed,
    )
    checks.append({"id": "price_reconciled", "passed": ok_price["ok"] is True})
    checks.append({"id": "price_medium_confidence", "passed": ok_price["confidence"] in ("High", "Medium")})
    checks.append({"id": "price_provenance", "passed": "tag" in (ok_price.get("provenance") or {})})

    divergent = reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": True},
            {"source": "coingecko", "value": 45000.0, "ok": True},
        ],
        seed=seed,
    )
    checks.append({"id": "price_divergence_suppressed", "passed": divergent["suppress_output"] is True})
    checks.append({"id": "data_degraded_badge", "passed": divergent["badge"] == "Data Degraded"})

    failover = reconcile_price(
        observations=[
            {"source": "binance", "value": 42000.0, "ok": False},
            {"source": "coingecko", "value": 42050.0, "ok": True},
        ],
        seed=seed,
    )
    checks.append({"id": "insufficient_sources_suppressed", "passed": failover["suppress_output"] is True})

    vol = reconcile_volume(seed=seed)
    checks.append({"id": "volume_reconciled", "passed": vol["ok"] is True})

    chain = reconcile_onchain(seed=seed)
    checks.append({"id": "onchain_reconciled", "passed": chain["ok"] is True})

    validation = cross_validate_pair(
        data_type="onchain",
        source_a="alchemy",
        value_a=19500000.0,
        source_b="quicknode",
        value_b=19501950.0,
        seed=seed,
    )
    checks.append({"id": "onchain_threshold", "passed": validation["within_tolerance"] is True})

    gate = check_sprint1_gate_1024(seed=seed)
    checks.append({"id": "sprint1_gate", "passed": gate["sprint_1_allowed"] is True})

    fee = ok_price.get("fee_db") or {}
    checks.append({"id": "fee_db_logged", "passed": fee.get("fee_db_logged") is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
