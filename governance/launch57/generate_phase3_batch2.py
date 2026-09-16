#!/usr/bin/env python3
"""Launch-57 Phase 3 Decision Batch 2 + completion report."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE3_BATCH2_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE3_BATCH2_REPORT.md"
COMPLETE_PATH = ROOT / "governance/launch57/PHASE3_DECISION_LAYER_REPORT.md"

SOURCE_COMMIT = "4d4dd6c7"
BATCH2_ORDER = [12, 37]
PHASE3_ORDER = [7, 8, 9, 10, 11, 12, 37]

CAP_ROWS: dict[int, dict] = {
    12: {
        "cap_ids": ["CAP-0028"],
        "numeric_ids": [28],
        "name": "Smart Money Conviction Engine",
        "entrypoint": "smart_money_conviction_engine",
        "runtime_path": "cap646/runtime.py → launch57/decision_batch2.py:smart_money_conviction_engine",
        "consumer_paths": ["launch57/decision_batch2.py", "bd_platform/retail_intelligence_layer.py"],
        "semantic_oracle": "conviction from live spine price; stale blocked",
        "tests": ["tests/launch57/test_decision_batch2.py::test_conviction_engine_live"],
    },
    37: {
        "cap_ids": ["CAP-0029"],
        "numeric_ids": [29],
        "name": "Cross-market decision engine",
        "entrypoint": "cross_market_decision_engine",
        "runtime_path": "cap646/runtime.py → launch57/decision_batch2.py:cross_market_decision_engine",
        "consumer_paths": [
            "launch57/decision_batch2.py",
            "bd_platform/pro_trader_layer.py",
            "bd_platform/institutional_delivery_intelligence_layer.py",
        ],
        "semantic_oracle": "multi_dim + cross_market on live spine; cost_claim needs Net-Edge",
        "tests": [
            "tests/launch57/test_decision_batch2.py::test_cross_market_live_path",
            "tests/launch57/test_decision_batch2.py::test_cross_market_blocks_stale",
        ],
    },
}


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "tests/launch57/test_decision_batch1.py",
            "tests/launch57/test_decision_batch2.py",
            "tests/launch57/test_decision_institutional_wire.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_decision_*.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def main() -> None:
    commit_sha = _git_sha()
    test_result = _run_tests()
    now = datetime.now(UTC).isoformat()

    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    phase3 = ssot.get("phase3_decision_batch1") or {}
    phase3.update(
        {
            "batch2_order_executed": BATCH2_ORDER,
            "full_build_order_executed": PHASE3_ORDER,
            "final_commit": commit_sha,
            "batch2_completed_at": now,
            "phase3_decision_layer_complete": True,
            "builder_status": "PENDING_VERIFICATION",
            "tests_all": test_result,
        }
    )
    ssot["phase3_decision_layer"] = phase3
    cap_index = {row["capability_id"]: row for row in ssot["canonical_capabilities"]}
    for launch_id in BATCH2_ORDER:
        for num in CAP_ROWS[launch_id]["numeric_ids"]:
            row = cap_index.get(f"CAP-{num:04d}")
            if row:
                meta = CAP_ROWS[launch_id]
                row["canonical_implementation"] = "launch57.decision_batch2"
                row["actual_consumer_paths"] = meta["consumer_paths"]
                row["launch57_phase3_batch2"] = {
                    "phase": "3_DECISION",
                    "batch": 2,
                    "launch_item_id": launch_id,
                    "builder_status": "PENDING_VERIFICATION",
                    "runtime_path": meta["runtime_path"],
                    "commit_sha": commit_sha,
                }

    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "3_DECISION_COMPLETE"
    register["final_commit"] = commit_sha
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BATCH2_ORDER:
            continue
        meta = CAP_ROWS[ln]
        item["phase3_batch2_build"] = {
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta["runtime_path"],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase3_decision_batch2",
            "tests_found": meta["tests"],
            "commit_sha": commit_sha,
        }
        item["canonical_implementation"] = ["launch57.decision_batch2"]
        item["actual_consumer_paths"] = meta["consumer_paths"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"

    register["phase3_batch2_verification"] = {
        "PHASE": "3_DECISION",
        "BATCH": 2,
        "FULL_PHASE3_ORDER": PHASE3_ORDER,
        "PHASE3_COMPLETE": "YES",
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
        "STOP": "Phase 4 not started",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    EVIDENCE_PATH.write_text(
        json.dumps(
            {
                "artifact": "PHASE3_BATCH2_EVIDENCE",
                "phase": "3_DECISION",
                "batch": 2,
                "final_commit": commit_sha,
                "build_order": BATCH2_ORDER,
                "full_order": PHASE3_ORDER,
                "tests": test_result,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    table = [
        "| Launch # | Name | Status | Module |",
        "|----------|------|--------|--------|",
        "| 7 | Market Regime / Compass | PENDING_VERIFICATION | launch57.decision_batch1 |",
        "| 8 | Beginner Decision Mode | PENDING_VERIFICATION | launch57.decision_batch1 |",
        "| 9 | Cross-Signal Confirmation | PENDING_VERIFICATION | launch57.decision_batch1 |",
        "| 10 | Contradiction Detection | PENDING_VERIFICATION | launch57.decision_batch1 |",
        "| 11 | Smart Money Actionability | PENDING_VERIFICATION | launch57.decision_batch1 |",
        "| 12 | Smart Money Conviction | PENDING_VERIFICATION | launch57.decision_batch2 |",
        "| 37 | Cross-market decision engine | PENDING_VERIFICATION | launch57.decision_batch2 |",
    ]
    COMPLETE_PATH.write_text(
        "\n".join(
            [
                "# Launch-57 Phase 3 — Decision Layer Complete",
                "",
                "## Status: PENDING_VERIFICATION (all 7 items)",
                "",
                f"Phase 1 baseline: 92b1d00e (PASS_ENGINEERING — not rebuilt)",
                f"Phase 2 baseline: 4d4dd6c7 (PASS_ENGINEERING — not rebuilt)",
                f"Phase 3 commit: {commit_sha}",
                f"BUILD_ORDER: {PHASE3_ORDER}",
                "",
                "## Open debt",
                "- legacy bypass when LAUNCH57_DECISION_BATCH*_CAP_IDS emptied → batch01_dedicated",
                "",
                *table,
                "",
                f"Tests: {test_result['stdout']}",
                "",
                "**STOP** — Phase 4 not started.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Updated SSOT/register phase3 complete @ {commit_sha}")


if __name__ == "__main__":
    main()
