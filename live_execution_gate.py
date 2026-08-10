"""
BLACKDARK — Live execution fail-closed gate.

Soft Launch never allows live money paths, even if LIVE_EXECUTION_ALLOW_API is set.
Strict production still requires an explicit allow flag for HTTP live orders.
"""

from __future__ import annotations

import os
from typing import Any


def soft_launch_active() -> bool:
    return os.getenv("SOFT_LAUNCH", "").lower() in {"1", "true", "yes"}


def live_execution_flag_enabled() -> bool:
    return os.getenv("LIVE_EXECUTION_ALLOW_API", "false").lower() in {"1", "true", "yes"}


def jupiter_live_flag_enabled() -> bool:
    return os.getenv("JUPITER_LIVE_EXECUTION", "").lower() in {"1", "true", "yes"}


def soft_launch_forbids_live_money() -> bool:
    """True when Soft Launch is active and any live-money flag is on (unsafe)."""
    if not soft_launch_active():
        return False
    return live_execution_flag_enabled() or jupiter_live_flag_enabled()


def assert_live_http_execution_allowed() -> None:
    """Raise HTTP 403 unless live HTTP execution is explicitly allowed and Soft Launch is off."""
    from fastapi import HTTPException

    if soft_launch_active():
        try:
            from security_events import record_security_event

            record_security_event(
                "live_execution_blocked_soft_launch",
                severity="critical",
                detail={"flag": "LIVE_EXECUTION_ALLOW_API"},
            )
        except Exception:
            pass
        raise HTTPException(
            status_code=403,
            detail={
                "error": "soft_launch_forbids_live_execution",
                "message": "Soft Launch forbids live execution. Unset SOFT_LAUNCH and use Postgres+ops bar first.",
            },
        )
    if not live_execution_flag_enabled():
        raise HTTPException(
            status_code=403,
            detail="Live execution via API disabled. Set LIVE_EXECUTION_ALLOW_API=true for admin live orders.",
        )


def force_safe_dry_run(requested: Any) -> bool:
    """Return True for dry-run. Live (False) only when Soft Launch is off and allow flag is set."""
    if requested is None:
        return True
    want_live = not bool(requested)
    if not want_live:
        return True
    assert_live_http_execution_allowed()
    return False
