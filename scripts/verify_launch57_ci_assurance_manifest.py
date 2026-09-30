#!/usr/bin/env python3
"""Verify launch57-cisa-assurance workflow implements institutional CI manifest (E-TEST)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "governance/launch57/LAUNCH57_CI_ASSURANCE_MANIFEST.json"
WORKFLOW = ROOT / ".github/workflows/launch57-cisa-assurance.yml"


def main() -> int:
    if not MANIFEST.is_file() or not WORKFLOW.is_file():
        print("MISSING manifest or workflow", file=sys.stderr)
        return 1
    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if spec.get("cisa_certification_claimed"):
        print("manifest must not claim certification", file=sys.stderr)
        return 1
    wf = WORKFLOW.read_text(encoding="utf-8")
    errors: list[str] = []
    job = spec.get("engineering_baseline_job") or {}
    for script in job.get("required_verify_scripts") or []:
        needle = f"python scripts/{script}"
        if needle not in wf:
            errors.append(f"workflow missing {needle}")
        if not (ROOT / "scripts" / script).is_file():
            errors.append(f"missing script file {script}")
    test_pat = job.get("required_test_invocation", "")
    if test_pat and test_pat not in wf:
        errors.append(f"workflow missing pytest for {test_pat}")
    for block in job.get("honest_nonzero_exits") or []:
        script = block.get("script", "")
        if script and script not in wf:
            errors.append(f"workflow missing honest exit check for {script}")
    syft = spec.get("syft_job") or {}
    if syft.get("script") and f"python scripts/{syft['script']}" not in wf:
        errors.append("workflow missing syft validation script")
    if errors:
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(json.dumps({"pass": True, "evidence_class": "E-TEST", "verify_scripts": len(job.get("required_verify_scripts") or [])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
