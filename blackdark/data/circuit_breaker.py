"""Per-source circuit breaker for data ingest (D-01 cascade prevention)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock

_STATE_OPEN = "open"
_STATE_CLOSED = "closed"
_STATE_HALF_OPEN = "half_open"


@dataclass
class _SourceCircuit:
    failures: int = 0
    state: str = _STATE_CLOSED
    opened_at: float = 0.0
    last_failure: str | None = None


_lock = Lock()
_circuits: dict[str, _SourceCircuit] = {}
_FAILURE_THRESHOLD = 3
_RESET_SECONDS = 300


def record_success(source_slug: str) -> None:
    with _lock:
        c = _circuits.setdefault(source_slug, _SourceCircuit())
        c.failures = 0
        c.state = _STATE_CLOSED
        c.last_failure = None


def record_failure(source_slug: str, reason: str) -> None:
    with _lock:
        c = _circuits.setdefault(source_slug, _SourceCircuit())
        c.failures += 1
        c.last_failure = reason[:500]
        if c.failures >= _FAILURE_THRESHOLD:
            c.state = _STATE_OPEN
            c.opened_at = time.time()


def is_open(source_slug: str) -> bool:
    with _lock:
        c = _circuits.get(source_slug)
        if not c or c.state != _STATE_OPEN:
            return False
        if time.time() - c.opened_at >= _RESET_SECONDS:
            c.state = _STATE_HALF_OPEN
            c.failures = 0
            return False
        return True


def snapshot() -> dict[str, dict]:
    with _lock:
        return {
            slug: {
                "state": c.state,
                "failures": c.failures,
                "last_failure": c.last_failure,
            }
            for slug, c in _circuits.items()
        }


def any_open() -> bool:
    return any(is_open(slug) for slug in list(_circuits.keys()))
