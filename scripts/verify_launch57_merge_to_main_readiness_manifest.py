#!/usr/bin/env python3
"""Verify merge-to-main readiness manifest vs institutional docs (pre-merge navigation)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "governance/launch57/LAUNCH57_MERGE_TO_MAIN_READINESS_MANIFEST.json"
READINESS_DOC = ROOT / "docs/governance/LAUNCH57_MERGE_TO_MAIN_READINESS.md"
HANDOFF = ROOT / "governance/launch57/LAUNCH57_ENGINEERING_HANDOFF.json"


def main() -> int:
    errors: list[str] = []
    for path in (MANIFEST, READINESS_DOC, HANDOFF):
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        print(json.dumps({"pass": False, "errors": errors}, indent=2))
        return 1

    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    doc = READINESS_DOC.read_text(encoding="utf-8")

    if spec.get("cisa_certification_claimed") or spec.get("program_complete"):
        errors.append("manifest must not claim certification or program complete")
    if handoff.get("merge_readiness_doc") != str(READINESS_DOC.relative_to(ROOT)):
        errors.append("engineering handoff merge_readiness_doc drift")

    for rel in (
        spec.get("pr_merge_checklist"),
        spec.get("pr_template"),
        spec.get("post_merge_ops_manifest"),
        spec.get("engineering_handoff"),
    ):
        if rel and not (ROOT / rel).is_file():
            errors.append(f"missing linked artifact {rel}")

    for gate in spec.get("pre_merge_gates") or []:
        script = gate.get("script", "")
        if not script or not (ROOT / script).is_file():
            errors.append(f"{gate.get('id')}: missing script {script}")
        elif script not in doc and Path(script).name not in doc:
            errors.append(f"{gate.get('id')}: {script} not referenced in MERGE_TO_MAIN_READINESS.md")

    for wf in (spec.get("reviewer_expectations") or {}).get("ci_workflows") or []:
        if not (ROOT / wf).is_file():
            errors.append(f"missing CI workflow {wf}")
        if wf not in doc and Path(wf).name not in doc:
            errors.append(f"readiness doc missing CI workflow reference {wf}")

    checklist = ROOT / str(spec.get("pr_merge_checklist", ""))
    if checklist.is_file() and "launch57-cisa-assurance" not in doc:
        errors.append("readiness doc should reference launch57-cisa-assurance CI")

    report = {
        "authority": spec.get("authority"),
        "manifest_pass": not errors,
        "cisa_certification_claimed": False,
        "program_complete": False,
        "pre_merge_gate_count": len(spec.get("pre_merge_gates") or []),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
