#!/usr/bin/env python3
"""Launch-57 Phase 6 Adaptive Batch 1 builder evidence generator (#34→#36, #51)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE6_ADAPTIVE_BATCH1_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE6_ADAPTIVE_BATCH1_REPORT.md"
BUILD_ORDER = [34, 35, 36, 51]
ENTRY_GATE_SHA = "d4f676d8"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase6_adaptive_batch1.py",
            "tests/launch57/test_explanation_ai_batch1.py",
            "tests/launch57/test_explanation_ai_institutional_wire.py",
            "tests/launch57/test_temporal_batch9.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase6_adaptive_batch1.py "
            "tests/launch57/test_explanation_ai_batch1.py "
            "tests/launch57/test_explanation_ai_institutional_wire.py "
            "tests/launch57/test_temporal_batch9.py -q"
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
        34: {
            "governing_requirement": "Adaptive Spec §24/§28 — signal explanation must not fabricate causal/decision certainty",
            "proven_adaptive_gap": "OQS why block presented inference (e.g. alignment checked) alongside footprint without observed/inference separation or causal guard",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.explanation_ai_batch1:signal_explanation_workflow + footprint_snapshot + build_oqs_why_block",
            "shared_support_path": "launch57.trust_adaptive_common:apply_signal_explanation_semantics",
            "builder_state": "PENDING_VERIFICATION",
        },
        35: {
            "governing_requirement": "Adaptive Spec §24 — price-move explanation keeps observed spine facts distinct from inference",
            "proven_adaptive_gap": "Flat reasons array mixed interpretive labels with observed price facts in consumer output",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.explanation_ai_batch1:price_move_explanation + load_decision_spine + build_sentiment_context_safe",
            "shared_support_path": "launch57.trust_adaptive_common:apply_price_move_explanation_semantics",
            "builder_state": "PENDING_VERIFICATION",
        },
        36: {
            "governing_requirement": "Adaptive Spec §24 — research agent grounded only in approved platform data; unapproved input cannot drive claims",
            "proven_adaptive_gap": "Compliance footer present but external/user-injected params could still affect agent output semantics",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.explanation_ai_batch1:ai_research_agent_grounded + build_research_lab_report",
            "shared_support_path": "launch57.trust_adaptive_common:apply_research_agent_grounding_filter",
            "builder_state": "PENDING_VERIFICATION",
        },
        51: {
            "governing_requirement": "Adaptive Spec §24 — research portal briefs from approved oracle track record only",
            "proven_adaptive_gap": "Brief builder did not reject unapproved supplemental evidence altering supported claims",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.explanation_ai_batch1:research_intelligence_portal + public_track_record",
            "shared_support_path": "launch57.trust_adaptive_common:apply_research_portal_evidence_filter",
            "builder_state": "PENDING_VERIFICATION",
        },
    }

    evidence = {
        "artifact": "PHASE6_ADAPTIVE_BATCH1_EVIDENCE",
        "phase": "6_ADAPTIVE_BATCH1",
        "build_order": BUILD_ORDER,
        "entry_gate": {
            "PHASE5_INDEPENDENT_VERDICT": "PASS_ENGINEERING",
            "PHASE6_MAY_BEGIN": True,
            "verified_at_sha": ENTRY_GATE_SHA,
        },
        "starting_head_sha": ENTRY_GATE_SHA,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "builder_status_max": "PENDING_VERIFICATION",
        "items": items,
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/explanation_ai_batch1.py",
        ],
        "support_files_changed": ["launch57/trust_adaptive_common.py"],
        "tests": tests,
        "confirmations": {
            "PHASE6_IMPLEMENTATION_STATUS": "PENDING_VERIFICATION",
            "PHASE7_NOT_STARTED": True,
            "PASS_ENGINEERING_NOT_CLAIMED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 6 Adaptive Batch 1 — Builder Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Entry gate: PHASE5_INDEPENDENT_VERDICT = PASS_ENGINEERING @ `{ENTRY_GATE_SHA}`",
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
            "PHASE6_IMPLEMENTATION_STATUS = PENDING_VERIFICATION",
            "PHASE7_NOT_STARTED = true",
            "PASS_ENGINEERING_NOT_CLAIMED = true",
            "PASS_LIVE_NOT_CLAIMED = true",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Phase 6 Adaptive Batch 1 evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
