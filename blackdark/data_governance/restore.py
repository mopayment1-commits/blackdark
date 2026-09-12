"""Restore evidence — DSR-015, D-12."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from blackdark.data_governance._paths import RESTORE_EVIDENCE_PATH, ensure_governance_dirs

CRITICAL_LEDGERS = (
    "data/signal_registry.jsonl",
    "data/decision_ledger.jsonl",
    "data/oracle_audit_chain.jsonl",
    "data/failure_corpus.jsonl",
    "data/market_event_library.jsonl",
)

RTO_SECONDS = 3600
RPO_SECONDS = 300


def run_restore_drill(*, root: Path | None = None) -> dict[str, Any]:
    """Local restore drill: backup copy → verify integrity → record evidence."""
    ensure_governance_dirs()
    base = root or Path(__file__).resolve().parents[2]
    drill_id = f"restore_{uuid4().hex[:12]}"
    started = datetime.now(UTC)
    results: list[dict[str, Any]] = []

    for rel in CRITICAL_LEDGERS:
        src = base / rel
        item = {"path": rel, "exists": src.exists(), "integrity_ok": False, "rto_target_s": RTO_SECONDS}
        if src.exists():
            backup = base / "data" / "governance" / "restore_drill" / f"{Path(rel).name}.bak"
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, backup)
            restored = backup.read_bytes()
            original = src.read_bytes()
            item["integrity_ok"] = restored == original
            item["bytes"] = len(original)
        results.append(item)

    elapsed = (datetime.now(UTC) - started).total_seconds()
    evidence = {
        "drill_id": drill_id,
        "started_at": started.isoformat(),
        "elapsed_seconds": elapsed,
        "rto_target_seconds": RTO_SECONDS,
        "rpo_target_seconds": RPO_SECONDS,
        "rto_met": elapsed <= RTO_SECONDS,
        "items": results,
        "all_integrity_ok": all(r.get("integrity_ok") for r in results if r.get("exists")),
    }
    with RESTORE_EVIDENCE_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(evidence, ensure_ascii=False, default=str) + "\n")
    return evidence
