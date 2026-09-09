"""Break-glass manual entitlement override (BILL-038)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from billing.audit_ledger import record_audit
from billing.plan_registry import normalize_plan, plan_rank

logger = logging.getLogger("BLACKDARK.Billing.BreakGlass")


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


async def create_override(
    *,
    user_id: int,
    actor: str,
    actor_role: str,
    reason: str,
    ticket: str,
    new_tier: str,
    old_tier: str | None = None,
    expires_in_hours: int = 24,
    approval_actor: str | None = None,
    require_dual_approval: bool = False,
) -> dict[str, Any]:
    """High-risk paid override requires dual approval when tier is paid."""
    tier = normalize_plan(new_tier)
    is_paid = plan_rank(tier) > 0
    if is_paid and require_dual_approval and not approval_actor:
        raise ValueError("Dual approval required for paid entitlement override")
    if is_paid and plan_rank(tier) >= 3 and not approval_actor:
        raise ValueError("Dual approval required for QUANT/INSTITUTIONAL override")

    expires_at = (datetime.now(UTC) + timedelta(hours=expires_in_hours)).isoformat()
    from database import get_connection

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO billing_break_glass_overrides (
                user_id, actor, actor_role, reason, ticket,
                old_tier, new_tier, created_at, expires_at,
                approval_actor, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                int(user_id),
                actor,
                actor_role,
                reason[:500],
                ticket[:120],
                normalize_plan(old_tier) if old_tier else None,
                tier,
                _utcnow_iso(),
                expires_at,
                approval_actor,
            ),
        )
    await record_audit(
        action="BREAK_GLASS_OVERRIDE",
        actor=actor,
        user_id=user_id,
        old_plan=old_tier,
        new_plan=tier,
        reason=f"ticket={ticket}; {reason}",
        metadata={"approval_actor": approval_actor, "expires_at": expires_at},
    )
    logger.warning("break_glass | user_id=%s actor=%s tier=%s ticket=%s", user_id, actor, tier, ticket)
    return {"user_id": user_id, "new_tier": tier, "expires_at": expires_at}


async def active_override_for_user(user_id: int) -> dict[str, Any] | None:
    from database import get_connection

    now = _utcnow_iso()
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT * FROM billing_break_glass_overrides
                WHERE user_id = ? AND active = 1 AND expires_at > ?
                ORDER BY id DESC LIMIT 1
                """,
                (int(user_id), now),
            )
        ).fetchone()
    if not row:
        return None
    data = dict(row)
    data["new_tier"] = data.get("new_tier")
    return data


async def revoke_override(override_id: int, *, actor: str) -> None:
    from database import get_connection

    async with get_connection() as db:
        await db.execute(
            "UPDATE billing_break_glass_overrides SET active = 0 WHERE id = ?",
            (int(override_id),),
        )
    await record_audit(action="BREAK_GLASS_REVOKED", actor=actor, reason=f"override_id={override_id}")
