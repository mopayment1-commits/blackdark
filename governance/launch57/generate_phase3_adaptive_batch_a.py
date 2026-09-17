#!/usr/bin/env python3
"""Launch-57 Phase 3 Adaptive Batch A builder evidence generator (#7→#8→#9→#10→#11)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE3_ADAPTIVE_BATCH_A_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE3_ADAPTIVE_BATCH_A_REPORT.md"
BUILD_ORDER = [7, 8, 9, 10, 11]
ENTRY_GATE_SHA = "b57efc37"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase3_adaptive_batch_a.py",
            "tests/launch57/test_decision_batch1.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase3_adaptive_batch_a.py "
            "tests/launch57/test_decision_batch1.py -q"
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
        7: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + market-context semantics (no trade instruction)",
            "proven_adaptive_gap": "Missing explicit market_context_disclosure framing context-only output",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.decision_batch1:market_regime_compass",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        8: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + simplification without hiding material risk",
            "proven_adaptive_gap": "Beginner mode missing beginner_simplification_disclosure with visible material risk",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.decision_batch1:beginner_decision_mode",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        9: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + dependence-aware confirmation",
            "proven_adaptive_gap": "Cross-signal confirmation treated duplicated evidence as independent",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.decision_batch1:cross_signal_confirmation",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        10: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + explicit material contradiction impact",
            "proven_adaptive_gap": "Contradiction list missing material_contradiction_impact and Level-1 wiring",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.decision_batch1:contradiction_detection",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
        11: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + actionability without unsupported precision",
            "proven_adaptive_gap": "Actionability score exposed without qualitative band / precision guard",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.decision_batch1:smart_money_actionability_score",
            "shared_support_path": "launch57.trust_adaptive_common",
            "builder_state": "PENDING_VERIFICATION",
        },
    }

    evidence = {
        "artifact": "PHASE3_ADAPTIVE_BATCH_A_EVIDENCE",
        "phase": "3_ADAPTIVE_BATCH_A",
        "build_order": BUILD_ORDER,
        "entry_gate": {
            "PHASE2_CROSS_BATCH_INTEGRATION": "PASS",
            "NEXT_PHASE_ALLOWED": "PHASE3",
            "verified_at_sha": ENTRY_GATE_SHA,
        },
        "starting_head_sha": ENTRY_GATE_SHA,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "builder_status_max": "PENDING_VERIFICATION",
        "items": items,
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/decision_batch1.py",
        ],
        "support_files_changed": ["launch57/trust_adaptive_common.py"],
        "tests": tests,
        "confirmations": {
            "PHASE3_BATCH_A_IMPLEMENTATION_STATUS": "PENDING_VERIFICATION",
            "PHASE3_BATCH_B_NOT_STARTED": True,
            "TEMPORAL_WORKSTREAM_REOPENED": False,
            "PASS_ENGINEERING_NOT_CLAIMED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 3 Adaptive Batch A — Builder Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Entry gate: PHASE2_CROSS_BATCH_INTEGRATION = PASS @ `{ENTRY_GATE_SHA}`",
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
            "PHASE3_BATCH_A_IMPLEMENTATION_STATUS = PENDING_VERIFICATION",
            "PHASE3_BATCH_B_NOT_STARTED = true",
            "TEMPORAL_WORKSTREAM_REOPENED = false",
            "PASS_ENGINEERING_NOT_CLAIMED = true",
            "PASS_LIVE_NOT_CLAIMED = true",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Phase 3 Adaptive Batch A evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
