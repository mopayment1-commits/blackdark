#!/usr/bin/env python3
"""Generate Launch-57 Commercial Capability Inventory audit artifacts (AUDIT ONLY)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GOV = ROOT / "governance" / "launch57"

INVENTORY_PATH = GOV / "BLACKDARK_LAUNCH57_COMMERCIAL_CAPABILITY_INVENTORY.json"
TIER_PATH = GOV / "BLACKDARK_LAUNCH57_TIER_VARIABLE_INVENTORY.json"
VALUE_PATH = GOV / "BLACKDARK_LAUNCH57_COMMERCIAL_VALUE_MATRIX.json"
COST_RIGHTS_PATH = GOV / "BLACKDARK_LAUNCH57_COST_RIGHTS_MATRIX.json"
READINESS_PATH = GOV / "BLACKDARK_LAUNCH57_COMMERCIAL_READINESS.json"
RECOMPUTE_PATH = GOV / "BLACKDARK_LAUNCH57_INDEPENDENT_RECOMPUTATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_COMMERCIAL_CAPABILITY_INVENTORY_AUDIT_REPORT.md"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Commercial_Capability_Inventory_FROM_SCRATCH_SPEC_4__1__268d.md"
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _spec_sha() -> str:
    if not SPEC_UPLOAD.exists():
        return "unknown"
    import hashlib

    return hashlib.sha256(SPEC_UPLOAD.read_bytes()).hexdigest()


def _run_tests() -> dict[str, Any]:
    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/launch57/test_commercial_inventory.py",
        "tests/launch57/test_billing_entitlement.py",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": str(proc.returncode),
        "stdout_tail": proc.stdout.strip()[-500:],
        "stderr_tail": proc.stderr.strip()[-500:],
        "passed": proc.returncode == 0,
    }


def main() -> None:
    from launch57.commercial_inventory_common import (
        AUDIT_MODE,
        COMMERCIAL_INVENTORY_VERSION,
        build_audit_baseline,
        build_commercial_capability_inventory,
        build_commercial_readiness,
        build_commercial_value_matrix,
        build_cost_rights_matrix,
        build_reconciliation_counters,
        build_tier_variable_inventory,
        independent_recomputation,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    baseline = build_audit_baseline()
    inventory = build_commercial_capability_inventory()
    counters = build_reconciliation_counters()
    readiness = build_commercial_readiness()
    recompute = independent_recomputation()

    inv_artifact = {
        "artifact": "BLACKDARK_LAUNCH57_COMMERCIAL_CAPABILITY_INVENTORY",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "audit_baseline": baseline,
        "commercial_inventory_version": COMMERCIAL_INVENTORY_VERSION,
        "audit_mode": AUDIT_MODE,
        "scope": "LAUNCH57_IDS",
        "not_a_new_ssot": True,
        "inventory_count": len(inventory),
        "capabilities": inventory,
        "reconciliation_counters": counters,
    }
    INVENTORY_PATH.write_text(json.dumps(inv_artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    tier_artifact = {
        "artifact": "BLACKDARK_LAUNCH57_TIER_VARIABLE_INVENTORY",
        "generated_at": now,
        "implementation_sha": sha,
        "tier_variables": build_tier_variable_inventory(),
        "not_counted_in_launch57_capability_count": True,
    }
    TIER_PATH.write_text(json.dumps(tier_artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    value_artifact = {
        "artifact": "BLACKDARK_LAUNCH57_COMMERCIAL_VALUE_MATRIX",
        "generated_at": now,
        "implementation_sha": sha,
        "matrix": build_commercial_value_matrix(),
    }
    VALUE_PATH.write_text(json.dumps(value_artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    cost_rights = {
        "artifact": "BLACKDARK_LAUNCH57_COST_RIGHTS_MATRIX",
        "generated_at": now,
        "implementation_sha": sha,
        "matrix": build_cost_rights_matrix(),
        "external_evidence_required": True,
    }
    COST_RIGHTS_PATH.write_text(json.dumps(cost_rights, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    readiness_artifact = {
        "artifact": "BLACKDARK_LAUNCH57_COMMERCIAL_READINESS",
        "generated_at": now,
        "implementation_sha": sha,
        **readiness,
        "tests_pass": tests["passed"],
    }
    READINESS_PATH.write_text(json.dumps(readiness_artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    recompute_artifact = {
        "artifact": "BLACKDARK_LAUNCH57_INDEPENDENT_RECOMPUTATION",
        "generated_at": now,
        "implementation_sha": sha,
        **recompute,
        "tests_pass": tests["passed"],
    }
    RECOMPUTE_PATH.write_text(json.dumps(recompute_artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Commercial Capability Inventory Audit Report",
        "",
        f"- Generated: {now}",
        f"- Audit SHA: `{baseline['AUDIT_BASELINE_SHA'][:12]}…`",
        f"- Branch: `{baseline['AUDIT_BRANCH']}`",
        f"- Mode: **{AUDIT_MODE}**",
        "",
        "## A. Executive Verdict",
        "",
        f"- `LAUNCH57_INVENTORY_COMPLETE`: **{readiness['LAUNCH57_INVENTORY_COMPLETE']}**",
        f"- `ENGINEERING_EVIDENCE_SUFFICIENT`: **{readiness['ENGINEERING_EVIDENCE_SUFFICIENT']}**",
        f"- `COMMERCIAL_READY_FOR_TIER_DESIGN`: **{readiness['COMMERCIAL_READY_FOR_TIER_DESIGN']}**",
        f"- `EXTERNAL_ASSURANCE_COMPLETE`: **{readiness['EXTERNAL_ASSURANCE_COMPLETE']}**",
        f"- `LAUNCH57_COMMERCIAL_INVENTORY_AUDIT_CLOSED`: **{readiness['LAUNCH57_COMMERCIAL_INVENTORY_AUDIT_CLOSED']}**",
        "",
        "## B. Baseline SHA",
        "",
        f"- `AUDIT_BASELINE_SHA`: `{baseline['AUDIT_BASELINE_SHA']}`",
        f"- `WORKTREE_DIRTY`: **{baseline['WORKTREE_DIRTY']}**",
        "",
        "## C. 57/57 Reconciliation",
        "",
        f"- Expected: **{counters['LAUNCH57_EXPECTED_COUNT']}**",
        f"- Reconciled: **{counters['LAUNCH57_RECONCILED_COUNT']}**",
        f"- Duplicate canonical: **{counters['DUPLICATE_CANONICAL_COUNT']}**",
        f"- PASS_ENGINEERING: **{counters['PASS_ENGINEERING_COUNT']}**",
        f"- PENDING_VERIFICATION: **{counters['PENDING_VERIFICATION_COUNT']}**",
        "",
        "## D. Full Capability Inventory",
        "",
        "| # | Capability | Engineering | Commercial Use | Access |",
        "|---|------------|-------------|----------------|--------|",
    ]
    for row in inventory:
        lines.append(
            f"| {row['launch_number']} | {row.get('canonical_name', '')[:40]} | "
            f"{row.get('engineering_state')} | {row.get('commercial_use_state')} | "
            f"{', '.join(row.get('access_states') or [])} |"
        )
    lines.extend(
        [
            "",
            "## U. Independent Recomputation",
            "",
            f"- `INDEPENDENT_RECOMPUTATION_MATCH`: **{recompute['INDEPENDENT_RECOMPUTATION_MATCH']}**",
            f"- `SELF_REFERENTIAL_AUDIT_EVIDENCE_COUNT`: **{recompute['SELF_REFERENTIAL_AUDIT_EVIDENCE_COUNT']}**",
            "",
            "## V. Final Four Verdicts",
            "",
            f"- Inventory complete: **{readiness['LAUNCH57_INVENTORY_COMPLETE']}**",
            f"- Engineering evidence sufficient: **{readiness['ENGINEERING_EVIDENCE_SUFFICIENT']}**",
            f"- Commercial ready for tier design: **{readiness['COMMERCIAL_READY_FOR_TIER_DESIGN']}**",
            f"- External assurance complete: **{readiness['EXTERNAL_ASSURANCE_COMPLETE']}**",
            "",
            "## Mandatory Stop",
            "",
            "Audit artifacts produced. **STOP** — no pricing, tier assignment, or product remediation in this task.",
            "",
            f"- Tests pass: **{tests['passed']}**",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        "Wrote",
        INVENTORY_PATH.name,
        TIER_PATH.name,
        VALUE_PATH.name,
        COST_RIGHTS_PATH.name,
        READINESS_PATH.name,
        RECOMPUTE_PATH.name,
        REPORT_PATH.name,
    )


if __name__ == "__main__":
    main()
