#!/usr/bin/env python3
"""Generate reviewer CI evidence bundle template (V-2 human URLs — never auto-filled)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"
SPEC = ROOT / "governance/launch57/LAUNCH57_CROSS_WORKFLOW_ASSURANCE.json"
OUT = ROOT / "governance/launch57/LAUNCH57_CI_REVIEWER_EVIDENCE_BUNDLE.json"


def _git_head_short() -> str:
    try:
        full = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        return full[:8] if full else ""
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def main() -> int:
    if not INDEX.is_file() or not SPEC.is_file():
        return 1
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    existing: dict = {}
    if OUT.is_file():
        existing = json.loads(OUT.read_text(encoding="utf-8"))
    # Preserve human-recorded URLs if reviewer already filled them.
    runs = existing.get("workflow_runs") or {}
    payload = {
        "schema": "launch57_ci_reviewer_evidence_bundle_v1",
        "authority": spec.get("authority"),
        "program_section": "§8.3 V-2",
        "evidence_class": "E-TEST",
        "cisa_certification_claimed": False,
        "program_complete": False,
        "generated_at": datetime.now(UTC).isoformat(),
        "remediation_sha": idx.get("remediation_sha"),
        "phase": idx.get("phase"),
        "git_head_short": _git_head_short(),
        "workflow_runs": {
            "security_pytest_security": {
                "workflow": ".github/workflows/security.yml",
                "job": "pytest-security",
                "green_run_url": runs.get("security_pytest_security", {}).get("green_run_url"),
            },
            "launch57_cisa_assurance": {
                "workflow": ".github/workflows/launch57-cisa-assurance.yml",
                "job": "engineering-baseline",
                "green_run_url": runs.get("launch57_cisa_assurance", {}).get("green_run_url"),
            },
        },
        "human_signoff": {
            "field": spec.get("qa_v2_human_signoff_field"),
            "recorded_by": existing.get("human_signoff", {}).get("recorded_by"),
            "recorded_at": existing.get("human_signoff", {}).get("recorded_at"),
            "instruction": "QA records both green_run_url values at remediation SHA; do not fabricate URLs in repo.",
        },
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
