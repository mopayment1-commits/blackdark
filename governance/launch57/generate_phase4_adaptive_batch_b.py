#!/usr/bin/env python3
"""Launch-57 Phase 4 Adaptive Batch B builder evidence generator (#15→#18→#19→#53→#54)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE4_ADAPTIVE_BATCH_B_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE4_ADAPTIVE_BATCH_B_REPORT.md"
BUILD_ORDER = [15, 18, 19, 53, 54]
ENTRY_GATE_SHA = "616314b6"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase4_adaptive_batch_b.py",
            "tests/launch57/test_smart_money_batch2.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase4_adaptive_batch_b.py "
            "tests/launch57/test_smart_money_batch2.py -q"
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
        15: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + entity interpretation distinct from raw movement",
            "proven_adaptive_gap": "Entity wallet intelligence returned raw search_address payload without attribution-driven interpretation or uncertainty",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch2:entity_aware_wallet_intelligence",
            "shared_support_path": "launch57.trust_adaptive_common:derive_entity_wallet_interpretation",
            "builder_state": "PENDING_VERIFICATION",
        },
        18: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + alert-worthy whale behavior from canonical qualification",
            "proven_adaptive_gap": "Whale alerts counted raw movements without classify_whale_alert runtime qualification",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch2:whale_accumulation_distribution_intelligence + whale_movement_alerts + whale_signal_classifier.classify_whale_alert",
            "shared_support_path": "launch57.trust_adaptive_common:apply_whale_alert_qualification_filter",
            "builder_state": "PENDING_VERIFICATION",
        },
        19: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + internal exchange movement excluded from inter-entity semantics",
            "proven_adaptive_gap": "Inter-entity flow passed onchain context without internal-flow classification filter",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch2:inter_entity_flow_intelligence + exchange_internal_flow_filter.classify_flow",
            "shared_support_path": "launch57.trust_adaptive_common:apply_inter_entity_internal_flow_filter",
            "builder_state": "PENDING_VERIFICATION",
        },
        53: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + approved Launch-57 evidence only for wallet DD semantics",
            "proven_adaptive_gap": "Wallet due diligence verdict derived from all inputs without approved-evidence guard",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch2:instant_wallet_due_diligence",
            "shared_support_path": "launch57.trust_adaptive_common:compute_approved_wallet_due_diligence_verdict",
            "builder_state": "PENDING_VERIFICATION",
        },
        54: {
            "governing_requirement": "Adaptive Spec §28 Level 1 + approved Launch-57 evidence only for token DD semantics",
            "proven_adaptive_gap": "Token due diligence risk_flags included unapproved financial_model_gap in decision-driving verdict",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.smart_money_batch2:instant_token_due_diligence",
            "shared_support_path": "launch57.trust_adaptive_common:compute_approved_token_due_diligence_verdict",
            "builder_state": "PENDING_VERIFICATION",
        },
    }

    evidence = {
        "artifact": "PHASE4_ADAPTIVE_BATCH_B_EVIDENCE",
        "phase": "4_ADAPTIVE_BATCH_B",
        "build_order": BUILD_ORDER,
        "entry_gate": {
            "PHASE4_BATCH_A_INDEPENDENT_VERDICT": "PASS_ENGINEERING",
            "PHASE4_BATCH_B_MAY_BEGIN": True,
            "verified_at_sha": ENTRY_GATE_SHA,
        },
        "starting_head_sha": ENTRY_GATE_SHA,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "builder_status_max": "PENDING_VERIFICATION",
        "items": items,
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/smart_money_batch2.py",
        ],
        "support_files_changed": ["launch57/trust_adaptive_common.py"],
        "tests": tests,
        "confirmations": {
            "PHASE4_BATCH_B_IMPLEMENTATION_STATUS": "PENDING_VERIFICATION",
            "PHASE4_BATCH_C_NOT_STARTED": True,
            "PASS_ENGINEERING_NOT_CLAIMED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 4 Adaptive Batch B — Builder Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Entry gate: PHASE4_BATCH_A_INDEPENDENT_VERDICT = PASS_ENGINEERING @ `{ENTRY_GATE_SHA}`",
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
            "PHASE4_BATCH_B_IMPLEMENTATION_STATUS = PENDING_VERIFICATION",
            "PHASE4_BATCH_C_NOT_STARTED = true",
            "PASS_ENGINEERING_NOT_CLAIMED = true",
            "PASS_LIVE_NOT_CLAIMED = true",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Phase 4 Adaptive Batch B evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
