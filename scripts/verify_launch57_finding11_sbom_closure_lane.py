#!/usr/bin/env python3
"""§6 FINDING-11 — SBOM closure lane repo gates (NTIA scope; no fake Sec Lead approval)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "governance/launch57/LAUNCH57_FINDING_11_SBOM_CLOSURE_LANE.json"
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"


def main() -> int:
    errors: list[str] = []
    if not LANE.is_file():
        print("missing closure lane spec", file=sys.stderr)
        return 1
    spec = json.loads(LANE.read_text(encoding="utf-8"))
    if spec.get("cisa_certification_claimed"):
        errors.append("lane must not claim CISA certification")

    for rel in (spec.get("repo_artifacts") or {}).values():
        if rel and not (ROOT / rel).is_file():
            errors.append(f"missing repo artifact {rel}")
    for rel in spec.get("generators") or []:
        if not (ROOT / rel).is_file():
            errors.append(f"missing generator {rel}")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_launch57_sbom_ntia_scope.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    ntia_ok = proc.returncode == 0
    if not ntia_ok:
        errors.append("verify_launch57_sbom_ntia_scope.py failed")

    syft = spec.get("syft_lock_artifact") or {}
    syft_path = ROOT / str(syft.get("default_path", ""))
    validator = syft.get("validator", "")
    syft_present = syft_path.is_file()
    syft_valid = False
    if validator and not (ROOT / validator).is_file():
        errors.append(f"missing validator {validator}")
    elif syft_present and validator:
        vproc = subprocess.run(
            [sys.executable, str(ROOT / validator), str(syft_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        syft_valid = vproc.returncode == 0
        if not syft_valid and vproc.returncode != 3:
            errors.append(f"syft artifact validation failed exit {vproc.returncode}")

    has_sec_lead_env = bool((os.getenv("LAUNCH57_SBOM_SEC_LEAD_APPROVAL_ID") or "").strip())
    has_container_env = bool((os.getenv("LAUNCH57_CONTAINER_SBOM_PATH") or "").strip())
    index_status = ""
    if INDEX.is_file():
        index_status = str((json.loads(INDEX.read_text(encoding="utf-8")).get("findings") or {}).get("FINDING-11", {}).get("status", ""))

    report = {
        "program_ref": "§6 FINDING-11",
        "repo_lane_pass": not errors,
        "cisa_certification_claimed": False,
        "index_status_finding_11": index_status,
        "ntia_scope_gate_pass": ntia_ok,
        "syft_artifact_present": syft_present,
        "syft_artifact_valid": syft_valid if syft_present else None,
        "sec_lead_approval_env_set": has_sec_lead_env,
        "container_sbom_env_set": has_container_env,
        "closure_path_ready": bool(
            has_sec_lead_env or syft_present or has_container_env
        ),
        "finding_11_closed_in_index": index_status == "CLOSED",
        "errors": errors,
        "honesty": "Repo lane PASS does not set FINDING-11 to CLOSED; use transition --apply after real approval or SBOM artifact.",
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
