"""Decision Truth API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Query, Request

from api.openapi_responses import COMMON_ERROR_RESPONSES
from decision_truth.daily_autopsy import build_daily_autopsy
from decision_truth.pipeline import evaluate_decision_truth
from decision_truth.rejection import rejection_stats
from i18n_service import resolve_request_lang

router = APIRouter(prefix="/api/decision-truth", tags=["decision-truth"], responses=COMMON_ERROR_RESPONSES)


@router.post("/evaluate")
async def decision_truth_evaluate(
    request: Request,
    payload: dict[str, Any] = Body(default={}),
) -> dict[str, Any]:
    lang = resolve_request_lang(request)
    portfolio = payload.get("portfolio") if isinstance(payload.get("portfolio"), dict) else {}
    opp = payload.get("opportunity") if isinstance(payload.get("opportunity"), dict) else payload
    result = evaluate_decision_truth(opp, portfolio=portfolio, lang=lang)
    return {"ok": True, "decision_truth": result.get("decision_truth"), "payload": result}


@router.get("/rejections/stats")
async def decision_truth_rejection_stats() -> dict[str, Any]:
    return rejection_stats()


@router.get("/daily-autopsy")
async def decision_truth_daily_autopsy(
    request: Request,
    headline: str = Query(""),
    summary: str = Query(""),
) -> dict[str, Any]:
    lang = resolve_request_lang(request)
    report = {"what_changed": headline, "why_it_matters": summary, "risks_invalidation": "Stale data or regime shift"}
    return build_daily_autopsy(report, lang=lang)
