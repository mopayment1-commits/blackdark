#!/usr/bin/env python3
"""Launch-57 Phase 7 Adaptive Batch B builder evidence generator (#1)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE7_ADAPTIVE_BATCH_B_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE7_ADAPTIVE_BATCH_B_REPORT.md"
BUILD_ORDER = [1]
ENTRY_GATE_SHA = "292d876c"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase7_adaptive_batch_b.py",
            "tests/launch57/test_edge_ui_batch2.py",
            "tests/test_decision_truth_p5_product_experience.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase7_adaptive_batch_b.py "
            "tests/launch57/test_edge_ui_batch2.py "
            "tests/test_decision_truth_p5_product_experience.py -q"
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
        1: {
            "governing_requirement": (
                "Adaptive Spec §23/§24/§28 — command home exposes only Launch-57 readiness-allowed "
                "capabilities; preserves trust/readiness; Six Heroes primary surfaces"
            ),
            "proven_adaptive_gap": (
                "Home eligible list lacked runtime guard rejecting PARKED/not-ready injection and "
                "metadata override; no adaptive disclosure on material home decisions"
            ),
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "entry_gate": "PHASE7_BATCH_A_INDEPENDENT_VERDICT = PASS_ENGINEERING @ 292d876c",
            "canonical_path_reused": (
                "launch57.edge_ui_batch2:six_heroes_command_home + "
                "decision_truth.product.six_heroes + launch57_home_eligible_ids"
            ),
            "shared_support_path": "launch57.trust_adaptive_common:apply_command_home_guard",
            "builder_state": "PENDING_VERIFICATION",
        },
    }

    evidence = {
        "artifact": "PHASE7_ADAPTIVE_BATCH_B_EVIDENCE",
        "phase": "7_ADAPTIVE_BATCH_B",
        "build_order": BUILD_ORDER,
        "entry_gate": {
            "PHASE7_BATCH_A_INDEPENDENT_VERDICT": "PASS_ENGINEERING",
            "PHASE7_BATCH_B_MAY_BEGIN": True,
            "verified_at_sha": ENTRY_GATE_SHA,
        },
        "starting_head_sha": ENTRY_GATE_SHA,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "builder_status_max": "PENDING_VERIFICATION",
        "items": items,
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/edge_ui_batch2.py",
        ],
        "support_files_changed": ["launch57/trust_adaptive_common.py"],
        "tests": tests,
        "confirmations": {
            "PHASE7_BATCH_B_IMPLEMENTATION_STATUS": "PENDING_VERIFICATION",
            "PHASE8_NOT_STARTED": True,
            "PASS_ENGINEERING_NOT_CLAIMED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 7 Adaptive Batch B — Builder Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Entry gate: PHASE7_BATCH_A_INDEPENDENT_VERDICT = PASS_ENGINEERING @ `{ENTRY_GATE_SHA}`",
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
            "PHASE7_BATCH_B_IMPLEMENTATION_STATUS = PENDING_VERIFICATION",
            "PHASE8_NOT_STARTED = true",
            "PASS_ENGINEERING_NOT_CLAIMED = true",
            "PASS_LIVE_NOT_CLAIMED = true",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Phase 7 Adaptive Batch B evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
