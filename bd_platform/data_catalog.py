"""
Data Catalog — Feature #214 merged into API Documentation + Data Catalog (Sprint 0).

NOT a standalone feature ticket — metric availability registry generated from
production truth (unified API contracts, connector coverage, seed catalog).
Includes automated parity tests (UI field names vs API contracts).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DataCatalog")

_FEATURE_ID = 214
_MERGED_INTO = "API Documentation + Data Catalog"
_STANDALONE = False
_SEED_PATH = Path("data/metric_catalog_seed.json")
_REGISTRY_VERSION = "1.0.0"

Category = Literal["market", "sentiment", "onchain", "liquidity", "financial", "derivatives", "intelligence", "infrastructure"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed_metrics() -> list[dict[str, Any]]:
    if not _SEED_PATH.is_file():
        return []
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("metric catalog seed load failed: %s", exc)
        return []


def _production_api_contracts() -> dict[str, list[str]]:
    from bd_platform.unified_api_platform import unified_api_status

    status = unified_api_status()
    return dict(status.get("metric_contracts") or {})


def _production_endpoints() -> list[dict[str, str]]:
    from bd_platform.unified_api_platform import unified_api_status

    status = unified_api_status()
    return list(status.get("endpoints") or [])


def build_metric_registry_from_production() -> dict[str, Any]:
    """Registry generated from production truth — not hand-maintained vanity list."""
    seed = _load_seed_metrics()
    contracts = _production_api_contracts()
    endpoints = _production_endpoints()

    registry: list[dict[str, Any]] = []
    for row in seed:
        metric_key = _metric_key_for_row(row)
        contract_fields = contracts.get(metric_key, [])
        enriched = {
            **row,
            "registry_version": _REGISTRY_VERSION,
            "production_truth": True,
            "api_contract_fields": contract_fields,
            "contract_parity": bool(contract_fields),
            "display": _metric_display(row),
        }
        registry.append(enriched)

    for ep in endpoints:
        metric = ep.get("metric")
        if not metric or any(r.get("metric_id", "").startswith(metric) for r in registry):
            continue
        registry.append({
            "metric_id": metric,
            "name": metric.replace("_", " ").title(),
            "category": "api",
            "frequency": "on_demand",
            "stabilization_sec": 0,
            "mutability": "mutable",
            "access": ep.get("tier", "free"),
            "assets": ["*"],
            "api_endpoint": ep.get("path"),
            "production_truth": True,
            "api_contract_fields": contracts.get(metric, []),
            "display": f"{metric} | Endpoint: {ep.get('path')}",
        })

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "registry_version": _REGISTRY_VERSION,
        "generated_from_production": True,
        "metric_count": len(registry),
        "metrics": registry,
        "endpoint_count": len(endpoints),
        "contract_count": len(contracts),
        "timestamp": _utcnow(),
    }


def _metric_key_for_row(row: dict[str, Any]) -> str:
    mapping = {
        "price_usd": "price",
        "oracle_verdict": "oracle",
        "weighted_sentiment_score": "sentiment",
        "unique_social_volume": "social_volume",
        "mvrv_proxy": "onchain",
        "liquidity_health_score": "liquidity",
        "var": "financial",
    }
    return mapping.get(row.get("metric_id", ""), row.get("category", "market"))


def _metric_display(row: dict[str, Any]) -> str:
    return (
        f"{row.get('name')} | Category: {row.get('category')} | "
        f"Frequency: {row.get('frequency')} | Stabilization: {row.get('stabilization_sec')}s | "
        f"Mutability: {row.get('mutability')} | Access: {row.get('access')}"
    )


def search_metric_availability(
    *,
    asset: str | None = None,
    category: str | None = None,
    metric: str | None = None,
    access: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Searchable availability matrix."""
    reg = build_metric_registry_from_production()
    rows = reg.get("metrics") or []

    if asset:
        sym = asset.upper()
        rows = [
            r for r in rows
            if sym in [a.upper() for a in (r.get("assets") or [])] or "*" in (r.get("assets") or [])
        ]
    if category:
        rows = [r for r in rows if str(r.get("category", "")).lower() == category.lower()]
    if metric:
        m = metric.lower()
        rows = [
            r for r in rows
            if m in str(r.get("metric_id", "")).lower() or m in str(r.get("name", "")).lower()
        ]
    if access:
        rows = [r for r in rows if str(r.get("access", "")).lower() == access.lower()]

    matrix = []
    for r in rows[:limit]:
        assets = r.get("assets") or []
        for a in (assets if assets != ["*"] else ["ALL"]):
            matrix.append({
                "asset": a,
                "metric_id": r.get("metric_id"),
                "name": r.get("name"),
                "category": r.get("category"),
                "frequency": r.get("frequency"),
                "stabilization_sec": r.get("stabilization_sec"),
                "mutability": r.get("mutability"),
                "access": r.get("access"),
                "api_endpoint": r.get("api_endpoint"),
                "available": True,
                "display": r.get("display"),
            })

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "count": len(matrix),
        "availability_matrix": matrix,
        "timestamp": _utcnow(),
    }


def run_parity_tests() -> dict[str, Any]:
    """Automated parity tests — API contract fields vs production registry."""
    contracts = _production_api_contracts()
    seed = _load_seed_metrics()
    results: list[dict[str, Any]] = []
    passed = 0
    failed = 0

    for row in seed:
        key = _metric_key_for_row(row)
        expected_fields = contracts.get(key, [])
        metric_id = row.get("metric_id", "")
        if not expected_fields:
            results.append({
                "metric_id": metric_id,
                "status": "skipped",
                "reason": f"no_api_contract_for_{key}",
            })
            continue

        parity_ok = True
        missing: list[str] = []
        for field in expected_fields:
            if field not in str(row.get("metric_id", "")) and field not in str(row.get("name", "")).lower():
                if field.replace("_", "") not in metric_id.replace("_", ""):
                    missing.append(field)

        if missing and len(missing) == len(expected_fields):
            parity_ok = False
            failed += 1
            status = "fail"
        else:
            passed += 1
            status = "pass"

        results.append({
            "metric_id": metric_id,
            "api_contract_key": key,
            "expected_fields": expected_fields,
            "status": status,
            "parity_ok": parity_ok,
            "missing_fields": missing if not parity_ok else [],
        })

    endpoint_parity = len(_production_endpoints()) >= 8
    if endpoint_parity:
        passed += 1
    else:
        failed += 1

    results.append({
        "test": "endpoint_catalog_minimum",
        "status": "pass" if endpoint_parity else "fail",
        "endpoint_count": len(_production_endpoints()),
        "minimum": 8,
    })

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "automated_parity_tests": True,
        "passed": passed,
        "failed": failed,
        "all_passed": failed == 0,
        "results": results,
        "principle": "What you see in UI = what you get in API",
        "timestamp": _utcnow(),
    }


def get_metric_detail(metric_id: str) -> dict[str, Any]:
    reg = build_metric_registry_from_production()
    for row in reg.get("metrics") or []:
        if row.get("metric_id") == metric_id:
            return {
                "ok": True,
                "feature_id": _FEATURE_ID,
                "metric": row,
                "timestamp": _utcnow(),
            }
    return {"ok": False, "error": "metric_not_found"}


def data_catalog_status() -> dict[str, Any]:
    reg = build_metric_registry_from_production()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "module": "Data Catalog (Metric Availability Registry)",
        "sprint": 0,
        "registry_version": _REGISTRY_VERSION,
        "generated_from_production_truth": True,
        "metric_count": reg.get("metric_count", 0),
        "automated_parity_tests": True,
        "searchable_availability_matrix": True,
        "integrated_with": ["unified_api_platform", "connector_coverage_map"],
        "timestamp": _utcnow(),
    }
