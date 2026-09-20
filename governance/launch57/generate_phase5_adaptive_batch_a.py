#!/usr/bin/env python3
"""Launch-57 Phase 5 Adaptive Batch A builder evidence generator (#25→#29)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GOV = ROOT / "governance" / "launch57"
EVIDENCE_PATH = GOV / "PHASE5_ADAPTIVE_BATCH_A_EVIDENCE.json"
REPORT_PATH = GOV / "PHASE5_ADAPTIVE_BATCH_A_REPORT.md"
BUILD_ORDER = [25, 26, 27, 28, 29]
ENTRY_GATE_SHA = "8164312d"


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_phase5_adaptive_batch_a.py",
            "tests/launch57/test_derivatives_batch1.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": (
            "python3 -m pytest tests/launch57/test_phase5_adaptive_batch_a.py "
            "tests/launch57/test_derivatives_batch1.py -q"
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
        25: {
            "governing_requirement": "Adaptive Spec §24/§28 — derivatives contract on OI with freshness, direction, limitation, direct evidence",
            "proven_adaptive_gap": "OI exposed raw hub values without derivatives contract semantics or funding/taker contradiction wiring",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.derivatives_batch1:futures_open_interest_intelligence + bd_platform.derivatives_hub.derivatives_overview",
            "shared_support_path": "launch57.trust_adaptive_common:apply_open_interest_derivatives_semantics",
            "builder_state": "PENDING_VERIFICATION",
        },
        26: {
            "governing_requirement": "Adaptive Spec §24/§28 — funding rate direction and material contradiction with taker flow",
            "proven_adaptive_gap": "Funding rate returned without direction semantics or contradiction/limitation in decision-driving output",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.derivatives_batch1:funding_rate_intelligence + bd_platform.derivatives_hub.derivatives_overview",
            "shared_support_path": "launch57.trust_adaptive_common:apply_funding_rate_derivatives_semantics",
            "builder_state": "PENDING_VERIFICATION",
        },
        27: {
            "governing_requirement": "Adaptive Spec §24/§28 — liquidation light heatmap limitation must drive semantics not presentation only",
            "proven_adaptive_gap": "Heatmap disclaimer present but derivatives contract fields absent from consumer semantics",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.derivatives_batch1:liquidation_intelligence_light + bd_platform.liquidation_radar.liquidation_radar",
            "shared_support_path": "launch57.trust_adaptive_common:apply_liquidation_derivatives_semantics",
            "builder_state": "PENDING_VERIFICATION",
        },
        28: {
            "governing_requirement": "Adaptive Spec §24/§28 — taker/leverage composite with visible component disagreement",
            "proven_adaptive_gap": "Taker and leverage exposed separately without composite evidence class or disagreement surfacing",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.derivatives_batch1:taker_buy_sell_pressure + estimated_leverage_ratio",
            "shared_support_path": "launch57.trust_adaptive_common:apply_taker_leverage_derivatives_semantics",
            "builder_state": "PENDING_VERIFICATION",
        },
        29: {
            "governing_requirement": "Adaptive Spec §24/§28 — composite must not hide material component disagreement",
            "proven_adaptive_gap": "composite_score copied sentiment only; derivatives component disagreement hidden",
            "execution_disposition": "ADAPTIVE_GAP_IMPLEMENTATION_REQUIRED",
            "canonical_path_reused": "launch57.derivatives_batch1:derivatives_sentiment_composite + sentiment_engine + derivatives_hub",
            "shared_support_path": "launch57.trust_adaptive_common:compute_derivatives_sentiment_composite",
            "builder_state": "PENDING_VERIFICATION",
        },
    }

    evidence = {
        "artifact": "PHASE5_ADAPTIVE_BATCH_A_EVIDENCE",
        "phase": "5_ADAPTIVE_BATCH_A",
        "build_order": BUILD_ORDER,
        "entry_gate": {
            "PHASE4_INDEPENDENT_VERDICT": "PASS_ENGINEERING",
            "PHASE5_MAY_BEGIN": True,
            "verified_at_sha": ENTRY_GATE_SHA,
        },
        "starting_head_sha": ENTRY_GATE_SHA,
        "implementation_sha": commit_sha,
        "generated_at": now,
        "builder_status_max": "PENDING_VERIFICATION",
        "items": items,
        "product_files_changed": [
            "launch57/trust_adaptive_common.py",
            "launch57/derivatives_batch1.py",
        ],
        "support_files_changed": ["launch57/trust_adaptive_common.py"],
        "tests": tests,
        "confirmations": {
            "PHASE5_BATCH_A_IMPLEMENTATION_STATUS": "PENDING_VERIFICATION",
            "PHASE5_BATCH_B_NOT_STARTED": True,
            "PASS_ENGINEERING_NOT_CLAIMED": True,
            "PASS_LIVE_NOT_CLAIMED": True,
            "REGISTER_STATUS_PROMOTION": False,
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Phase 5 Adaptive Batch A — Builder Report",
        "",
        f"Implementation SHA: `{commit_sha}`",
        f"Entry gate: PHASE4_INDEPENDENT_VERDICT = PASS_ENGINEERING @ `{ENTRY_GATE_SHA}`",
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
            "PHASE5_BATCH_A_IMPLEMENTATION_STATUS = PENDING_VERIFICATION",
            "PHASE5_BATCH_B_NOT_STARTED = true",
            "PASS_ENGINEERING_NOT_CLAIMED = true",
            "PASS_LIVE_NOT_CLAIMED = true",
            "```",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote Phase 5 Adaptive Batch A evidence @ {commit_sha[:8]}")


if __name__ == "__main__":
    main()
