"""Proprietary Asset Graph — §12 traceability chain."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GRAPH_CHAIN = (
    "raw_data",
    "derived_data",
    "entity",
    "event",
    "feature",
    "signal",
    "prediction",
    "decision",
    "confidence",
    "user_exposure",
    "outcome",
    "error",
    "learning",
    "model_version",
    "improvement",
    "commercial_impact",
    "evidence",
)

ANCHOR_MODULES = {
    "signal": "signal_registry.py",
    "decision": "decision_ledger.py",
    "event": "market_event_library.py",
    "error": "failure_corpus.py",
    "evidence": "oracle_audit_chain.py",
    "prediction": "oracle_audit_chain.py",
    "outcome": "blackdark/data_governance/outcome_registry.py",
    "model_version": "data/models/regime/training_status.json",
}


def trace_artifact(*, artifact_type: str, artifact_id: str) -> dict[str, Any]:
    """Trace an artifact through the proprietary asset graph."""
    chain_position = list(GRAPH_CHAIN)
    idx = chain_position.index(artifact_type) if artifact_type in chain_position else -1
    upstream = chain_position[:idx] if idx > 0 else []
    downstream = chain_position[idx + 1 :] if idx >= 0 else chain_position

    links: dict[str, Any] = {}
    if artifact_type == "decision":
        try:
            from decision_ledger import get_decision

            row = get_decision(artifact_id)
            if row:
                links = {
                    "prediction_id": row.get("prediction_id"),
                    "exposure_id": row.get("exposure_id"),
                    "outcome_id": row.get("outcome_id"),
                    "evidence_class": row.get("evidence_class"),
                }
        except Exception:
            pass

    return {
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "graph_chain": list(GRAPH_CHAIN),
        "position": idx,
        "upstream_stages": upstream,
        "downstream_stages": downstream,
        "links": links,
        "anchors": ANCHOR_MODULES,
        "traceable": artifact_type in ANCHOR_MODULES or bool(links),
        "traced_at": datetime.now(UTC).isoformat(),
    }


def graph_stats(*, root: Path | None = None) -> dict[str, Any]:
    """Measurable graph coverage stats for gate/compliance."""
    base = root or Path(__file__).resolve().parents[2]
    present = {}
    for stage, anchor in ANCHOR_MODULES.items():
        p = base / anchor
        present[stage] = p.exists()
    coverage = round(100 * sum(present.values()) / len(present), 1)
    return {
        "chain_length": len(GRAPH_CHAIN),
        "anchored_stages": len(ANCHOR_MODULES),
        "present_anchors": present,
        "coverage_pct": coverage,
        "fully_traceable": coverage >= 85.0,
    }
