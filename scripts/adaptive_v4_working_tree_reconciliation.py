#!/usr/bin/env python3
"""Classify non-clean working tree items."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/WORKING_TREE_RECONCILIATION.json"
ADAPTIVE_PREFIXES = (
    "bd_platform/adaptive_intelligence/",
    "api/routers/adaptive_intelligence.py",
    "governance/adaptive_ux",
    "tests/test_adaptive_v4",
    "scripts/adaptive_v4",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/",
)
UNRELATED_SAFE_PREFIXES = (
    "data/",
    "docs/CODEQL",
    ".codeql",
    ".codeql-db/",
    ".venv-a11y/",
    "blackdark/data/",
)


def main() -> None:
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    items = []
    unexplained = 0
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        status, path = line[:2].strip(), line[3:].strip()
        related = any(path.startswith(p) for p in ADAPTIVE_PREFIXES)
        safe = not related and (
            any(path.startswith(p) for p in UNRELATED_SAFE_PREFIXES)
            or path.endswith(".json")
            or path.endswith(".jsonl")
            or path.endswith(".joblib")
            or path.endswith(".parquet")
        )
        if related:
            unexplained += 1
        elif not safe and status.strip():
            unexplained += 1
        items.append(
            {
                "path": path,
                "status": status,
                "related_to_adaptive": related,
                "safe_to_exclude": safe or not related,
                "reason": "adaptive_work_in_progress" if related else "pre_existing_unrelated_artifact",
            }
        )
    payload = {
        "reconciliation_version": "adaptive-v4-gate-8",
        "items": items,
        "UNEXPLAINED_WORKING_TREE_CHANGES": unexplained,
        "adaptive_uncommitted": [i for i in items if i["related_to_adaptive"]],
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"items": len(items), "unexplained": unexplained, "adaptive_uncommitted": len(payload["adaptive_uncommitted"])}, indent=2))


if __name__ == "__main__":
    main()
