"""
BLACKDARK — Redis coordination helpers for multi-worker safety.

Provides: rate-limit counters, distributed locks, short-lived KV state.
Falls back to process-local stores when Redis is unavailable (soft-launch).
"""

from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Iterator

logger = logging.getLogger("BLACKDARK.RedisCoord")

_sync_client: Any = None
_local_counters: dict[str, list[float]] = defaultdict(list)
_local_kv: dict[str, tuple[Any, float]] = {}
_local_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
_LOCAL_KV_LOCK = threading.Lock()


def redis_url() -> str:
    return (os.getenv("REDIS_URL") or "").strip()


def _sync_redis() -> Any | None:
    global _sync_client
    url = redis_url()
    if not url:
        return None
    if _sync_client is not None:
        try:
            _sync_client.ping()
            return _sync_client
        except Exception:
            _sync_client = None
    try:
        import redis

        client = redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=1.5,
            socket_timeout=1.5,
        )
        client.ping()
        _sync_client = client
        return _sync_client
    except Exception as exc:
        logger.debug("Redis coord sync client unavailable: %s", exc)
        _sync_client = None
        return None


def rate_limit_check(
    key: str,
    *,
    limit: int,
    window_sec: int,
    namespace: str = "login",
) -> tuple[bool, int]:
    """
    Sliding-window rate limit check (does not increment).
    Returns (allowed, current_count).
    """
    redis_key = f"bd:rl:{namespace}:{key}"
    client = _sync_redis()
    now = time.time()
    if client is not None:
        try:
            pipe = client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, now - window_sec)
            pipe.zcard(redis_key)
            pipe.expire(redis_key, window_sec + 5)
            _, count, _ = pipe.execute()
            count_i = int(count or 0)
            return count_i < limit, count_i
        except Exception:
            logger.debug("Redis rate_limit_check failed — local fallback", exc_info=True)

    window = _local_counters[redis_key]
    _local_counters[redis_key] = [t for t in window if now - t < window_sec]
    count_i = len(_local_counters[redis_key])
    return count_i < limit, count_i


def rate_limit_hit(
    key: str,
    *,
    limit: int,
    window_sec: int,
    namespace: str = "login",
) -> tuple[bool, int]:
    """Record one hit and return (still_allowed_after, count)."""
    redis_key = f"bd:rl:{namespace}:{key}"
    client = _sync_redis()
    now = time.time()
    member = f"{now}:{uuid.uuid4().hex[:8]}"
    if client is not None:
        try:
            pipe = client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, now - window_sec)
            pipe.zadd(redis_key, {member: now})
            pipe.zcard(redis_key)
            pipe.expire(redis_key, window_sec + 5)
            _, _, count, _ = pipe.execute()
            count_i = int(count or 0)
            return count_i < limit, count_i
        except Exception:
            logger.debug("Redis rate_limit_hit failed — local fallback", exc_info=True)

    window = _local_counters[redis_key]
    _local_counters[redis_key] = [t for t in window if now - t < window_sec]
    _local_counters[redis_key].append(now)
    count_i = len(_local_counters[redis_key])
    return count_i < limit, count_i


def kv_set(key: str, value: str, *, ttl_sec: int = 600, namespace: str = "kv") -> bool:
    redis_key = f"bd:{namespace}:{key}"
    client = _sync_redis()
    if client is not None:
        try:
            client.set(redis_key, value, ex=max(1, int(ttl_sec)))
            return True
        except Exception:
            logger.debug("Redis kv_set failed — local fallback", exc_info=True)
    with _LOCAL_KV_LOCK:
        _local_kv[redis_key] = (value, time.time() + max(1, int(ttl_sec)))
    return False


def kv_get(key: str, *, namespace: str = "kv") -> str | None:
    redis_key = f"bd:{namespace}:{key}"
    client = _sync_redis()
    if client is not None:
        try:
            val = client.get(redis_key)
            return str(val) if val is not None else None
        except Exception:
            logger.debug("Redis kv_get failed — local fallback", exc_info=True)
    with _LOCAL_KV_LOCK:
        row = _local_kv.get(redis_key)
        if not row:
            return None
        value, expires = row
        if time.time() > expires:
            _local_kv.pop(redis_key, None)
            return None
        return str(value)


def kv_pop(key: str, *, namespace: str = "kv") -> str | None:
    redis_key = f"bd:{namespace}:{key}"
    client = _sync_redis()
    if client is not None:
        try:
            # GETDEL when available; else GET + DEL
            try:
                val = client.getdel(redis_key)
            except Exception:
                val = client.get(redis_key)
                if val is not None:
                    client.delete(redis_key)
            return str(val) if val is not None else None
        except Exception:
            logger.debug("Redis kv_pop failed — local fallback", exc_info=True)
    with _LOCAL_KV_LOCK:
        row = _local_kv.pop(redis_key, None)
        if not row:
            return None
        value, expires = row
        if time.time() > expires:
            return None
        return str(value)


_UNLOCK_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
else
  return 0
end
"""


@contextmanager
def distributed_lock(
    name: str,
    *,
    ttl_sec: int = 5,
    wait_sec: float = 2.0,
    namespace: str = "lock",
) -> Iterator[bool]:
    """
    Best-effort distributed lock. Yields True when lock acquired (Redis or local).
    Always releases in finally.
    """
    redis_key = f"bd:{namespace}:{name}"
    token = uuid.uuid4().hex
    client = _sync_redis()
    acquired = False
    used_redis = False

    if client is not None:
        deadline = time.time() + max(0.05, float(wait_sec))
        while time.time() <= deadline:
            try:
                ok = client.set(redis_key, token, nx=True, ex=max(1, int(ttl_sec)))
                if ok:
                    acquired = True
                    used_redis = True
                    break
            except Exception:
                logger.debug("Redis lock acquire failed", exc_info=True)
                break
            time.sleep(0.02)

    if not acquired and not used_redis:
        lock = _local_locks[redis_key]
        got = lock.acquire(timeout=max(0.05, float(wait_sec)))
        acquired = bool(got)

    try:
        yield acquired
    finally:
        if used_redis and acquired and client is not None:
            try:
                client.eval(_UNLOCK_LUA, 1, redis_key, token)
            except Exception:
                logger.debug("Redis lock release failed", exc_info=True)
        elif not used_redis and acquired:
            try:
                _local_locks[redis_key].release()
            except RuntimeError:
                pass


def coord_stats() -> dict[str, Any]:
    return {
        "redis_configured": bool(redis_url()),
        "sync_client_ready": _sync_client is not None,
        "local_counter_keys": len(_local_counters),
        "local_kv_keys": len(_local_kv),
    }
