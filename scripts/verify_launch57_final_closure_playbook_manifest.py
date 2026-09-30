#!/usr/bin/env python3
"""Verify final closure playbook manifest vs ops playbook doc and evidence index."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "governance/launch57/LAUNCH57_FINAL_CLOSURE_PLAYBOOK_MANIFEST.json"
PLAYBOOK = ROOT / "docs/ops/LAUNCH57_FINAL_CLOSURE_PLAYBOOK.md"
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"


def main() -> int:
    errors: list[str] = []
    for path in (MANIFEST, PLAYBOOK, INDEX):
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        print(json.dumps({"pass": False, "errors": errors}, indent=2))
        return 1

    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    doc = PLAYBOOK.read_text(encoding="utf-8")

    if spec.get("cisa_certification_claimed") or spec.get("program_complete"):
        errors.append("manifest must not claim certification or program complete")

    ops_field = spec.get("evidence_index_ops_playbook_field", "ops_playbook")
    if idx.get(ops_field) != str(PLAYBOOK.relative_to(ROOT)):
        errors.append("evidence index ops_playbook path drift vs manifest")

    for rel in (
        spec.get("open_ops_closure_package"),
        spec.get("post_merge_ops_manifest"),
        spec.get("merge_to_main_readiness_manifest"),
        spec.get("finding_transition_runbook"),
    ):
        if rel and not (ROOT / rel).is_file():
            errors.append(f"missing linked artifact {rel}")

    for step in spec.get("steps") or []:
        for script in step.get("scripts") or []:
            if not (ROOT / script).is_file():
                errors.append(f"{step.get('id')}: missing script {script}")
            elif script not in doc and Path(script).name not in doc:
                errors.append(f"{step.get('id')}: {script} not referenced in FINAL_CLOSURE_PLAYBOOK.md")
        for art in step.get("artifacts") or []:
            if not (ROOT / art).is_file():
                errors.append(f"{step.get('id')}: missing artifact {art}")
        spec_rel = step.get("spec")
        if spec_rel and not (ROOT / spec_rel).is_file():
            errors.append(f"{step.get('id')}: missing spec {spec_rel}")
        runbook = step.get("runbook")
        if runbook and not (ROOT / runbook).is_file():
            errors.append(f"{step.get('id')}: missing runbook {runbook}")
        mod = step.get("test_module")
        if mod and not (ROOT / mod).is_file():
            errors.append(f"{step.get('id')}: missing test module {mod}")

    for script in spec.get("aggregate_gates") or []:
        if not (ROOT / script).is_file():
            errors.append(f"missing aggregate gate {script}")

    report = {
        "authority": spec.get("authority"),
        "manifest_pass": not errors,
        "cisa_certification_claimed": False,
        "program_complete": False,
        "step_count": len(spec.get("steps") or []),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
