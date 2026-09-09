"""Error flood deduplication and cooldown (ERR-035)."""

from __future__ import annotations

import time
from threading import Lock

_lock = Lock()
_seen: dict[str, float] = {}
_COOLDOWN_SECONDS = 8.0


def should_surface(key: str, *, cooldown_seconds: float = _COOLDOWN_SECONDS) -> bool:
    now = time.time()
    with _lock:
        last = _seen.get(key)
        if last is not None and now - last < cooldown_seconds:
            return False
        _seen[key] = now
        if len(_seen) > 5000:
            cutoff = now - cooldown_seconds * 2
            for k, ts in list(_seen.items()):
                if ts < cutoff:
                    _seen.pop(k, None)
        return True


def aggregate_keys(*parts: str) -> str:
    return "|".join(p for p in parts if p)
