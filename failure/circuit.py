"""Unified circuit breaker facade over existing per-domain breakers (ERR-010)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from failure.states import FailureState


class CircuitState(StrEnum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


def record_success(dependency: str) -> None:
    from blackdark.data import circuit_breaker

    circuit_breaker.record_success(dependency)


def record_failure(dependency: str, reason: str) -> None:
    from blackdark.data import circuit_breaker

    circuit_breaker.record_failure(dependency, reason)


def is_open(dependency: str) -> bool:
    from blackdark.data import circuit_breaker

    return circuit_breaker.is_open(dependency)


def snapshot() -> dict[str, dict[str, Any]]:
    from blackdark.data import circuit_breaker

    raw = circuit_breaker.snapshot()
    out: dict[str, dict[str, Any]] = {}
    for slug, meta in raw.items():
        state = str(meta.get("state", "closed")).upper()
        if state == "OPEN":
            mapped = CircuitState.OPEN
        elif state == "HALF_OPEN":
            mapped = CircuitState.HALF_OPEN
        else:
            mapped = CircuitState.CLOSED
        out[slug] = {**meta, "canonical_state": mapped.value}
    return out


def degraded_failure_state(dependency: str) -> FailureState:
    return FailureState.DEGRADED if is_open(dependency) else FailureState.SUCCESS


def user_scope_message(dependency: str, *, lang: str | None = None) -> str | None:
    if not is_open(dependency):
        return None
    try:
        from i18n_service import t

        return t("error.component.degraded", lang, component=dependency)
    except Exception:
        return "This component is temporarily unavailable. The rest of the platform continues to operate."
