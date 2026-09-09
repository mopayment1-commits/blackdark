"""Break-glass facade — emergency privileged access controls."""

from __future__ import annotations

from typing import Any


async def create_break_glass_override(**kwargs: Any) -> dict[str, Any]:
    from billing.break_glass import create_override

    result = await create_override(**kwargs)
    from financial_data_security.audit_trail import record_financial_audit

    record_financial_audit(
        actor=str(kwargs.get("actor") or "unknown"),
        action="break_glass.override",
        resource=f"user:{kwargs.get('user_id')}",
        result="created",
        auth_strength="break_glass",
        policy_decision="dual_approval" if kwargs.get("approval_actor") else "single_approval",
        meta={"ticket": kwargs.get("ticket"), "new_tier": kwargs.get("new_tier")},
    )
    try:
        from security_events import record_security_event

        record_security_event(
            event_type="break_glass_override",
            severity="critical",
            detail={"user_id": kwargs.get("user_id"), "actor": kwargs.get("actor")},
        )
    except Exception:
        pass
    return result


def break_glass_status() -> dict[str, Any]:
    return {
        "default_state": "disabled_until_invoked",
        "dual_approval_for_paid": True,
        "time_limited": True,
        "audited": True,
        "alerted": True,
    }
