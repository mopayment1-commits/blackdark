"""Reconciliation worker — Stripe vs Billing Projection vs Entitlement (BILL-029)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from billing.entitlement_state import decide_entitlement
from billing.plan_registry import normalize_plan

logger = logging.getLogger("BLACKDARK.Billing.Reconciliation")


class ReconciliationResult(StrEnum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"


async def reconcile_account(
    sub: dict[str, Any],
    *,
    stripe_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare billing projection vs entitlement decision vs optional Stripe snapshot."""
    uid = int(sub["user_id"])
    decision = decide_entitlement(sub)
    projection_plan = normalize_plan(str(sub.get("plan")))
    projection_status = str(sub.get("subscription_status"))
    effective = decision.effective_tier

    mismatches: list[str] = []
    if effective != projection_plan and decision.state.value not in {"PAID_RECOVERY", "PAID_CANCELING_AT_PERIOD_END"}:
        if not (projection_status == "past_due" and decision.allowed):
            mismatches.append(f"entitlement_tier={effective} vs projection_plan={projection_plan}")

    if decision.allowed and projection_plan == "free" and effective != "free":
        mismatches.append("paid_entitlement_without_billing_proof")

    if not decision.allowed and projection_plan not in {"free"} and str(sub.get("payment_status")) == "current":
        mismatches.append("entitlement_denied_with_current_payment")

    stripe_result = ReconciliationResult.UNKNOWN
    if stripe_snapshot:
        stripe_plan = normalize_plan((stripe_snapshot.get("metadata") or {}).get("tier"))
        stripe_status = str(stripe_snapshot.get("status") or "")
        if stripe_plan and stripe_plan != projection_plan:
            mismatches.append(f"stripe_plan={stripe_plan} vs projection={projection_plan}")
        if stripe_status and stripe_status != projection_status and stripe_status not in {"active", "trialing"}:
            if not (stripe_status == "past_due" and projection_status == "past_due"):
                mismatches.append(f"stripe_status={stripe_status} vs projection={projection_status}")
        stripe_result = ReconciliationResult.MISMATCH if mismatches else ReconciliationResult.MATCH
    else:
        stripe_result = ReconciliationResult.UNKNOWN

    result = ReconciliationResult.MISMATCH if mismatches else ReconciliationResult.MATCH
    record = {
        "user_id": uid,
        "email": sub.get("email"),
        "result": result.value,
        "stripe_result": stripe_result.value,
        "mismatches": mismatches,
        "projection_plan": projection_plan,
        "effective_tier": effective,
        "entitlement_state": decision.state.value,
        "checked_at": datetime.now(UTC).isoformat(),
    }
    if mismatches:
        await _persist_mismatch(record)
        logger.warning("billing_reconciliation_mismatch | user_id=%s %s", uid, mismatches)
    return record


async def _persist_mismatch(record: dict[str, Any]) -> None:
    from database import get_connection

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO billing_reconciliation_runs (
                user_id, email, result, mismatches_json, checked_at
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                record["user_id"],
                record.get("email"),
                record["result"],
                __import__("json").dumps(record.get("mismatches") or []),
                record["checked_at"],
            ),
        )


async def run_reconciliation_batch(*, limit: int = 100) -> dict[str, Any]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT * FROM subscription_accounts
                WHERE plan != 'free' OR subscription_status != 'active'
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (int(limit),),
            )
        ).fetchall()
    results = {"MATCH": 0, "MISMATCH": 0, "UNKNOWN": 0, "records": []}
    for row in rows:
        sub = dict(row)
        sub["cancel_at_period_end"] = bool(int(sub.get("cancel_at_period_end") or 0))
        rec = await reconcile_account(sub)
        results[rec["result"]] = results.get(rec["result"], 0) + 1
        if rec["result"] == "MISMATCH":
            results["records"].append(rec)
    return results
