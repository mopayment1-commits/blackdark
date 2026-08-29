"""Unified alert orchestration surface (PDF #18)."""

from __future__ import annotations

from typing import Any


def alert_orchestration_status_18() -> dict[str, Any]:
    from alert_service import whatsapp_cloud_configured
    from instant_alert_engine import engine_stats

    stats = engine_stats()
    channels = {
        "telegram": True,
        "email": True,
        "whatsapp": whatsapp_cloud_configured(),
        "in_app": True,
    }
    return {
        "ok": True,
        "success": True,
        "capability_id": 18,
        "orchestrator": "alert_service+instant_alert_engine",
        "channels": channels,
        "engine": stats,
    }
