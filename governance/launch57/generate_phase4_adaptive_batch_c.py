#!/usr/bin/env python3
"""Launch-57 Phase 4 Adaptive Batch C builder evidence generator (#55→#56→#57)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE4_ADAPTIVE_BATCH_C_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE4_ADAPTIVE_BATCH_C_REPORT.md"
BUILD_ORDER = [55, 56, 57]
ENTRY_GATE_SHA = "9f1aaa08"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase4_adaptive_batch_c.py",
            "tests/launch57/test_smart_money_batch3.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase4_adaptive_batch_c.py "
            "tests/launch57/test_smart_money_batch3.py -q"
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
        55: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + manipulation alert from suspicious-pattern evidence only",
            "proven_adaptive_gap": "Pump/dump alerts fired on raw movement or loose whale rows without canonical pattern qualification",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch3:pump_dump_manipulation_alerts + sentiment_manipulation_guard",
            "shared_support_path": "launch57.trust_adaptive_common:apply_manipulation_pattern_qualification_filter",
            "builder_state": "PENDING_VERIFICATION",
        },
        56: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + evidence-based suspicious activity with limited mini-AML scope",
            "proven_adaptive_gap": "All raw flags promoted to decision-driving suspicion without confidence/severity gating",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch3:suspicious_activity_flags + fraud_suspicious_activity_297",
            "shared_support_path": "launch57.trust_adaptive_common:apply_suspicious_activity_evidence_filter",
            "builder_state": "PENDING_VERIFICATION",
        },
        57: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + exchange transparency indicators only (no solvency certification)",
            "proven_adaptive_gap": "Health/reserve scores exposed without runtime guard against solvency/safety certification semantics",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch3:exchange_transparency_risk_indicators + build_exchange_health_with_counterparty_92",
            "shared_support_path": "launch57.trust_adaptive_common:apply_exchange_transparency_risk_guard",
            "builder_state": "PENDING_VERIFICATION",
        },
    }

    evidence = {
        "artifact": "PHASE4_ADAPTIVE_BATCH_C_EVIDENCE",
        "phase": "4_ADAPTIVE_BATCH_C",
        "build_order": BUILD_ORDER,
        "entry_gate": {
            "PHASE4_BATCH_B_INDEPENDENT_VERDICT": "PASS_ENGINEERING",
            "PHASE4_BATCH_C_MAY_BEGIN": True,
            "verified_at_sha": ENTRY_GATE_SHA,
        },
        "starting_head_sha": ENTRY_GATE_SHA,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "builder_status_max": "PENDING_VERIFICATION",
        "items": items,
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/smart_money_batch3.py",
        ],
        "support_files_changed": ["launch57.trust_adaptive_common.py"],
        "tests": tests,
        "confirmations": {
            "PHASE4_BATCH_C_IMPLEMENTATION_STATUS": "PENDING_VERIFICATION",
            "PHASE5_NOT_STARTED": True,
            "PASS_ENGINEERING_NOT_CLAIMED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 4 Adaptive Batch C — Builder Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Entry gate: PHASE4_BATCH_B_INDEPENDENT_VERDICT = PASS_ENGINEERING @ `{ENTRY_GATE_SHA}`",
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
            "PHASE4_BATCH_C_IMPLEMENTATION_STATUS = PENDING_VERIFICATION",
            "PHASE5_NOT_STARTED = true",
            "PASS_ENGINEERING_NOT_CLAIMED = true",
            "PASS_LIVE_NOT_CLAIMED = true",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Phase 4 Adaptive Batch C evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
