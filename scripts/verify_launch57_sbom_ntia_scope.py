#!/usr/bin/env python3
"""Program §6 FINDING-11 / NTIA-MIN — verify SBOM scope statement and gap analysis artifact (no fake Sec Lead approval)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAP = ROOT / "governance/launch57/LAUNCH57_NTIA_SBOM_GAP_ANALYSIS.json"
SCOPE = ROOT / "docs/security/SBOM_SCOPE_STATEMENT.md"
PROGRAM = ROOT / "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md"
REQUIRED_SCRIPTS = (
    "scripts/generate_sbom.py",
    "scripts/generate_syft_lockfile_sbom.sh",
    "scripts/generate_container_sbom.sh",
)


def main() -> int:
    errors: list[str] = []
    if not all(p.is_file() for p in (GAP, SCOPE, PROGRAM)):
        print("MISSING gap analysis, scope statement, or program", file=sys.stderr)
        return 1
    gap = json.loads(GAP.read_text(encoding="utf-8"))
    elements = gap.get("ntia_minimum_elements") or {}
    for key, row in elements.items():
        if str(row.get("status", "")) != "PRESENT":
            errors.append(f"NTIA element {key} not PRESENT")
        if not row.get("evidence"):
            errors.append(f"NTIA element {key} missing evidence pointer")
    for rel in REQUIRED_SCRIPTS:
        if not (ROOT / rel).is_file():
            errors.append(f"missing generator {rel}")
    scope_text = SCOPE.read_text(encoding="utf-8")
    if "NTIA" not in scope_text and "ntia" not in scope_text.lower():
        errors.append("SBOM_SCOPE_STATEMENT.md must reference NTIA minimum elements")
    if "LAUNCH57_NTIA_SBOM_GAP_ANALYSIS.json" not in scope_text:
        errors.append("SBOM_SCOPE_STATEMENT.md must link LAUNCH57_NTIA_SBOM_GAP_ANALYSIS.json")
    approval = (os.getenv("LAUNCH57_SBOM_SEC_LEAD_APPROVAL_ID") or "").strip() or gap.get("security_lead_approval_id")
    report = {
        "pass": not errors,
        "program_ref": "§6 FINDING-11",
        "security_lead_approval_recorded": bool(approval),
        "finding_11_repo_acceptance_met": not errors,
        "finding_11_full_closed": bool(approval) and not errors,
        "cisa_certification_claimed": False,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    if errors:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
