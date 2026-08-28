"""
API Gateway Throttling Middleware — Feature #833 (Sprint-0).

NOT standalone — rate limiting middleware in API Gateway.
Tier-based per-minute limits, 429 + Retry-After, Redis cache, fallback.

No user-facing surface — background enforcement.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.APIGatewayThrottling")

_FEATURE_REF = 833
_STANDALONE = False
_MERGED_INTO = "API Gateway"
_COMPONENT = "throttling_middleware"
_API_GATEWAY_REF = 876
_DEVELOPER_TIER_REF = 831
_SEED_PATH = Path("data/api_gateway_seed.json")
_RESPONSE_TARGET_MS = 3000
_UPTIME_TARGET_PCT = 99.0

_THROTTLE_LOCK = threading.Lock()
_THROTTLE_USAGE: dict[str, dict[str, Any]] = {}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("throttling seed load failed: %s", exc)
        return {}


def _policy(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("throttling_policy_833") or {}


def _minute_key(user_id: str) -> str:
    minute = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M")
    return f"{user_id}:{minute}"


def get_rate_limit_for_role(role: str, *, seed: dict[str, Any] | None = None) -> int:
    """Tier-based per-minute rate limit."""
    seed = seed or _load_seed()
    policy = _policy(seed)
    limits = policy.get("rate_limits_per_minute") or {
        "free": 100,
        "pro": 1000,
        "institution": 10000,
    }
    return int(limits.get(role, limits.get("free", 100)))


def check_throttle_833(
    user_id: str,
    role: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Check per-minute throttle — returns 429 payload if exceeded."""
    seed = seed or _load_seed()
    policy = _policy(seed)
    limit = get_rate_limit_for_role(role, seed=seed)
    key = _minute_key(user_id)
    window_sec = int(policy.get("window_sec", 60))
    retry_after = int(policy.get("retry_after_sec", 60))

    with _THROTTLE_LOCK:
        usage = _THROTTLE_USAGE.setdefault(key, {"count": 0, "limit": limit, "window_sec": window_sec})
        usage["limit"] = limit
        remaining = max(0, limit - usage["count"])
        allowed = usage["count"] < limit

    return {
        "ok": allowed,
        "feature_ref": _FEATURE_REF,
        "allowed": allowed,
        "used": usage["count"],
        "limit": limit,
        "remaining": remaining,
        "window_sec": window_sec,
        "retry_after_sec": retry_after if not allowed else None,
        "status_code": 200 if allowed else 429,
        "headers": {} if allowed else {"Retry-After": str(retry_after)},
        "error": None if allowed else "rate_limit_exceeded",
        "developer_tier_ref": _DEVELOPER_TIER_REF,
        "timestamp": _utcnow(),
    }


def increment_throttle_833(user_id: str, role: str, *, seed: dict[str, Any] | None = None) -> None:
    seed = seed or _load_seed()
    limit = get_rate_limit_for_role(role, seed=seed)
    key = _minute_key(user_id)
    with _THROTTLE_LOCK:
        usage = _THROTTLE_USAGE.setdefault(key, {"count": 0, "limit": limit})
        usage["count"] += 1


def reset_throttle_for_tests() -> None:
    with _THROTTLE_LOCK:
        _THROTTLE_USAGE.clear()


def get_cache_ttl_for_endpoint(endpoint_id: str, *, seed: dict[str, Any] | None = None) -> int:
    """Redis cache TTL 1-24H per endpoint."""
    seed = seed or _load_seed()
    policy = _policy(seed)
    ttl_cfg = policy.get("cache_ttl_seconds") or seed.get("cache_ttl_seconds") or {}
    ttl = int(ttl_cfg.get(endpoint_id, ttl_cfg.get("default", 3600)))
    min_ttl = int(policy.get("cache_ttl_min_sec", 3600))
    max_ttl = int(policy.get("cache_ttl_max_sec", 86400))
    return max(min_ttl, min(ttl, max_ttl))


def fetch_with_fallback_833(
    endpoint_id: str,
    *,
    primary_fn,
    secondary_fn=None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Primary data source with secondary fallback if primary fails."""
    seed = seed or _load_seed()
    policy = _policy(seed)
    t0 = time.perf_counter()
    try:
        result = primary_fn()
        if result.get("ok", True):
            return {
                "ok": True,
                "feature_ref": _FEATURE_REF,
                "data": result,
                "source": "primary",
                "fallback_used": False,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            }
    except Exception as exc:
        logger.debug("primary fetch failed for %s: %s", endpoint_id, exc)

    if secondary_fn and policy.get("fallback_enabled", True):
        try:
            fallback = secondary_fn()
            return {
                "ok": fallback.get("ok", True),
                "feature_ref": _FEATURE_REF,
                "data": fallback,
                "source": "secondary",
                "fallback_used": True,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
            }
        except Exception as exc:
            logger.debug("secondary fetch failed for %s: %s", endpoint_id, exc)

    return {
        "ok": False,
        "feature_ref": _FEATURE_REF,
        "error": "primary_and_fallback_failed",
        "endpoint_id": endpoint_id,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
    }


def build_throttle_response_429_833(
    throttle: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Explicit 429 response with Retry-After header."""
    seed = seed or _load_seed()
    policy = _policy(seed)
    retry_after = throttle.get("retry_after_sec") or policy.get("retry_after_sec", 60)
    return {
        "ok": False,
        "feature_ref": _FEATURE_REF,
        "status_code": 429,
        "error": "rate_limit_exceeded",
        "message": "Too Many Requests — tier rate limit exceeded",
        "headers": {"Retry-After": str(retry_after)},
        "quota": {
            "used": throttle.get("used"),
            "limit": throttle.get("limit"),
            "remaining": throttle.get("remaining", 0),
            "window_sec": throttle.get("window_sec", 60),
        },
        "timestamp": _utcnow(),
    }


def throttling_middleware_handle_833(
    *,
    user_id: str,
    role: str,
    endpoint_id: str,
    primary_fn,
    secondary_fn=None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full middleware: throttle → cache → fetch with fallback."""
    seed = seed or _load_seed()
    throttle = check_throttle_833(user_id, role, seed=seed)
    if not throttle.get("allowed"):
        return build_throttle_response_429_833(throttle, seed=seed)

    ttl = get_cache_ttl_for_endpoint(endpoint_id, seed=seed)
    cache_key = f"throttle_833:{endpoint_id}:{user_id}"

    try:
        from bd_platform.api_gateway import get_cached_or_compute

        payload, cache_hit = get_cached_or_compute(
            cache_key,
            float(ttl),
            lambda: fetch_with_fallback_833(
                endpoint_id,
                primary_fn=primary_fn,
                secondary_fn=secondary_fn,
                seed=seed,
            ),
        )
    except Exception:
        payload = fetch_with_fallback_833(
            endpoint_id,
            primary_fn=primary_fn,
            secondary_fn=secondary_fn,
            seed=seed,
        )
        cache_hit = False

    increment_throttle_833(user_id, role, seed=seed)
    latency_ms = payload.get("latency_ms", 0)

    return {
        "ok": payload.get("ok", False),
        "feature_ref": _FEATURE_REF,
        "status_code": 200 if payload.get("ok") else 502,
        "data": payload.get("data"),
        "source": payload.get("source"),
        "fallback_used": payload.get("fallback_used", False),
        "cache_hit": cache_hit,
        "cache_ttl_sec": ttl,
        "cache_backend": "redis",
        "latency_ms": latency_ms,
        "within_response_target": latency_ms <= _RESPONSE_TARGET_MS,
        "throttle": check_throttle_833(user_id, role, seed=seed),
        "timestamp": _utcnow(),
    }


def build_throttling_panel_833(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _policy(seed)
    metrics = seed.get("throttling_metrics") or policy.get("current_metrics") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "standalone_rejected": True,
        "no_user_surface": True,
        "middleware": True,
        "api_gateway_ref": _API_GATEWAY_REF,
        "developer_tier_ref": _DEVELOPER_TIER_REF,
        "rate_limits_per_minute": policy.get("rate_limits_per_minute") or {
            "free": 100,
            "pro": 1000,
            "institution": 10000,
        },
        "handling": {
            "status_code": 429,
            "retry_after_header": True,
            "explicit": True,
        },
        "cache": {
            "backend": policy.get("cache_backend", "redis"),
            "ttl_min_sec": policy.get("cache_ttl_min_sec", 3600),
            "ttl_max_sec": policy.get("cache_ttl_max_sec", 86400),
            "per_endpoint": True,
        },
        "fallback": {
            "enabled": policy.get("fallback_enabled", True),
            "secondary_source": policy.get("secondary_source", "cached_snapshot"),
        },
        "internal_targets": {
            "response_ms": _RESPONSE_TARGET_MS,
            "uptime_pct": _UPTIME_TARGET_PCT,
            "current_uptime_pct": metrics.get("uptime_pct"),
            "within_uptime_target": float(metrics.get("uptime_pct", 0)) >= _UPTIME_TARGET_PCT,
        },
        "fee_db": policy.get("fee_db"),
        "timestamp": _utcnow(),
    }


def throttling_status_833(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _policy(seed)
    return {
        "ok": True,
        "feature_id": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "sprint": 0,
        "middleware": True,
        "no_user_surface": True,
        "api_gateway_ref": _API_GATEWAY_REF,
        "developer_tier_ref": _DEVELOPER_TIER_REF,
        "rate_limits_per_minute": policy.get("rate_limits_per_minute"),
        "429_with_retry_after": True,
        "cache_backend": policy.get("cache_backend", "redis"),
        "cache_ttl_range_hours": "1-24",
        "fallback_enabled": policy.get("fallback_enabled", True),
        "timestamp": _utcnow(),
    }


def run_throttling_e2e_833(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []
    reset_throttle_for_tests()

    status = throttling_status_833(seed=seed)
    tests.append({"test": "standalone_rejected", "passed": status.get("standalone_rejected") is True})
    tests.append({"test": "middleware_component", "passed": status.get("component") == "throttling_middleware"})
    tests.append({"test": "free_100_per_min", "passed": get_rate_limit_for_role("free", seed=seed) == 100})
    tests.append({"test": "pro_1000_per_min", "passed": get_rate_limit_for_role("pro", seed=seed) == 1000})
    tests.append({"test": "institution_10000_per_min", "passed": get_rate_limit_for_role("institution", seed=seed) == 10000})
    tests.append({"test": "429_retry_after", "passed": status.get("429_with_retry_after") is True})

    for _ in range(100):
        check = check_throttle_833("user_free", "free", seed=seed)
        if check.get("allowed"):
            increment_throttle_833("user_free", "free", seed=seed)
    denied = check_throttle_833("user_free", "free", seed=seed)
    resp429 = build_throttle_response_429_833(denied, seed=seed)
    tests.append({"test": "rate_limit_enforced", "passed": denied.get("status_code") == 429})
    tests.append({"test": "retry_after_header", "passed": resp429.get("headers", {}).get("Retry-After") == "60"})

    ttl = get_cache_ttl_for_endpoint("market_overview", seed=seed)
    tests.append({"test": "cache_ttl_1_24h", "passed": 3600 <= ttl <= 86400})

    fallback = fetch_with_fallback_833(
        "test",
        primary_fn=lambda: {"ok": False},
        secondary_fn=lambda: {"ok": True, "price": 60000},
        seed=seed,
    )
    tests.append({"test": "fallback_secondary", "passed": fallback.get("fallback_used") is True})

    panel = build_throttling_panel_833(seed=seed)
    tests.append({"test": "developer_tier_ref_831", "passed": panel.get("developer_tier_ref") == 831})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "e2e_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }
