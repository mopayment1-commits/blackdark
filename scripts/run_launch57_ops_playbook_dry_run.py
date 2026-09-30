#!/usr/bin/env python3
"""Dry-run ops playbook: verify scripts only — never transition --apply (program §3.3)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "governance/launch57/LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json"
DRY_RUN_SCRIPTS = (
    "scripts/verify_launch57_sbom_ntia_scope.py",
    "scripts/record_launch57_finding01_pledge_readiness.py",
    "scripts/verify_launch57_open_ops_closure_package.py",
)


def _run(script: str) -> int:
    return subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT).returncode


def main() -> int:
    if not PKG.is_file():
        return 1
    pkg = json.loads(PKG.read_text(encoding="utf-8"))
    results: list[dict] = []
    failures: list[str] = []
    for script in DRY_RUN_SCRIPTS:
        code = _run(script)
        results.append({"script": script, "exit_code": code})
        if code != 0:
            failures.append(f"{script} exit {code}")
    for fid, spec in (pkg.get("open_or_partial_findings") or {}).items():
        for script in spec.get("operator_scripts") or []:
            if "transition_launch57" in script:
                continue
            if script in DRY_RUN_SCRIPTS:
                continue
            if not script.startswith("scripts/verify_"):
                continue
            if not (ROOT / script).is_file():
                failures.append(f"{fid}: missing {script}")
    report = {
        "mode": "dry_run",
        "apply_transitions": False,
        "cisa_certification_claimed": False,
        "results": results,
        "failures": failures,
        "honesty": "Use transition_launch57_finding_status.py --apply only after real ops/legal evidence.",
    }
    print(json.dumps(report, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
