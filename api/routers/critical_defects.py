"""Platform critical defects closure API (D-15)."""

from __future__ import annotations

from fastapi import APIRouter

from critical_defects_closure import build_closure_report

router = APIRouter(prefix="/api/v1/platform", tags=["platform-critical-defects"])


@router.get("/critical-defects")
async def get_critical_defects_closure(run_tests: bool = False):
    return build_closure_report(run_tests=run_tests)
