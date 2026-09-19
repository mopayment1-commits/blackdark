#!/usr/bin/env python3
"""Launch-57 Phase 3 Batch B #37 targeted remediation evidence generator."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE3_BATCH_B_37_REMEDIATION_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE3_BATCH_B_37_REMEDIATION_REPORT.md"
FAILED_IV_SHA = "6c9614b6"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase3_adaptive_batch_b.py",
            "tests/launch57/test_decision_batch2.py",
            "tests/launch57/test_phase3_adaptive_batch_a.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase3_adaptive_batch_b.py "
            "tests/launch57/test_decision_batch2.py tests/launch57/test_phase3_adaptive_batch_a.py -q"
        ),
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "passed": proc.returncode == 0,
    }


def main() -> None:
    commit_sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()

    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    evidence["implementation_sha"] = commit_sha
    evidence["generated_at"] = now
    evidence["tests"] = tests
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 3 Batch B — #37 Targeted Remediation Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Failed IV SHA: `{FAILED_IV_SHA}`",
        "",
        "## Root cause",
        "",
        evidence["root_cause"],
        "",
        "## Remediation",
        "",
        evidence["remediation"],
        "",
        "## Canonical path preserved",
        "",
        f"`{evidence['canonical_path_preserved']}`",
        "",
        "## Runtime non-influence proof",
        "",
        "```json",
        json.dumps(evidence["runtime_non_influence_proof"], indent=2),
        "```",
        "",
        "## Tests",
        "",
        f"- command: `{tests['command']}`",
        f"- exit_code: {tests['exit_code']}",
        f"- stdout: {tests['stdout']}",
        "",
        "## Residual gap",
        "",
        evidence["residual_gap"],
        "",
        "## Confirmations",
        "",
        "```text",
        "P3B_37_REMEDIATION_STATUS = PENDING_VERIFICATION",
        "PHASE3_INTEGRATION_REMAINS_OPEN = true",
        "PHASE4_NOT_STARTED = true",
        "PASS_ENGINEERING_NOT_CLAIMED_FOR_37 = true",
        "PASS_LIVE_NOT_CLAIMED = true",
        "```",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote #37 remediation evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
