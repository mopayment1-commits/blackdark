#!/usr/bin/env python3
"""Generate SPEC_06 Compounding Evidence Track Record closure artifacts."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.launch57.gov_io import write_artifact_json, write_artifact_lines

OUT = ROOT / "governance" / "launch57" / "SPEC_06_COMPOUNDING_EVIDENCE_TRACK_RECORD"


def _md_truth_table(rows: list[dict]) -> str:
    lines = [
        "# SPEC_06 Runtime Truth Table",
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
    return f"""# SPEC_06 Local Closure Report

## Verdict

- **closure_status**: `{status.get('closure_status')}`
- **PASS_ENGINEERING**: {status.get('PASS_ENGINEERING')}
- **LOCAL_INSTITUTIONAL_CLOSURE**: {status.get('LOCAL_INSTITUTIONAL_CLOSURE')}
- **LOCAL_WORK_REMAINING**: {status.get('LOCAL_WORK_REMAINING')}
- **PASS_LIVE**: {status.get('PASS_LIVE')} (must remain false)
- **LIVE_VALIDATION_PENDING**: {status.get('LIVE_VALIDATION_PENDING')}

## Domain

Compounding Evidence Track Record — Launch-57 FILE 06 only.

## Builder

- SHA: `{status.get('final_sha')}`
- Builder status: `{status.get('BUILDER_STATUS')}`
- Runtime truth YES: {status.get('runtime_truth_yes_count')}/{status.get('runtime_truth_total')}
- `evidence_class_integrity_ok`: {status.get('evidence_class_integrity_ok')}
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

> LIVE / DELAYED / SIM separation — SIM cannot contaminate live accuracy (§8–§9)

> Outcome resolution required before accuracy claims (§7)

> Append-only tamper-evident track record via oracle audit chain (§8)

> Public accuracy #4 live-origin only; FILE 02 public vs FILE 03 entitlement (§8, §15)

## Mandatory stop

SPEC_06 FILE 06 only — do not proceed to files 07–13 without owner review.
"""


def main() -> None:
    from launch57.compounding_evidence_track_record_spec_common import (
        SPEC06_VERSION,
        build_final_status,
        build_requirements_register,
        build_runtime_truth_table,
        independent_verification,
        run_targeted_tests,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()

    requirements = {
        "artifact": "SPEC_06_REQUIREMENTS_REGISTER",
        "domain": "SPEC_06_COMPOUNDING_EVIDENCE_TRACK_RECORD",
        "generated_at": now,
        "spec_version": SPEC06_VERSION,
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
