"""Fault injection access control — fail-closed in production (ERR-050)."""

from __future__ import annotations

import os

from fastapi import HTTPException


def is_production_environment() -> bool:
    env = (
        os.getenv("ENV")
        or os.getenv("ENVIRONMENT")
        or os.getenv("BLACKDARK_ENV")
        or ""
    ).lower()
    return env in {"production", "prod", "live"}


def fault_injection_enabled() -> bool:
    """Explicit opt-in only; fail-closed when ambiguous in production."""
    if os.getenv("DISABLE_FAULT_INJECTION", "").lower() in {"1", "true", "yes"}:
        return False
    if is_production_environment():
        return os.getenv("ENABLE_FAULT_INJECTION", "").lower() in {"1", "true", "yes"}
    soft = os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}
    explicit = os.getenv("ENABLE_FAULT_INJECTION", "").lower() in {"1", "true", "yes"}
    return explicit or soft


def assert_fault_injection_allowed() -> None:
    if not fault_injection_enabled():
        raise HTTPException(status_code=404, detail="Not found")
