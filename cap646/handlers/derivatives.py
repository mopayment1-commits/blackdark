"""Derivatives capabilities — T05/T08."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer
from data_freshness import attach_oracle_freshness


async def handle_derivatives_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    symbol = str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")

    if capability_id == 48:
        from bd_platform.derivatives_hub import derivatives_overview

        data = await derivatives_overview(symbol)
        payload = attach_oracle_freshness(
            {"capability_id": 48, "surface": "futures_intelligence_suite", "overview": data, "success": bool(data)}
        )
        return ai_compliance_footer(payload)

    if capability_id == 263:
        from options_fetcher import fetch_options_overview

        data = await fetch_options_overview([symbol])
        return ai_compliance_footer({"capability_id": 263, "surface": "options_volume", "data": data, "success": True})

    from bd_platform.derivatives_hub import derivatives_overview

    overview = await derivatives_overview(symbol)
    surface = {
        86: "funding_rate_intelligence",
        88: "liquidation_intelligence",
        126: "futures_volume_intelligence",
        205: "open_interest_intelligence",
        235: "long_short_ratio_intelligence",
        252: "liquidation_heatmap",
        85: "futures_open_interest_intelligence",
        124: "futures_funding_rate_intelligence",
    }.get(capability_id, "derivatives_intelligence")

    payload = attach_oracle_freshness(
        {"capability_id": capability_id, "surface": surface, "overview": overview, "success": bool(overview)}
    )
    return ai_compliance_footer(payload)
