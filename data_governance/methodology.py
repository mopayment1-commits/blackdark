"""Methodology cards registry for derived metrics."""

from __future__ import annotations

from typing import Any

METHODOLOGY_CARDS: dict[str, dict[str, Any]] = {
    "net_edge": {
        "metric_id": "net_edge",
        "definition": "Expected profit after fees, slip, and withdrawal",
        "formula": "gross_edge - trading_fees - slippage - withdrawal",
        "inputs": ["quote_amount", "fees", "slippage_bps"],
        "freshness_limit_s": 15,
        "minimum_history_days": 30,
        "methodology_version": "3.2.0",
        "owner": "decision_truth",
        "limitations": ["requires_executable_quote"],
    },
    "execution_feasibility": {
        "metric_id": "execution_feasibility",
        "definition": "Probability-weighted ability to execute at stated size",
        "formula": "depth_capacity * fill_probability - impact",
        "inputs": ["depth_usd", "spread_bps", "venue_count"],
        "freshness_limit_s": 5,
        "minimum_history_days": 7,
        "requires_l2": True,
        "methodology_version": "2.1.0",
        "owner": "decision_truth",
    },
    "evidence_grade": {
        "metric_id": "evidence_grade",
        "definition": "Composite evidence quality grade A-F",
        "methodology_version": "1.4.0",
        "owner": "decision_truth",
    },
    "data_provenance_score": {
        "metric_id": "data_provenance_score",
        "definition": "Freshness + venue depth + source diversity composite",
        "methodology_version": "1.0.0",
        "owner": "data_governance",
    },
    "admission_gate": {
        "metric_id": "admission_gate",
        "definition": "Multi-gate decision admission",
        "methodology_version": "1.2.0",
        "owner": "decision_truth",
    },
}


def get_methodology_card(metric_id: str) -> dict[str, Any] | None:
    return METHODOLOGY_CARDS.get(metric_id)


def methodology_registry_status() -> dict[str, Any]:
    return {
        "registered_metrics": list(METHODOLOGY_CARDS.keys()),
        "count": len(METHODOLOGY_CARDS),
        "unversioned_critical": [k for k, v in METHODOLOGY_CARDS.items() if not v.get("methodology_version")],
    }
