"""
BLACKDARK — Viral launch capacity controls.

Protects the process under sudden concurrent traffic:
  · shared Redis (or memory) rate limits for Oracle / auth / API bursts
  · shared Redis in-flight ceiling + load shedding (503) — falls back local
  · Oracle compute semaphore (prevents stampedes on heavy path)
  · shared Redis short-TTL cache for identical Oracle /quick bursts
  · honest readiness report (codepath ≠ signed HA proof)

English product surfaces remain Prove-it honest: Soft Launch SQLite is not viral HA.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse

# Sonar S1192: duplicated string literals
STR_BD_VIRAL_INFLIGHT = 'bd:viral:inflight'

logger = logging.getLogger("BLACKDARK.ViralCapacity")

# Tunables (env-overridable)
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
_redis_fail_until = 0.0
_rl_backend = "memory"
_inflight_backend = "memory"
_cache_backend = "memory"
# Fail-fast when REDIS_URL is set but unreachable (Windows dead localhost often
# costs full socket timeouts per call — enough to push k6 past 500ms).
_REDIS_CONNECT_TIMEOUT = float(os.getenv("VIRAL_REDIS_CONNECT_TIMEOUT_SEC", "0.08"))
_REDIS_SOCKET_TIMEOUT = float(os.getenv("VIRAL_REDIS_SOCKET_TIMEOUT_SEC", "0.08"))
_REDIS_NEG_TTL_SEC = float(os.getenv("VIRAL_REDIS_NEG_TTL_SEC", "30"))


def viral_mode_enabled() -> bool:
    return os.getenv("VIRAL_MODE", "true").lower() in {"1", "true", "yes"}


def rate_limit_backend() -> str:
    return _rl_backend


def inflight_backend() -> str:
    return _inflight_backend


def cache_backend() -> str:
    return _cache_backend


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except asyncio.CancelledError:
        raise
    except Exception:
        return default


def effective_parallelism() -> dict[str, int]:
    """Workers × replicas — honest multi-instance signal for viral/HA gates."""
    workers = max(1, _env_int("WEB_CONCURRENCY", _env_int("UVICORN_WORKERS", 1)))
    replicas = max(
        1,
        _env_int(
            "WEB_REPLICAS",
            _env_int("K8S_REPLICAS", _env_int("RAILWAY_REPLICA_COUNT", 1)),
        ),
    )
    # railway.json numReplicas is deploy-time; expose WEB_REPLICAS in templates when known.
    total = workers * replicas
    return {"workers": workers, "replicas": replicas, "parallelism": total}


def get_oracle_semaphore() -> asyncio.Semaphore:
    global _oracle_sem
    if _oracle_sem is None:
        _oracle_sem = asyncio.Semaphore(max(1, _env_int("VIRAL_ORACLE_CONCURRENCY", ORACLE_CONCURRENCY)))
    return _oracle_sem


def _redis_client():
    """Shared sync Redis client (lazy). Prefer REDIS_URL when set.

    Negative-caches failed connects so a dead REDIS_URL cannot add tens/hundreds
    of ms on every HTML/API request (begin_inflight + rate limit each probe).
    """
    global _redis, _rl_backend, _redis_fail_until
    if _redis is not None:
        return _redis
    now = time.time()
    if now < _redis_fail_until:
        return None
    with _redis_lock:
        if _redis is not None:
            return _redis
        if time.time() < _redis_fail_until:
            return None
        try:
            import config

            url = (getattr(config, "REDIS_URL", "") or os.getenv("REDIS_URL", "")).strip()
            if not url:
                return None
            import redis

            client = redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=_REDIS_CONNECT_TIMEOUT,
                socket_timeout=_REDIS_SOCKET_TIMEOUT,
                max_connections=int(os.getenv("VIRAL_REDIS_MAX_CONNECTIONS", "50")),
            )
            client.ping()
            _redis = client
            _redis_fail_until = 0.0
            _rl_backend = "redis"
            logger.info("Viral capacity Redis client ready")
            return _redis
        except asyncio.CancelledError:
            raise
        except Exception:
            _redis_fail_until = time.time() + max(1.0, _REDIS_NEG_TTL_SEC)
            _rl_backend = "memory"
            logger.debug(
                "Viral Redis unavailable — memory fallback for %.0fs",
                _REDIS_NEG_TTL_SEC,
                exc_info=True,
            )
            return None


def redis_live() -> bool:
    client = _redis_client()
    if client is None:
        return False
    try:
        return bool(client.ping())
    except asyncio.CancelledError:
        raise
    except Exception:
        return False


def reset_redis_client() -> None:
    """Drop cached client so drills can inject a dead REDIS_URL."""
    global _redis, _redis_fail_until, _rl_backend
    with _redis_lock:
        _redis = None
        _redis_fail_until = 0.0
        _rl_backend = "memory"


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
        except asyncio.CancelledError:
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
    if path.startswith(("/health", "/static")) or path == "/favicon.ico":
        return None  # never rate-limit probes/static
    if path.startswith(("/oracle/", "/api/oracle")):
        return "oracle"
    if path.startswith(("/api/auth/login", "/api/auth/register")):
        return "auth"
    if path.startswith(("/api/", "/oracle")):
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


def begin_inflight() -> tuple[bool, str]:
    """Reserve an in-flight slot. Returns (accepted, backend_token). backend_token for end_inflight."""
    global _inflight, _inflight_backend
    ceiling = _env_int("VIRAL_MAX_INFLIGHT", MAX_INFLIGHT)
    client = _redis_client()
    if client is not None:
        try:
            key = STR_BD_VIRAL_INFLIGHT
            n = int(client.incr(key))
            if n == 1:
                client.expire(key, 180)
            if n > ceiling:
                client.decr(key)
                _inflight_backend = "redis"
                return False, ""
            _inflight_backend = "redis"
            return True, "redis"
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("Redis inflight failed — local fallback", exc_info=True)
    with _inflight_lock:
        if _inflight >= ceiling:
            _inflight_backend = "memory"
            return False, ""
        _inflight += 1
        _inflight_backend = "memory"
        return True, "memory"


def end_inflight(backend: str = "memory") -> None:
    global _inflight
    if backend == "redis":
        client = _redis_client()
        if client is not None:
            try:
                key = STR_BD_VIRAL_INFLIGHT
                n = int(client.decr(key))
                if n < 0:
                    client.set(key, 0, ex=180)
                return
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("Redis inflight decr failed", exc_info=True)
                return
    if backend == "memory":
        with _inflight_lock:
            _inflight = max(0, _inflight - 1)


def inflight_count() -> int:
    client = _redis_client()
    if client is not None:
        try:
            return max(0, int(client.get(STR_BD_VIRAL_INFLIGHT) or 0))
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
    with _inflight_lock:
        return _inflight


def _cache_key(symbol: str, lang: str, mode: str) -> str:
    return f"{symbol.upper()}:{lang}:{mode}"


def quick_cache_get(symbol: str, lang: str, mode: str) -> dict[str, Any] | None:
    global _cache_backend
    key = _cache_key(symbol, lang, mode)
    client = _redis_client()
    if client is not None:
        try:
            raw = client.get(f"bd:viral:qcache:{key}")
            if raw:
                payload = json.loads(raw)
                if isinstance(payload, dict):
                    out = dict(payload)
                    out["viral_cache"] = "hit"
                    _cache_backend = "redis"
                    return out
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("Redis quick cache get failed", exc_info=True)
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
        _cache_backend = "memory"
        return out


def quick_cache_set(symbol: str, lang: str, mode: str, payload: dict[str, Any]) -> None:
    global _cache_backend
    ttl = float(os.getenv("VIRAL_QUICK_CACHE_TTL_SEC", str(QUICK_CACHE_TTL_SEC)))
    key = _cache_key(symbol, lang, mode)
    body = {k: v for k, v in dict(payload).items() if k != "viral_cache"}
    client = _redis_client()
    if client is not None:
        try:
            client.setex(
                f"bd:viral:qcache:{key}",
                max(1, int(ttl + 0.999)),
                json.dumps(body, default=str),
            )
            _cache_backend = "redis"
            return
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("Redis quick cache set failed", exc_info=True)
    with _quick_lock:
        if len(_quick_cache) > 5000:
            _quick_cache.clear()
        _quick_cache[key] = (time.time() + max(0.2, ttl), body)
        _cache_backend = "memory"


async def run_oracle_bounded(coro_factory: Callable[[], Any]) -> Any:
    """Run heavy Oracle work under a process-local concurrency semaphore."""
    sem = get_oracle_semaphore()
    async with sem:
        return await coro_factory()


def viral_middleware_enabled() -> bool:
    return viral_mode_enabled() or os.getenv("ENV", "").lower() in {"production", "prod"}


async def viral_protection_middleware(request: Request, call_next):
    """Load shed + class-based rate limits. Skips health/static."""
    if not viral_middleware_enabled():
        return await call_next(request)

    path = request.url.path or "/"
    kind = _path_class(path)
    if kind is None:
        return await call_next(request)

    accepted, inflight_token = begin_inflight()
    if not accepted:
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
        if path in {"/", "/dashboard", "/oracle-accuracy", "/compliance", "/capabilities"}:
            # Landing shell is mostly static per locale; 15s forced re-render
            # and re-download on every navigation. Prefer short CDN-friendly TTL.
            response.headers.setdefault(
                "Cache-Control",
                "public, max-age=120, stale-while-revalidate=600",
            )
        elif path.startswith("/static"):
            response.headers.setdefault("Cache-Control", "public, max-age=86400, immutable")
        response.headers.setdefault("X-Viral-Capacity", "1")
        response.headers.setdefault("X-Viral-Inflight", str(inflight_count()))
        response.headers.setdefault("X-Viral-RL-Backend", rate_limit_backend())
        return response
    except HTTPException as exc:
        return JSONResponse(
            exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail},
            status_code=exc.status_code,
            headers=dict(exc.headers or {}),
        )
    finally:
        end_inflight(inflight_token)


def viral_health_payload() -> dict[str, Any]:
    """Lightweight probe for LB / ops — Redis + middleware + parallelism."""
    soft = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    parallel = effective_parallelism()
    redis_ok = redis_live()
    ok = (
        viral_middleware_enabled()
        and not soft
        and redis_ok
        and parallel["parallelism"] >= 2
    )
    return {
        "status": "ok" if ok else "degraded",
        "probe": "viral",
        "ok": ok,
        "soft_launch": soft,
        "redis_live": redis_ok,
        "middleware": viral_middleware_enabled(),
        "parallelism": parallel,
        "inflight": inflight_count(),
        "backends": {
            "rate_limit": rate_limit_backend(),
            "inflight": inflight_backend(),
            "quick_cache": cache_backend(),
        },
    }


def viral_readiness_report() -> dict[str, Any]:
    from scale_readiness import scale_readiness_report

    scale = scale_readiness_report()
    soft = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    parallel = effective_parallelism()
    redis_ok = redis_live()
    viral_codepath = bool(scale.get("ha_ready_codepath")) and viral_middleware_enabled()

    checks = list(scale.get("checks") or [])
    checks.extend(
        [
            {
                "id": "viral_middleware",
                "ok": viral_middleware_enabled(),
                "required_for_viral": True,
                "detail": {"VIRAL_MODE": viral_mode_enabled()},
            },
            {
                "id": "inflight_ceiling",
                "ok": _env_int("VIRAL_MAX_INFLIGHT", MAX_INFLIGHT) >= 50,
                "required_for_viral": True,
                "detail": {
                    "max_inflight": _env_int("VIRAL_MAX_INFLIGHT", MAX_INFLIGHT),
                    "current": inflight_count(),
                    "backend": inflight_backend(),
                },
            },
            {
                "id": "oracle_semaphore",
                "ok": _env_int("VIRAL_ORACLE_CONCURRENCY", ORACLE_CONCURRENCY) >= 8,
                "required_for_viral": True,
                "detail": {"oracle_concurrency": _env_int("VIRAL_ORACLE_CONCURRENCY", ORACLE_CONCURRENCY)},
            },
            {
                "id": "shared_rate_limits",
                "ok": redis_ok and rate_limit_backend() == "redis",
                "required_for_viral": True,
                "detail": {
                    "backend": rate_limit_backend(),
                    "redis_live": redis_ok,
                    "note": "Viral approval requires live Redis (not memory fallback)",
                },
            },
            {
                "id": "shared_inflight_and_cache",
                "ok": redis_ok,
                "required_for_viral": True,
                "detail": {
                    "inflight_backend": inflight_backend(),
                    "cache_backend": cache_backend(),
                },
            },
            {
                "id": "soft_launch_not_viral",
                "ok": not soft,
                "required_for_viral": True,
                "detail": "SOFT_LAUNCH must be unset for viral production",
            },
            {
                "id": "multi_worker_viral",
                "ok": parallel["parallelism"] >= 2,
                "required_for_viral": True,
                "detail": parallel,
            },
        ]
    )
    required_ok = all(c["ok"] for c in checks if c.get("required_for_viral") or c.get("required_for_ha"))
    return {
        "product": "BLACKDARK",
        "surface": "viral_launch_capacity",
        "viral_codepath_ready": viral_codepath and not soft and parallel["parallelism"] >= 2 and redis_ok,
        "viral_production_approved": required_ok and bool(scale.get("ha_ready_codepath")) and redis_ok,
        "inflight": inflight_count(),
        "rate_limit_backend": rate_limit_backend(),
        "inflight_backend": inflight_backend(),
        "cache_backend": cache_backend(),
        "parallelism": parallel,
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
            "WEB_REPLICAS": "2",
            "PG_POOL_MAX": "40",
            "SOFT_LAUNCH": "unset",
        },
        "honesty": _signed_capacity_honesty(),
        "playbook": "docs/VIRAL_LAUNCH_CAPACITY.md",
    }


def _signed_capacity_honesty() -> dict[str, Any]:
    """C1 cure: proven_signed_load_test flips when verified signed capacity is deposited."""
    proven = False
    capacity = None
    try:
        from institutional_assurance import get_signed_capacity, verify_signed_capacity

        capacity = get_signed_capacity()
        proven = bool(capacity and verify_signed_capacity(capacity) and capacity.get("ha_claim_eligible"))
    except Exception:
        proven = False
    return {
        "code_protects_under_spike": True,
        "proven_signed_load_test": proven,
        "signed_capacity": capacity,
        "proof_path": "data/institutional_assurance/signed_capacity.json",
        "proof_log": "docs/LOAD_TEST_RUN_LOG.md",
        "note": (
            "Protections reduce collapse risk under viral spikes. "
            "HA marketing numbers require verified signed capacity with postgres+redis+workers≥2."
            if not proven
            else "Verified signed capacity row present and HA-eligible."
        ),
    }


def fingerprint_body(data: dict[str, Any]) -> str:
    raw = repr(sorted((k, str(data.get(k))) for k in ("symbol", "lang", "ux_mode"))).encode()
    return hashlib.sha256(raw).hexdigest()[:16]
