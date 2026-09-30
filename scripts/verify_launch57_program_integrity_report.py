#!/usr/bin/env python3
"""Institutional honesty report: §8.1 incomplete + no false CISA claims in governance JSON."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_JSON = (
    "governance/launch57/LAUNCH57_COMPLETION_STATUS.json",
    "governance/launch57/LAUNCH57_ENGINEERING_CLOSURE.json",
    "governance/launch57/LAUNCH57_RELEASE_ATTESTATION_82.json",
    "governance/launch57/LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json",
    "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json",
    "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REPO_BUNDLE.json",
    "governance/launch57/LAUNCH57_POST_MERGE_OPS_MANIFEST.json",
    "governance/launch57/LAUNCH57_MERGE_TO_MAIN_READINESS_MANIFEST.json",
)


def _false_cisa_claim(data: dict) -> bool:
    if data.get("cisa_certification_claimed") is True:
        return True
    if data.get("program_complete_81") is True:
        return True
    if data.get("program_closure_verification_complete") is True:
        return True
    rollup = data.get("rollup") or {}
    if rollup.get("program_complete") is True:
        return True
    return False


def main() -> int:
    errors: list[str] = []
    for rel in GOVERNANCE_JSON:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing {rel}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if _false_cisa_claim(data):
            errors.append(f"{rel}: forbidden true completion/certification flag")
    proc81 = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_launch57_program_closure_81.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc81.returncode != 2:
        errors.append(f"§8.1 gate expected exit 2, got {proc81.returncode}")
    try:
        closure = json.loads(proc81.stdout)
        if closure.get("program_complete_81"):
            errors.append("§8.1 report claims program_complete_81 true")
    except json.JSONDecodeError:
        errors.append("§8.1 gate invalid JSON stdout")
    eng_path = ROOT / "governance/launch57/LAUNCH57_ENGINEERING_CLOSURE.json"
    completion_path = ROOT / "governance/launch57/LAUNCH57_COMPLETION_STATUS.json"
    eng = json.loads(eng_path.read_text(encoding="utf-8")) if eng_path.is_file() else {}
    completion = json.loads(completion_path.read_text(encoding="utf-8")) if completion_path.is_file() else {}
    if not eng.get("engineering_closure_declared"):
        errors.append("engineering_closure_declared is false")
    if completion.get("rollup", {}).get("program_complete"):
        errors.append("completion rollup claims program_complete true")
    report = {
        "authority": "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md",
        "program_sections": ["§8.1", "§1.2", "§8.2"],
        "integrity_pass": not errors,
        "cisa_certification_claimed": False,
        "program_complete_81": False,
        "engineering_closure_declared": bool(eng.get("engineering_closure_declared")),
        "open_finding_ids": (completion.get("rollup") or {}).get("open_finding_ids"),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
