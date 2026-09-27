#!/usr/bin/env python3
"""Generate SPEC_11 Global Time Temporal Consistency closure artifacts."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.launch57.gov_io import write_artifact_json, write_artifact_lines

OUT = ROOT / "governance" / "launch57" / "SPEC_11_GLOBAL_TIME_TEMPORAL_CONSISTENCY"


def _md_truth_table(rows: list[dict]) -> str:
    lines = [
        "# SPEC_11 Runtime Truth Table",
        "",
        "| Req ID | Section | Status | Evidence |",
        "|--------|---------|--------|----------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['req_id']} | {row['spec_section']} | **{row['status']}** | {row['evidence']} |"
        )
    return "\n".join(lines) + "\n"


def _md_local_closure(status: dict, iv: dict, tests: dict) -> str:
    gaps = status.get("LOCAL_ENGINEERING_GAPS") or []
    gap_lines = "\n".join(
        f"- **{g.get('priority')}** `{g.get('req_id')}` — {g.get('title')}: {g.get('evidence')}"
        for g in gaps
    )
    if not gap_lines:
        gap_lines = "- None"
    return f"""# SPEC_11 Local Closure Report

## Verdict

- **closure_status**: `{status.get('closure_status')}`
- **PASS_ENGINEERING**: {status.get('PASS_ENGINEERING')}
- **LOCAL_INSTITUTIONAL_CLOSURE**: {status.get('LOCAL_INSTITUTIONAL_CLOSURE')}
- **LOCAL_WORK_REMAINING**: {status.get('LOCAL_WORK_REMAINING')}
- **PASS_LIVE**: {status.get('PASS_LIVE')} (must remain false)
- **LIVE_VALIDATION_PENDING**: {status.get('LIVE_VALIDATION_PENDING')}

## Domain

Global Time Temporal Consistency — Launch-57 FILE 11 only.

## Builder

- SHA: `{status.get('final_sha')}`
- Builder status: `{status.get('BUILDER_STATUS')}`
- Runtime truth YES: {status.get('runtime_truth_yes_count')}/{status.get('runtime_truth_total')}
- `temporal_canonical_ok`: {status.get('temporal_canonical_ok')}
- `launch57_only_ok`: {status.get('launch57_only_ok')}

## Independent Verification

- IV status: `{status.get('IV_STATUS')}`
- Probes passed: {iv.get('passed_count')}/{iv.get('probe_count')}
- `INDEPENDENT_VERIFICATION_PASS`: {iv.get('INDEPENDENT_VERIFICATION_PASS')}

## Tests

```
{tests.get('command')}
exit_code={tests.get('exit_code')}
{tests.get('summary')}
```

## Local engineering gaps

{gap_lines}

## Live blockers only (external)

{chr(10).join('- ' + b for b in status.get('live_blockers_only', []))}

## Spec quotes (governing themes)

> UTC = canonical event/storage instant; display TZ is presentation only (§2)

> available_at <= decision_time for point-in-time-known evidence (§4)

> Expired/stale must not present as current on #5/#33/#44-class surfaces (§15–§19)

> B1–B15 temporal batches reconciled; no false global PASS_LIVE (§42)

## Mandatory stop

SPEC_11 FILE 11 only — do not proceed to files 12–13 without owner review.
"""


def main() -> None:
    from launch57.global_time_temporal_consistency_spec_common import (
        SPEC11_VERSION,
        build_final_status,
        build_requirements_register,
        build_runtime_truth_table,
        independent_verification,
        run_targeted_tests,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()

    requirements = {
        "artifact": "SPEC_11_REQUIREMENTS_REGISTER",
        "domain": "SPEC_11_GLOBAL_TIME_TEMPORAL_CONSISTENCY",
        "generated_at": now,
        "spec_version": SPEC11_VERSION,
        "requirement_count": len(build_requirements_register()),
        "requirements": build_requirements_register(),
    }

    truth = build_runtime_truth_table()
    iv = independent_verification()

    write_artifact_json((OUT / "REQUIREMENTS_REGISTER.json"), requirements)
    write_artifact_lines((OUT / "RUNTIME_TRUTH_TABLE.md"), _md_truth_table(truth).splitlines())
    write_artifact_json((OUT / "INDEPENDENT_VERIFICATION.json"), {**iv, "generated_at": now})

    tests = run_targeted_tests()
    status = build_final_status(tests=tests)
    write_artifact_lines((OUT / "LOCAL_CLOSURE_REPORT.md"), _md_local_closure(status, iv, tests).splitlines())
    status["tests"] = tests
    status["generated_at"] = now
    write_artifact_json((OUT / "FINAL_STATUS.json"), status)

    print(
        "Wrote",
        OUT / "REQUIREMENTS_REGISTER.json",
        OUT / "RUNTIME_TRUTH_TABLE.md",
        OUT / "LOCAL_CLOSURE_REPORT.md",
        OUT / "INDEPENDENT_VERIFICATION.json",
        OUT / "FINAL_STATUS.json",
    )
    print("closure_status=", status.get("closure_status"))
    if status.get("closure_status") != "CLOSED_LOCAL":
        sys.exit(1)


if __name__ == "__main__":
    main()
