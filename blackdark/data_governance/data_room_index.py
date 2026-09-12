"""Living Data Room index — DSR-021, D-16."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from blackdark.data_governance._paths import DATA_ROOM_INDEX_PATH, ensure_governance_dirs


def build_data_room_index(*, root: Path | None = None) -> dict[str, Any]:
    """Canonical index with completeness, freshness, evidence strength."""
    ensure_governance_dirs()
    base = root or Path(__file__).resolve().parents[2]
    artifacts = [
        {
            "artifact_id": "signal_registry",
            "owner": "platform-intelligence",
            "scope": "Signal accumulation",
            "path": "data/signal_registry.jsonl",
            "evidence_strength": "engineering_verified",
        },
        {
            "artifact_id": "decision_ledger",
            "owner": "platform-intelligence",
            "scope": "Decision→outcome chain",
            "path": "data/decision_ledger.jsonl",
            "evidence_strength": "shadow_simulated_only",
        },
        {
            "artifact_id": "oracle_audit_chain",
            "owner": "platform-trust",
            "scope": "Tamper-evident predictions",
            "path": "data/oracle_audit_chain.jsonl",
            "evidence_strength": "hash_chain_verified",
        },
        {
            "artifact_id": "governance_contracts",
            "owner": "platform-governance",
            "scope": "Data asset contracts",
            "path": "data/governance/contracts",
            "evidence_strength": "canonical",
        },
        {
            "artifact_id": "corporate_data_room",
            "owner": "platform-corporate",
            "scope": "DD snapshot",
            "path": "data/corporate/DATA_ROOM_SNAPSHOT.json",
            "evidence_strength": "partial",
        },
    ]
    now = datetime.now(UTC).isoformat()
    indexed = []
    for art in artifacts:
        p = base / art["path"]
        exists = p.exists()
        freshness = "current" if exists else "missing"
        if exists and p.is_file():
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=UTC).isoformat()
        elif exists and p.is_dir():
            files = list(p.glob("*.json"))
            mtime = (
                datetime.fromtimestamp(max(f.stat().st_mtime for f in files), tz=UTC).isoformat()
                if files
                else None
            )
        else:
            mtime = None
        indexed.append(
            {
                **art,
                "exists": exists,
                "freshness": freshness,
                "last_modified": mtime,
                "residual_risk": "none" if exists else "artifact_missing",
                "indexed_at": now,
            }
        )
    index = {
        "index_version": "1.0.0",
        "built_at": now,
        "completeness_pct": round(100 * sum(1 for a in indexed if a["exists"]) / len(indexed), 1),
        "artifacts": indexed,
    }
    DATA_ROOM_INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return index
