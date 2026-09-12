"""Monitoring & alerting status API."""

from __future__ import annotations

from fastapi import APIRouter

from api.openapi_responses import COMMON_ERROR_RESPONSES

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"], responses=COMMON_ERROR_RESPONSES)


@router.get("/status")
async def monitoring_status_api():
    from ops.monitoring_alerting import monitoring_status

    return await monitoring_status()


@router.post("/probe")
async def monitoring_probe_now():
    """Manual probe — useful after deploy or in staging smoke tests."""
    from ops.monitoring_alerting import probe_endpoints

    return await probe_endpoints()
