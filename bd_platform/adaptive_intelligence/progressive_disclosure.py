"""Progressive disclosure with Safety Floor on Level 1 (spec §12)."""

from __future__ import annotations

from typing import Any

from bd_platform.adaptive_intelligence.safety_floor import enforce_safety_floor

LEVELS = (
    "answer",
    "why",
    "drivers",
    "evidence",
    "expert",
)


def build_disclosure_levels(payload: dict[str, Any]) -> dict[str, Any]:
    base = enforce_safety_floor(
        {
            **payload,
            "decision_critical": True,
            "freshness": payload.get("freshness") or "near_live",
            "evidence_state": payload.get("evidence_state") or "forward_shadow",
            "uncertainty": payload.get("uncertainty") or "medium",
            "critical_limitation": payload.get("critical_limitation") or "Advisory only.",
            "invalidation_or_next_check": payload.get("invalidation_or_next_check") or "recheck_on_stale",
        }
    )
    return {
        "level_1_answer": {
            "stance": base.get("stance") or payload.get("stance"),
            "uncertainty": base["uncertainty"],
            "freshness": base["freshness"],
            "critical_contradiction": payload.get("contradictions", [])[:1],
            "critical_limitation": base["critical_limitation"],
            "invalidation_or_next_check": base["invalidation_or_next_check"],
            "safety_floor_enforced": True,
        },
        "level_2_why": {"summary": payload.get("why") or payload.get("router_explanation")},
        "level_3_drivers": {"drivers": payload.get("key_drivers") or []},
        "level_4_evidence": {"evidence_class": base.get("evidence_state"), "lineage": payload.get("lineage")},
        "level_5_expert": {"methodology": payload.get("methodology"), "versions": payload.get("version_lineage")},
        "levels": list(LEVELS),
    }
