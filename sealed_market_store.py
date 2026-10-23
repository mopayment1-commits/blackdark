"""Persistence for Oracle Sealed Prediction Markets."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.SealedMarket")

MAX_BET_USDT = 50.0
PLATFORM_FEE_RATE = 0.05


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


async def _create_tables(db: Any) -> None:
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS oracle_sealed_markets (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id       INTEGER NOT NULL UNIQUE,
            asset               TEXT    NOT NULL,
            decision_action     TEXT    NOT NULL,
            verdict_raw         TEXT    NOT NULL,
            certificate_hash    TEXT    NOT NULL,
            sealed_at           TEXT    NOT NULL,
            betting_closes_at   TEXT    NOT NULL,
            status              TEXT    NOT NULL,
            total_pool_usdt     REAL    NOT NULL DEFAULT 0,
            yes_pool_usdt       REAL    NOT NULL DEFAULT 0,
            no_pool_usdt        REAL    NOT NULL DEFAULT 0,
            participant_count   INTEGER NOT NULL DEFAULT 0,
            outcome_label       TEXT,
            platform_fee_usdt   REAL,
            settled_at          TEXT,
            created_at          TEXT    NOT NULL,
            updated_at          TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sealed_markets_status
            ON oracle_sealed_markets (status, betting_closes_at DESC)
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS oracle_sealed_market_bets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            market_id       INTEGER NOT NULL,
            user_id         INTEGER NOT NULL,
            side            TEXT    NOT NULL,
            stake_usdt      REAL    NOT NULL,
            funding         TEXT    NOT NULL,
            status          TEXT    NOT NULL,
            payout_usdt     REAL,
            created_at      TEXT    NOT NULL
        )
        """
    )
    await db.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_sealed_bets_market
            ON oracle_sealed_market_bets (market_id, status)
        """
    )
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS user_market_balances (
            user_id         INTEGER PRIMARY KEY,
            balance_usdt    REAL    NOT NULL DEFAULT 0,
            updated_at      TEXT    NOT NULL
        )
        """
    )


async def ensure_sealed_market_schema() -> None:
    from database import get_connection

    async with get_connection() as db:
        await _create_tables(db)


async def ensure_sealed_market_schema_on_db(db: Any) -> None:
    await _create_tables(db)


async def insert_market(row: dict[str, Any]) -> int:
    from database import get_connection

    await ensure_sealed_market_schema()
    now = _utcnow_iso()
    async with get_connection() as db:
        cur = await db.execute(
            """
            INSERT INTO oracle_sealed_markets (
                prediction_id, asset, decision_action, verdict_raw, certificate_hash,
                sealed_at, betting_closes_at, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(row["prediction_id"]),
                row["asset"],
                row["decision_action"],
                row["verdict_raw"],
                row["certificate_hash"],
                row["sealed_at"],
                row["betting_closes_at"],
                row.get("status", "open"),
                now,
                now,
            ),
        )
        return int(getattr(cur, "lastrowid", None) or 0)


async def fetch_market_by_prediction(prediction_id: int) -> dict[str, Any] | None:
    from database import get_connection

    await ensure_sealed_market_schema()
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT * FROM oracle_sealed_markets WHERE prediction_id = ?",
                (int(prediction_id),),
            )
        ).fetchone()
    return _row_dict(row) or None


async def fetch_market(market_id: int) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute("SELECT * FROM oracle_sealed_markets WHERE id = ?", (int(market_id),))
        ).fetchone()
    return _row_dict(row) or None


async def list_markets(*, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    from database import get_connection

    await ensure_sealed_market_schema()
    async with get_connection() as db:
        if status:
            rows = await (
                await db.execute(
                    """
                    SELECT * FROM oracle_sealed_markets
                    WHERE status = ?
                    ORDER BY betting_closes_at DESC
                    LIMIT ?
                    """,
                    (status, int(limit)),
                )
            ).fetchall()
        else:
            rows = await (
                await db.execute(
                    """
                    SELECT * FROM oracle_sealed_markets
                    ORDER BY betting_closes_at DESC
                    LIMIT ?
                    """,
                    (int(limit),),
                )
            ).fetchall()
    return [_row_dict(r) for r in rows]


async def update_market(market_id: int, **fields: Any) -> None:
    from database import get_connection

    allowed = {
        "status",
        "total_pool_usdt",
        "yes_pool_usdt",
        "no_pool_usdt",
        "participant_count",
        "outcome_label",
        "platform_fee_usdt",
        "settled_at",
        "updated_at",
    }
    parts: list[str] = []
    values: list[Any] = []
    for k, v in fields.items():
        if k in allowed:
            parts.append(f"{k} = ?")
            values.append(v)
    if not parts:
        return
    parts.append("updated_at = ?")
    values.append(_utcnow_iso())
    values.append(int(market_id))
    sql = f"UPDATE oracle_sealed_markets SET {', '.join(parts)} WHERE id = ?"  # nosec B608
    async with get_connection() as db:
        await db.execute(sql, tuple(values))


async def insert_bet(row: dict[str, Any]) -> int:
    from database import get_connection

    await ensure_sealed_market_schema()
    async with get_connection() as db:
        cur = await db.execute(
            """
            INSERT INTO oracle_sealed_market_bets (
                market_id, user_id, side, stake_usdt, funding, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(row["market_id"]),
                int(row["user_id"]),
                row["side"],
                float(row["stake_usdt"]),
                row.get("funding", "internal"),
                row.get("status", "open"),
                _utcnow_iso(),
            ),
        )
        return int(getattr(cur, "lastrowid", None) or 0)


async def list_bets_for_market(market_id: int) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (
            await db.execute(
                "SELECT id, market_id, user_id, side, stake_usdt, funding, status, payout_usdt, created_at "
                "FROM oracle_sealed_market_bets WHERE market_id = ?",
                (int(market_id),),
            )
        ).fetchall()
    return [_row_dict(r) for r in rows]


async def list_open_bets(market_id: int) -> list[dict[str, Any]]:
    bets = await list_bets_for_market(market_id)
    return [b for b in bets if b.get("status") == "open"]


async def update_bet(bet_id: int, **fields: Any) -> None:
    from database import get_connection

    allowed = {"status", "payout_usdt"}
    parts = []
    values: list[Any] = []
    for k, v in fields.items():
        if k in allowed:
            parts.append(f"{k} = ?")
            values.append(v)
    if not parts:
        return
    values.append(int(bet_id))
    sql = f"UPDATE oracle_sealed_market_bets SET {', '.join(parts)} WHERE id = ?"  # nosec B608
    async with get_connection() as db:
        await db.execute(sql, tuple(values))


async def get_user_balance(user_id: int) -> float:
    from database import get_connection

    await ensure_sealed_market_schema()
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT balance_usdt FROM user_market_balances WHERE user_id = ?",
                (int(user_id),),
            )
        ).fetchone()
    if not row:
        return 0.0
    return float(_row_dict(row).get("balance_usdt") or 0.0)


async def adjust_user_balance(user_id: int, delta: float) -> float:
    from database import get_connection

    await ensure_sealed_market_schema()
    now = _utcnow_iso()
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT balance_usdt FROM user_market_balances WHERE user_id = ?",
                (int(user_id),),
            )
        ).fetchone()
        if row:
            bal = float(_row_dict(row).get("balance_usdt") or 0.0) + float(delta)
            await db.execute(
                "UPDATE user_market_balances SET balance_usdt = ?, updated_at = ? WHERE user_id = ?",
                (bal, now, int(user_id)),
            )
        else:
            bal = max(0.0, float(delta))
            await db.execute(
                "INSERT INTO user_market_balances (user_id, balance_usdt, updated_at) VALUES (?, ?, ?)",
                (int(user_id), bal, now),
            )
    return bal
