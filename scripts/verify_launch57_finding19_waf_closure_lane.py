#!/usr/bin/env python3
"""§6 FINDING-19 — WAF/CDN closure lane repo gates (E-OPS when CDN_WAF_ACTIVE set)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "governance/launch57/LAUNCH57_FINDING_19_WAF_CLOSURE_LANE.json"
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"


def main() -> int:
    errors: list[str] = []
    if not LANE.is_file():
        return 1
    spec = json.loads(LANE.read_text(encoding="utf-8"))
    if spec.get("cisa_certification_claimed"):
        errors.append("lane must not claim CISA certification")

    for key, rel in (spec.get("repo_artifacts") or {}).items():
        if not rel or not (ROOT / rel).is_file():
            errors.append(f"missing {key}: {rel}")

    waf_env = (os.getenv(str((spec.get("environment") or {}).get("waf_active_var", "CDN_WAF_ACTIVE"))) or "").strip()
    waf_verify_pass: bool | None = None
    if waf_env:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/verify_edge_waf_cdn.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        waf_verify_pass = proc.returncode == 0

    evidence_dir = ROOT / str(spec.get("evidence_dir_gitignored", ""))
    has_erun = evidence_dir.is_dir() and any(evidence_dir.glob("WAF_CDN_RUN_*.json"))

    index_status = ""
    if INDEX.is_file():
        index_status = str(
            (json.loads(INDEX.read_text(encoding="utf-8")).get("findings") or {}).get("FINDING-19", {}).get("status", "")
        )

    report = {
        "program_ref": "§6 FINDING-19",
        "repo_lane_pass": not errors,
        "cisa_certification_claimed": False,
        "index_status_finding_19": index_status,
        "cdn_waf_active_env_set": bool(waf_env),
        "waf_verify_pass": waf_verify_pass,
        "erun_record_present": has_erun,
        "closure_ready_for_apply": waf_verify_pass is True,
        "finding_19_closed_in_index": index_status == "CLOSED",
        "errors": errors,
        "honesty": "Repo lane PASS does not close FINDING-19; set CDN_WAF_ACTIVE=1 and pass verify_edge_waf_cdn before --apply.",
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
