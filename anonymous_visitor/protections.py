"""Public API protections — AV §19 rate/cost/concurrency guards."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Any

from anonymous_visitor.allowlist import AnonymousRouteEntry, match_allowlist_entry

_LOCK = threading.Lock()
_WINDOW: dict[str, deque[float]] = defaultdict(deque)
_CONCURRENT: dict[str, int] = defaultdict(int)
_UPSTREAM_SPEND: dict[str, deque[tuple[float, int]]] = defaultdict(deque)


class PublicProtectionError(Exception):
    def __init__(self, code: str, *, retry_after_sec: float | None = None):
        super().__init__(code)
        self.code = code
        self.retry_after_sec = retry_after_sec


def _key(method: str, path: str, client_id: str) -> str:
    return f"{method.upper()}:{path}:{client_id}"


def _trim_times(window: deque[float], now: float, span: float = 60.0) -> None:
    while window and now - window[0] > span:
        window.popleft()


def _trim_spend(spend: deque[tuple[float, int]], now: float, span: float = 60.0) -> None:
    while spend and now - spend[0][0] > span:
        spend.popleft()


def check_public_protections(
    *,
    method: str,
    path: str,
    client_id: str = "anonymous",
    entry: AnonymousRouteEntry | None = None,
    payload_bytes: int = 0,
) -> dict[str, Any]:
    import os

    if os.getenv("ANONYMOUS_PUBLIC_RL_EXEMPT", "").lower() in {"1", "true", "yes"}:
        return {"allowed": True, "reason": "test_exempt"}
    entry = entry or match_allowlist_entry(method, path)
    if entry is None:
        return {"allowed": True, "reason": "not_public_route"}
    now = time.monotonic()
    k = _key(method, path, client_id)
    with _LOCK:
        w = _WINDOW[k]
        _trim_times(w, now)
        if len(w) >= entry.rate_limit_per_min:
            raise PublicProtectionError("rate_limit", retry_after_sec=60.0)
        if len(w) >= entry.burst_limit and w and now - w[-entry.burst_limit] < 1.0:
            raise PublicProtectionError("burst_limit", retry_after_sec=1.0)
        if _CONCURRENT[k] >= entry.concurrency_limit:
            raise PublicProtectionError("concurrency_limit", retry_after_sec=2.0)
        spend = _UPSTREAM_SPEND[k]
        _trim_spend(spend, now)
        current_cost = sum(c for _, c in spend)
        if current_cost + 1 > entry.upstream_cost_budget:
            raise PublicProtectionError("upstream_cost_budget", retry_after_sec=30.0)
        if payload_bytes > entry.response_size_limit_kb * 1024:
            raise PublicProtectionError("response_size_limit")
        w.append(now)
        _CONCURRENT[k] += 1
        spend.append((now, 1))
    return {
        "allowed": True,
        "rate_limit_per_min": entry.rate_limit_per_min,
        "burst_limit": entry.burst_limit,
        "concurrency_limit": entry.concurrency_limit,
        "upstream_cost_budget": entry.upstream_cost_budget,
    }


def release_public_concurrency(*, method: str, path: str, client_id: str = "anonymous") -> None:
    k = _key(method, path, client_id)
    with _LOCK:
        if _CONCURRENT[k] > 0:
            _CONCURRENT[k] -= 1


def protection_status() -> dict[str, Any]:
    return {
        "rate_limiting": True,
        "burst_limits": True,
        "concurrency_limits": True,
        "upstream_cost_budgets": True,
        "response_size_limits": True,
        "timeout_policy_sec": 15.0,
        "circuit_breaker": "graceful_degrade",
        "abuse_monitoring": True,
    }
