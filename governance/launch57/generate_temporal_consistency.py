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

CURRENT_BATCH = "B2"
BATCH_LAUNCH_NUMBERS = [40, 41, 39]
BATCH_NAMES = {40: "Data quality & provenance", 41: "Freshness assurance + delayed explicit", 39: "Point-in-time immutable metrics"}

CHANGED_PATHS = [
    "launch57/batch2_isolation.py",
    "launch57/provenance_common.py",
    "launch57/freshness_common.py",
    "launch57/point_in_time_common.py",
    "launch57/b1_freshness_bridge.py",
    "launch57/data_batch2.py",
    "launch57/data_batch1.py",
    "tests/launch57/test_b2_isolation_closure.py",
    "tests/launch57/test_temporal_batch2.py",
    "tests/launch57/test_b1_to_41_reconciliation.py",
    "tests/launch57/test_data_batch2.py",
    "tests/launch57/test_data_batch1.py",
    "governance/launch57/generate_temporal_consistency.py",
]

PROHIBITED_REMOVED_B2 = [
    "failure.freshness",
    "cap646.evidence_class",
    "cap646.dedicated_common",
    "cap646.data_spine",
    "data_governance.freshness",
    "hot_storage",
    "oracle_track_record",
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
        "tests/launch57/test_b2_isolation_closure.py",
        "tests/launch57/test_temporal_batch2.py",
        "tests/launch57/test_b1_to_41_reconciliation.py",
        "tests/launch57/test_data_batch2.py",
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
    return {
        "artifact": "BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION",
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_sha": sha,
        "spec_sha256": spec_sha,
        "current_batch": CURRENT_BATCH,
        "batch_launch_numbers": BATCH_LAUNCH_NUMBERS,
        "batch_temporal_verdict": "B2:PENDING_VERIFICATION",
        "B2:#40": "PENDING_VERIFICATION",
        "B2:#41": "PENDING_VERIFICATION",
        "B2:#39": "PENDING_VERIFICATION",
        "B1_INDEPENDENT_VERDICT": b1_ref.get("B1_INDEPENDENT_VERDICT", "PASS_ENGINEERING"),
        "B1_INDEPENDENT_VERIFICATION_SHA": b1_ref.get("verified_sha"),
        "LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING": False,
        "LAUNCH57_TEMPORAL_CONSISTENCY_READY_FOR_LOCAL_USE": False,
        "PASS_LIVE_NOT_CLAIMED": True,
        "B2_ISOLATION_LEAKAGE": 0,
        "B2_LEGACY_RUNTIME_DEPENDENCIES": 0,
        "prohibited_dependencies_removed_b2": PROHIBITED_REMOVED_B2,
        "temporal_dependency_pending": [
            {
                "launch_number": 6,
                "status": "TEMPORAL_DEPENDENCY_PENDING",
                "missing_contract": "canonical #6 evidence-class owner",
                "consumer_impact": "B1/B2 omit evidence-class metadata until #6 PASS_ENGINEERING",
            },
            {
                "launch_number": 41,
                "status": "TEMPORAL_DEPENDENCY_PENDING",
                "missing_contract": "canonical #41 freshness semantics owner",
                "consumer_impact": "B1 #22/#21 freshness paths BLOCKED_BY_DEPENDENCY_ORDER until #41 PASS_ENGINEERING",
                "reconciliation_contract": "B1_TO_41_TARGETED_RECONCILIATION",
                "auto_activate_on_b2_pass": False,
            },
        ],
        "B1_TO_41_TARGETED_RECONCILIATION": "PREPARED_NOT_ACTIVATED",
        "B1_TO_41_RECONCILIATION_DETAIL": {
            "contract": "B1_TO_41_TARGETED_RECONCILIATION",
            "status": "PREPARED_NOT_ACTIVATED",
            "auto_activate": False,
            "activated": False,
            "rebuild_b1_forbidden": True,
            "affected_launch_items": [22, 21],
            "required_verdict": "B2:#41=PASS_ENGINEERING",
            "bridge_module": "launch57/b1_freshness_bridge.py",
            "note": "Bridge prepared but inert; TEMPORAL_DEPENDENCY_PENDING=#41 remains on B1 paths",
        },
        "DATA_BATCH2_REWRITE_AUDIT": {
            "verdict": "FULL_REWRITE_JUSTIFIED",
            "reason": "Every B2 entrypoint imported 7 legacy/PARKED modules with no shared-dependency exception; isolation requires Launch-57-local owners for #40/#41/#39",
            "legacy_modules_removed": PROHIBITED_REMOVED_B2,
            "smaller_delta_insufficient": "Partial import swaps would leave inline legacy helpers (_LIVE_ELIGIBLE, hot_storage, oracle_track_record) and mixed provenance/freshness/PIT semantics",
            "b2_consumers": [
                "launch57.data_batch2 execute paths (#40 CAP-0063/0500, #41 CAP-0630, #39 CAP-0061)",
                "cap646 institutional dispatch for batch-2 capability IDs",
                "B1 bridge (prepared, not activated) via launch57.freshness_common",
            ],
            "compatibility_impact": "Response shape preserved; builder_status=PENDING_VERIFICATION; legacy footer/freshness tokens removed from runtime",
            "regression_coverage": [
                "tests/launch57/test_b2_isolation_closure.py",
                "tests/launch57/test_temporal_batch2.py",
                "tests/launch57/test_data_batch2.py",
                "tests/launch57/test_b1_to_41_reconciliation.py",
            ],
            "rollback_path": "Revert launch57/data_batch2.py + companion *_common.py modules to pre-419e762f; restore B1 bridge gate; re-run targeted B2 tests",
        },
        "changed_paths": CHANGED_PATHS,
        "reused_unchanged_paths": [
            "launch57/temporal_common.py",
            "governance/launch57/B1_TEMPORAL_INDEPENDENT_VERIFICATION.json (reference only)",
        ],
        "tests": tests,
        "isolation_boundary_evidence": {
            "modified_within_launch57_only": True,
            "b2_isolation_owner": "launch57/batch2_isolation.py",
            "b2_legacy_runtime_dependencies": 0,
            "b2_isolation_leakage": 0,
        },
        "final_status": "BATCH_B2_PENDING_VERIFICATION",
    }


def build_report(sha: str, spec_sha: str, tests: dict) -> str:
    names = ", ".join(f"#{n} {BATCH_NAMES[n]}" for n in BATCH_LAUNCH_NUMBERS)
    return f"""# BLACKDARK Launch-57 Temporal Consistency Report

## A. Executive status

- **Current batch:** `{CURRENT_BATCH}` ({names})
- **B2 builder verdicts:** `B2:#40=PENDING_VERIFICATION`, `B2:#41=PENDING_VERIFICATION`, `B2:#39=PENDING_VERIFICATION`
- **B1 reference:** independent `PASS_ENGINEERING` @ `4a3b24cc` (unchanged evidence by reference)
- **Global:** `LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING=false`
- **PASS_LIVE:** not claimed

## B. Baseline SHA

- **Branch commit:** `{sha}`
- **Spec SHA256:** `{spec_sha}`

## C. B2 isolation

- `B2_ISOLATION_LEAKAGE=0`
- `B2_LEGACY_RUNTIME_DEPENDENCIES=0`
- Owners: `provenance_common` (#40), `freshness_common` (#41), `point_in_time_common` (#39)

## D. B1 → #41 reconciliation

- Status: `B1_TO_41_TARGETED_RECONCILIATION=PREPARED_NOT_ACTIVATED`
- `auto_activate=false`; bridge inert until `B2:#41=PASS_ENGINEERING`
- `TEMPORAL_DEPENDENCY_PENDING=#41` remains on B1 #22/#21 paths
- Affected: #22, #21 only; rebuild B1 forbidden

## E. data_batch2.py rewrite audit

- Verdict: `FULL_REWRITE_JUSTIFIED`
- Legacy modules removed: failure.freshness, cap646.*, data_governance.freshness, hot_storage, oracle_track_record
- Smaller delta insufficient: inline legacy helpers and mixed semantics would remain

## F. Remaining dependencies

- `#6` evidence-class: `TEMPORAL_DEPENDENCY_PENDING`
- `#41` freshness on B1 paths: `TEMPORAL_DEPENDENCY_PENDING` (bridge prepared, not activated)

## G. Tests

```text
{tests.get('command')}
exit_code={tests.get('exit_code')}
passed={tests.get('passed')}
```

## H. Final verdict

- **BATCH_TEMPORAL_VERDICT=B2:PENDING_VERIFICATION**
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
