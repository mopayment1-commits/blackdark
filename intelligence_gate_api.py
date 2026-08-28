"""Intelligence Gate API — Epistemic Humility Gate (/intelligence/gate)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Query

from api.openapi_responses import COMMON_ERROR_RESPONSES
from security_auth import require_admin, require_authenticated

router = APIRouter(prefix="/api/intelligence/gate", tags=["intelligence-gate"], responses=COMMON_ERROR_RESPONSES)


@router.get("/status")
async def epistemic_gate_status_route():
    from bd_platform.epistemic_humility_gate import epistemic_gate_status

    return epistemic_gate_status()


@router.get("/methodology")
async def epistemic_gate_methodology_route():
    from bd_platform.epistemic_humility_gate import get_public_methodology

    return get_public_methodology()


@router.post("/evaluate")
async def epistemic_gate_evaluate_route(
    data: dict = Body(default={}),
    user: dict = Depends(require_authenticated),
):
    from bd_platform.epistemic_humility_gate import evaluate_epistemic_gate

    tier = str(user.get("tier") or user.get("plan") or "free")
    return evaluate_epistemic_gate(
        asset=data.get("asset", "BTC"),
        confidence_score=float(data.get("confidence_score", 7.0)),
        sample_size=int(data.get("sample_size", 100)),
        fact_a=data.get("fact_a"),
        fact_b=data.get("fact_b"),
        data_age_hours=float(data.get("data_age_hours", 1.0)),
        evidence=data.get("evidence"),
        output_layer=data.get("output_layer", "inference"),
        user_tier=tier,
        signal_type=data.get("signal_type", "oracle_direction"),
    )


@router.post("/publish")
async def epistemic_gate_publish_route(
    data: dict = Body(default={}),
    user: dict = Depends(require_authenticated),
):
    from bd_platform.epistemic_humility_gate import gate_signal_before_publish

    tier = str(user.get("tier") or user.get("plan") or "free")
    return gate_signal_before_publish(
        asset=data.get("asset", "BTC"),
        confidence_score=float(data.get("confidence_score", 7.0)),
        sample_size=int(data.get("sample_size", 100)),
        fact_a=data.get("fact_a"),
        fact_b=data.get("fact_b"),
        data_age_hours=float(data.get("data_age_hours", 1.0)),
        evidence=data.get("evidence"),
        signal_type=data.get("signal_type", "oracle_direction"),
        user_tier=tier,
    )


@router.get("/hit-rate")
async def epistemic_gate_hit_rate_route(_admin: dict = Depends(require_admin)):
    from bd_platform.epistemic_humility_gate import get_gate_hit_rate_panel

    return get_gate_hit_rate_panel()


@router.get("/e2e")
async def epistemic_gate_e2e_route(_admin: dict = Depends(require_admin)):
    from bd_platform.epistemic_humility_gate import run_epistemic_gate_e2e

    return run_epistemic_gate_e2e()
