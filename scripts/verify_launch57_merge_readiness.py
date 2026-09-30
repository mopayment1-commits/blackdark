#!/usr/bin/env python3
"""Pre-merge gate: engineering remediation safe to land on main (ops may stay open)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
ENGINEERING = ROOT / "governance" / "launch57" / "LAUNCH57_ENGINEERING_CLOSURE.json"

GATES = (
    "verify_launch57_finding_inventory_lock.py",
    "verify_launch57_normative_traceability.py",
    "verify_launch57_repo_evidence.py",
    "verify_launch57_generated_artifacts_fresh.py",
    "verify_launch57_independent_verification.py",
    "verify_launch57_release_attestation_82.py",
    "verify_launch57_evidence_class_register.py",
    "verify_launch57_sbom_ntia_scope.py",
    "verify_launch57_security_lead_inventory_rerun.py",
    "verify_launch57_qa_ci_bundle.py",
    "verify_launch57_ops_v3_bundle.py",
    "verify_launch57_open_ops_closure_package.py",
    "verify_launch57_legal_v4_bundle.py",
    "verify_launch57_iv_repo_bundle.py",
    "verify_launch57_program_integrity_report.py",
)


def _run(script: str) -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        if proc.stdout:
            print(proc.stdout, file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
    return proc.returncode


def main() -> int:
    failures: list[str] = []
    for script in GATES:
        code = _run(script)
        if code != 0:
            failures.append(f"{script} exit {code}")
    if os.getenv("LAUNCH57_MERGE_READINESS_INCLUDE_PYTEST", "").strip():
        pytest_code = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_cisa_launch57_remediation.py", "-q", "--tb=no"],
            cwd=ROOT,
        ).returncode
        if pytest_code != 0:
            failures.append(f"pytest exit {pytest_code}")
    program_complete = False
    engineering_declared = False
    open_ids: list[str] = []
    if INDEX.is_file():
        idx = json.loads(INDEX.read_text(encoding="utf-8"))
        open_ids = [
            fid
            for fid, meta in (idx.get("findings") or {}).items()
            if str(meta.get("status", "")).startswith("OPEN")
        ]
    if ENGINEERING.is_file():
        eng = json.loads(ENGINEERING.read_text(encoding="utf-8"))
        engineering_declared = bool(eng.get("engineering_closure_declared"))
        program_complete = bool(eng.get("program_complete"))
    if program_complete:
        failures.append("unexpected program_complete=true before ops sign-off")
    if not engineering_declared:
        failures.append("engineering_closure_declared is false — run generate_launch57_engineering_closure.py")
    report = {
        "safe_to_merge_engineering": not failures,
        "program_complete": program_complete,
        "engineering_closure_declared": engineering_declared,
        "open_finding_ids": open_ids,
        "expected_open_ops": ["FINDING-01", "FINDING-18", "FINDING-19"],
        "failures": failures,
        "honesty": "Merge approval covers repository engineering; production ops closure is post-merge.",
    }
    print(json.dumps(report, indent=2))
    if failures:
        print("MERGE_READINESS_FAIL", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
