"""Step-up authentication for high-risk financial actions."""

from __future__ import annotations

from typing import Any

from identity.step_up import SENSITIVE_ACTIONS, require_step_up


async def enforce_billing_step_up(user: dict[str, Any], *, action: str = "billing.sensitive") -> None:
    if action not in SENSITIVE_ACTIONS:
        raise ValueError(f"Unknown sensitive action: {action}")
    await require_step_up(user, action=action)


async def enforce_financial_step_up(user: dict[str, Any], *, action: str) -> None:
    await require_step_up(user, action=action)
