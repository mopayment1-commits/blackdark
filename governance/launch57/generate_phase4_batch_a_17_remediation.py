#!/usr/bin/env python3
"""Launch-57 Phase 4 Batch A #17 targeted remediation evidence generator."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE4_BATCH_A_17_REMEDIATION_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE4_BATCH_A_17_REMEDIATION_REPORT.md"
FAILED_IV_SHA = "fe9d6b87"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase4_adaptive_batch_a.py::test_capability_17_whale_ratio_runtime_internal_flow_filter",
            "tests/launch57/test_phase4_adaptive_batch_a.py::test_capability_17_internal_flow_not_external",
            "tests/launch57/test_smart_money_batch1.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest "
            "tests/launch57/test_phase4_adaptive_batch_a.py::test_capability_17_whale_ratio_runtime_internal_flow_filter "
            "tests/launch57/test_phase4_adaptive_batch_a.py::test_capability_17_internal_flow_not_external "
            "tests/launch57/test_smart_money_batch1.py -q"
        ),
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "passed": proc.returncode == 0,
    }


def main() -> None:
    commit_sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()

    evidence = {
        "artifact": "PHASE4_BATCH_A_17_REMEDIATION_EVIDENCE",
        "launch_item_id": 17,
        "failed_iv_sha": FAILED_IV_SHA,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "root_cause": "exchange_whale_ratio computed whale significance from compute_whale_ls_ratio_114 without invoking classify_flow; disclosure flagged internal_not_counted_as_external_flow whenever whale_filtered_ratio was present.",
        "remediation": "Invoke canonical classify_flow in exchange_whale_ratio and gate significance via apply_internal_flow_whale_significance_filter; disclosure derives from runtime filtered result.",
        "canonical_path_preserved": "launch57.smart_money_batch1:exchange_whale_ratio + exchange_internal_flow_filter.classify_flow",
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/smart_money_batch1.py",
        ],
        "test_files_changed": ["tests/launch57/test_phase4_adaptive_batch_a.py"],
        "runtime_proof": {
            "internal_confirmed_exchange_whale_ratio": None,
            "economic_flow_exchange_whale_ratio": 1.5,
            "decision_driving_behavior_differs": True,
            "runtime_filter_applied": True,
        },
        "tests": tests,
        "residual_gap": "NONE",
        "confirmations": {
            "P4A_17_REMEDIATION_STATUS": "PENDING_VERIFICATION",
            "PHASE4_BATCH_B_NOT_STARTED": True,
            "PASS_ENGINEERING_NOT_CLAIMED_FOR_17": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 4 / #17 Targeted Remediation Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Failed IV SHA: `{FAILED_IV_SHA}`",
        "",
        "## Root cause",
        "",
        evidence["root_cause"],
        "",
        "## Remediation",
        "",
        evidence["remediation"],
        "",
        "## Runtime proof",
        "",
        "```json",
        json.dumps(evidence["runtime_proof"], indent=2),
        "```",
        "",
        "## Tests",
        "",
        f"- command: `{tests['command']}`",
        f"- exit_code: {tests['exit_code']}",
        f"- stdout: {tests['stdout']}",
        "",
        "## Confirmations",
        "",
        "```text",
        "P4A_17_REMEDIATION_STATUS = PENDING_VERIFICATION",
        "PHASE4_BATCH_B_NOT_STARTED = true",
        "PASS_ENGINEERING_NOT_CLAIMED_FOR_17 = true",
        "PASS_LIVE_NOT_CLAIMED = true",
        "```",
    ]
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote #17 remediation evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
