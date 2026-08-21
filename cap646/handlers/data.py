"""Data platform capabilities — T03 and provenance."""

from __future__ import annotations

from typing import Any

from cap646.data_spine import (
    data_quality_pipeline_report,
    freshness_assurance_report,
    ingestion_architecture_report,
    normalization_report,
)
from cap646.evidence_class import ai_compliance_footer
from data_provenance_score import attach_provenance, compute_data_provenance_score
from hot_storage import get_hot_storage_stats


async def handle_data_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    symbol = str(params.get("symbol") or "BTC")

    if capability_id == 631:
        return await ingestion_architecture_report()
    if capability_id == 630:
        return await freshness_assurance_report(symbol=symbol)
    if capability_id == 338:
        return await data_quality_pipeline_report()
    if capability_id == 500:
        return await normalization_report(symbol=symbol)

    if capability_id == 632:
        from cap646.handlers.verified import handle_verified_capability

        return await handle_verified_capability(632, params=params)

    if capability_id == 63:
        from cap646.handlers.verified import handle_verified_capability

        return await handle_verified_capability(63, params=params)

    if capability_id in {478, 525, 636}:
        prov = compute_data_provenance_score(symbol=symbol.replace("/USDT", ""))
        hot = get_hot_storage_stats()
        return ai_compliance_footer(
            {
                "capability_id": capability_id,
                "surface": "data_quality_analytics",
                "provenance": prov,
                "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else hot,
                "success": True,
            }
        )

    from data_lake import lake_status

    lake = await lake_status()
    prov = compute_data_provenance_score(symbol=symbol.replace("/USDT", ""))
    payload = attach_provenance({"capability_id": capability_id, "lake": lake, "success": bool(lake)})
    return ai_compliance_footer(payload)
