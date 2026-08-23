"""Phase 4 — Learning Compounding: predictions → outcomes → counterfactuals."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from compounding_common import dumps_json, loads_json, row_signature, utcnow, verify_row_signature

logger = logging.getLogger("BLACKDARK.LearningCompounding")

_PRED_SIGN = ("prediction_id", "symbol", "action", "confidence", "timestamp", "expiry", "oracle_prediction_id", "context_json")
_OUT_SIGN = ("outcome_id", "prediction_id", "actual_result", "accuracy_score", "verified_at", "counterfactual_json")
_CF_SIGN = ("cf_id", "prediction_id", "scenario", "alternate_action", "projected_outcome", "timestamp")


async def create_prediction(
    *,
    symbol: str,
    action: str,
    confidence: float,
    expiry: str | None = None,
    oracle_prediction_id: int | None = None,
    context: dict[str, Any] | None = None,
    prediction_id: str | None = None,
) -> dict[str, Any]:
    from database import get_connection

    pid = prediction_id or f"pred_{uuid4().hex[:14]}"
    row = {
        "prediction_id": pid,
        "symbol": str(symbol).upper(),
        "action": str(action),
        "confidence": float(confidence),
        "timestamp": utcnow(),
        "expiry": expiry,
        "oracle_prediction_id": oracle_prediction_id,
        "context_json": dumps_json(context or {}),
    }
    row["signature"] = row_signature(row, _PRED_SIGN)

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO learning_predictions (
                prediction_id, symbol, action, confidence, timestamp, expiry,
                oracle_prediction_id, context_json, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["prediction_id"],
                row["symbol"],
                row["action"],
                row["confidence"],
                row["timestamp"],
                row["expiry"],
                row["oracle_prediction_id"],
                row["context_json"],
                row["signature"],
            ),
        )
    return _pred_api(row)


async def record_outcome(
    *,
    prediction_id: str,
    actual_result: str,
    accuracy_score: float | None = None,
    counterfactual: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from database import get_connection

    oid = f"out_{uuid4().hex[:14]}"
    row = {
        "outcome_id": oid,
        "prediction_id": prediction_id,
        "actual_result": str(actual_result),
        "accuracy_score": accuracy_score,
        "verified_at": utcnow(),
        "counterfactual_json": dumps_json(counterfactual) if counterfactual else None,
    }
    row["signature"] = row_signature(row, _OUT_SIGN)

    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO learning_outcomes (
                outcome_id, prediction_id, actual_result, accuracy_score,
                verified_at, counterfactual_json, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["outcome_id"],
                row["prediction_id"],
                row["actual_result"],
                row["accuracy_score"],
                row["verified_at"],
                row["counterfactual_json"],
                row["signature"],
            ),
        )

    pred = await get_prediction(prediction_id)
    if pred:
        try:
            from knowledge_graph import create_edge, create_node, get_node

            out_node = f"outcome_{oid}"
            pred_node = f"prediction_{prediction_id}"
            if not await get_node(pred_node):
                await create_node(
                    node_id=pred_node,
                    node_type="Decision",
                    label=prediction_id,
                    properties={"prediction_id": prediction_id, "symbol": pred.get("symbol")},
                )
            await create_node(
                node_id=out_node,
                node_type="Outcome",
                label=oid,
                properties={"actual_result": actual_result, "accuracy_score": accuracy_score},
            )
            await create_edge(source_node_id=pred_node, target_node_id=out_node, edge_type="resulted_in")
        except Exception:
            logger.exception("KG learning outcome ingest failed")

    return _out_api(row)


async def get_prediction(prediction_id: str) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        raw = await (await db.execute(
            "SELECT * FROM learning_predictions WHERE prediction_id = ?", (prediction_id,)
        )).fetchone()
    return _pred_api(dict(raw)) if raw else None


async def get_prediction_with_outcome(prediction_id: str) -> dict[str, Any] | None:
    pred = await get_prediction(prediction_id)
    if not pred:
        return None
    from database import get_connection

    async with get_connection() as db:
        raw = await (await db.execute(
            "SELECT * FROM learning_outcomes WHERE prediction_id = ? ORDER BY verified_at DESC LIMIT 1",
            (prediction_id,),
        )).fetchone()
    pred["outcome"] = _out_api(dict(raw)) if raw else None
    return pred


async def accuracy_track_record(*, limit: int = 100) -> dict[str, Any]:
    from database import fetch_labeled_oracle_predictions, fetch_oracle_audit_stats

    stats = await fetch_oracle_audit_stats(limit=limit, include_synthetic=False)
    labeled = await fetch_labeled_oracle_predictions(limit=limit, include_synthetic=False)

    learning_rows = await list_learning_predictions(limit=limit)
    resolved = [r for r in labeled if r.get("resolved")]
    correct = sum(1 for r in resolved if str(r.get("label") or "") == "correct")

    history = []
    for r in (stats.get("recent") or [])[:limit]:
        if not r.get("resolved"):
            continue
        history.append(
            {
                "prediction_id": r.get("id"),
                "asset": r.get("asset"),
                "verdict": r.get("verdict"),
                "label": r.get("label"),
                "accuracy_score": r.get("accuracy_score"),
                "timestamp": r.get("timestamp"),
                "resolved_at": r.get("resolved_at"),
            }
        )

    learning_outcomes = await list_outcomes(limit=limit)
    return {
        "oracle": {
            "resolved_count": len(resolved),
            "correct_count": correct,
            "hit_rate_percent": round(correct / len(resolved) * 100, 2) if resolved else 0.0,
            "history": history,
        },
        "learning_registry": {
            "predictions": len(learning_rows),
            "outcomes": len(learning_outcomes),
            "recent_outcomes": learning_outcomes[:20],
        },
        "track_record": "historical",
        "generated_at": utcnow(),
    }


async def list_learning_predictions(*, limit: int = 100) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (await db.execute(
            "SELECT * FROM learning_predictions ORDER BY timestamp DESC LIMIT ?",
            (max(1, min(limit, 500)),),
        )).fetchall()
    return [_pred_api(dict(r)) for r in rows]


async def list_outcomes(*, limit: int = 100) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (await db.execute(
            "SELECT * FROM learning_outcomes ORDER BY verified_at DESC LIMIT ?",
            (max(1, min(limit, 500)),),
        )).fetchall()
    return [_out_api(dict(r)) for r in rows]


async def missed_opportunities(*, limit: int = 40) -> dict[str, Any]:
    from public_miss_feed import build_public_miss_feed

    feed = await build_public_miss_feed(limit=limit)
    cf_rows = await list_counterfactuals(limit=limit)
    return {
        "missed_opportunities": feed.get("items") or [],
        "count": feed.get("count", 0),
        "counterfactuals": cf_rows,
        "generated_at": utcnow(),
    }


async def log_counterfactual(
    *,
    prediction_id: str,
    scenario: str,
    alternate_action: str,
    projected_outcome: str,
) -> dict[str, Any]:
    from database import get_connection

    cf_id = f"cf_{uuid4().hex[:12]}"
    row = {
        "cf_id": cf_id,
        "prediction_id": prediction_id,
        "scenario": scenario,
        "alternate_action": alternate_action,
        "projected_outcome": projected_outcome,
        "timestamp": utcnow(),
    }
    row["signature"] = row_signature(row, _CF_SIGN)
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO counterfactual_log (
                cf_id, prediction_id, scenario, alternate_action, projected_outcome, timestamp, signature
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["cf_id"],
                row["prediction_id"],
                row["scenario"],
                row["alternate_action"],
                row["projected_outcome"],
                row["timestamp"],
                row["signature"],
            ),
        )
    row["signature_valid"] = verify_row_signature(row, _CF_SIGN)
    return row


async def list_counterfactuals(*, limit: int = 50) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (await db.execute(
            "SELECT * FROM counterfactual_log ORDER BY timestamp DESC LIMIT ?",
            (max(1, min(limit, 200)),),
        )).fetchall()
    out = []
    for r in rows:
        item = dict(r)
        item["signature_valid"] = verify_row_signature(item, _CF_SIGN)
        out.append(item)
    return out


async def sync_from_oracle_prediction(pred: dict[str, Any]) -> dict[str, Any] | None:
    """Bridge oracle_predictions row into learning registry."""
    pid = pred.get("id")
    if pid is None:
        return None
    lp_id = f"oracle_{pid}"
    existing = await get_prediction(lp_id)
    if existing:
        return existing
    return await create_prediction(
        symbol=str(pred.get("asset") or "UNKNOWN"),
        action=str(pred.get("verdict") or "observe"),
        confidence=float(pred.get("confidence") or 0) / 100.0 if float(pred.get("confidence") or 0) > 1 else float(pred.get("confidence") or 0.5),
        oracle_prediction_id=int(pid),
        context={"verdict": pred.get("verdict"), "opportunity_score": pred.get("opportunity_score")},
        prediction_id=lp_id,
    )


def _pred_api(row: dict[str, Any]) -> dict[str, Any]:
    api = {
        "prediction_id": row.get("prediction_id"),
        "symbol": row.get("symbol"),
        "action": row.get("action"),
        "confidence": row.get("confidence"),
        "timestamp": row.get("timestamp"),
        "expiry": row.get("expiry"),
        "oracle_prediction_id": row.get("oracle_prediction_id"),
        "context": loads_json(row.get("context_json")),
        "signature": row.get("signature"),
    }
    sign_row = {**row, "context_json": row.get("context_json") or dumps_json(api["context"])}
    api["signature_valid"] = verify_row_signature(sign_row, _PRED_SIGN)
    return api


def _out_api(row: dict[str, Any]) -> dict[str, Any]:
    api = {
        "outcome_id": row.get("outcome_id"),
        "prediction_id": row.get("prediction_id"),
        "actual_result": row.get("actual_result"),
        "accuracy_score": row.get("accuracy_score"),
        "verified_at": row.get("verified_at"),
        "counterfactual": loads_json(row.get("counterfactual_json")) if row.get("counterfactual_json") else None,
        "signature": row.get("signature"),
    }
    sign_row = {**row, "counterfactual_json": row.get("counterfactual_json")}
    api["signature_valid"] = verify_row_signature(sign_row, _OUT_SIGN)
    return api
