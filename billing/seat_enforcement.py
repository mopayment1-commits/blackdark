"""B2B seat enforcement (BILL-044) and org billing architecture (BILL-043)."""

from __future__ import annotations

from typing import Any


async def check_seat_availability(org_id: int) -> dict[str, Any]:
    from database import get_connection

    async with get_connection() as db:
        org = await (
            await db.execute("SELECT * FROM billing_org_accounts WHERE org_id = ?", (int(org_id),))
        ).fetchone()
        if not org:
            return {"allowed": False, "reason": "org_not_found"}
        paid_seats = int(org["paid_seats"] or 0)
        active = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM billing_org_members
                WHERE org_id = ? AND entitled = 1
                """,
                (int(org_id),),
            )
        ).fetchone()
    active_count = int(active["c"] if active else 0)
    return {
        "org_id": org_id,
        "paid_seats": paid_seats,
        "active_entitled_members": active_count,
        "allowed": active_count < paid_seats,
        "reason": "seat_limit_reached" if active_count >= paid_seats else "ok",
    }


async def ensure_org_billing_account(
    *,
    org_id: int,
    billing_owner_user_id: int,
    paid_seats: int = 1,
    contract_id: str | None = None,
    custom_entitlement_profile: str | None = None,
) -> dict[str, Any]:
    from database import get_connection
    from datetime import UTC, datetime

    now = datetime.now(UTC).isoformat()
    async with get_connection() as db:
        existing = await (
            await db.execute("SELECT * FROM billing_org_accounts WHERE org_id = ?", (int(org_id),))
        ).fetchone()
        if existing:
            return dict(existing)
        await db.execute(
            """
            INSERT INTO billing_org_accounts (
                org_id, billing_owner_user_id, paid_seats, contract_id,
                custom_entitlement_profile, contract_start, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(org_id),
                int(billing_owner_user_id),
                int(paid_seats),
                contract_id,
                custom_entitlement_profile,
                now,
                now,
            ),
        )
        row = await (
            await db.execute("SELECT * FROM billing_org_accounts WHERE org_id = ?", (int(org_id),))
        ).fetchone()
    return dict(row) if row else {}
