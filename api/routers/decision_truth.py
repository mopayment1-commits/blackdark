"""Decision Truth API (DTS-016 contract surface)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

router = APIRouter(tags=["decision-truth"])


@router.get("/api/decision-truth/status")
async def decision_truth_status() -> dict[str, Any]:
    from decision_truth import pipeline_status

    return pipeline_status()


@router.post("/api/decision-truth/evaluate")
async def decision_truth_evaluate(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    from decision_truth import evaluate_opportunity

    contract = evaluate_opportunity(body, symbol=body.get("symbol"))
    return {"ok": True, "contract": contract.to_dict()}


@router.get("/api/decision-truth/ledger")
async def decision_truth_ledger(limit: int = 50) -> dict[str, Any]:
    from decision_truth.ledger import recent_outcomes

    rows = recent_outcomes(limit=limit)
    return {"count": len(rows), "items": rows}
