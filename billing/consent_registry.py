"""Consent evidence registry (BILL-048)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


async def record_consent(
    *,
    user_id: int,
    terms_version: str,
    renewal_disclosure_version: str,
    consent_source: str,
    tier: str,
    billing_frequency: str = "monthly",
) -> int:
    from database import get_connection

    now = datetime.now(UTC).isoformat()
    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO billing_consent_records (
                user_id, terms_version, renewal_disclosure_version,
                consent_at, consent_source, tier, billing_frequency
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                terms_version[:40],
                renewal_disclosure_version[:40],
                now,
                consent_source[:80],
                tier[:40],
                billing_frequency[:20],
            ),
        )
        return int(cursor.lastrowid or 0)


async def latest_consent(user_id: int) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT * FROM billing_consent_records
                WHERE user_id = ? ORDER BY id DESC LIMIT 1
                """,
                (int(user_id),),
            )
        ).fetchone()
    return dict(row) if row else None
