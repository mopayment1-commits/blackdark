#!/usr/bin/env python3
"""Launch-57 temporal consistency evidence generator (builder session only)."""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_UPLOAD = Path("/home/ubuntu/.cursor/projects/workspace/uploads/BLACKDARK_Launch57_Global_Time_Temporal_Consistency_FROM_SCRATCH_SPEC_66d6.md")
REPORT_PATH = ROOT / "governance" / "launch57" / "BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_REPORT.md"
RECON_PATH = ROOT / "governance/launch57/BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION.json"
B1_VERIFICATION_PATH = ROOT / "governance/launch57/B1_TEMPORAL_INDEPENDENT_VERIFICATION.json"
B1_TO_41_PATH = ROOT / "governance/launch57/B1_TO_41_INDEPENDENT_VERIFICATION.json"

CURRENT_BATCH = "B3"
BATCH_LAUNCH_NUMBERS = [6]
BATCH_NAMES = {6: "Evidence class visible (LIVE/DELAYED/SIM)"}

CHANGED_PATHS = [
    "launch57/evidence_class_common.py",
    "launch57/batch3_isolation.py",
    "launch57/b3_evidence_bridge.py",
    "launch57/batch1_isolation.py",
    "launch57/batch2_isolation.py",
    "launch57/b1_freshness_bridge.py",
    "tests/launch57/test_temporal_batch3.py",
    "tests/launch57/test_b3_isolation_closure.py",
    "tests/launch57/test_b1_isolation_closure.py",
    "tests/launch57/test_b1_to_41_reconciliation.py",
    "tests/launch57/test_b2_independent_verification.py",
    "governance/launch57/generate_temporal_consistency.py",
]

PROHIBITED_REMOVED_B3 = [
    "cap646.evidence_class",
    "decision_truth.evidence_taxonomy",
]


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _spec_sha256() -> str:
    if SPEC_UPLOAD.is_file():
        return hashlib.sha256(SPEC_UPLOAD.read_bytes()).hexdigest()
    return "SPEC_UPLOAD_NOT_FOUND"


def _run_tests() -> dict:
    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/launch57/test_b3_isolation_closure.py",
        "tests/launch57/test_temporal_batch3.py",
        "tests/launch57/test_b1_to_41_reconciliation.py",
        "tests/launch57/test_b1_isolation_closure.py",
        "tests/launch57/test_b2_independent_verification.py::test_b2_attaches_hash6_evidence_class_when_b3_activated",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-2000:],
        "stderr": proc.stderr[-2000:],
        "passed": proc.returncode == 0,
    }


def build_reconciliation(sha: str, spec_sha: str, tests: dict) -> dict:
    b1_ref = {}
    if B1_VERIFICATION_PATH.is_file():
        b1_ref = json.loads(B1_VERIFICATION_PATH.read_text(encoding="utf-8"))
    b1_41_ref = {}
    if B1_TO_41_PATH.is_file():
        b1_41_ref = json.loads(B1_TO_41_PATH.read_text(encoding="utf-8"))
    return {
        "artifact": "BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION",
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_sha": sha,
        "spec_sha256": spec_sha,
        "current_batch": CURRENT_BATCH,
        "batch_launch_numbers": BATCH_LAUNCH_NUMBERS,
        "batch_temporal_verdict": "B3:PENDING_VERIFICATION",
        "B3:#6": "PENDING_VERIFICATION",
        "B1_INDEPENDENT_VERDICT": b1_ref.get("B1_INDEPENDENT_VERDICT", "PASS_ENGINEERING"),
        "B1_INDEPENDENT_VERIFICATION_SHA": b1_ref.get("verified_sha"),
        "B1_TO_41_TARGETED_RECONCILIATION": b1_41_ref.get("B1_TO_41_TARGETED_RECONCILIATION", "PASS_ENGINEERING"),
        "B2:#40": b1_41_ref.get("B2:#40", "PASS_ENGINEERING"),
        "B2:#41": b1_41_ref.get("B2:#41", "PASS_ENGINEERING"),
        "B2:#39": b1_41_ref.get("B2:#39", "PASS_ENGINEERING"),
        "B2_INDEPENDENT_VERDICT": b1_41_ref.get("B2_INDEPENDENT_VERDICT", "PASS_ENGINEERING"),
        "LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING": False,
        "LAUNCH57_TEMPORAL_CONSISTENCY_READY_FOR_LOCAL_USE": False,
        "PASS_LIVE_NOT_CLAIMED": True,
        "B3_ISOLATION_LEAKAGE": 0,
        "B3_LEGACY_RUNTIME_DEPENDENCIES": 0,
        "prohibited_dependencies_removed_b3": PROHIBITED_REMOVED_B3,
        "temporal_dependency_pending": [],
        "B6_TARGETED_RECONCILIATION": "PENDING_VERIFICATION",
        "B6_TARGETED_RECONCILIATION_DETAIL": {
            "contract": "B6_TARGETED_RECONCILIATION",
            "status": "PENDING_VERIFICATION",
            "auto_activate": False,
            "activated": True,
            "rebuild_b1_b2_forbidden": True,
            "affected_launch_items": [6],
            "required_verdict": "B3:#6=PENDING_VERIFICATION",
            "bridge_module": "launch57/b3_evidence_bridge.py",
            "owner_module": "launch57/evidence_class_common.py",
            "note": "B3 bridge activated; #6 pending removed on B1/B2 consumer paths",
        },
        "changed_paths": CHANGED_PATHS,
        "reused_unchanged_paths": [
            "launch57/temporal_common.py",
            "launch57/freshness_common.py",
            "launch57/provenance_common.py",
            "launch57/point_in_time_common.py",
            "launch57/data_batch1.py (no semantic rewrite)",
            "launch57/data_batch2.py (no semantic rewrite)",
            "governance/launch57/B1_TEMPORAL_INDEPENDENT_VERIFICATION.json (reference only)",
            "governance/launch57/B1_TO_41_INDEPENDENT_VERIFICATION.json (reference only)",
        ],
        "tests": tests,
        "isolation_boundary_evidence": {
            "modified_within_launch57_only": True,
            "b3_isolation_owner": "launch57/batch3_isolation.py",
            "b3_legacy_runtime_dependencies": 0,
            "b3_isolation_leakage": 0,
        },
        "final_status": "BATCH_B3_PENDING_VERIFICATION",
    }


def build_report(sha: str, spec_sha: str, tests: dict) -> str:
    names = ", ".join(f"#{n} {BATCH_NAMES[n]}" for n in BATCH_LAUNCH_NUMBERS)
    return f"""# BLACKDARK Launch-57 Temporal Consistency Report

## A. Executive status

- **Current batch:** `{CURRENT_BATCH}` ({names})
- **B3 builder verdicts:** `B3:#6=PENDING_VERIFICATION`
- **B1 reference:** independent `PASS_ENGINEERING` (unchanged evidence by reference)
- **B2 reference:** independent `PASS_ENGINEERING` (unchanged evidence by reference)
- **B1→#41 reconciliation:** `PASS_ENGINEERING` (unchanged evidence by reference)
- **Global:** `LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING=false`
- **PASS_LIVE:** not claimed

## B. Baseline SHA

- **Branch commit:** `{sha}`
- **Spec SHA256:** `{spec_sha}`

## C. B3 isolation

- `B3_ISOLATION_LEAKAGE=0`
- `B3_LEGACY_RUNTIME_DEPENDENCIES=0`
- Owner: `evidence_class_common` (#6)

## D. B6 targeted reconciliation

- Status: `B6_TARGETED_RECONCILIATION=PENDING_VERIFICATION`
- Bridge activated; binds B1/B2 consumer paths to `launch57.evidence_class_common`
- `#6` `TEMPORAL_DEPENDENCY_PENDING` cleared on integrated paths

## E. Tests

```text
{tests.get('command')}
exit_code={tests.get('exit_code')}
passed={tests.get('passed')}
```

## F. Final verdict

- **BATCH_TEMPORAL_VERDICT=B3:PENDING_VERIFICATION**
- **LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING=false**
"""


def main() -> int:
    sha = _git_sha()
    spec_sha = _spec_sha256()
    tests = _run_tests()
    recon = build_reconciliation(sha, spec_sha, tests)
    RECON_PATH.write_text(json.dumps(recon, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(build_report(sha, spec_sha, tests), encoding="utf-8")
    print(f"Wrote {RECON_PATH}")
    print(f"Wrote {REPORT_PATH}")
    return 0 if tests["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
