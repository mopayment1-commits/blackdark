"""
Launch-57 Phase 6 — shared explanation + AI spine consuming Phase 1–3 layers.
"""

from __future__ import annotations

from typing import Any, Literal

from launch57.decision_common import attach_decision_envelope, load_decision_spine, stale_gate_body, stamp_decision_batch

AiSystemType = Literal["RULE_BASED", "STATISTICAL", "ML", "LLM", "HYBRID"]

_PLATFORM_ONLY_DISCLAIMER = (
    "Platform-data grounding only — responses cite internal spine/trust sources. "
    "No external web sources are presented as verified facts."
)

_COPILOT_COMPLIANCE_FOOTER = (
    "AI copilot surfaces are decision evidence only — not financial advice. "
    "Outputs are grounded on platform data; unknown is not zero."
)

_RESEARCH_PORTAL_SCOPE = (
    "Limited launch research portal — short shareable briefs from oracle track record "
    "and platform research feeds only."
)


def attach_explanation_ai_envelope(body: dict[str, Any], *, spine: dict[str, Any] | None = None) -> dict[str, Any]:
    out = attach_decision_envelope(body, spine=spine)
    out["explanation_ai_layer"] = {
        "phase": "6_EXPLANATION_AI",
        "data_spine_consumed": (spine or {}).get("data_spine"),
        "freshness_state": (spine or {}).get("freshness_state"),
        "live_eligible": (spine or {}).get("live_eligible"),
        "evidence_class_visible": out.get("evidence_class_visible"),
        "ai_system_type": out.get("ai_system_type"),
    }
    return out


def platform_data_only_footer(*, surfaces: list[str] | None = None) -> dict[str, Any]:
    return {
        "disclaimer": _PLATFORM_ONLY_DISCLAIMER,
        "platform_data_only": True,
        "external_sources_as_fact": "FORBIDDEN",
        "llm_used": False,
        "copilot_surfaces": surfaces or ["launch_chat", "footer_compliance"],
        "compliance_text": _COPILOT_COMPLIANCE_FOOTER,
        "visible": True,
    }


def research_portal_scope_footer() -> dict[str, Any]:
    return {
        "disclaimer": _RESEARCH_PORTAL_SCOPE,
        "limited_launch_scope": True,
        "shareable_briefs": True,
        "full_institutional_research_suite": False,
    }


def classify_ai_type(*, launch_item_id: int) -> AiSystemType:
    if launch_item_id in {34, 35}:
        return "RULE_BASED"
    if launch_item_id == 36:
        return "STATISTICAL"
    return "STATISTICAL"


async def gated_explanation(
    *,
    capability_id: int,
    launch_item_id: int,
    surface: str,
    entrypoint: str,
    symbol: str,
    params: dict[str, Any],
    module: str,
    binding: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    spine = await load_decision_spine(symbol, params)
    if not spine["live_eligible"]:
        body = stamp_decision_batch(
            stale_gate_body(
                capability_id=capability_id,
                launch_item_id=launch_item_id,
                surface=surface,
                symbol=spine["symbol"],
                spine=spine,
                entrypoint=entrypoint,
            ),
            capability_id=capability_id,
            launch_item_id=launch_item_id,
            entrypoint=entrypoint,
            batch_module=module,
            binding_source=binding,
        )
        body["ai_system_type"] = classify_ai_type(launch_item_id=launch_item_id)
        return attach_explanation_ai_envelope(body, spine=spine), None
    return None, spine


def build_short_brief(*, symbol: str, track_record: dict[str, Any]) -> dict[str, Any]:
    cumulative = track_record.get("cumulative") or {}
    resolved = int(cumulative.get("resolved_predictions") or 0)
    hit = cumulative.get("hit_rate_percent")
    headline = f"{symbol} research brief — platform oracle track record"
    if resolved > 0 and hit is not None:
        summary = (
            f"Live-only oracle metrics: {resolved} resolved predictions, "
            f"{hit}% hit rate (correct-only definition)."
        )
    else:
        summary = "Limited launch brief — cumulative oracle metrics pending more live resolutions."

    return {
        "headline": headline,
        "summary": summary,
        "shareable": True,
        "max_length_chars": 480,
        "symbol": symbol,
        "metrics_scope": cumulative.get("metrics_scope") or "live_only",
    }
