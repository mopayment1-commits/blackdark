"""Shared TTL cache + rate-limit helpers for ingestion connectors."""

from __future__ import annotations

import json
import time
from typing import Any

import aiohttp

_HEADERS = {"User-Agent": "BLACKDARK/1.0", "Accept": "application/json"}


class IngestionCache:
    def __init__(self, *, default_ttl_sec: int = 3600, max_ttl_sec: int = 86400) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._rate_limit_until = 0.0
        self.default_ttl = max(60, min(max_ttl_sec, default_ttl_sec))
        self.max_ttl = max_ttl_sec

    def ttl(self, env_key: str, default: int | None = None) -> int:
        import os

        raw = int(os.getenv(env_key, str(default or self.default_ttl)))
        return max(60, min(self.max_ttl, raw))

    def get(self, key: str, *, ttl: int) -> Any | None:
        row = self._store.get(key)
        if row and time.time() - row[0] < ttl:
            return row[1]
        return None

    def get_stale(self, key: str) -> Any | None:
        row = self._store.get(key)
        return row[1] if row else None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)

    def rate_limited(self) -> bool:
        return time.time() < self._rate_limit_until

    def mark_rate_limited(self, *, backoff_sec: float = 60) -> None:
        self._rate_limit_until = time.time() + backoff_sec

    async def http_get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_sec: float = 3.0,
        cache_key: str,
        ttl: int,
    ) -> dict[str, Any]:
        cached = self.get(cache_key, ttl=ttl)
        if cached is not None:
            return {**cached, "cache_hit": True}

        if self.rate_limited():
            stale = self.get_stale(cache_key)
            if stale:
                return {**stale, "cache_hit": True, "stale_fallback": True, "rate_limited": True}
            return {"ok": False, "error": "rate_limited"}

        merged = {**_HEADERS, **(headers or {})}
        timeout = aiohttp.ClientTimeout(total=timeout_sec)
        t0 = time.perf_counter()
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, params=params, headers=merged) as resp:
                    latency_ms = round((time.perf_counter() - t0) * 1000, 1)
                    if resp.status == 429:
                        self.mark_rate_limited()
                        stale = self.get_stale(cache_key)
                        if stale:
                            return {
                                **stale,
                                "ok": True,
                                "cache_hit": True,
                                "stale_fallback": True,
                                "rate_limited": True,
                                "latency_ms": latency_ms,
                            }
                        return {"ok": False, "error": "rate_limited", "latency_ms": latency_ms}
                    if resp.status != 200:
                        stale = self.get_stale(cache_key)
                        if stale:
                            return {
                                **stale,
                                "ok": True,
                                "stale_fallback": True,
                                "http_status": resp.status,
                                "latency_ms": latency_ms,
                            }
                        return {"ok": False, "error": f"http_{resp.status}", "latency_ms": latency_ms}
                    data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as exc:
            stale = self.get_stale(cache_key)
            if stale:
                return {**stale, "ok": True, "stale_fallback": True, "error": str(exc)}
            return {"ok": False, "error": str(exc)}

        result = {
            "ok": True,
            "data": data,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "cache_hit": False,
        }
        self.set(cache_key, result)
        return result


def cache_key(*parts: Any) -> str:
    return json.dumps(parts, sort_keys=True, default=str)
