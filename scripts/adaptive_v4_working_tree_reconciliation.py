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
CANONICAL_CLOSURE_ARTIFACTS = {
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_FINAL_LOCAL_BASELINE.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_EVIDENCE_MANIFEST.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_REOPEN_CONDITIONS.md",
    "ADAPTIVE_V4_FINAL_LOCAL_CLOSURE.md",
    "scripts/adaptive_v4_baseline_integrity.py",
    "tests/test_adaptive_v4_baseline_integrity.py",
}
GATE_RUNNER_EPHEMERAL = {
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/FINAL_GATE_ASSERTIONS.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/WORKING_TREE_RECONCILIATION.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_LOCAL_PERFORMANCE_EVIDENCE.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_SECURITY_VERIFICATION_MATRIX.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ADAPTIVE_V4_REGRESSION_IMPACT_MATRIX.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ACCESSIBILITY_LOCAL_VERIFICATION_MATRIX.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/ACCESSIBILITY_LOCAL_VERIFICATION_REPORT.md",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/PRIMARY_TO_ATOMIC_REQUIREMENT_MAPPING.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/INDEPENDENT_REQUIREMENT_AUDIT.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/HISTORICAL_REQUIREMENT_PROVENANCE.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/REQUIREMENT_RECONCILIATION.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/SOURCE_REQUIREMENTS.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/CHILD_REQUIREMENTS.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/RTM.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/RTM_HIERARCHICAL.json",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/FULL_TRUTH_TABLE.md",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/FINAL_INSTITUTIONAL_REPORT.md",
    "institutional_due_diligence_2026/ADAPTIVE_V4_COMPLIANCE/RESIDUAL_RISK_32_1.json",
}
UNRELATED_SAFE_PREFIXES = (
    "data/",
    "FREE_API_RATE_LIMIT_AUDIT.json",
    "docs/CODEQL",
    ".codeql",
    ".codeql-db/",
    ".venv-a11y/",
    "blackdark/data/",
    "scripts/execute_826_verify.py",
    "scripts/sonar",
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
        if path in CANONICAL_CLOSURE_ARTIFACTS:
            pass
        elif related and path not in GATE_RUNNER_EPHEMERAL:
            unexplained += 1
        elif not related and not safe and status.strip():
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
