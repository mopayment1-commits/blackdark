#!/usr/bin/env python3
"""Machine-check automated items from LAUNCH57_PR_MERGE_CHECKLIST.md (institutional)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKLIST = ROOT / "docs/governance/LAUNCH57_PR_MERGE_CHECKLIST.md"

GATES = (
    "verify_launch57_finding_inventory_lock.py",
    "verify_launch57_repo_evidence.py",
    "verify_launch57_ci_assurance_manifest.py",
    "verify_launch57_program_integrity_report.py",
    "verify_launch57_merge_readiness.py",
    "verify_launch57_evidence_index_schema.py",
)


def main() -> int:
    if not CHECKLIST.is_file():
        return 1
    failures: list[str] = []
    results: list[dict] = []
    for script in GATES:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        ok = proc.returncode == 0
        results.append({"script": script, "pass": ok, "exit_code": proc.returncode})
        if not ok:
            failures.append(script)
    report = {
        "checklist_doc": str(CHECKLIST.relative_to(ROOT)),
        "cisa_certification_claimed": False,
        "automated_gates_pass": not failures,
        "results": results,
        "failures": failures,
        "honesty": "Does not replace human reviewer sign-off in checklist.",
    }
    print(json.dumps(report, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
