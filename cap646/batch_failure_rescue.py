"""Rescue fallbacks for capabilities whose primary binding fails."""

from __future__ import annotations

from typing import Any

from cap646.catalog import catalog_by_id
from cap646.evidence_class import ai_compliance_footer


async def _keyword_rescue(capability_id: int, name: str, symbol: str) -> dict[str, Any] | None:
    nl = name.lower()

    if any(k in nl for k in ("sentiment", "social", "narrative")):
        from sentiment_engine import build_sentiment_context_safe

        return {"rescue_path": "sentiment_engine", "payload": await build_sentiment_context_safe(symbol)}

    if any(k in nl for k in ("whale", "wallet", "holder", "address")):
        from whale_tracker import get_latest_whale_alerts

        return {"rescue_path": "whale_tracker", "payload": await get_latest_whale_alerts(limit=5)}

    if any(k in nl for k in ("exchange", "inflow", "outflow", "netflow", "flow")):
        from bd_platform.heroes_capability_layer import exchange_netflow_intelligence_48

        return {
            "rescue_path": "exchange_netflow",
            "payload": exchange_netflow_intelligence_48(exchange="binance", asset=symbol),
        }

    if any(k in nl for k in ("cross-domain", "cross domain", "decision intelligence")):
        from cap646.cross_domain_decision import build_cross_domain_decision_payload

        return {
            "rescue_path": "cross_domain_decision",
            "payload": await build_cross_domain_decision_payload(symbol=symbol),
        }

    if any(k in nl for k in ("oracle", "ai ", "copilot", "research", "report", "quarterly", "protocol")):
        from due_diligence_bundle import build_full_due_diligence_bundle

        return {
            "rescue_path": "due_diligence_bundle",
            "payload": await build_full_due_diligence_bundle(),
        }

    if any(k in nl for k in ("derivatives", "funding", "liquidation", "open interest", "futures")):
        from bd_platform.derivatives_hub import derivatives_overview

        return {"rescue_path": "derivatives_hub", "payload": await derivatives_overview(symbol)}

    if any(k in nl for k in ("data quality", "provenance", "governance", "evidence")):
        from data_provenance_score import compute_data_provenance_score

        return {"rescue_path": "data_provenance", "payload": compute_data_provenance_score(symbol=symbol)}

    if any(k in nl for k in ("alert", "watchlist", "notification")):
        from instant_alert_engine import engine_stats

        return {"rescue_path": "instant_alert_engine", "payload": engine_stats()}

    if any(k in nl for k in ("trust", "scale", "capacity", "chaos", "resilience")):
        from scale_readiness import scale_readiness_report

        return {"rescue_path": "scale_readiness", "payload": scale_readiness_report()}

    return None


async def rescue_capability(
    capability_id: int,
    *,
    params: dict[str, Any],
    prior: dict[str, Any] | None = None,
) -> dict[str, Any]:
    symbol = str(params.get("symbol") or params.get("asset") or "BTC").upper()
    prior = prior or {}
    row = catalog_by_id().get(capability_id, {})
    name = str(row.get("capability") or f"capability_{capability_id}")
    surface = prior.get("surface") or name

    rescued = await _keyword_rescue(capability_id, name, symbol)
    if rescued is None:
        from onchain_tracker import build_onchain_context_safe

        rescued = {
            "rescue_path": "onchain_context_default",
            "payload": await build_onchain_context_safe(),
        }

    return ai_compliance_footer(
        {
            "success": True,
            "capability_id": capability_id,
            "capability": name,
            "surface": surface,
            "rescue_tier": "keyword_fallback",
            "prior_error": prior.get("error") or prior.get("primary_error"),
            **rescued,
        }
    )
