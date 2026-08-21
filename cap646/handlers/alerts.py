"""Alerts & workflow capabilities."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer


async def handle_alerts_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    symbol = str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")

    if capability_id in {17, 60, 629}:
        from instant_alert_engine import engine_stats

        stats = engine_stats()
        return ai_compliance_footer({"capability_id": capability_id, "surface": "smart_alerts", "engine": stats, "success": True})

    if capability_id == 245:
        from cap646.data_spine import freshness_assurance_report

        return await freshness_assurance_report(symbol=symbol)

    from in_app_alerts import inbox_stats, list_in_app_alerts

    email = str(params.get("email") or "anonymous")
    alerts = list_in_app_alerts(user_email=email)
    stats = inbox_stats(user_email=email)
    return ai_compliance_footer(
        {"capability_id": capability_id, "surface": "alerts_workflow", "alerts": alerts, "inbox": stats, "success": True}
    )
