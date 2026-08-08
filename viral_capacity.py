"""
BLACKDARK — Viral launch capacity controls.

Protects the process under sudden concurrent traffic:
  · shared Redis (or memory) rate limits for Oracle / auth / API bursts
  · in-flight concurrency ceiling + load shedding (503)
  · Oracle compute semaphore (prevents stampedes on heavy path)
  · short-TTL cache for identical Oracle /quick bursts
  · honest readiness report (codepath ≠ signed HA proof)

English product surfaces remain Prove-it honest: Soft Launch SQLite is not viral HA.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import threading
import time
from collections import defaultdict
from typing import Any, Callable

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("BLACKDARK.ViralCapacity")

# Tunables (env-overridable)
VIRAL_MODE = os.getenv("VIRAL_MODE", "true").lower() in {"1", "true", "yes"}
MAX_INFLIGHT = int(os.getenv("VIRAL_MAX_INFLIGHT", "200"))
ORACLE_CONCURRENCY = int(os.getenv("VIRAL_ORACLE_CONCURRENCY", "32"))
ORACLE_RL_PER_MIN = int(os.getenv("VIRAL_ORACLE_RL_PER_MIN", "60"))
AUTH_RL_PER_MIN = int(os.getenv("VIRAL_AUTH_RL_PER_MIN", "30"))
API_RL_PER_MIN = int(os.getenv("VIRAL_API_RL_PER_MIN", "120"))
QUICK_CACHE_TTL_SEC = float(os.getenv("VIRAL_QUICK_CACHE_TTL_SEC", "2.0"))
SHED_RETRY_AFTER_SEC = int(os.getenv("VIRAL_SHED_RETRY_AFTER_SEC", "2"))

_inflight = 0
_inflight_lock = threading.Lock()
_oracle_sem: asyncio.Semaphore | None = None
_memory_buckets: dict[str, list[float]] = defaultdict(list)
_quick_cache: dict[str, tuple[float, dict[str, Any]]] = {}
_quick_lock = threading.Lock()
_redis = None
_redis_lock = threading.Lock()
_rl_backend = "memory"


def rate_limit_backend() -> str:
    return _rl_backend


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def get_oracle_semaphore() -> asyncio.Semaphore:
    global _oracle_sem
    if _oracle_sem is None:
        _oracle_sem = asyncio.Semaphore(max(1, _env_int("VIRAL_ORACLE_CONCURRENCY", ORACLE_CONCURRENCY)))
    return _oracle_sem


def _redis_client():
    """Shared sync Redis client (lazy). Prefer REDIS_URL when set."""
    global _redis, _rl_backend
    if _redis is not None:
        return _redis
    with _redis_lock:
        if _redis is not None:
            return _redis
        try:
            import config

            url = (getattr(config, "REDIS_URL", "") or os.getenv("REDIS_URL", "")).strip()
            if not url:
                return None
            import redis

            client = redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=0.35,
                socket_timeout=0.35,
                max_connections=int(os.getenv("VIRAL_REDIS_MAX_CONNECTIONS", "50")),
            )
            client.ping()
            _redis = client
            _rl_backend = "redis"
            logger.info("Viral capacity Redis client ready")
            return _redis
        except Exception:
            logger.debug("Viral Redis unavailable — memory fallback", exc_info=True)
            return None


def _client_key(request: Request) -> str:
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    host = forwarded or (request.client.host if request.client else "unknown")
    return host or "unknown"


def _memory_hit(bucket: str, limit: int, window_sec: int = 60) -> bool:
    """Return True if over limit (should reject)."""
    now = time.time()
    arr = _memory_buckets[bucket]
    _memory_buckets[bucket] = [t for t in arr if now - t < window_sec]
    if len(_memory_buckets[bucket]) >= limit:
        return True
    _memory_buckets[bucket].append(now)
    return False


def check_rate_limit(key: str, *, limit: int, window_sec: int = 60, prefix: str = "viral") -> None:
    """Raise 429 when rate exceeded. Redis shared when available."""
    global _rl_backend
    redis_key = f"bd:{prefix}:rl:{key}"
    client = _redis_client()
    if client is not None:
        try:
            count = int(client.incr(redis_key))
            if count == 1:
                client.expire(redis_key, window_sec)
            _rl_backend = "redis"
            if count > limit:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "rate_limited",
                        "message": "Too many requests — slow down and retry.",
                        "retry_after_sec": window_sec,
                    },
                    headers={"Retry-After": str(window_sec)},
                )
            return
        except HTTPException:
            raise
        except Exception:
            logger.debug("Redis RL failed — memory fallback", exc_info=True)
    _rl_backend = "memory"
    if _memory_hit(f"{prefix}:{key}", limit, window_sec):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "message": "Too many requests — slow down and retry.",
                "retry_after_sec": window_sec,
            },
            headers={"Retry-After": str(window_sec)},
        )


def _path_class(path: str) -> str | None:
    if path.startswith("/health") or path.startswith("/static") or path == "/favicon.ico":
        return None  # never rate-limit probes/static
    if path.startswith("/oracle/") or path.startswith("/api/oracle"):
        return "oracle"
    if path.startswith("/api/auth/login") or path.startswith("/api/auth/register"):
        return "auth"
    if path.startswith("/api/") or path.startswith("/oracle"):
        return "api"
    return "web"


def _limits_for(kind: str) -> tuple[int, int]:
    if kind == "oracle":
        return _env_int("VIRAL_ORACLE_RL_PER_MIN", ORACLE_RL_PER_MIN), 60
    if kind == "auth":
        return _env_int("VIRAL_AUTH_RL_PER_MIN", AUTH_RL_PER_MIN), 60
    if kind == "api":
        return _env_int("VIRAL_API_RL_PER_MIN", API_RL_PER_MIN), 60
    return _env_int("VIRAL_WEB_RL_PER_MIN", 240), 60


def begin_inflight() -> bool:
    """Reserve an in-flight slot. False => shed load."""
    global _inflight
    ceiling = _env_int("VIRAL_MAX_INFLIGHT", MAX_INFLIGHT)
    with _inflight_lock:
        if _inflight >= ceiling:
            return False
        _inflight += 1
        return True


def end_inflight() -> None:
    global _inflight
    with _inflight_lock:
        _inflight = max(0, _inflight - 1)


def inflight_count() -> int:
    with _inflight_lock:
        return _inflight


def quick_cache_get(symbol: str, lang: str, mode: str) -> dict[str, Any] | None:
    key = f"{symbol.upper()}:{lang}:{mode}"
    with _quick_lock:
        row = _quick_cache.get(key)
        if not row:
            return None
        expires, payload = row
        if time.time() > expires:
            _quick_cache.pop(key, None)
            return None
        out = dict(payload)
        out["viral_cache"] = "hit"
        return out


def quick_cache_set(symbol: str, lang: str, mode: str, payload: dict[str, Any]) -> None:
    ttl = float(os.getenv("VIRAL_QUICK_CACHE_TTL_SEC", str(QUICK_CACHE_TTL_SEC)))
    key = f"{symbol.upper()}:{lang}:{mode}"
    with _quick_lock:
        # Bound memory under stampede
        if len(_quick_cache) > 5000:
            _quick_cache.clear()
        _quick_cache[key] = (time.time() + max(0.2, ttl), dict(payload))


async def run_oracle_bounded(coro_factory: Callable[[], Any]) -> Any:
    """Run heavy Oracle work under a process-local concurrency semaphore."""
    sem = get_oracle_semaphore()
    async with sem:
        return await coro_factory()


def viral_middleware_enabled() -> bool:
    return VIRAL_MODE or os.getenv("ENV", "").lower() in {"production", "prod"}


async def viral_protection_middleware(request: Request, call_next):
    """Load shed + class-based rate limits. Skips health/static."""
    if not viral_middleware_enabled():
        return await call_next(request)

    path = request.url.path or "/"
    kind = _path_class(path)
    if kind is None:
        return await call_next(request)

    if not begin_inflight():
        return JSONResponse(
            {
                "status": "overloaded",
                "error": "load_shed",
                "message": "Server is absorbing a traffic spike — retry shortly.",
                "retry_after_sec": SHED_RETRY_AFTER_SEC,
            },
            status_code=503,
            headers={"Retry-After": str(SHED_RETRY_AFTER_SEC)},
        )

    try:
        limit, window = _limits_for(kind)
        client = _client_key(request)
        check_rate_limit(f"{kind}:{client}", limit=limit, window_sec=window, prefix=kind)
        response = await call_next(request)
        # Cache-Control for static-ish HTML under viral load (short)
        if path in {"/", "/dashboard", "/oracle-accuracy", "/compliance", "/capabilities"}:
            response.headers.setdefault("Cache-Control", "public, max-age=15")
        elif path.startswith("/static"):
            response.headers.setdefault("Cache-Control", "public, max-age=86400, immutable")
        response.headers.setdefault("X-Viral-Capacity", "1")
        response.headers.setdefault("X-Viral-Inflight", str(inflight_count()))
        return response
    except HTTPException as exc:
        return JSONResponse(
            exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail},
            status_code=exc.status_code,
            headers=dict(exc.headers or {}),
        )
    finally:
        end_inflight()


def viral_readiness_report() -> dict[str, Any]:
    from scale_readiness import scale_readiness_report

    scale = scale_readiness_report()
    soft = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    redis_ok = rate_limit_backend() == "redis" or bool(
        (os.getenv("REDIS_URL") or "").strip()
    )
    workers = int(os.getenv("WEB_CONCURRENCY", os.getenv("UVICORN_WORKERS", "1")) or 1)
    viral_codepath = bool(scale.get("ha_ready_codepath")) and viral_middleware_enabled()

    checks = list(scale.get("checks") or [])
    checks.extend(
        [
            {
                "id": "viral_middleware",
                "ok": viral_middleware_enabled(),
                "required_for_viral": True,
                "detail": {"VIRAL_MODE": VIRAL_MODE},
            },
            {
                "id": "inflight_ceiling",
                "ok": _env_int("VIRAL_MAX_INFLIGHT", MAX_INFLIGHT) >= 50,
                "required_for_viral": True,
                "detail": {"max_inflight": _env_int("VIRAL_MAX_INFLIGHT", MAX_INFLIGHT), "current": inflight_count()},
            },
            {
                "id": "oracle_semaphore",
                "ok": _env_int("VIRAL_ORACLE_CONCURRENCY", ORACLE_CONCURRENCY) >= 8,
                "required_for_viral": True,
                "detail": {"oracle_concurrency": _env_int("VIRAL_ORACLE_CONCURRENCY", ORACLE_CONCURRENCY)},
            },
            {
                "id": "shared_rate_limits",
                "ok": rate_limit_backend() == "redis" or not soft,
                "required_for_viral": True,
                "detail": rate_limit_backend(),
            },
            {
                "id": "soft_launch_not_viral",
                "ok": not soft,
                "required_for_viral": True,
                "detail": "SOFT_LAUNCH must be unset for viral production",
            },
            {
                "id": "multi_worker_viral",
                "ok": workers >= 2,
                "required_for_viral": True,
                "detail": {"web_concurrency": workers},
            },
        ]
    )
    required_ok = all(c["ok"] for c in checks if c.get("required_for_viral") or c.get("required_for_ha"))
    return {
        "product": "BLACKDARK",
        "surface": "viral_launch_capacity",
        "viral_codepath_ready": viral_codepath and not soft and workers >= 2,
        "viral_production_approved": required_ok and bool(scale.get("ha_ready_codepath")),
        "inflight": inflight_count(),
        "rate_limit_backend": rate_limit_backend(),
        "limits": {
            "max_inflight": _env_int("VIRAL_MAX_INFLIGHT", MAX_INFLIGHT),
            "oracle_concurrency": _env_int("VIRAL_ORACLE_CONCURRENCY", ORACLE_CONCURRENCY),
            "oracle_rl_per_min": _env_int("VIRAL_ORACLE_RL_PER_MIN", ORACLE_RL_PER_MIN),
            "auth_rl_per_min": _env_int("VIRAL_AUTH_RL_PER_MIN", AUTH_RL_PER_MIN),
            "api_rl_per_min": _env_int("VIRAL_API_RL_PER_MIN", API_RL_PER_MIN),
            "quick_cache_ttl_sec": float(os.getenv("VIRAL_QUICK_CACHE_TTL_SEC", str(QUICK_CACHE_TTL_SEC))),
        },
        "scale": scale,
        "checks": checks,
        "recommended_env": {
            **(scale.get("recommended_env") or {}),
            "VIRAL_MODE": "true",
            "VIRAL_MAX_INFLIGHT": "200",
            "VIRAL_ORACLE_CONCURRENCY": "32",
            "WEB_CONCURRENCY": "4",
            "PG_POOL_MAX": "40",
            "SOFT_LAUNCH": "unset",
        },
        "honesty": {
            "code_protects_under_spike": True,
            "proven_signed_load_test": False,
            "proof_path": "docs/LOAD_TEST_RUN_LOG.md",
            "note": (
                "Protections reduce collapse risk under viral spikes. "
                "Do not claim infinite capacity; run signed Postgres+Redis multi-worker load before marketing HA numbers."
            ),
        },
        "playbook": "docs/VIRAL_LAUNCH_CAPACITY.md",
    }


def fingerprint_body(data: dict[str, Any]) -> str:
    raw = repr(sorted((k, str(data.get(k))) for k in ("symbol", "lang", "ux_mode"))).encode()
    return hashlib.sha256(raw).hexdigest()[:16]
