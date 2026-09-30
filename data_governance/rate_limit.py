"""Rate-limit and quota governance."""

from __future__ import annotations

import threading
import time
from typing import Any

from data_governance.registry import canonical_source_registry

_COUNTERS: dict[str, list[float]] = {}
_LOCK = threading.Lock()

DEFAULT_LIMITS: dict[str, dict[str, int]] = {
    "coingecko_prices": {"per_minute": 30, "per_day": 10000},
    "binance_spot": {"per_minute": 1200, "per_day": 100000},
    "fred": {"per_minute": 120, "per_day": 100000},
}


def record_request(source_id: str) -> None:
    with _LOCK:
        bucket = _COUNTERS.setdefault(source_id, [])
        bucket.append(time.time())
        cutoff = time.time() - 86400
        _COUNTERS[source_id] = [t for t in bucket if t >= cutoff]


def check_quota(source_id: str) -> dict[str, Any]:
    limits = DEFAULT_LIMITS.get(source_id, {"per_minute": 60, "per_day": 10000})
    with _LOCK:
        times = _COUNTERS.get(source_id, [])
    now = time.time()
    minute_count = sum(1 for t in times if t >= now - 60)
    day_count = len(times)
    allowed = minute_count < limits["per_minute"] and day_count < limits["per_day"]
    return {
        "source_id": source_id,
        "allowed": allowed,
        "minute_usage": minute_count,
        "minute_limit": limits["per_minute"],
        "day_usage": day_count,
        "day_limit": limits["per_day"],
        "throttle_recommended": not allowed,
    }


def quota_matrix() -> dict[str, Any]:
    keyed = [e.source_id for e in canonical_source_registry() if e.env_key or e.source_id in DEFAULT_LIMITS]
    return {"sources": [check_quota(s) for s in keyed[:20]], "governance": "rate_limit_governed"}
