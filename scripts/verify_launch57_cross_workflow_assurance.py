#!/usr/bin/env python3
"""Program §8.3 V-2 + PR merge checklist — dual CI workflow wiring (E-TEST repo gate)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "governance/launch57/LAUNCH57_CROSS_WORKFLOW_ASSURANCE.json"
REGISTER = ROOT / "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json"
CHECKLIST = ROOT / "docs/governance/LAUNCH57_PR_MERGE_CHECKLIST.md"


def _workflow_text(rel: str) -> str:
    path = ROOT / rel
    if not path.is_file():
        raise FileNotFoundError(rel)
    return path.read_text(encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    if not SPEC.is_file():
        print(f"missing {SPEC}", file=sys.stderr)
        return 1
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    if spec.get("cisa_certification_claimed"):
        errors.append("spec must not claim CISA certification")
    if not CHECKLIST.is_file():
        errors.append("missing PR merge checklist doc")
    else:
        cl = CHECKLIST.read_text(encoding="utf-8")
        if "test_cisa_launch57_remediation.py" not in cl:
            errors.append("checklist missing Launch-57 pytest reference")
        if "launch57-cisa-assurance" not in cl:
            errors.append("checklist missing launch57-cisa-assurance reference")

    if REGISTER.is_file():
        v2 = json.loads(REGISTER.read_text(encoding="utf-8")).get("steps", {}).get("V-2", {})
        for wf in v2.get("repo_gates") or []:
            if not (ROOT / wf).is_file():
                errors.append(f"V-2 register missing workflow {wf}")
    else:
        errors.append("missing independent verification register")

    bundle_rel = spec.get("reviewer_evidence_bundle", "")
    if bundle_rel and not (ROOT / bundle_rel).is_file():
        errors.append(f"missing reviewer bundle {bundle_rel}")

    for entry in spec.get("workflows") or []:
        rel = entry.get("path", "")
        job = entry.get("job", "")
        try:
            text = _workflow_text(rel)
        except FileNotFoundError:
            errors.append(f"missing workflow {rel}")
            continue
        if job and f"{job}:" not in text:
            errors.append(f"{rel}: job {job} not found")
        for mod in entry.get("required_pytest_modules") or []:
            if mod not in text:
                errors.append(f"{rel}: pytest module {mod} not wired")

    report = {
        "program_sections": spec.get("program_sections"),
        "repo_gate_pass": not errors,
        "cisa_certification_claimed": False,
        "qa_ci_green_run_url_required": True,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
