#!/usr/bin/env python3
"""Generate SPEC_12 Identity Auth Profile closure artifacts."""

from __future__ import annotations

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.launch57.gov_io import write_artifact_json, write_artifact_lines

OUT = ROOT / "governance" / "launch57" / "SPEC_12_IDENTITY_AUTH_PROFILE"


def _md_truth_table(rows: list[dict]) -> str:
    lines = [
        "# SPEC_12 Runtime Truth Table",
        "",
        "| Req ID | Section | Status | Evidence |",
        "|--------|---------|--------|----------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['req_id']} | {row['spec_section']} | **{row['status']}** | {row['evidence']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    from launch57.identity_auth_profile_spec_common import (
        SPEC12_VERSION,
        TruthStatus,
        build_final_status,
        build_requirements_register,
        build_runtime_truth_table,
        independent_verification,
        run_targeted_tests,
    )

    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC).isoformat()

    requirements = {
        "artifact": "SPEC_12_REQUIREMENTS_REGISTER",
        "domain": "SPEC_12_IDENTITY_AUTH_PROFILE",
        "generated_at": now,
        "spec_version": SPEC12_VERSION,
        "requirement_count": len(build_requirements_register()),
        "requirements": build_requirements_register(),
    }

    truth = build_runtime_truth_table()
    runtime_yes_count = sum(1 for row in truth if row["status"] == TruthStatus.YES.value)
    runtime_truth_total = len(truth)

    write_artifact_json((OUT / "REQUIREMENTS_REGISTER.json"), requirements)
    write_artifact_lines((OUT / "RUNTIME_TRUTH_TABLE.md"), _md_truth_table(truth).splitlines())

    tests = run_targeted_tests()
    iv_internal = independent_verification()
    status_internal = build_final_status(tests=tests)
    if not iv_internal["INDEPENDENT_VERIFICATION_PASS"]:
        print("SPEC_12 independent verification failed (in-process)")
        sys.exit(1)
    if status_internal["closure_status"] != "CLOSED_LOCAL":
        print("SPEC_12 closure_status not CLOSED_LOCAL (in-process)")
        sys.exit(1)

    subprocess.run(
        [sys.executable, "-m", "governance.launch57.emit_spec12_public_artifacts"],
        cwd=ROOT,
        check=True,
    )

    print(
        "Wrote",
        OUT / "REQUIREMENTS_REGISTER.json",
        OUT / "RUNTIME_TRUTH_TABLE.md",
        OUT / "LOCAL_CLOSURE_REPORT.md",
        OUT / "INDEPENDENT_VERIFICATION.json",
        OUT / "FINAL_STATUS.json",
    )
    print("closure_status= CLOSED_LOCAL")


if __name__ == "__main__":
    main()
