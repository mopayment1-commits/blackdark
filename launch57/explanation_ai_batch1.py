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
    classify_ai_type,
    gated_explanation,
    platform_data_only_footer,
    research_portal_scope_footer,
)
from launch57.trust_adaptive_common import (
    apply_price_move_explanation_semantics,
    apply_research_agent_grounding_filter,
    apply_research_portal_evidence_filter,
    apply_signal_explanation_semantics,
    attach_adaptive_disclosure,
    build_level1_decision_disclosure,
    build_price_move_explanation_disclosure,
    build_research_agent_disclosure,
    build_research_portal_disclosure,
    build_signal_explanation_disclosure,
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


def _governed_params(p: dict[str, Any], semantics: dict[str, Any], spine: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(p)
    governed = dict(out.get("governed_payload") or {})
    contract = semantics.get("contract") or {}
    if contract.get("material_limitation"):
        governed["critical_limitation"] = contract["material_limitation"]
    if semantics.get("unsupported_causal_rejected") or semantics.get("unsupported_input_rejected"):
        governed["unsupported_input_rejected"] = True
    out["governed_payload"] = governed
    if spine:
        out["freshness_state"] = spine.get("freshness_state")
    return out


def _attach_explanation_adaptive(
    wrapped: dict[str, Any],
    *,
    p: dict[str, Any],
    spine: dict[str, Any] | None,
    launch_item_id: int,
    surface: str,
    semantics: dict[str, Any],
    disclosure_key: str,
    disclosure: dict[str, Any],
) -> dict[str, Any]:
    contract = semantics.get("contract") or {}
    if contract:
        wrapped["explanation_contract"] = contract
        wrapped["evidence_class_visible"] = contract.get("evidence_class")
    wrapped["evidence_display"] = {
        "canonical_evidence_class": contract.get("evidence_class"),
        "freshness_state": (spine or {}).get("freshness_state"),
        "uncertainty": contract.get("uncertainty"),
    }
    governed_p = _governed_params(p, semantics, spine)
    uncertainty = contract.get("uncertainty") or (
        "qualified"
        if semantics.get("unsupported_causal_rejected")
        or semantics.get("unsupported_input_rejected")
        or semantics.get("unsupported_evidence_rejected")
        else "standard"
    )
    level1 = build_level1_decision_disclosure(
        governed_p,
        launch_item_id=launch_item_id,
        surface=surface,
        answer_state=semantics.get("answer_state"),
        evidence_display=wrapped.get("evidence_display"),
        uncertainty=uncertainty,
    )
    return attach_adaptive_disclosure(wrapped, level1, extra={disclosure_key: disclosure})


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
    semantics = apply_signal_explanation_semantics(
        footprint=footprint,
        why_block=why,
        spine=spine,
        params=p,
    )
    qualified = semantics.get("qualified_explanation") or {}
    body = stamp_decision_batch(
        {
            "surface": "signal_explanation_workflow",
            "symbol": spine["symbol"],
            "success": bool(semantics.get("signal_observable")) and not semantics.get("unsupported_causal_rejected"),
            "signal": footprint,
            "explanation": qualified,
            "explanation_semantics": semantics,
            "observed_facts": semantics.get("observed_facts"),
            "inferences": semantics.get("inferences"),
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
    wrapped = attach_explanation_ai_envelope(ai_compliance_footer(body), spine=spine, params=p)
    disclosure = build_signal_explanation_disclosure(semantics)
    return _attach_explanation_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=34,
        surface="signal_explanation_workflow",
        semantics=semantics,
        disclosure_key="signal_explanation_disclosure",
        disclosure=disclosure,
    )


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

    semantics = apply_price_move_explanation_semantics(
        change=change,
        price=price,
        sentiment=compound,
        reasons_raw=reasons,
        spine=spine,
    )
    body = stamp_decision_batch(
        {
            "surface": "price_move_explanation",
            "symbol": spine["symbol"],
            "success": semantics.get("answer_state") == "PRICE_MOVE_EXPLAINED",
            "price_move_explanation": semantics.get("price_move_explanation"),
            "price_move_semantics": semantics,
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
    wrapped = attach_explanation_ai_envelope(ai_compliance_footer(body), spine=spine, params=p)
    disclosure = build_price_move_explanation_disclosure(semantics)
    return _attach_explanation_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=35,
        surface="price_move_explanation",
        semantics=semantics,
        disclosure_key="price_move_explanation_disclosure",
        disclosure=disclosure,
    )


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
    filtered = apply_research_agent_grounding_filter(
        report,
        params=p,
        spine=spine,
        symbol=spine["symbol"],
    )
    grounded = filtered.get("research_agent") or {}
    compliance = platform_data_only_footer(surfaces=["launch_chat", "footer_compliance", "copilot_panel"])
    body = stamp_decision_batch(
        {
            "surface": "ai_research_agent_grounded",
            "symbol": spine["symbol"],
            "success": bool(filtered.get("supported_claims")) and not filtered.get("unsupported_input_rejected"),
            "research_agent": grounded,
            "research_agent_qualification": filtered,
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
    wrapped = attach_explanation_ai_envelope(out, spine=spine, params=p)
    disclosure = build_research_agent_disclosure(filtered)
    return _attach_explanation_adaptive(
        wrapped,
        p=p,
        spine=spine,
        launch_item_id=36,
        surface="ai_research_agent_grounded",
        semantics=filtered,
        disclosure_key="research_agent_disclosure",
        disclosure=disclosure,
    )


async def research_intelligence_portal(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #51 / CAP-0065 — research portal with short shareable briefs."""
    from oracle_track_record import public_track_record

    p = dict(params or {})
    asset = str(p.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    track = public_track_record()
    filtered = apply_research_portal_evidence_filter(track, {}, params=p, symbol=asset)
    brief = filtered.get("qualified_brief") or {}
    scope = research_portal_scope_footer()
    body = stamp_decision_batch(
        {
            "surface": "research_intelligence_portal",
            "symbol": asset,
            "success": filtered.get("answer_state") == "RESEARCH_BRIEF_GROUNDED",
            "research_portal": {
                "track_record": track,
                "short_brief": brief,
                "portal_status": "limited_launch",
                "portal_qualification": filtered,
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
    wrapped = attach_explanation_ai_envelope(ai_compliance_footer(body), params=p)
    disclosure = build_research_portal_disclosure(filtered)
    return _attach_explanation_adaptive(
        wrapped,
        p=p,
        spine=None,
        launch_item_id=51,
        surface="research_intelligence_portal",
        semantics=filtered,
        disclosure_key="research_portal_disclosure",
        disclosure=disclosure,
    )


async def research_reports(*, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Launch #51 / CAP-0100 — short research report feed companion."""
    from oracle_track_record import public_track_record

    p = dict(params or {})
    asset = str(p.get("symbol") or symbol or "BTC").upper().replace("/USDT", "")
    track = public_track_record()
    filtered = apply_research_portal_evidence_filter(track, {}, params=p, symbol=asset)
    brief = filtered.get("qualified_brief") or {}
    scope = research_portal_scope_footer()
    body = stamp_decision_batch(
        {
            "surface": "research_reports",
            "symbol": asset,
            "success": filtered.get("answer_state") == "RESEARCH_BRIEF_GROUNDED",
            "research_reports": {
                "track_record": track,
                "report_feed": "institutional_limited_launch",
                "short_brief": brief,
                "portal_qualification": filtered,
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
    wrapped = attach_explanation_ai_envelope(ai_compliance_footer(body), params=p)
    disclosure = build_research_portal_disclosure(filtered)
    return _attach_explanation_adaptive(
        wrapped,
        p=p,
        spine=None,
        launch_item_id=51,
        surface="research_reports",
        semantics=filtered,
        disclosure_key="research_portal_disclosure",
        disclosure=disclosure,
    )


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
