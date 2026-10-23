"""Persistence for Verified Miss Bounty claims (public accuracy ledger)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.MissBounty")


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _row_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return dict(row)
    try:
        return dict(row)
    except Exception:
        return {}


async def _create_miss_bounty_tables(db: Any) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS miss_bounty_claims (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            public_ref          TEXT    NOT NULL UNIQUE,
            user_id             INTEGER NOT NULL,
            prediction_id       INTEGER NOT NULL,
            decision_link       TEXT    NOT NULL,
            source_a_url        TEXT    NOT NULL,
            source_b_url        TEXT    NOT NULL,
            source_a_close      REAL    NOT NULL,
            source_b_close      REAL    NOT NULL,
            agreed_close        REAL,
            status              TEXT    NOT NULL,
            auto_reject_reason  TEXT,
            review_due_at       TEXT    NOT NULL,
            reviewed_at         TEXT,
            reviewer_note       TEXT,
            reward_discount_pct INTEGER NOT NULL DEFAULT 20,
            reward_months       INTEGER NOT NULL DEFAULT 1,
            created_at          TEXT    NOT NULL,
            updated_at          TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_miss_bounty_user_created
            ON miss_bounty_claims (user_id, created_at DESC)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_miss_bounty_status_created
            ON miss_bounty_claims (status, created_at DESC)
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_miss_bounty_prediction
            ON miss_bounty_claims (prediction_id)
        """
    )


async def ensure_miss_bounty_schema() -> None:
    from database import get_connection

    async with get_connection() as db:
        await _create_miss_bounty_tables(db)


async def ensure_miss_bounty_schema_on_db(db: Any) -> None:
    await _create_miss_bounty_tables(db)


async def insert_miss_bounty_claim(row: dict[str, Any]) -> int:
    from database import get_connection

    await ensure_miss_bounty_schema()
    now = _utcnow_iso()
    async with get_connection() as db:
        cur = await db.execute(
            """
            INSERT INTO miss_bounty_claims (
                public_ref, user_id, prediction_id, decision_link,
                source_a_url, source_b_url, source_a_close, source_b_close,
                agreed_close, status, auto_reject_reason, review_due_at,
                reward_discount_pct, reward_months, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["public_ref"],
                int(row["user_id"]),
                int(row["prediction_id"]),
                row["decision_link"],
                row["source_a_url"],
                row["source_b_url"],
                float(row["source_a_close"]),
                float(row["source_b_close"]),
                row.get("agreed_close"),
                row["status"],
                row.get("auto_reject_reason"),
                row["review_due_at"],
                int(row.get("reward_discount_pct", 20)),
                int(row.get("reward_months", 1)),
                now,
                now,
            ),
        )
        last_id = getattr(cur, "lastrowid", None)
        if last_id is None:
            fetched = await (
                await db.execute(
                    "SELECT id FROM miss_bounty_claims WHERE public_ref = ?",
                    (row["public_ref"],),
                )
            ).fetchone()
            return int(_row_dict(fetched).get("id") or 0)
        return int(last_id)


async def fetch_miss_bounty_claim(claim_id: int) -> dict[str, Any] | None:
    from database import get_connection

    await ensure_miss_bounty_schema()
    async with get_connection() as db:
        row = await (
            await db.execute("SELECT * FROM miss_bounty_claims WHERE id = ?", (int(claim_id),))
        ).fetchone()
    data = _row_dict(row)
    return data or None


async def fetch_miss_bounty_by_ref(public_ref: str) -> dict[str, Any] | None:
    from database import get_connection

    await ensure_miss_bounty_schema()
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT * FROM miss_bounty_claims WHERE public_ref = ?",
                (public_ref.strip(),),
            )
        ).fetchone()
    data = _row_dict(row)
    return data or None


async def update_miss_bounty_claim(claim_id: int, **fields: Any) -> None:
    from database import get_connection

    if not fields:
        return
    allowed = {
        "status",
        "auto_reject_reason",
        "reviewed_at",
        "reviewer_note",
        "agreed_close",
        "updated_at",
    }
    parts: list[str] = []
    values: list[Any] = []
    for key, val in fields.items():
        if key not in allowed:
            continue
        parts.append(f"{key} = ?")
        values.append(val)
    if not parts:
        return
    parts.append("updated_at = ?")
    values.append(_utcnow_iso())
    values.append(int(claim_id))
    sql = f"UPDATE miss_bounty_claims SET {', '.join(parts)} WHERE id = ?"  # nosec B608
    async with get_connection() as db:
        await db.execute(sql, tuple(values))


async def count_miss_bounty_approved_on_day(day_key: str) -> int:
    """day_key = YYYY-MM-DD UTC for reviewed_at date."""
    from database import get_connection

    await ensure_miss_bounty_schema()
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT COUNT(*) FROM miss_bounty_claims
                WHERE status = 'approved'
                  AND reviewed_at IS NOT NULL
                  AND substr(reviewed_at, 1, 10) = ?
                """,
                (day_key,),
            )
        ).fetchone()
    from database import _sql_count

    return _sql_count(row)


async def user_miss_bounty_claims_since(
    user_id: int,
    *,
    since_iso: str,
    statuses: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    from database import get_connection

    await ensure_miss_bounty_schema()
    async with get_connection() as db:
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            sql = (
                f"SELECT * FROM miss_bounty_claims WHERE user_id = ? "
                f"AND created_at >= ? AND status IN ({placeholders}) "
                "ORDER BY created_at DESC"
            )
            params: tuple[Any, ...] = (int(user_id), since_iso, *statuses)
        else:
            sql = (
                "SELECT * FROM miss_bounty_claims WHERE user_id = ? AND created_at >= ? "
                "ORDER BY created_at DESC"
            )
            params = (int(user_id), since_iso)
        rows = await (await db.execute(sql, params)).fetchall()
    return [_row_dict(r) for r in rows]


async def fetch_public_miss_bounty_log(limit: int = 100) -> list[dict[str, Any]]:
    from database import get_connection, fetch_oracle_prediction_public_row

    await ensure_miss_bounty_schema()
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT public_ref, prediction_id, status, auto_reject_reason,
                       reviewer_note, reviewed_at, created_at, agreed_close
                FROM miss_bounty_claims
                WHERE status IN ('approved', 'rejected', 'auto_rejected')
                ORDER BY COALESCE(reviewed_at, created_at) DESC
                LIMIT ?
                """,
                (int(limit),),
            )
        ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        data = _row_dict(row)
        pred = await fetch_oracle_prediction_public_row(int(data.get("prediction_id") or 0))
        out.append(
            {
                "public_ref": data.get("public_ref"),
                "prediction_id": data.get("prediction_id"),
                "asset": pred.get("asset") if pred else None,
                "verdict": pred.get("verdict") if pred else None,
                "label": pred.get("label") if pred else None,
                "status": data.get("status"),
                "outcome_note": data.get("reviewer_note") or data.get("auto_reject_reason"),
                "decided_at": data.get("reviewed_at") or data.get("created_at"),
                "agreed_close": data.get("agreed_close"),
            }
        )
    return out


async def insert_miss_bounty_reward(
    *,
    user_id: int,
    claim_id: int,
    discount_percent: int,
    billing_months: int,
) -> None:
    from database import get_connection

    await ensure_miss_bounty_schema()
    async with get_connection() as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS miss_bounty_rewards (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL,
                claim_id         INTEGER NOT NULL UNIQUE,
                discount_percent INTEGER NOT NULL,
                billing_months   INTEGER NOT NULL,
                redeemed_at      TEXT,
                created_at       TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            INSERT INTO miss_bounty_rewards (
                user_id, claim_id, discount_percent, billing_months, created_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                int(claim_id),
                int(discount_percent),
                int(billing_months),
                _utcnow_iso(),
            ),
        )


async def list_pending_miss_bounty_claims(limit: int = 50) -> list[dict[str, Any]]:
    from database import get_connection

    await ensure_miss_bounty_schema()
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT * FROM miss_bounty_claims
                WHERE status = 'pending_review'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (int(limit),),
            )
        ).fetchall()
    return [_row_dict(r) for r in rows]
