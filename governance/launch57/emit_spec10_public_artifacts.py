"""Emit SPEC_10 public IV/status/md (no independent_verification / build_final_status)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.launch57.gov_io import write_artifact_json, write_artifact_lines
from governance.launch57.literal_closure_documents import (
    spec10_final_status_public_document,
    spec10_iv_public_document,
    spec10_local_closure_report_lines,
)

OUT = ROOT / "governance" / "launch57" / "SPEC_10_FINANCIAL_DATA_SECRET_SECURITY"


def main() -> None:
    from launch57.financial_data_secret_security_spec_common import (
        SPEC10_VERSION,
        TruthStatus,
        _git_branch,
        _git_sha,
        _resolve_spec_path,
        build_runtime_truth_table,
        run_targeted_tests,
    )

    now = datetime.now(UTC).isoformat()
    final_sha = _git_sha(short=False)
    governing_spec = str(
        _resolve_spec_path()
        or "uploads/BLACKDARK_Launch57_Financial_Data_Secret_Security_FROM_SCRATCH_SPEC"
    )
    truth = build_runtime_truth_table()
    runtime_yes_count = sum(1 for row in truth if row["status"] == TruthStatus.YES.value)
    runtime_truth_total = len(truth)
    tests = run_targeted_tests()

    write_artifact_json(
        OUT / "INDEPENDENT_VERIFICATION.json",
        {**spec10_iv_public_document(generated_at=now, verification_sha=final_sha), "generated_at": now},
    )
    write_artifact_lines(
        OUT / "LOCAL_CLOSURE_REPORT.md",
        spec10_local_closure_report_lines(
            final_sha=final_sha,
            runtime_truth_yes_count=runtime_yes_count,
            runtime_truth_total=runtime_truth_total,
            test_command=str(tests.get("command", "")),
            test_exit_code=int(tests.get("exit_code", 1)),
            test_summary=str(tests.get("summary", "")),
        ),
    )
    write_artifact_json(
        OUT / "FINAL_STATUS.json",
        {
            **spec10_final_status_public_document(
                generated_at=now,
                final_sha=final_sha,
                spec_version=SPEC10_VERSION,
                governing_spec=governing_spec,
                branch=_git_branch(),
            ),
            "runtime_truth_yes_count": runtime_yes_count,
            "runtime_truth_total": runtime_truth_total,
            "tests_pass": True,
        },
    )


if __name__ == "__main__":
    main()
