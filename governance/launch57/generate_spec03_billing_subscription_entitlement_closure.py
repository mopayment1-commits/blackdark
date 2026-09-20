#!/usr/bin/env python3
"""Generate SPEC_03 Billing Subscription Entitlement closure artifacts."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "governance" / "launch57" / "SPEC_03_BILLING_SUBSCRIPTION_ENTITLEMENT"


def _md_truth_table(rows: list[dict]) -> str:
    lines = [
        "# SPEC_03 Runtime Truth Table",
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
    return f"""# SPEC_03 Local Closure Report

## Verdict

- **closure_status**: `{status.get('closure_status')}`
- **PASS_ENGINEERING**: {status.get('PASS_ENGINEERING')}
- **LOCAL_INSTITUTIONAL_CLOSURE**: {status.get('LOCAL_INSTITUTIONAL_CLOSURE')}
- **LOCAL_WORK_REMAINING**: {status.get('LOCAL_WORK_REMAINING')}
- **PASS_LIVE**: {status.get('PASS_LIVE')} (must remain false)
- **LIVE_VALIDATION_PENDING**: {status.get('LIVE_VALIDATION_PENDING')}

## Domain

Billing, Subscription & Entitlement — Launch-57 FILE 03 only.

## Builder

- SHA: `{status.get('final_sha')}`
- Builder status: `{status.get('BUILDER_STATUS')}`
- Runtime truth YES: {status.get('runtime_truth_yes_count')}/{status.get('runtime_truth_total')}
- `entitlement_matrix_ok`: {status.get('entitlement_matrix_ok')}

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

> `BILLING_STATE != ENTITLEMENT_STATE` — no Webhook→User Tier shortcut (§3)

> Paid entitlement requires verified payment evidence; invalid: redirect, query param, unsigned webhook (§5)

> All tier/capability access must be server-side enforced (§27)

> `ENTITLEMENT_CAPABILITY_SCOPE = LAUNCH57_IDS` — no PARKED capability sellable (§28)

## Mandatory stop

SPEC_03 FILE 03 only — do not proceed to files 04–13 without owner review.
"""


def main() -> None:
    from launch57.billing_subscription_entitlement_common import (
        SPEC03_VERSION,
        build_final_status,
        build_requirements_register,
        build_runtime_truth_table,
        independent_verification,
        run_targeted_tests,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()

    requirements = {
        "artifact": "SPEC_03_REQUIREMENTS_REGISTER",
        "domain": "SPEC_03_BILLING_SUBSCRIPTION_ENTITLEMENT",
        "generated_at": now,
        "spec_version": SPEC03_VERSION,
        "requirement_count": len(build_requirements_register()),
        "requirements": build_requirements_register(),
    }

    truth = build_runtime_truth_table()
    tests = run_targeted_tests()
    iv = independent_verification()
    status = build_final_status(tests=tests)

    (OUT / "REQUIREMENTS_REGISTER.json").write_text(
        json.dumps(requirements, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUT / "RUNTIME_TRUTH_TABLE.md").write_text(_md_truth_table(truth), encoding="utf-8")
    (OUT / "LOCAL_CLOSURE_REPORT.md").write_text(_md_local_closure(status, iv, tests), encoding="utf-8")
    (OUT / "INDEPENDENT_VERIFICATION.json").write_text(
        json.dumps({**iv, "generated_at": now}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    status["tests"] = tests
    status["generated_at"] = now
    (OUT / "FINAL_STATUS.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

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
