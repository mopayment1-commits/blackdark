"""Six Heroes canonical binding — product heroes aligned with governance (AIE-001)."""

from __future__ import annotations

from typing import Any

# Product canon from HEROES_STRATEGY_BINDING.md
PRODUCT_HEROES = (
    "single_sentence_oracle",
    "public_accuracy_ledger",
    "opportunity_score_explainability",
    "portfolio_ai",
    "whale_signal_vs_noise",
    "decision_certificate",
)

# Legacy governance IDs map to product heroes (reuse, no parallel SSOT)
GOVERNANCE_TO_PRODUCT = {
    "market_pulse": "single_sentence_oracle",
    "opportunity_radar": "opportunity_score_explainability",
    "risk_shield": "portfolio_ai",
    "execution_desk": "whale_signal_vs_noise",
    "evidence_room": "public_accuracy_ledger",
    "institutional_lens": "decision_certificate",
}


def heroes_manifest() -> dict[str, Any]:
    return {
        "product_heroes": list(PRODUCT_HEROES),
        "governance_alias_map": GOVERNANCE_TO_PRODUCT,
        "primary_surfaces": True,
        "typed_edges_required": True,
    }
