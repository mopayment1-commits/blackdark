#!/usr/bin/env python3
"""§6 FINDING-14 / RFC-9116 — security.txt closure lane (repo + optional prod env)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "governance/launch57/LAUNCH57_FINDING_14_SECURITY_TXT_CLOSURE_LANE.json"
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"


def main() -> int:
    errors: list[str] = []
    if not LANE.is_file():
        return 1
    spec = json.loads(LANE.read_text(encoding="utf-8"))
    if spec.get("cisa_certification_claimed"):
        errors.append("lane must not claim CISA certification")

    arts = spec.get("repo_artifacts") or {}
    for key, rel in arts.items():
        if not rel or not (ROOT / rel).is_file():
            errors.append(f"missing {key}: {rel}")

    proc_repo = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_well_known_security_txt.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    repo_verify_ok = proc_repo.returncode == 0
    if not repo_verify_ok:
        errors.append("repo security.txt verification failed")

    prod = (os.getenv(str((spec.get("environment") or {}).get("prod_url_var", "LAUNCH57_PROD_URL"))) or "").strip()
    prod_verify_ok: bool | None = None
    if prod:
        proc_prod = subprocess.run(
            [sys.executable, str(ROOT / "scripts/verify_well_known_security_txt.py"), "--url", prod],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        prod_verify_ok = proc_prod.returncode == 0

    evidence_dir = ROOT / str(spec.get("evidence_dir_gitignored", ""))
    has_erun = evidence_dir.is_dir() and any(evidence_dir.glob("SECURITY_TXT_PROD_RUN_*.json"))

    index_status = ""
    if INDEX.is_file():
        index_status = str(
            (json.loads(INDEX.read_text(encoding="utf-8")).get("findings") or {}).get("FINDING-14", {}).get("status", "")
        )

    report = {
        "program_ref": "§6 FINDING-14; RFC-9116",
        "repo_lane_pass": not errors,
        "cisa_certification_claimed": False,
        "index_status_finding_14": index_status,
        "repo_security_txt_verify_pass": repo_verify_ok,
        "prod_url_set": bool(prod),
        "prod_security_txt_verify_pass": prod_verify_ok,
        "erun_record_present": has_erun,
        "closure_ready_for_apply": bool(prod and prod_verify_ok),
        "finding_14_closed_in_index": index_status == "CLOSED",
        "errors": errors,
        "honesty": "Repo PASS does not close FINDING-14; record E-RUN on prod then transition --apply.",
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
