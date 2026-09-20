#!/usr/bin/env python3
"""Launch-57 Phase 2 Adaptive Batch B builder evidence generator (#47→#48→#44→#45→#46)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE2_ADAPTIVE_BATCH_B_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE2_ADAPTIVE_BATCH_B_REPORT.md"
BUILD_ORDER = [47, 48, 44, 45, 46]
ENTRY_GATE_SHA = "5f483351"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase2_adaptive_batch_b.py",
            "tests/launch57/test_trust_batch2.py",
            "tests/launch57/test_temporal_batch10.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase2_adaptive_batch_b.py "
            "tests/launch57/test_trust_batch2.py "
            "tests/launch57/test_temporal_batch10.py -q"
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
        47: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + direct material risk access",
            "proven_adaptive_gap": "Missing direct material_risk access on one-click risk disclosure output",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.trust_batch2:one_click_risk_disclosure",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        48: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + first-class abstain/reject disclosure",
            "proven_adaptive_gap": "Missing explicit abstention_reject_disclosure and Level-1 adaptive wiring",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.trust_batch2:abstain_reject_reasons_visible",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        44: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + shareable truth evidence/timestamp/material risk",
            "proven_adaptive_gap": "Shareable card missing shareable_truth_context and unsupported LIVE claim guard",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.trust_batch2:shareable_decision_card",
            "shared_support_path": "launch57.trust_adaptive_common + launch57.evidence_class_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        45: {
            "governing_requirement": "Adaptive Spec §7 live-only ledger interpretation (consistent with #4)",
            "proven_adaptive_gap": "Shareable accuracy page missing ledger_interpretation_context and Level-1 disclosure",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.trust_batch2:shareable_accuracy_page",
            "shared_support_path": "launch57.trust_adaptive_common + launch57.public_accuracy_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        46: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + approved Launch-57 public trust surfaces only",
            "proven_adaptive_gap": "Guest trust surface missing approved_public_trust_surfaces inventory",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.trust_batch2:guest_trust_surface",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
    }

    evidence = {
        "artifact": "PHASE2_ADAPTIVE_BATCH_B_EVIDENCE",
        "phase": "2_ADAPTIVE_BATCH_B",
        "build_order": BUILD_ORDER,
        "entry_gate": {
            "PHASE2_BATCH_A_INDEPENDENT_VERDICT": "PASS_ENGINEERING",
            "verified_at_sha": ENTRY_GATE_SHA,
        },
        "starting_head_sha": ENTRY_GATE_SHA,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "builder_status_max": "PENDING_VERIFICATION",
        "items": items,
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/trust_batch2.py",
        ],
        "support_files_changed": ["launch57/trust_adaptive_common.py"],
        "tests": tests,
        "confirmations": {
            "PHASE2_BATCH_B_IMPLEMENTATION_STATUS": "PENDING_VERIFICATION",
            "PHASE3_NOT_STARTED": True,
            "TEMPORAL_WORKSTREAM_REOPENED": False,
            "PASS_ENGINEERING_NOT_CLAIMED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 2 Adaptive Batch B — Builder Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Entry gate: PHASE2_BATCH_A_INDEPENDENT_VERDICT = PASS_ENGINEERING @ `{ENTRY_GATE_SHA}`",
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
            "PHASE2_BATCH_B_IMPLEMENTATION_STATUS = PENDING_VERIFICATION",
            "PHASE3_NOT_STARTED = true",
            "TEMPORAL_WORKSTREAM_REOPENED = false",
            "PASS_ENGINEERING_NOT_CLAIMED = true",
            "PASS_LIVE_NOT_CLAIMED = true",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Phase 2 Adaptive Batch B evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
