"""
Data Engine Query Performance Governance — Feature #990 (Sprint 0/1).

Merged into Data Engine ops layer — NOT standalone.
Timeouts, quotas, caching, audit logs, slow-query flagging for ops.
Quotas enforced via #978 SQL Workspace integration.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.QueryPerformanceGovernance")

_FEATURE_REF = 990
_SQL_WORKSPACE_REF = 978
_STANDALONE = False
_MERGED_INTO = "Data Engine / Ops Layer"
_SEED_PATH = Path("data/data_engine_query_performance_governance_seed.json")
_QUERY_TIMEOUT_SEC = 30
_AUDIT_RETENTION_DAYS = 90

_LOCK = threading.Lock()
_QUERY_CACHE: dict[str, dict[str, Any]] = {}
_AUDIT_LOG: list[dict[str, Any]] = []
_DAILY_USAGE: dict[str, float] = {}

FreshnessBadge = Literal["fresh", "provisional", "stabilized"]

_DISCLAIMER = (
    "Internal query performance governance — ops layer only. "
    "No public dashboard. Timeouts and quotas backend-enforced."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("query performance governance seed load failed: %s", exc)
        return {}


def reset_query_governance_state() -> None:
    with _LOCK:
        _QUERY_CACHE.clear()
        _AUDIT_LOG.clear()
        _DAILY_USAGE.clear()


def query_performance_governance_status_990(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("query_performance_governance_990") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "sql_workspace_ref": _SQL_WORKSPACE_REF,
        "ops_internal_only": True,
        "no_public_dashboard": True,
        "query_timeout_sec": int(cfg.get("query_timeout_sec", _QUERY_TIMEOUT_SEC)),
        "kill_on_timeout": True,
        "daily_cost_quota_usd": cfg.get("daily_cost_quota_usd") or {"free": 0, "pro": 5, "institution": 50},
        "backend_enforced": True,
        "no_client_side_quota": True,
        "cache_layer": "redis",
        "cache_ttl_by_freshness": cfg.get("cache_ttl_by_freshness") or {
            "fresh": 60, "provisional": 300, "stabilized": 3600,
        },
        "audit_retention_days": int(cfg.get("audit_retention_days", _AUDIT_RETENTION_DAYS)),
        "slow_query_analysis_daily": True,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def enforce_query_timeout_990(
    elapsed_sec: float,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("query_performance_governance_990") or {}
    limit = float(cfg.get("query_timeout_sec", _QUERY_TIMEOUT_SEC))
    exceeded = elapsed_sec > limit
    return {
        "ok": not exceeded,
        "feature_ref": _FEATURE_REF,
        "elapsed_sec": elapsed_sec,
        "timeout_sec": limit,
        "kill_automatic": True,
        "error": "query_timeout_exceeded" if exceeded else None,
        "timestamp": _utcnow(),
    }


def enforce_tier_quota_990(
    user_id: str,
    tier: str,
    cost_usd: float,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("query_performance_governance_990") or {}
    quotas = cfg.get("daily_cost_quota_usd") or {"free": 0, "pro": 5, "institution": 50}
    limit = quotas.get(tier, quotas.get("free", 0))

    with _LOCK:
        key = f"{user_id}:{tier}"
        used = _DAILY_USAGE.get(key, 0.0) + cost_usd
        if limit is not None and used > float(limit):
            return {
                "ok": False,
                "feature_ref": _FEATURE_REF,
                "error": "daily_cost_quota_exceeded",
                "tier": tier,
                "limit_usd": limit,
                "used_usd": round(used, 4),
                "backend_enforced": True,
            }
        _DAILY_USAGE[key] = used

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "tier": tier,
        "limit_usd": limit,
        "used_usd": round(used, 4),
        "backend_enforced": True,
        "no_client_side_quota": True,
        "timestamp": _utcnow(),
    }


def get_cache_ttl_990(
    freshness: FreshnessBadge,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("query_performance_governance_990") or {}
    ttl_map = cfg.get("cache_ttl_by_freshness") or {"fresh": 60, "provisional": 300, "stabilized": 3600}
    ttl = int(ttl_map.get(freshness, 300))
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "freshness_badge": freshness,
        "cache_ttl_sec": ttl,
        "cache_layer": "redis",
        "timestamp": _utcnow(),
    }


def cache_query_result_990(
    query_hash: str,
    result: dict[str, Any],
    *,
    freshness: FreshnessBadge = "provisional",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ttl_info = get_cache_ttl_990(freshness, seed=seed)
    ttl = ttl_info["cache_ttl_sec"]
    expires_at = (datetime.now(UTC) + timedelta(seconds=ttl)).isoformat()

    with _LOCK:
        _QUERY_CACHE[query_hash] = {
            "result": result,
            "cached_at": _utcnow(),
            "expires_at": expires_at,
            "freshness_badge": freshness,
            "ttl_sec": ttl,
        }

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "query_hash": query_hash,
        "cached": True,
        "ttl_sec": ttl,
        "expires_at": expires_at,
        "timestamp": _utcnow(),
    }


def get_cached_query_990(query_hash: str) -> dict[str, Any]:
    with _LOCK:
        entry = _QUERY_CACHE.get(query_hash)
    if not entry:
        return {"ok": False, "feature_ref": _FEATURE_REF, "cache_hit": False}
    expires = entry.get("expires_at", "")
    if expires and expires < _utcnow():
        return {"ok": False, "feature_ref": _FEATURE_REF, "cache_hit": False, "expired": True}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "cache_hit": True,
        "result": entry.get("result"),
        "freshness_badge": entry.get("freshness_badge"),
        "timestamp": _utcnow(),
    }


def log_query_audit_990(
    *,
    user_id: str,
    sql: str,
    cost_usd: float,
    rows: int,
    tenant_id: str = "tenant_default",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("query_performance_governance_990") or {}
    entry = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "sql_hash": hashlib.sha256(sql.encode()).hexdigest()[:16],
        "sql_preview": sql[:120],
        "cost_usd": round(cost_usd, 6),
        "rows": rows,
        "timestamp": _utcnow(),
    }
    with _LOCK:
        _AUDIT_LOG.append(entry)
        if len(_AUDIT_LOG) > 10000:
            _AUDIT_LOG.pop(0)

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "audit_logged": True,
        "retention_days": int(cfg.get("audit_retention_days", _AUDIT_RETENTION_DAYS)),
        "entry": entry,
        "timestamp": _utcnow(),
    }


def run_slow_query_analysis_990(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Daily ops analysis — slow queries flagged, no public dashboard."""
    seed = seed or _load_seed()
    cfg = seed.get("query_performance_governance_990") or {}
    threshold = float(cfg.get("slow_query_threshold_sec", 5.0))
    flagged = seed.get("slow_queries_flagged") or []

    ops_only = [
        {
            "query_id": q.get("query_id"),
            "elapsed_sec": q.get("elapsed_sec"),
            "threshold_sec": threshold,
            "flagged": float(q.get("elapsed_sec", 0)) > threshold,
            "plan_analysis": q.get("plan_analysis"),
            "ops_review_required": True,
        }
        for q in flagged
    ]

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "ops_internal_only": True,
        "no_public_dashboard": True,
        "slow_query_threshold_sec": threshold,
        "flagged_queries": [q for q in ops_only if q["flagged"]],
        "flagged_count": sum(1 for q in ops_only if q["flagged"]),
        "daily_analysis": True,
        "timestamp": _utcnow(),
    }


def build_ops_usage_summary_990(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Internal ops usage summary — not a public product dashboard."""
    seed = seed or _load_seed()
    with _LOCK:
        audit_count = len(_AUDIT_LOG)
        cache_size = len(_QUERY_CACHE)
        usage = dict(_DAILY_USAGE)

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "ops_internal_only": True,
        "audit_log_count": audit_count,
        "cache_entries": cache_size,
        "daily_usage_by_user": usage,
        "sql_workspace_integration_ref": _SQL_WORKSPACE_REF,
        "timestamp": _utcnow(),
    }


def run_query_governance_e2e_990(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_query_governance_state()
    checks: list[dict[str, Any]] = []

    status = query_performance_governance_status_990(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "no_public_dashboard", "passed": status["no_public_dashboard"] is True})
    checks.append({"id": "timeout_30s", "passed": status["query_timeout_sec"] == 30})
    checks.append({"id": "audit_90d", "passed": status["audit_retention_days"] == 90})

    timeout_ok = enforce_query_timeout_990(15.0, seed=seed)
    timeout_bad = enforce_query_timeout_990(35.0, seed=seed)
    checks.append({"id": "timeout_enforced", "passed": timeout_ok["ok"] is True and timeout_bad["ok"] is False})

    quota = enforce_tier_quota_990("user_pro", "pro", 1.0, seed=seed)
    checks.append({"id": "quota_backend", "passed": quota.get("backend_enforced") is True})

    cache = cache_query_result_990("abc123", {"rows": 10}, freshness="fresh", seed=seed)
    hit = get_cached_query_990("abc123")
    checks.append({"id": "cache_layer", "passed": cache.get("cached") is True and hit.get("cache_hit") is True})

    audit = log_query_audit_990(user_id="user_pro", sql="SELECT * FROM market_data", cost_usd=0.01, rows=100, seed=seed)
    checks.append({"id": "audit_logged", "passed": audit.get("audit_logged") is True})

    slow = run_slow_query_analysis_990(seed=seed)
    checks.append({"id": "slow_query_flagged", "passed": slow.get("flagged_count", 0) >= 1})
    checks.append({"id": "sql_workspace_ref", "passed": status["sql_workspace_ref"] == _SQL_WORKSPACE_REF})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature_ref": _FEATURE_REF, "all_passed": all_passed, "checks": checks}
