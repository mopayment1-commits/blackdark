"""Persistent security state: password history, login fingerprints, session activity."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger("BLACKDARK.SecurityStore")

PASSWORD_HISTORY_LIMIT = 5


async def _ensure_security_tables_on_db(db: Any) -> None:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_password_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_password_history_user
            ON user_password_history (user_id, created_at DESC)
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_login_fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                device_hash TEXT NOT NULL,
                country TEXT,
                user_agent TEXT,
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                UNIQUE(user_id, device_hash)
            )
            """
        )
        await db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_login_fp_user
            ON user_login_fingerprints (user_id, last_seen_at DESC)
            """
        )
        from database import _ensure_missing_columns

        await _ensure_missing_columns(
            db,
            "user_sessions",
            (
                (
                    "last_activity_at",
                    "ALTER TABLE user_sessions ADD COLUMN last_activity_at TEXT",
                ),
            ),
        )


async def ensure_security_tables(db: Any | None = None) -> None:
    from database import get_connection

    if db is not None:
        await _ensure_security_tables_on_db(db)
        return
    async with get_connection() as conn:
        await _ensure_security_tables_on_db(conn)


async def append_password_history(user_id: int, password_hash: str) -> None:
    from database import get_connection, _utcnow_iso

    await ensure_security_tables()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO user_password_history (user_id, password_hash, created_at)
            VALUES (?, ?, ?)
            """,
            (int(user_id), password_hash, _utcnow_iso()),
        )
        rows = await db.execute(
            """
            SELECT id FROM user_password_history
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (int(user_id),),
        )
        keep = await rows.fetchall()
        if len(keep) > PASSWORD_HISTORY_LIMIT:
            drop_ids = [int(r[0] if not isinstance(r, dict) else r["id"]) for r in keep[PASSWORD_HISTORY_LIMIT:]]
            for drop_id in drop_ids:
                await db.execute("DELETE FROM user_password_history WHERE id = ?", (drop_id,))


async def password_reused_recently(user_id: int, plain_password: str) -> bool:
    from database import get_connection
    from password_kdf import verify_password

    await ensure_security_tables()
    async with get_connection() as db:
        rows = await db.execute(
            """
            SELECT password_hash FROM user_password_history
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (int(user_id), PASSWORD_HISTORY_LIMIT),
        )
        hist = await rows.fetchall()
    for row in hist:
        stored = row[0] if not isinstance(row, dict) else row.get("password_hash")
        if stored and verify_password(plain_password, str(stored)):
            return True
    return False


def device_fingerprint_hash(user_agent: str, *, accept_language: str = "") -> str:
    raw = f"{user_agent}|{accept_language}".strip().lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def record_login_fingerprint(
    user_id: int,
    *,
    user_agent: str,
    country: str | None,
) -> dict[str, Any]:
    from database import get_connection, _utcnow_iso

    await ensure_security_tables()
    device_hash = device_fingerprint_hash(user_agent)
    now = _utcnow_iso()
    is_new_device = False
    is_new_country = False
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT id, country FROM user_login_fingerprints
                WHERE user_id = ? AND device_hash = ?
                """,
                (int(user_id), device_hash),
            )
        ).fetchone()
        if row is None:
            is_new_device = True
            await db.execute(
                """
                INSERT INTO user_login_fingerprints
                (user_id, device_hash, country, user_agent, first_seen_at, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (int(user_id), device_hash, country, user_agent[:512], now, now),
            )
        else:
            prev_country = row[1] if not isinstance(row, dict) else row.get("country")
            if country and prev_country and str(country).upper() != str(prev_country).upper():
                is_new_country = True
            await db.execute(
                """
                UPDATE user_login_fingerprints
                SET last_seen_at = ?, country = COALESCE(?, country), user_agent = ?
                WHERE user_id = ? AND device_hash = ?
                """,
                (now, country, user_agent[:512], int(user_id), device_hash),
            )
        if country:
            other = await (
                await db.execute(
                    """
                    SELECT COUNT(*) AS c FROM user_login_fingerprints
                    WHERE user_id = ? AND country IS NOT NULL AND country != ?
                    """,
                    (int(user_id), country),
                )
            ).fetchone()
            from database import _sql_count

            if _sql_count(other) == 0 and not is_new_device:
                pass
            elif _sql_count(other) == 0 and is_new_device:
                is_new_country = False
            elif is_new_device:
                is_new_country = True
    return {
        "device_hash": device_hash,
        "is_new_device": is_new_device,
        "is_new_country": is_new_country,
        "country": country,
    }


def session_idle_minutes() -> int:
    import os

    raw = int(os.getenv("AUTH_SESSION_IDLE_MINUTES", "30"))
    return max(15, min(120, raw))


def session_idle_cutoff_iso() -> str:
    return (datetime.now(UTC) - timedelta(minutes=session_idle_minutes())).isoformat()


async def touch_session_activity(token_hash: str) -> None:
    from database import get_connection, _utcnow_iso

    await ensure_security_tables()
    async with get_connection() as db:
        await db.execute(
            "UPDATE user_sessions SET last_activity_at = ? WHERE token = ?",
            (_utcnow_iso(), token_hash),
        )


async def session_idle_expired(token_hash: str) -> bool:
    from database import get_connection

    cutoff = session_idle_cutoff_iso()
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT last_activity_at FROM user_sessions WHERE token = ?
                """,
                (token_hash,),
            )
        ).fetchone()
    if row is None:
        return True
    last = row[0] if not isinstance(row, dict) else row.get("last_activity_at")
    if not last:
        return False
    return str(last) < cutoff
