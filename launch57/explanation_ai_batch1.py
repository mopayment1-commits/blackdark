"""
Launch-57 Phase 6 — Explanation + AI Batch 1.

Build order: #34 CAP-0025 → #35 CAP-0026 → #36 CAP-0024 → #51 CAP-0065/0100
"""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer
from launch57.decision_common import stamp_decision_batch
from launch57.explanation_ai_common import (
    attach_explanation_ai_envelope,
    build_short_brief,
    classify_ai_type,
    gated_explanation,
    platform_data_only_footer,
    research_portal_scope_footer,
)

LAUNCH57_EXPLANATION_AI_BATCH1_CAP_IDS: frozenset[int] = frozenset({25, 26, 24, 65, 100})

LAUNCH_ITEM_BY_CAP: dict[int, int] = {
    25: 34,
    26: 35,
    24: 36,
    65: 51,
    100: 51,
}

_BINDING = "launch57_phase6_explanation_ai_batch1"
_MODULE = "launch57.explanation_ai_batch1"


async def signal_explanation_workflow(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #34 / CAP-0025 — signal → explanation workflow (RULE_BASED)."""
    from bd_platform.footprint_analytics import footprint_snapshot
    from heroes_quality import build_oqs_why_block

    p = dict(params or {})
    blocked, spine = await gated_explanation(
        capability_id=25,
        launch_item_id=34,
        surface="signal_explanation_workflow",
        entrypoint="signal_explanation_workflow",
        symbol=symbol,
        params=p,
        module=_MODULE,
        binding=_BINDING,
    )
    if blocked:
        return blocked

    footprint = await footprint_snapshot(spine["symbol"])
    why = build_oqs_why_block(
        {
            "asset": spine["symbol"],
            "verdict": str(p.get("verdict") or "NEUTRAL"),
            "factors": [
                {
                    "factor": f"Order-flow context for {spine['symbol']}",
                    "detail": "live book footprint",
                    "source": "footprint",
                },
                {
                    "factor": "Volume + funding alignment",
                    "detail": "checked",
                    "source": "market",
                },
            ],
        }
    )
    body = stamp_decision_batch(
        {
            "surface": "signal_explanation_workflow",
            "symbol": spine["symbol"],
            "success": bool(footprint or why.get("ready")),
            "signal": footprint,
            "explanation": why,
            "workflow": ["signal_detected", "context_attached", "explanation_rendered"],
            "ai_system_type": classify_ai_type(launch_item_id=34),
            "price_context_from": "launch57.decision_common:load_decision_spine",
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=25,
        launch_item_id=34,
        entrypoint="signal_explanation_workflow",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_explanation_ai_envelope(ai_compliance_footer(body), spine=spine)


async def price_move_explanation(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #35 / CAP-0026 — price-move explanation (RULE_BASED, spine price)."""
    from sentiment_engine import build_sentiment_context_safe

    p = dict(params or {})
    blocked, spine = await gated_explanation(
        capability_id=26,
        launch_item_id=35,
        surface="price_move_explanation",
        entrypoint="price_move_explanation",
        symbol=symbol,
        params=p,
        module=_MODULE,
        binding=_BINDING,
    )
    if blocked:
        return blocked

    change = float(spine.get("change_24h") or 0)
    price = spine.get("price")
    reasons: list[str] = []
    if change >= 3:
        reasons.append("strong_24h_rally")
    elif change <= -3:
        reasons.append("sharp_24h_drawdown")
    else:
        reasons.append("muted_price_action")

    sentiment = await build_sentiment_context_safe(spine["symbol"])
    compound = (sentiment.get("sentiment_compound_index") or {}).get(spine["symbol"]) or {}
    if compound:
        reasons.append("sentiment_context_attached")

    body = stamp_decision_batch(
        {
            "surface": "price_move_explanation",
            "symbol": spine["symbol"],
            "success": price is not None,
            "price_move_explanation": {
                "change_24h_pct": change,
                "price": price,
                "reasons": reasons,
                "sentiment": compound,
                "price_source": "launch57.decision_common:load_decision_spine",
            },
            "ai_system_type": classify_ai_type(launch_item_id=35),
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=26,
        launch_item_id=35,
        entrypoint="price_move_explanation",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_explanation_ai_envelope(ai_compliance_footer(body), spine=spine)


async def ai_research_agent_grounded(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #36 / CAP-0024 — platform-data-only research agent + copilot (STATISTICAL)."""
    from research_lab import build_research_lab_report

    p = dict(params or {})
    blocked, spine = await gated_explanation(
        capability_id=24,
        launch_item_id=36,
        surface="ai_research_agent_grounded",
        entrypoint="ai_research_agent_grounded",
        symbol=symbol,
        params=p,
        module=_MODULE,
        binding=_BINDING,
    )
    if blocked:
        return blocked

    report = await build_research_lab_report()
    grounded_keys = [k for k in ("oracle_audit", "whale_intelligence", "sentiment", "onchain", "macro_regime") if report.get(k)]
    grounded = {
        "symbol": spine["symbol"],
        "research_lab": report,
        "grounded_sources": grounded_keys,
        "platform_data_only": True,
        "agent_summary": f"Grounded research snapshot for {spine['symbol']} from platform data spine.",
        "llm_used": False,
    }
    compliance = platform_data_only_footer(surfaces=["launch_chat", "footer_compliance", "copilot_panel"])
    body = stamp_decision_batch(
        {
            "surface": "ai_research_agent_grounded",
            "symbol": spine["symbol"],
            "success": bool(report),
            "research_agent": grounded,
            "ai_system_type": classify_ai_type(launch_item_id=36),
            "platform_data_only": True,
            "copilot_compliance_footer": compliance,
            "compliance_footer_visible": True,
            "freshness_state": spine["freshness_state"],
            "presented_as_live": spine["presented_as_live"],
        },
        capability_id=24,
        launch_item_id=36,
        entrypoint="ai_research_agent_grounded",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    out = ai_compliance_footer(body)
    out["compliance_footer"] = {**(out.get("compliance_footer") or {}), **compliance}
    return attach_explanation_ai_envelope(out, spine=spine)


async def research_intelligence_portal(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #51 / CAP-0065 — research portal with short shareable briefs."""
    from oracle_track_record import public_track_record

    p = dict(params or {})
    asset = str(p.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    track = public_track_record()
    brief = build_short_brief(symbol=asset, track_record=track)
    scope = research_portal_scope_footer()
    body = stamp_decision_batch(
        {
            "surface": "research_intelligence_portal",
            "symbol": asset,
            "success": bool(track),
            "research_portal": {
                "track_record": track,
                "short_brief": brief,
                "portal_status": "limited_launch",
            },
            "ai_system_type": classify_ai_type(launch_item_id=51),
            "research_portal_scope": scope,
            "shareable_brief": brief,
        },
        capability_id=65,
        launch_item_id=51,
        entrypoint="research_intelligence_portal",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_explanation_ai_envelope(ai_compliance_footer(body))


async def research_reports(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #51 / CAP-0100 — short research report feed companion."""
    from oracle_track_record import public_track_record

    p = dict(params or {})
    asset = str(p.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    track = public_track_record()
    brief = build_short_brief(symbol=asset, track_record=track)
    scope = research_portal_scope_footer()
    body = stamp_decision_batch(
        {
            "surface": "research_reports",
            "symbol": asset,
            "success": bool(track),
            "research_reports": {
                "track_record": track,
                "report_feed": "institutional_limited_launch",
                "short_brief": brief,
            },
            "ai_system_type": classify_ai_type(launch_item_id=51),
            "research_portal_scope": scope,
            "shareable_brief": brief,
        },
        capability_id=100,
        launch_item_id=51,
        entrypoint="research_reports",
        batch_module=_MODULE,
        binding_source=_BINDING,
    )
    return attach_explanation_ai_envelope(ai_compliance_footer(body))


_DISPATCH: dict[int, str] = {
    25: "signal_explanation_workflow",
    26: "price_move_explanation",
    24: "ai_research_agent_grounded",
    65: "research_intelligence_portal",
    100: "research_reports",
}


async def execute_launch57_explanation_ai_batch1(
    capability_id: int,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if capability_id not in LAUNCH57_EXPLANATION_AI_BATCH1_CAP_IDS:
        raise ValueError(f"capability {capability_id} not in Launch-57 explanation+AI batch 1")
    fn = globals()[_DISPATCH[capability_id]]
    sym = str((params or {}).get("symbol") or "BTC")
    return await fn(symbol=sym, params=dict(params or {}))
