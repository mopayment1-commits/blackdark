"""Shared TTL cache + rate-limit + circuit-breaker helpers for ingestion connectors."""

from __future__ import annotations

import json
import time
from typing import Any

import aiohttp

from blackdark.data import circuit_breaker as cb

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

    def _circuit_blocked(self, source_slug: str | None, cache_key: str) -> dict[str, Any] | None:
        """Fail-closed when upstream circuit is open — stale cache only, no live call."""
        if not source_slug or not cb.is_open(source_slug):
            return None
        stale = self.get_stale(cache_key)
        if stale:
            return {
                **stale,
                "ok": True,
                "cache_hit": True,
                "stale_fallback": True,
                "circuit_open": True,
                "fail_closed": True,
            }
        return {
            "ok": False,
            "error": "circuit_open",
            "circuit_open": True,
            "fail_closed": True,
        }

    async def http_get(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_sec: float = 3.0,
        cache_key: str,
        ttl: int,
        source_slug: str | None = None,
    ) -> dict[str, Any]:
        cached = self.get(cache_key, ttl=ttl)
        if cached is not None:
            return {**cached, "cache_hit": True}

        blocked = self._circuit_blocked(source_slug, cache_key)
        if blocked is not None:
            return blocked

        if self.rate_limited():
            stale = self.get_stale(cache_key)
            if stale:
                return {**stale, "cache_hit": True, "stale_fallback": True, "rate_limited": True}
            if source_slug:
                cb.record_failure(source_slug, "rate_limited")
            return {"ok": False, "error": "rate_limited", "fail_closed": True}

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
                            if source_slug:
                                cb.record_failure(source_slug, "rate_limited")
                            return {
                                **stale,
                                "ok": True,
                                "cache_hit": True,
                                "stale_fallback": True,
                                "rate_limited": True,
                                "latency_ms": latency_ms,
                            }
                        if source_slug:
                            cb.record_failure(source_slug, "rate_limited")
                        return {"ok": False, "error": "rate_limited", "latency_ms": latency_ms, "fail_closed": True}
                    if resp.status != 200:
                        stale = self.get_stale(cache_key)
                        if stale:
                            if source_slug:
                                cb.record_failure(source_slug, f"http_{resp.status}")
                            return {
                                **stale,
                                "ok": True,
                                "stale_fallback": True,
                                "http_status": resp.status,
                                "latency_ms": latency_ms,
                            }
                        if source_slug:
                            cb.record_failure(source_slug, f"http_{resp.status}")
                        return {"ok": False, "error": f"http_{resp.status}", "latency_ms": latency_ms, "fail_closed": True}
                    data = await resp.text()
        except (aiohttp.ClientError, TimeoutError) as exc:
            stale = self.get_stale(cache_key)
            if stale:
                if source_slug:
                    cb.record_failure(source_slug, str(exc))
                return {**stale, "ok": True, "stale_fallback": True, "error": str(exc)}
            if source_slug:
                cb.record_failure(source_slug, str(exc))
            return {"ok": False, "error": str(exc), "fail_closed": True}

        if source_slug:
            cb.record_success(source_slug)
        result = {
            "ok": True,
            "data": data,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
            "cache_hit": False,
        }
        self.set(cache_key, result)
        return result

    async def http_get_json(
        self,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout_sec: float = 3.0,
        cache_key: str,
        ttl: int,
        source_slug: str | None = None,
    ) -> dict[str, Any]:
        """JSON variant of http_get — same circuit-breaker + cache semantics."""
        resp = await self.http_get(
            url,
            params=params,
            headers=headers,
            timeout_sec=timeout_sec,
            cache_key=cache_key,
            ttl=ttl,
            source_slug=source_slug,
        )
        if not resp.get("ok"):
            return resp
        raw = resp.get("data")
        if isinstance(raw, (dict, list)):
            return {**resp, "data": raw}
        try:
            parsed = json.loads(str(raw or ""))
        except json.JSONDecodeError as exc:
            if source_slug:
                cb.record_failure(source_slug, f"json_decode:{exc}")
            stale = self.get_stale(cache_key)
            if stale and stale.get("data") is not None:
                return {**stale, "ok": True, "stale_fallback": True, "error": str(exc)}
            return {"ok": False, "error": f"json_decode:{exc}", "fail_closed": True}
        out = {**resp, "data": parsed}
        self.set(cache_key, out)
        return out


def cache_key(*parts: Any) -> str:
    return json.dumps(parts, sort_keys=True, default=str)
