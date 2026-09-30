#!/usr/bin/env python3
"""Single local entry: merge readiness + optional pytest (program §8.3 V-2 repo complement)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    steps: list[dict] = []
    failures: list[str] = []

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_launch57_merge_readiness.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    steps.append({"name": "merge_readiness", "exit_code": proc.returncode})
    if proc.returncode != 0:
        failures.append("merge_readiness")

    proc_ci = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_launch57_ci_assurance_manifest.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    steps.append({"name": "ci_assurance_manifest", "exit_code": proc_ci.returncode})
    if proc_ci.returncode != 0:
        failures.append("ci_assurance_manifest")

    if not os.getenv("LAUNCH57_SKIP_PYTEST", "").strip():
        pytest_code = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_cisa_launch57_remediation.py", "-q", "--tb=no"],
            cwd=ROOT,
        ).returncode
        steps.append({"name": "pytest_cisa_launch57", "exit_code": pytest_code})
        if pytest_code != 0:
            failures.append("pytest")

    report = {
        "authority": "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md",
        "program_sections": ["§8.3 V-2", "§3.2 E-TEST"],
        "cisa_certification_claimed": False,
        "program_complete": False,
        "suite_pass": not failures,
        "steps": steps,
        "failures": failures,
        "note": "Record CI run URL separately for V-2 human sign-off (LAUNCH57_CI_ASSURANCE_MANIFEST.json).",
    }
    print(json.dumps(report, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
