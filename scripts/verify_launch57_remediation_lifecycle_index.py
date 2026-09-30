#!/usr/bin/env python3
"""Verify remediation lifecycle index links manifests, docs, and evidence index (navigation only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "governance/launch57/LAUNCH57_REMEDIATION_LIFECYCLE_INDEX.json"
EVIDENCE_INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"


def main() -> int:
    errors: list[str] = []
    if not INDEX_PATH.is_file():
        print("missing lifecycle index", file=sys.stderr)
        return 1
    spec = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    if spec.get("cisa_certification_claimed") or spec.get("program_complete"):
        errors.append("lifecycle index must not claim certification or program complete")

    idx_rel = spec.get("evidence_index")
    if not idx_rel or not (ROOT / idx_rel).is_file():
        errors.append("missing evidence index")
    else:
        idx = json.loads((ROOT / idx_rel).read_text(encoding="utf-8"))
        for key in (
            "merge_to_main_readiness_manifest",
            "post_merge_ops_manifest",
            "final_closure_playbook_manifest",
            "open_ops_closure_package",
        ):
            if key in idx and idx.get(key):
                path = ROOT / str(idx[key])
                if not path.is_file():
                    errors.append(f"evidence index broken link {key}")

    for stage in spec.get("lifecycle_stages") or []:
        for field in ("manifest", "manifest_gate", "primary_doc"):
            rel = stage.get(field, "")
            if not rel or not (ROOT / rel).is_file():
                errors.append(f"{stage.get('id')}: missing {field} {rel}")

    readiness = spec.get("open_findings_closure_readiness", "")
    if readiness and not (ROOT / readiness).is_file():
        errors.append(f"missing {readiness}")

    for gate in spec.get("program_closure_gates") or []:
        script = gate.get("script", "")
        if not script or not (ROOT / script).is_file():
            errors.append(f"missing program gate script {script}")

    for rel in (spec.get("open_findings_register"), spec.get("open_ops_closure_package")):
        if rel and not (ROOT / rel).is_file():
            errors.append(f"missing {rel}")

    report = {
        "program_sections": spec.get("program_sections"),
        "lifecycle_pass": not errors,
        "cisa_certification_claimed": False,
        "stage_count": len(spec.get("lifecycle_stages") or []),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

