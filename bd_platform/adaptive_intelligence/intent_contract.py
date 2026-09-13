"""Intent Contract — spec §6 (AIE-009)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class IntentContract:
    goal: str
    asset_scope: str = ""
    horizon: str = "intraday"
    decision_type: str = "monitoring"
    required_safety_lenses: list[str] = field(default_factory=list)
    evidence_minimum: dict[str, Any] = field(default_factory=dict)
    output_mode: str = "answer"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_MANDATORY_LENSES: dict[str, list[str]] = {
    "opportunity": ["freshness", "evidence_class", "liquidity", "net_edge"],
    "risk": ["freshness", "exposure", "contradiction", "invalidation"],
    "due_diligence": ["provenance", "methodology", "limitations", "evidence_class"],
    "monitoring": ["freshness", "staleness"],
}


def resolve_intent_contract(
    *,
    query: str | None = None,
    intent_id: str | None = None,
    asset: str | None = None,
    horizon: str | None = None,
    decision_type: str | None = None,
    output_mode: str = "answer",
) -> IntentContract:
    """Resolve natural-language or intent-id request into structured Intent Contract."""
    from intent_router import resolve_intent

    goal = (query or "").strip()
    dtype = (decision_type or "monitoring").strip().lower()
    if intent_id:
        row = resolve_intent(intent_id)
        goal = goal or row.get("label") or intent_id
        dtype = _infer_decision_type(row.get("id") or intent_id)
    lenses = list(_MANDATORY_LENSES.get(dtype, _MANDATORY_LENSES["monitoring"]))
    return IntentContract(
        goal=goal or "general_intelligence",
        asset_scope=(asset or "*").upper(),
        horizon=horizon or "intraday",
        decision_type=dtype,
        required_safety_lenses=lenses,
        evidence_minimum={"freshness_max_age_sec": 300, "coverage": "partial_ok"},
        output_mode=output_mode,
    )


def _infer_decision_type(intent_id: str) -> str:
    mapping = {
        "decide": "opportunity",
        "verify": "due_diligence",
        "my_book": "risk",
        "alerts": "monitoring",
    }
    return mapping.get(intent_id, "monitoring")
