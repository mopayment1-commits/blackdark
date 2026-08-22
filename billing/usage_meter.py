"""Usage metering — enforce plan limits (fail-closed)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from billing.plan_registry import normalize_plan
from auth_service import TIER_FEATURES


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _period_key(capability_key: str) -> str:
    now = datetime.now(UTC)
    if capability_key.endswith("_daily"):
        return now.strftime("%Y-%m-%d")
    return now.strftime("%Y-%m")


def _limit_for(plan: str, capability_key: str) -> int | None:
    features = TIER_FEATURES.get(normalize_plan(plan), TIER_FEATURES["free"])
    if capability_key == "oracle_decision":
        daily = features.get("oracle_daily_limit")
        return int(daily) if daily is not None else None
    if capability_key == "export":
        return features.get("export_monthly_limit")
    if capability_key == "api_call":
        return features.get("api_monthly_limit")
    if capability_key == "backtest_hour":
        return features.get("backtest_hours_monthly")
    return None


async def get_usage(user_id: int, capability_key: str) -> dict[str, Any]:
    from database import get_connection

    period = _period_key(capability_key)
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT count, limit_value FROM usage_meters
                WHERE user_id = ? AND capability_key = ? AND period_key = ?
                """,
                (int(user_id), capability_key, period),
            )
        ).fetchone()
    if row is None:
        return {"count": 0, "period_key": period, "limit": None}
    return {"count": int(row["count"]), "period_key": period, "limit": row["limit_value"]}


async def check_and_increment(
    user_id: int,
    plan: str,
    capability_key: str,
    *,
    amount: int = 1,
) -> dict[str, Any]:
    """Return allowed=True if under limit; increment atomically when allowed."""
    from database import get_connection

    limit = _limit_for(plan, capability_key)
    if limit is None:
        return {"allowed": True, "unlimited": True, "count": None, "limit": None}

    period = _period_key(capability_key)
    now = _utcnow_iso()
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT id, count FROM usage_meters
                WHERE user_id = ? AND capability_key = ? AND period_key = ?
                """,
                (int(user_id), capability_key, period),
            )
        ).fetchone()
        current = int(row["count"]) if row else 0
        if current + amount > limit:
            return {
                "allowed": False,
                "reason": "usage_exceeded",
                "count": current,
                "limit": limit,
                "period_key": period,
            }
        if row:
            await db.execute(
                "UPDATE usage_meters SET count = count + ?, updated_at = ? WHERE id = ?",
                (amount, now, int(row["id"])),
            )
            new_count = current + amount
        else:
            await db.execute(
                """
                INSERT INTO usage_meters (user_id, capability_key, period_key, count, limit_value, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (int(user_id), capability_key, period, amount, limit, now),
            )
            new_count = amount
    return {"allowed": True, "count": new_count, "limit": limit, "period_key": period}
