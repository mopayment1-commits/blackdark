#!/usr/bin/env python3
"""Aggregate honest readiness for open/partial findings (dry-run only; no --apply)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "governance/launch57/LAUNCH57_OPEN_OPS_CLOSURE_PACKAGE.json"
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"
TRANSITION = ROOT / "scripts/transition_launch57_finding_status.py"


def main() -> int:
    steps: list[dict] = []
    if not PKG.is_file() or not INDEX.is_file():
        return 1

    proc81 = subprocess.run(
        [sys.executable, str(ROOT / "scripts/verify_launch57_program_closure_81.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    try:
        closure81 = json.loads(proc81.stdout)
    except json.JSONDecodeError:
        closure81 = {}
    steps.append({"name": "program_closure_81", "exit_code": proc81.returncode})

    proc_preflight = subprocess.run(
        [sys.executable, str(ROOT / "scripts/preflight_launch57_open_finding_transitions.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    preflight = json.loads(proc_preflight.stdout) if proc_preflight.stdout.strip() else {}
    steps.append({"name": "open_finding_transitions_preflight", "exit_code": proc_preflight.returncode})

    proc_iv = subprocess.run(
        [sys.executable, str(ROOT / "scripts/preflight_launch57_iv_human_signoffs.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    iv = json.loads(proc_iv.stdout) if proc_iv.stdout.strip() else {}
    steps.append({"name": "iv_human_signoffs_preflight", "exit_code": proc_iv.returncode})

    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    open_rows = {
        fid: row
        for fid, row in (idx.get("findings") or {}).items()
        if str(row.get("status", "")) != "CLOSED"
    }

    report = {
        "authority": "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md",
        "program_section": "§8.1 / §3.3",
        "cisa_certification_claimed": False,
        "program_complete_81": bool(closure81.get("program_complete_81")),
        "findings_not_closed_exact": closure81.get("findings_not_closed_exact"),
        "open_inventory_summary": {fid: row.get("status") for fid, row in open_rows.items()},
        "transition_preflight": {
            "ready_for_apply_with_evidence": preflight.get("ready_for_apply_with_evidence", []),
            "blocked": preflight.get("blocked", []),
        },
        "iv_human": {
            "all_recorded": iv.get("all_human_signoffs_recorded"),
            "steps": iv.get("steps"),
        },
        "steps": steps,
        "honesty": "exit 0 reports status only; use transition --apply after real E-OPS/E-LEGAL evidence.",
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
