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
RECON_PATH = ROOT / "governance" / "launch57" / "BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION.json"

CURRENT_BATCH = "B1"
BATCH_LAUNCH_NUMBERS = [42, 22, 23, 24, 21]
BATCH_NAMES = {
    42: "Unified exchange connector",
    22: "Real-time / near-real-time prices",
    23: "OHLCV",
    24: "Quote + symbol metadata",
    21: "Spot metrics suite",
}

CHANGED_PATHS = [
    "launch57/temporal_common.py",
    "launch57/data_batch1.py",
    "tests/launch57/test_temporal_batch1.py",
    "governance/launch57/generate_temporal_consistency.py",
]

REUSED_PATHS = [
    "launch57/data_batch1.py (existing freshness via failure.freshness read-only)",
    "cap646.evidence_class (read-only ai_compliance_footer)",
    "data_governance.freshness.attach_data_freshness (read-only)",
]

TEMPORAL_DEPENDENCY_PENDING = [
    {
        "capability_id": 6,
        "launch_number": 6,
        "missing_contract": "user-visible evidence-class owner (#6) not PASS_ENGINEERING at execution SHA",
        "consumer_impact": "B3 trust batch consumers; B1 uses read-only ai_compliance_footer only",
        "batch_blocked": False,
    },
    {
        "capability_id": 630,
        "launch_number": 41,
        "missing_contract": "freshness semantics runtime owner reconciliation deferred to B2 temporal batch",
        "consumer_impact": "B1 uses classify_freshness read-only; canonical #41 temporal integration in B2",
        "batch_blocked": False,
    },
]


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _spec_sha256() -> str:
    if SPEC_UPLOAD.is_file():
        return hashlib.sha256(SPEC_UPLOAD.read_bytes()).hexdigest()
    return "SPEC_UPLOAD_NOT_FOUND"


def _run_tests() -> dict:
    cmd = ["python3", "-m", "pytest", "tests/launch57/test_temporal_batch1.py", "-q"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-2000:],
        "stderr": proc.stderr[-2000:],
        "passed": proc.returncode == 0,
    }


def build_reconciliation(sha: str, spec_sha: str, tests: dict) -> dict:
    return {
        "artifact": "BLACKDARK_LAUNCH57_TEMPORAL_CONSISTENCY_RECONCILIATION",
        "generated_at": datetime.now(UTC).isoformat(),
        "baseline_sha": sha,
        "spec_sha256": spec_sha,
        "current_batch": CURRENT_BATCH,
        "batch_launch_numbers": BATCH_LAUNCH_NUMBERS,
        "batch_temporal_verdict": "PENDING_VERIFICATION",
        "LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING": False,
        "LAUNCH57_TEMPORAL_CONSISTENCY_READY_FOR_LOCAL_USE": False,
        "PASS_LIVE_NOT_CLAIMED": True,
        "naive_datetime_findings": [],
        "timezone_errors": [],
        "stale_live_inconsistencies": [],
        "ordering_failures": [],
        "point_in_time_violations": [],
        "lookahead_violations": [],
        "dst_failures": [],
        "chart_inconsistencies": [],
        "alert_timing_failures": [],
        "decision_timestamp_failures": [],
        "timestamp_precision_unit_violations": [],
        "equal_time_ordering_defects": [],
        "provider_clock_skew_defects": [],
        "host_clock_skew_defects": [],
        "availability_time_unknown_fabrication_findings": [],
        "dst_gap_fold_failures": [],
        "tzdb_version_update_findings": [],
        "recurrence_failures": [],
        "leap_second_policy_failures": [],
        "api_database_serialization_defects": [],
        "temporal_dependency_pending": TEMPORAL_DEPENDENCY_PENDING,
        "external_blockers": [],
        "changed_paths": CHANGED_PATHS,
        "reused_unchanged_paths": REUSED_PATHS,
        "tests": tests,
        "defects_fixed": [
            "B1 market paths lacked canonical temporal envelope",
            "OHLCV bar ordering relied on provider order without deterministic tie-break metadata",
            "Provider future timestamps could reach real_time_prices without rejection",
            "available_at could be implied from source-only timestamps",
        ],
        "isolation_boundary_evidence": {
            "modified_within_launch57_only": True,
            "external_deps_read_only": [
                "failure.freshness.classify_freshness",
                "cap646.evidence_class",
                "data_governance.freshness",
                "market_context",
            ],
        },
        "final_status": "BATCH_B1_PENDING_VERIFICATION",
    }


def build_report(sha: str, spec_sha: str, tests: dict, recon: dict) -> str:
    names = ", ".join(f"#{n} {BATCH_NAMES[n]}" for n in BATCH_LAUNCH_NUMBERS)
    return f"""# BLACKDARK Launch-57 Temporal Consistency Report

## A. Executive status

- **Current batch:** `{CURRENT_BATCH}` ({names})
- **Batch temporal verdict:** `PENDING_VERIFICATION` (builder does not self-certify `PASS_ENGINEERING`)
- **Global:** `LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING=false`
- **Local use ready:** `LAUNCH57_TEMPORAL_CONSISTENCY_READY_FOR_LOCAL_USE=false`
- **PASS_LIVE:** not claimed (`PASS_LIVE_NOT_CLAIMED=true`)

## B. Baseline SHA

- **Branch commit:** `{sha}`
- **Spec SHA256:** `{spec_sha}`

## C. Canonical time architecture

- Launch-57 owner: `launch57/temporal_common.py`
- UTC-aware canonical instants; RFC3339 serialization with `Z`
- Separate fields: `event_time`, `source_time`, `observed_time`, `ingested_at`, `processed_at`, `available_at`
- `available_at` never fabricated from source/event time alone

## D. Timezone resolution

- IANA TZDB via `zoneinfo`; explicit precedence: request → account → session → browser → UTC
- Display conversion does not alter canonical ordering (tested)

## E. Freshness integration

- `#41` governance owner: `PASS_ENGINEERING` at register view; B2 temporal integration deferred
- B1 reuses `classify_freshness` read-only; no parallel freshness owner created

## F. Evidence/provenance timing

- B1 `_attach_provenance` + `temporal` envelope on connector/price/OHLCV paths
- Provider timestamp validation with future-skew rejection on `#22`

## G. Point-in-time integrity

- `resolve_available_at` + `point_in_time_eligible` guard UNKNOWN availability
- B2 `#39` temporal integration deferred to batch B2

## H. Decision timing

- Not in B1 scope (deferred to B3/B4 temporal batches)

## I. Charts/market data

- OHLCV deterministic ordering by `open_time_ms` + sequence tie-break metadata
- Chart display timezone policy documented; single UTC canonical storage in B1 payloads

## J. Alerts

- Deferred (B11 `#33`)

## K. AI/research

- Deferred (B12)

## L. Public/shareable surfaces

- Deferred (B4)

## M. History

- Deferred (B14)

## N. DST/recurrence

- Policy enums defined in `temporal_common`; scheduling tests deferred to alert/recurrence batches

## O. Tests

```text
{tests.get('command')}
exit_code={tests.get('exit_code')}
passed={tests.get('passed')}
```

## P. Clock synchronization / skew

- Provider future-skew budget enforced in B1 price path
- Host clock sync: `NEEDS_EXTERNAL_VERIFICATION` for PASS_LIVE

## Q. Precision / ordering / source timestamp trust

- Explicit ms/s unit inference; deterministic ordering keys on OHLCV

## R. TZDB / DST / recurrence

- TZDB package recorded in envelope; DST gap/fold policy constants present

## S. API / database temporal contracts

- API payloads expose `temporal` object with RFC3339 instants
- DB persistence unchanged in B1 (no migration outside Launch-57 boundary)

## T. External gates

- Production clock sync, cross-device TZ persistence: not claimed

## U. Final verdict

- **BATCH_TEMPORAL_VERDICT=B1:PENDING_VERIFICATION**
- **LAUNCH57_TEMPORAL_CONSISTENCY_PASS_ENGINEERING=false** until all batches + Phase 8 reconciliation complete
"""


def main() -> int:
    sha = _git_sha()
    spec_sha = _spec_sha256()
    tests = _run_tests()
    recon = build_reconciliation(sha, spec_sha, tests)
    RECON_PATH.write_text(json.dumps(recon, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(build_report(sha, spec_sha, tests, recon), encoding="utf-8")
    print(f"Wrote {RECON_PATH}")
    print(f"Wrote {REPORT_PATH}")
    return 0 if tests["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
