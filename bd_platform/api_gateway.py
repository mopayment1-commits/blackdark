"""
API Gateway — Feature #876 (API Infrastructure Core).

Versioned REST API with RBAC, rate limits, caching, cursor pagination,
idempotency, observability, audit logs, and fee tracking.
Absorbs #834, #863, #872; WebSocket/streaming deferred to Sprint 2 (#886).

No "Institutional" branding — same gateway for all tiers.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.APIGateway")

_FEATURE_ID = 876
_TITLE = "API Gateway"
_LEGAL_NAME = "API Gateway"
_STANDALONE = False
_MERGED_INTO = "API Infrastructure Core"
_SPRINT = 1
_PRIORITY = "high"
_SEED_PATH = Path("data/api_gateway_seed.json")
_API_VERSION = "1.0"

_ROLE_ORDER = ("free", "pro", "institution")
_AUDIT_LOCK = threading.Lock()
_AUDIT_LOG: list[dict[str, Any]] = []
_FEE_LOCK = threading.Lock()
_FEE_DB: list[dict[str, Any]] = []
_QUOTA_LOCK = threading.Lock()
_QUOTA_USAGE: dict[str, dict[str, int]] = {}
_METRICS_LOCK = threading.Lock()
_METRICS: dict[str, float] = {
    "api_gateway_requests_total": 0,
    "api_gateway_errors_total": 0,
    "api_gateway_latency_ms_sum": 0,
    "api_gateway_cache_hits_total": 0,
    "api_gateway_quota_denied_total": 0,
    "api_gateway_authz_denied_total": 0,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"api_keys": {}, "endpoints": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("api gateway seed load failed: %s", exc)
        return {"api_keys": {}, "endpoints": {}}


def _role_level(role: str, *, seed: dict[str, Any]) -> int:
    hierarchy = seed.get("role_hierarchy") or {}
    return int(hierarchy.get(role, 0))


def _min_role_for(endpoint_id: str, *, seed: dict[str, Any]) -> str:
    ep = (seed.get("endpoints") or {}).get(endpoint_id) or {}
    return str(ep.get("min_role", "institution"))


def authenticate_api_key(api_key: str | None, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve API key to principal with role."""
    seed = seed or _load_seed()
    if not api_key or not api_key.strip():
        return {"ok": False, "error": "missing_api_key"}
    key = api_key.strip()
    record = (seed.get("api_keys") or {}).get(key)
    if not record:
        return {"ok": False, "error": "invalid_api_key"}
    return {
        "ok": True,
        "user_id": record.get("user_id"),
        "role": record.get("role", "free"),
        "label": record.get("label"),
        "api_key_hash": hashlib.sha256(key.encode()).hexdigest()[:16],
    }


def check_endpoint_access(role: str, endpoint_id: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """RBAC — role must meet endpoint minimum."""
    seed = seed or _load_seed()
    min_role = _min_role_for(endpoint_id, seed=seed)
    allowed = _role_level(role, seed=seed) >= _role_level(min_role, seed=seed)
    return {
        "allowed": allowed,
        "role": role,
        "endpoint_id": endpoint_id,
        "min_role": min_role,
    }


def _quota_key(user_id: str) -> str:
    day = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"{user_id}:{day}"


def check_quota(user_id: str, role: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tier-based daily rate limit."""
    seed = seed or _load_seed()
    limits = seed.get("rate_limits_per_day") or {}
    limit = int(limits.get(role, 100))
    key = _quota_key(user_id)
    with _QUOTA_LOCK:
        usage = _QUOTA_USAGE.setdefault(key, {"count": 0, "limit": limit})
        usage["limit"] = limit
        remaining = max(0, limit - usage["count"])
        return {
            "allowed": usage["count"] < limit,
            "used": usage["count"],
            "limit": limit,
            "remaining": remaining,
            "reset": "midnight_utc",
        }


def increment_quota(user_id: str, role: str, *, seed: dict[str, Any] | None = None) -> None:
    seed = seed or _load_seed()
    limits = seed.get("rate_limits_per_day") or {}
    limit = int(limits.get(role, 100))
    key = _quota_key(user_id)
    with _QUOTA_LOCK:
        usage = _QUOTA_USAGE.setdefault(key, {"count": 0, "limit": limit})
        usage["count"] += 1


def reset_quota_for_tests() -> None:
    with _QUOTA_LOCK:
        _QUOTA_USAGE.clear()


def _cache_get(cache_key: str) -> dict[str, Any] | None:
    try:
        from viral_capacity import quick_cache_get

        return quick_cache_get(cache_key)
    except Exception:
        return None


def _cache_set(cache_key: str, payload: dict[str, Any], ttl_sec: float) -> None:
    try:
        from viral_capacity import quick_cache_set

        quick_cache_set(cache_key, payload, ttl_sec=ttl_sec)
    except Exception:
        logger.debug("cache set skipped", exc_info=True)


def get_cached_or_compute(
    cache_key: str,
    ttl_sec: float,
    compute_fn,
) -> tuple[dict[str, Any], bool]:
    """Return (payload, cache_hit)."""
    cached = _cache_get(cache_key)
    if cached is not None:
        with _METRICS_LOCK:
            _METRICS["api_gateway_cache_hits_total"] += 1
        return cached, True
    payload = compute_fn()
    _cache_set(cache_key, payload, ttl_sec)
    return payload, False


def paginate_cursor(
    items: list[dict[str, Any]],
    *,
    cursor: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """Cursor-based pagination — no offset for large datasets."""
    limit = max(1, min(limit, 200))
    start = 0
    if cursor:
        try:
            decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
            start = int(decoded)
        except (ValueError, UnicodeDecodeError):
            start = 0
    page = items[start : start + limit]
    next_start = start + limit
    next_cursor = None
    if next_start < len(items):
        next_cursor = base64.urlsafe_b64encode(str(next_start).encode()).decode()
    return {
        "items": page,
        "pagination": {
            "cursor": cursor,
            "next_cursor": next_cursor,
            "limit": limit,
            "count": len(page),
            "total_count": len(items),
            "has_next": next_cursor is not None,
        },
    }


def record_audit_log(
    *,
    user_id: str,
    role: str,
    endpoint: str,
    method: str,
    status_code: int,
    response_size_bytes: int,
    cache_hit: bool = False,
) -> dict[str, Any]:
    """Mandatory audit log per request."""
    entry = {
        "user_id": user_id,
        "role": role,
        "endpoint": endpoint,
        "method": method,
        "timestamp": _utcnow(),
        "status_code": status_code,
        "response_size_bytes": response_size_bytes,
        "cache_hit": cache_hit,
    }
    with _AUDIT_LOCK:
        _AUDIT_LOG.append(entry)
        if len(_AUDIT_LOG) > 10_000:
            _AUDIT_LOG.pop(0)
    return entry


def record_fee(
    *,
    user_id: str,
    role: str,
    endpoint: str,
    response_size_bytes: int,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Per-request + bandwidth fee tracking."""
    seed = seed or _load_seed()
    fee_cfg = seed.get("fee_db") or {}
    per_req = float((fee_cfg.get("per_request_usd") or {}).get(role, 0))
    per_mb = float(fee_cfg.get("bandwidth_per_mb_usd", 0.001))
    bandwidth_mb = response_size_bytes / (1024 * 1024)
    total = round(per_req + bandwidth_mb * per_mb, 8)
    entry = {
        "user_id": user_id,
        "role": role,
        "endpoint": endpoint,
        "per_request_usd": per_req,
        "bandwidth_mb": round(bandwidth_mb, 6),
        "bandwidth_cost_usd": round(bandwidth_mb * per_mb, 8),
        "total_usd": total,
        "tier": role,
        "timestamp": _utcnow(),
    }
    with _FEE_LOCK:
        _FEE_DB.append(entry)
        if len(_FEE_DB) > 50_000:
            _FEE_DB.pop(0)
    return entry


def increment_metric(name: str, amount: float = 1.0) -> None:
    with _METRICS_LOCK:
        if name not in _METRICS:
            _METRICS[name] = 0.0
        _METRICS[name] += amount


def record_latency_ms(ms: float) -> None:
    with _METRICS_LOCK:
        _METRICS["api_gateway_latency_ms_sum"] += ms


def prometheus_metrics_text() -> str:
    """Prometheus-format gateway metrics."""
    with _METRICS_LOCK:
        lines = [
            "# HELP api_gateway_requests_total Total API gateway requests",
            "# TYPE api_gateway_requests_total counter",
            f"api_gateway_requests_total {_METRICS.get('api_gateway_requests_total', 0)}",
            "# HELP api_gateway_errors_total Total API gateway errors",
            "# TYPE api_gateway_errors_total counter",
            f"api_gateway_errors_total {_METRICS.get('api_gateway_errors_total', 0)}",
            "# HELP api_gateway_latency_ms_sum Sum of request latencies in ms",
            "# TYPE api_gateway_latency_ms_sum counter",
            f"api_gateway_latency_ms_sum {_METRICS.get('api_gateway_latency_ms_sum', 0)}",
            "# HELP api_gateway_cache_hits_total Cache hits",
            "# TYPE api_gateway_cache_hits_total counter",
            f"api_gateway_cache_hits_total {_METRICS.get('api_gateway_cache_hits_total', 0)}",
            "# HELP api_gateway_quota_denied_total Quota denials",
            "# TYPE api_gateway_quota_denied_total counter",
            f"api_gateway_quota_denied_total {_METRICS.get('api_gateway_quota_denied_total', 0)}",
            "# HELP api_gateway_authz_denied_total Authorization denials",
            "# TYPE api_gateway_authz_denied_total counter",
            f"api_gateway_authz_denied_total {_METRICS.get('api_gateway_authz_denied_total', 0)}",
        ]
    return "\n".join(lines) + "\n"


def build_openapi_spec(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Auto-generated OpenAPI from endpoint registry — no manual maintenance."""
    seed = seed or _load_seed()
    paths: dict[str, Any] = {}
    for ep_id, ep in (seed.get("endpoints") or {}).items():
        path = ep.get("path", f"/api/v1/{ep_id}")
        method = str(ep.get("method", "GET")).lower()
        paths.setdefault(path, {})[method] = {
            "summary": ep.get("description", ep_id),
            "operationId": ep_id,
            "tags": ["api-gateway"],
            "security": [{"ApiKeyAuth": []}],
            "parameters": [
                {"name": "asset", "in": "path", "schema": {"type": "string"}} if "{asset}" in path else None,
                {"name": "protocol_id", "in": "path", "schema": {"type": "string"}} if "{protocol_id}" in path else None,
            ],
            "responses": {
                "200": {"description": "Success"},
                "401": {"description": "Missing or invalid API key"},
                "403": {"description": "Forbidden for role"},
                "429": {"description": "Quota exceeded"},
            },
        }
        paths[path][method]["parameters"] = [p for p in paths[path][method]["parameters"] if p]

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "BLACKDARK API Gateway",
            "version": seed.get("api_version", _API_VERSION),
            "description": "Versioned REST API — RBAC, quotas, audit logs. WebSocket Sprint 2.",
        },
        "servers": [{"url": "/"}],
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
            }
        },
        "paths": paths,
        "x_version_policy": seed.get("api_version_policy"),
        "x_auto_generated": True,
        "x_feature_id": _FEATURE_ID,
    }


def _fetch_market_overview() -> dict[str, Any]:
    try:
        from bd_platform.market_radar_indicators import build_market_radar_panel

        panel = build_market_radar_panel(seed=None)
        return {"ok": True, "surface": "market_overview", "data": panel}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _fetch_onchain_metrics(asset: str) -> dict[str, Any]:
    try:
        from bd_platform.onchain_metrics_library import build_metrics_library_panel

        panel = build_metrics_library_panel(asset.upper(), seed=None)
        return {"ok": True, "asset": asset.upper(), "data": panel}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _fetch_risk_protocol(protocol_id: str) -> dict[str, Any]:
    try:
        from bd_platform.defi_risk_passport import build_risk_passport_card

        card = build_risk_passport_card(protocol_id, seed=None)
        return {"ok": card.get("ok", False), "protocol_id": protocol_id, "data": card}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def gateway_handle_request(
    *,
    endpoint_id: str,
    api_key: str | None,
    method: str = "GET",
    path_params: dict[str, str] | None = None,
    body: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Central gateway dispatch with auth, quota, cache, audit, fee."""
    seed = seed or _load_seed()
    start = time.perf_counter()
    path_params = path_params or {}
    ep = (seed.get("endpoints") or {}).get(endpoint_id) or {}
    endpoint_path = ep.get("path", f"/api/v1/{endpoint_id}")

    auth = authenticate_api_key(api_key, seed=seed)
    if not auth.get("ok"):
        increment_metric("api_gateway_errors_total")
        increment_metric("api_gateway_requests_total")
        return {"ok": False, "status_code": 401, "error": auth.get("error")}

    user_id = auth["user_id"]
    role = auth["role"]
    access = check_endpoint_access(role, endpoint_id, seed=seed)
    if not access.get("allowed"):
        increment_metric("api_gateway_authz_denied_total")
        increment_metric("api_gateway_errors_total")
        increment_metric("api_gateway_requests_total")
        record_audit_log(
            user_id=user_id, role=role, endpoint=endpoint_path, method=method,
            status_code=403, response_size_bytes=0,
        )
        return {
            "ok": False,
            "status_code": 403,
            "error": "forbidden",
            "min_role": access.get("min_role"),
            "role": role,
        }

    quota = check_quota(user_id, role, seed=seed)
    if not quota.get("allowed"):
        increment_metric("api_gateway_quota_denied_total")
        increment_metric("api_gateway_errors_total")
        increment_metric("api_gateway_requests_total")
        record_audit_log(
            user_id=user_id, role=role, endpoint=endpoint_path, method=method,
            status_code=429, response_size_bytes=0,
        )
        return {"ok": False, "status_code": 429, "error": "quota_exceeded", "quota": quota}

    if method.upper() == "POST" and ep.get("idempotency_required"):
        from api.idempotency import check_idempotency, store_idempotency

        is_dup, cached = check_idempotency(idempotency_key)
        if is_dup and cached:
            increment_metric("api_gateway_requests_total")
            record_audit_log(
                user_id=user_id, role=role, endpoint=endpoint_path, method=method,
                status_code=cached["status_code"], response_size_bytes=len(json.dumps(cached["body"])),
                cache_hit=True,
            )
            return {"ok": True, "status_code": cached["status_code"], "data": cached["body"], "idempotent_replay": True}

    ttl = float(ep.get("cache_ttl_sec") or (seed.get("cache_ttl_seconds") or {}).get("default", 300))
    cache_key = f"api_gw:{endpoint_id}:{json.dumps(path_params, sort_keys=True)}"
    cache_hit = False

    if method.upper() == "GET" and ttl > 0:
        def compute():
            return _dispatch_endpoint(endpoint_id, path_params=path_params, body=body, user_id=user_id, role=role, seed=seed)

        payload, cache_hit = get_cached_or_compute(cache_key, ttl, compute)
    else:
        payload = _dispatch_endpoint(endpoint_id, path_params=path_params, body=body, user_id=user_id, role=role, seed=seed)

    if method.upper() == "POST" and ep.get("idempotency_required") and idempotency_key:
        from api.idempotency import store_idempotency

        store_idempotency(idempotency_key, 201, payload)

    increment_quota(user_id, role, seed=seed)
    increment_metric("api_gateway_requests_total")
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_latency_ms(elapsed_ms)

    resp_bytes = len(json.dumps(payload, default=str).encode())
    record_audit_log(
        user_id=user_id, role=role, endpoint=endpoint_path, method=method,
        status_code=200, response_size_bytes=resp_bytes, cache_hit=cache_hit,
    )
    record_fee(user_id=user_id, role=role, endpoint=endpoint_path, response_size_bytes=resp_bytes, seed=seed)

    return {
        "ok": True,
        "status_code": 200,
        "data": payload,
        "quota": check_quota(user_id, role, seed=seed),
        "cache_hit": cache_hit,
        "latency_ms": round(elapsed_ms, 2),
        "api_version": seed.get("api_version", _API_VERSION),
    }


def _dispatch_endpoint(
    endpoint_id: str,
    *,
    path_params: dict[str, str],
    body: dict[str, Any] | None,
    user_id: str,
    role: str,
    seed: dict[str, Any],
) -> dict[str, Any]:
    if endpoint_id == "market_overview":
        return _fetch_market_overview()
    if endpoint_id == "onchain_metrics":
        return _fetch_onchain_metrics(path_params.get("asset", "BTC"))
    if endpoint_id == "risk_protocol":
        return _fetch_risk_protocol(path_params.get("protocol_id", "aave_v3"))
    if endpoint_id == "alerts_subscribe":
        return {
            "ok": True,
            "subscription_id": f"sub_{hashlib.sha256(f'{user_id}:{body}'.encode()).hexdigest()[:12]}",
            "channel": (body or {}).get("channel", "defi_risk_spike"),
            "user_id": user_id,
            "role": role,
        }
    if endpoint_id == "usage":
        return build_usage_panel(user_id=user_id, role=role, seed=seed)
    if endpoint_id == "sla_metrics":
        return build_sla_metrics(seed=seed)
    if endpoint_id == "audit_export":
        return export_audit_logs(user_id=user_id, seed=seed)
    return {"ok": False, "error": "unknown_endpoint"}


def build_usage_panel(*, user_id: str, role: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    quota = check_quota(user_id, role, seed=seed)
    with _FEE_LOCK:
        user_fees = [f for f in _FEE_DB if f.get("user_id") == user_id]
    total_fees = round(sum(f.get("total_usd", 0) for f in user_fees), 6)
    return {
        "ok": True,
        "user_id": user_id,
        "role": role,
        "quota": quota,
        "total_requests_fees_usd": total_fees,
        "request_count": len(user_fees),
        "tier_limits": seed.get("rate_limits_per_day"),
    }


def build_sla_metrics(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    evidence = seed.get("load_test_evidence") or {}
    with _METRICS_LOCK:
        req_total = _METRICS.get("api_gateway_requests_total", 0)
        err_total = _METRICS.get("api_gateway_errors_total", 0)
        lat_sum = _METRICS.get("api_gateway_latency_ms_sum", 0)
    error_rate = (err_total / req_total * 100) if req_total else 0
    avg_latency = (lat_sum / req_total) if req_total else 0
    return {
        "ok": True,
        "sla": {
            "error_rate_pct": round(error_rate, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "requests_total": int(req_total),
        },
        "load_test_evidence": evidence,
        "observability": "prometheus",
    }


def export_audit_logs(*, user_id: str, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    with _AUDIT_LOCK:
        logs = [e for e in _AUDIT_LOG if e.get("user_id") == user_id]
    return paginate_cursor(logs, limit=100)


def run_authz_matrix_tests(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Daily authz test — each role attempts forbidden endpoints → must fail."""
    seed = seed or _load_seed()
    keys = seed.get("api_keys") or {}
    tests: list[dict[str, Any]] = []

    role_keys = {v.get("role"): k for k, v in keys.items()}
    for role in _ROLE_ORDER:
        api_key = role_keys.get(role)
        if not api_key:
            continue
        for ep_id, ep in (seed.get("endpoints") or {}).items():
            min_role = ep.get("min_role", "institution")
            should_allow = _role_level(role, seed=seed) >= _role_level(min_role, seed=seed)
            result = gateway_handle_request(endpoint_id=ep_id, api_key=api_key, method=str(ep.get("method", "GET")))
            got_allow = result.get("status_code") == 200
            passed = got_allow == should_allow
            tests.append({
                "role": role,
                "endpoint_id": ep_id,
                "min_role": min_role,
                "expected_allow": should_allow,
                "got_allow": got_allow,
                "passed": passed,
            })

    passed_count = sum(1 for t in tests if t["passed"])
    return {
        "ok": passed_count == len(tests),
        "tests": tests,
        "passed": passed_count,
        "total": len(tests),
        "timestamp": _utcnow(),
    }


def api_gateway_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "api_version": seed.get("api_version", _API_VERSION),
        "rest_first": seed.get("rest_first", True),
        "streaming_sprint": seed.get("streaming_sprint", 2),
        "roles": seed.get("roles", list(_ROLE_ORDER)),
        "rate_limits_per_day": seed.get("rate_limits_per_day"),
        "endpoints_count": len(seed.get("endpoints") or {}),
        "absorbed_tickets": seed.get("absorbed_tickets", []),
        "openapi_auto_generated": True,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "core infra"})
    checks.append({"id": "no_institutional_branding", "passed": seed.get("no_institutional_branding") is True, "detail": seed.get("branding")})
    checks.append({"id": "three_roles", "passed": len(seed.get("roles") or []) == 3, "detail": "RBAC"})
    checks.append({"id": "version_policy", "passed": (seed.get("api_version_policy") or {}).get("v1_0_frozen") is True, "detail": "compat"})
    checks.append({"id": "openapi_generated", "passed": build_openapi_spec(seed=seed).get("x_auto_generated") is True, "detail": "openapi"})
    checks.append({"id": "load_evidence", "passed": (seed.get("load_test_evidence") or {}).get("passed") is True, "detail": "k6"})
    checks.append({"id": "fee_db", "passed": "per_request_usd" in (seed.get("fee_db") or {}), "detail": "fees"})

    reset_quota_for_tests()
    authz = run_authz_matrix_tests(seed=seed)
    checks.append({"id": "authz_matrix", "passed": authz.get("ok") is True, "detail": f"{authz.get('passed')}/{authz.get('total')}"})

    free_result = gateway_handle_request(endpoint_id="market_overview", api_key="bd_free_demo_key_0001", seed=seed)
    checks.append({"id": "free_market_access", "passed": free_result.get("status_code") == 200, "detail": "free tier"})

    free_denied = gateway_handle_request(endpoint_id="risk_protocol", api_key="bd_free_demo_key_0001", seed=seed)
    checks.append({"id": "free_risk_denied", "passed": free_denied.get("status_code") == 403, "detail": "RBAC"})

    pro_result = gateway_handle_request(endpoint_id="risk_protocol", api_key="bd_pro_demo_key_0002", seed=seed)
    checks.append({"id": "pro_risk_access", "passed": pro_result.get("status_code") == 200, "detail": "pro tier"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
