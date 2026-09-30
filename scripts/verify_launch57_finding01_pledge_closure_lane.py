#!/usr/bin/env python3
"""§6 FINDING-01 / CISA-SBDf — pledge closure lane (E-LEGAL prep; no fake signature)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "governance/launch57/LAUNCH57_FINDING_01_PLEDGE_CLOSURE_LANE.json"
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"
HTTPS_RE = re.compile(r"https://[^\s|]+", re.I)


def main() -> int:
    errors: list[str] = []
    if not LANE.is_file():
        return 1
    spec = json.loads(LANE.read_text(encoding="utf-8"))
    if spec.get("cisa_certification_claimed"):
        errors.append("lane must not claim CISA certification")

    status_path = ROOT / str((spec.get("repo_artifacts") or {}).get("pledge_status", ""))
    for key, rel in (spec.get("repo_artifacts") or {}).items():
        if not rel or not (ROOT / rel).is_file():
            errors.append(f"missing {key}: {rel}")

    readiness = ROOT / "scripts/record_launch57_finding01_pledge_readiness.py"
    proc = subprocess.run([sys.executable, str(readiness)], cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        errors.append("record_launch57_finding01_pledge_readiness.py failed")

    pledge_url_in_status = False
    if status_path.is_file():
        text = status_path.read_text(encoding="utf-8")
        if "does **not** claim pledge participation" not in text and "Pending executive" not in text:
            if "pledge signed" in text.lower() and spec.get("status_submission_heading") not in text:
                errors.append("STATUS may claim pledge without Submission record section")
        heading = str(spec.get("status_submission_heading", "## Submission record"))
        if heading in text:
            section = text.split(heading, 1)[-1]
            pledge_url_in_status = bool(HTTPS_RE.search(section))

    evidence_dir = ROOT / str(spec.get("evidence_dir_gitignored", ""))
    has_erun = evidence_dir.is_dir() and any(evidence_dir.glob("PLEDGE_*.json"))

    index_status = ""
    if INDEX.is_file():
        index_status = str(
            (json.loads(INDEX.read_text(encoding="utf-8")).get("findings") or {}).get("FINDING-01", {}).get("status", "")
        )

    report = {
        "program_ref": "§6 FINDING-01; CISA-SBDf",
        "repo_lane_pass": not errors,
        "cisa_certification_claimed": False,
        "index_status_finding_01": index_status,
        "pledge_submission_recorded_in_status_md": pledge_url_in_status,
        "readiness_record_present": has_erun,
        "closure_ready_for_apply": pledge_url_in_status,
        "finding_01_closed_in_index": index_status == "CLOSED",
        "errors": errors,
        "honesty": "Repo lane PASS does not close FINDING-01; executive records CISA portal URL then transition --apply with --pledge-url.",
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
