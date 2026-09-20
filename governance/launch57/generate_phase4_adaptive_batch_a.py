#!/usr/bin/env python3
"""Launch-57 Phase 4 Adaptive Batch A builder evidence generator (#20→#16→#17→#13→#14)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE4_ADAPTIVE_BATCH_A_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE4_ADAPTIVE_BATCH_A_REPORT.md"
BUILD_ORDER = [20, 16, 17, 13, 14]
ENTRY_GATE_SHA = "c58c58a4"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase4_adaptive_batch_a.py",
            "tests/launch57/test_smart_money_batch1.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase4_adaptive_batch_a.py "
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

    items = {
        20: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + attribution/cohort distinct from raw movement",
            "proven_adaptive_gap": "Address labels missing attribution_cohort_disclosure with coverage/uncertainty limits",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch1:address_labels_cohorts",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        16: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + exchange flow distinct from generic movement",
            "proven_adaptive_gap": "Exchange flow outputs missing exchange_flow_disclosure with qualified attribution/coverage",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch1:exchange_flow_intelligence + exchange_flow_netflow_layer",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        17: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + whale ratio with internal-flow filter preserved",
            "proven_adaptive_gap": "Whale ratio and internal-flow filter missing adaptive disclosures guarding misclassification",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch1:exchange_whale_ratio + internal_flow_filter",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        13: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + accumulation/distribution as inference with visible uncertainty",
            "proven_adaptive_gap": "Accumulation detection missing inference/uncertainty disclosure",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch1:accumulation_distribution_detection",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        14: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + screener from approved Launch-57 smart-money evidence",
            "proven_adaptive_gap": "Token screener missing approved-evidence screening disclosure",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch1:smart_money_token_screener",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
    }

    evidence = {
        "artifact": "PHASE4_ADAPTIVE_BATCH_A_EVIDENCE",
        "phase": "4_ADAPTIVE_BATCH_A",
        "build_order": BUILD_ORDER,
        "entry_gate": {
            "PHASE3_INTEGRATION": "PASS",
            "PHASE4_MAY_BEGIN": True,
            "verified_at_sha": ENTRY_GATE_SHA,
        },
        "starting_head_sha": ENTRY_GATE_SHA,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "builder_status_max": "PENDING_VERIFICATION",
        "items": items,
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/smart_money_batch1.py",
        ],
        "support_files_changed": ["launch57/trust_adaptive_common.py"],
        "tests": tests,
        "confirmations": {
            "PHASE4_BATCH_A_IMPLEMENTATION_STATUS": "PENDING_VERIFICATION",
            "PHASE4_BATCH_B_NOT_STARTED": True,
            "TEMPORAL_WORKSTREAM_REOPENED": False,
            "PASS_ENGINEERING_NOT_CLAIMED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 4 Adaptive Batch A — Builder Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Entry gate: PHASE3_INTEGRATION = PASS @ `{ENTRY_GATE_SHA}`",
        f"Build order: `{BUILD_ORDER}`",
        "",
        "## Per-capability",
        "",
    ]
    for lid in BUILD_ORDER:
        item = items[lid]
        lines.append(f"### #{lid}")
        for key, value in item.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    lines.extend(
        [
            "## Tests",
            f"- command: `{tests['command']}`",
            f"- exit_code: {tests['exit_code']}",
            f"- stdout: {tests['stdout']}",
            "",
            "## Confirmations",
            "```text",
            "PHASE4_BATCH_A_IMPLEMENTATION_STATUS = PENDING_VERIFICATION",
            "PHASE4_BATCH_B_NOT_STARTED = true",
            "TEMPORAL_WORKSTREAM_REOPENED = false",
            "PASS_ENGINEERING_NOT_CLAIMED = true",
            "PASS_LIVE_NOT_CLAIMED = true",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Phase 4 Adaptive Batch A evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
