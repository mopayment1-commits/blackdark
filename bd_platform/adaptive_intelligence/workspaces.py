"""Workspaces / Missions — composition views over canonical capabilities (spec §7, AIE-012)."""

from __future__ import annotations

from typing import Any

WORKSPACES: tuple[dict[str, Any], ...] = (
    {
        "workspace_id": "market_opportunity",
        "title": "Market Opportunity",
        "capabilities": ["opportunity_score_explainability", "single_sentence_oracle"],
        "playbooks": [],
    },
    {
        "workspace_id": "whale_intelligence",
        "title": "Whale Intelligence",
        "capabilities": ["whale_signal_vs_noise"],
        "playbooks": [],
    },
    {
        "workspace_id": "risk_center",
        "title": "Risk Center",
        "capabilities": ["portfolio_ai"],
        "playbooks": [],
    },
    {
        "workspace_id": "institutional_research",
        "title": "Institutional Research",
        "capabilities": ["decision_certificate", "public_accuracy_ledger"],
        "playbooks": [],
    },
)


def list_workspaces() -> list[dict[str, Any]]:
    return [dict(w) for w in WORKSPACES]


def get_workspace(workspace_id: str) -> dict[str, Any] | None:
    for row in WORKSPACES:
        if row["workspace_id"] == workspace_id:
            return dict(row)
    return None
