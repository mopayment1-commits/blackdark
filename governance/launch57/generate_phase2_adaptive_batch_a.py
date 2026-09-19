#!/usr/bin/env python3
"""Launch-57 Phase 2 Adaptive Batch A builder evidence generator (#6→#5→#4→#3→#2)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE2_ADAPTIVE_BATCH_A_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE2_ADAPTIVE_BATCH_A_REPORT.md"
BUILD_ORDER = [6, 5, 4, 3, 2]


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase2_adaptive_batch_a.py",
            "tests/launch57/test_trust_batch1.py",
            "tests/launch57/test_capability_6_governance_reconciliation.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase2_adaptive_batch_a.py "
            "tests/launch57/test_trust_batch1.py "
            "tests/launch57/test_capability_6_governance_reconciliation.py -q"
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
        6: {
            "governing_requirement": "Adaptive Spec §9 evidence class LIVE/DELAYED/SIM",
            "proven_adaptive_gap": "NONE",
            "execution_disposition": "NO_PRODUCT_CHANGE",
            "canonical_path_reused": "launch57.evidence_class_common",
            "shared_support_path": None,
            "builder_state": "NO_PRODUCT_CHANGE",
        },
        5: {
            "governing_requirement": "Adaptive Spec §8 net-edge cost treatment + §28 Level 1 safety floor",
            "proven_adaptive_gap": "Missing explicit gross-vs-net safety floor on net-edge consumer output",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.trust_batch1:net_edge_truth_score",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        4: {
            "governing_requirement": "Adaptive Spec §7 live-only ledger interpretation context",
            "proven_adaptive_gap": "Missing ledger interpretation context to prevent misleading public accuracy reading",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.trust_batch1:public_accuracy_ledger",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        3: {
            "governing_requirement": "Adaptive Spec §6 certificate drivers/contradictions/limitations + §28 Level 1",
            "proven_adaptive_gap": "Certificate missing structured key_drivers/contradictions/limitations and Level-1 disclosure",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.trust_batch1:decision_certificate_export",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        2: {
            "governing_requirement": "Adaptive Spec §5 oracle backing + §28 Level 1 safety floor",
            "proven_adaptive_gap": "Oracle output missing explicit contradiction/limitation/abstention/deeper-evidence Level-1 fields",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.trust_batch1:single_sentence_oracle",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
    }

    evidence = {
        "artifact": "PHASE2_ADAPTIVE_BATCH_A_EVIDENCE",
        "phase": "2_ADAPTIVE_BATCH_A",
        "build_order": BUILD_ORDER,
        "starting_head_sha": None,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "builder_status_max": "PENDING_VERIFICATION",
        "items": items,
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/trust_batch1.py",
            "launch57/decision_timing_common.py",
            "launch57/b5_public_accuracy_bridge.py",
        ],
        "support_files_changed": ["launch57/trust_adaptive_common.py"],
        "tests": tests,
        "confirmations": {
            "PHASE2_BATCH_B_NOT_STARTED": True,
            "TEMPORAL_WORKSTREAM_REOPENED": False,
            "PASS_ENGINEERING_NOT_CLAIMED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 2 Adaptive Batch A — Builder Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
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
            "PHASE2_BATCH_B_NOT_STARTED = true",
            "TEMPORAL_WORKSTREAM_REOPENED = false",
            "PASS_ENGINEERING_NOT_CLAIMED = true",
            "PASS_LIVE_NOT_CLAIMED = true",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Phase 2 Adaptive Batch A evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
