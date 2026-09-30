#!/usr/bin/env python3
"""Verify post-merge ops manifest matches institutional ops doc and script inventory."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "governance/launch57/LAUNCH57_POST_MERGE_OPS_MANIFEST.json"
OPS_DOC = ROOT / "docs/ops/LAUNCH57_POST_MERGE_OPS.md"
HANDOFF = ROOT / "governance/launch57/LAUNCH57_ENGINEERING_HANDOFF.json"


def main() -> int:
    errors: list[str] = []
    for path in (MANIFEST, OPS_DOC, HANDOFF):
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        print(json.dumps({"pass": False, "errors": errors}, indent=2))
        return 1

    spec = json.loads(MANIFEST.read_text(encoding="utf-8"))
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    if spec.get("cisa_certification_claimed") or spec.get("program_complete"):
        errors.append("manifest must not claim certification or program complete")
    if handoff.get("post_merge_ops") != str(OPS_DOC.relative_to(ROOT)):
        errors.append("handoff post_merge_ops path drift vs manifest authority doc")

    ops_text = OPS_DOC.read_text(encoding="utf-8")
    seen_scripts: set[str] = set()
    for step in spec.get("steps") or []:
        for script in step.get("scripts") or []:
            seen_scripts.add(script)
            if not (ROOT / script).is_file():
                errors.append(f"{step.get('id')}: missing script {script}")
            if script not in ops_text and script.replace("scripts/", "") not in ops_text:
                errors.append(f"{step.get('id')}: script {script} not referenced in POST_MERGE_OPS.md")
        rec = step.get("recording_spec")
        if rec and not (ROOT / rec).is_file():
            errors.append(f"{step.get('id')}: missing recording_spec {rec}")
    for script in spec.get("aggregate_gates") or []:
        if not (ROOT / script).is_file():
            errors.append(f"missing aggregate gate {script}")

    pkg_rel = spec.get("open_ops_closure_package")
    if pkg_rel and not (ROOT / pkg_rel).is_file():
        errors.append(f"missing open_ops_closure_package {pkg_rel}")

    report = {
        "authority": spec.get("authority"),
        "program_sections": spec.get("program_sections"),
        "manifest_pass": not errors,
        "cisa_certification_claimed": False,
        "script_count": len(seen_scripts),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
