"""Verified Miss Bounty — public ledger claims."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.openapi_responses import COMMON_ERROR_RESPONSES
from dashboard import require_authenticated
from security_auth import optional_user_from_request, require_admin_dev

router = APIRouter(tags=["miss-bounty"], responses=COMMON_ERROR_RESPONSES)


class MissBountyClaimBody(BaseModel):
    decision_link: str = Field(..., min_length=8, max_length=2048)
    source_a_url: str = Field(..., min_length=8, max_length=2048)
    source_b_url: str = Field(..., min_length=8, max_length=2048)
    source_a_close: float = Field(..., gt=0)
    source_b_close: float = Field(..., gt=0)


class MissBountyReviewBody(BaseModel):
    note: str = Field(default="", max_length=2000)


@router.get("/api/oracle/miss-bounty/eligibility")
async def miss_bounty_eligibility(
    prediction_id: int = Query(..., ge=1),
    user: dict | None = Depends(optional_user_from_request),
):
    from miss_bounty_service import build_claim_eligibility

    uid = int(user["id"]) if user else None
    return await build_claim_eligibility(user_id=uid, prediction_id=prediction_id)


@router.post("/api/oracle/miss-bounty/claims")
async def miss_bounty_submit(
    body: MissBountyClaimBody,
    user: dict = Depends(require_authenticated),
):
    from miss_bounty_service import submit_miss_bounty_claim

    try:
        return await submit_miss_bounty_claim(
            user_id=int(user["id"]),
            decision_link=body.decision_link,
            source_a_url=body.source_a_url,
            source_b_url=body.source_b_url,
            source_a_close=body.source_a_close,
            source_b_close=body.source_b_close,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/oracle/miss-bounty/public-log")
async def miss_bounty_public_log(limit: int = Query(100, ge=1, le=200)):
    from miss_bounty_store import fetch_public_miss_bounty_log

    return {
        "claims": await fetch_public_miss_bounty_log(limit=limit),
        "privacy": "No personal data — public refs only",
        "reward": {"type": "subscription_discount", "percent": 20, "months": 1},
    }


@router.get("/api/admin/miss-bounty/claims")
async def admin_list_miss_bounty_claims(
    _admin: dict = Depends(require_admin_dev),
):
    from miss_bounty_store import list_pending_miss_bounty_claims

    return {"pending": await list_pending_miss_bounty_claims()}


@router.post("/api/admin/miss-bounty/claims/{claim_id}/approve")
async def admin_approve_miss_bounty(
    claim_id: int,
    body: MissBountyReviewBody,
    _admin: dict = Depends(require_admin_dev),
):
    from miss_bounty_service import approve_miss_bounty_claim

    try:
        return await approve_miss_bounty_claim(claim_id, reviewer_note=body.note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/admin/miss-bounty/claims/{claim_id}/reject")
async def admin_reject_miss_bounty(
    claim_id: int,
    body: MissBountyReviewBody,
    _admin: dict = Depends(require_admin_dev),
):
    from miss_bounty_service import reject_miss_bounty_claim

    try:
        return await reject_miss_bounty_claim(claim_id, reviewer_note=body.note)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
