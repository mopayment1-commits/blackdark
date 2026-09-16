#!/usr/bin/env python3
"""Launch-57 Phase 3 Decision Batch 1 — SSOT + register (builder PENDING only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE3_BATCH1_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE3_BATCH1_REPORT.md"

SOURCE_COMMIT = "4d4dd6c7"
BUILD_ORDER = [7, 8, 9, 10, 11]

CAP_ROWS: dict[int, dict] = {
    7: {
        "cap_ids": ["CAP-0035"],
        "numeric_ids": [35],
        "name": "Market Regime / Compass",
        "entrypoint": "market_regime_compass",
        "runtime_path": "cap646/runtime.py → launch57/decision_batch1.py:market_regime_compass",
        "consumer_paths": ["launch57/decision_batch1.py", "launch57/decision_common.py", "weight_aggregator.py"],
        "semantic_oracle": "regime from live spine; STALE/UNKNOWN blocks live decision",
        "tests": [
            "tests/launch57/test_decision_batch1.py::test_market_regime_blocks_stale_not_live",
            "tests/launch57/test_decision_batch1.py::test_market_regime_live_path",
        ],
    },
    8: {
        "cap_ids": ["CAP-0034"],
        "numeric_ids": [34],
        "name": "Beginner Decision Mode",
        "entrypoint": "beginner_decision_mode",
        "runtime_path": "cap646/runtime.py → launch57/decision_batch1.py:beginner_decision_mode",
        "consumer_paths": ["launch57/decision_batch1.py", "bd_platform/retail_intelligence_layer.py"],
        "semantic_oracle": "beginner clear_answer only on live-eligible spine",
        "tests": ["tests/launch57/test_decision_batch1.py::test_execute_dispatch_all_batch1_caps"],
    },
    9: {
        "cap_ids": ["CAP-0031"],
        "numeric_ids": [31],
        "name": "Cross-Signal Confirmation",
        "entrypoint": "cross_signal_confirmation",
        "runtime_path": "cap646/runtime.py → launch57/decision_batch1.py:cross_signal_confirmation",
        "consumer_paths": ["launch57/decision_batch1.py", "signal_registry.py", "sentiment_gate.py"],
        "semantic_oracle": "price from launch57.data_batch1 spine not parallel fetch",
        "tests": ["tests/launch57/test_decision_batch1.py::test_cross_signal_confirmation_uses_spine_price"],
    },
    10: {
        "cap_ids": ["CAP-0032"],
        "numeric_ids": [32],
        "name": "Contradiction Detection",
        "entrypoint": "contradiction_detection",
        "runtime_path": "cap646/runtime.py → launch57/decision_batch1.py:contradiction_detection",
        "consumer_paths": ["launch57/decision_batch1.py", "sentiment_gate.py"],
        "semantic_oracle": "contradictions from live spine price + sentiment",
        "tests": ["tests/launch57/test_decision_batch1.py::test_execute_dispatch_all_batch1_caps"],
    },
    11: {
        "cap_ids": ["CAP-0033"],
        "numeric_ids": [33],
        "name": "Smart Money Actionability Score",
        "entrypoint": "smart_money_actionability_score",
        "runtime_path": "cap646/runtime.py → launch57/decision_batch1.py:smart_money_actionability_score",
        "consumer_paths": ["launch57/decision_batch1.py", "whale_tracker.py", "launch57/trust_batch1.py"],
        "semantic_oracle": "cost_claim requires Net-Edge (#5) path",
        "tests": ["tests/launch57/test_decision_batch1.py::test_actionability_blocks_cost_claim_without_net_edge"],
    },
}

ENTRYPOINT_BY_NUM = {35: "market_regime_compass", 34: "beginner_decision_mode", 31: "cross_signal_confirmation", 32: "contradiction_detection", 33: "smart_money_actionability_score"}


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        ["python3", "-m", "pytest", "tests/launch57/test_decision_batch1.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_decision_batch1.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def _update_cap_row(cap: dict, launch_id: int, commit_sha: str, test_result: dict) -> None:
    meta = CAP_ROWS[launch_id]
    cap_num = int(cap["capability_id"].split("-")[1])
    cap["canonical_implementation"] = "launch57.decision_batch1"
    cap["actual_consumer_paths"] = meta["consumer_paths"]
    cap["launch57_phase3_batch1"] = {
        "phase": "3_DECISION",
        "batch": 1,
        "launch_item_id": launch_id,
        "builder_status": "PENDING_VERIFICATION",
        "prior_pass_trusted_for_launch": "NO",
        "runtime_path": meta["runtime_path"],
        "consumer_paths": meta["consumer_paths"],
        "backend_module": "launch57.decision_batch1",
        "backend_entrypoint": ENTRYPOINT_BY_NUM.get(cap_num),
        "binding_source": "launch57_phase3_decision_batch1",
        "semantic_oracle": meta["semantic_oracle"],
        "tests_run": meta["tests"],
        "tests_result": "PASS" if test_result["passed"] else "FAIL",
        "evidence_reference": "governance/launch57/PHASE3_BATCH1_EVIDENCE.json",
        "commit_sha": commit_sha,
        "known_gaps": ["independent_verification_pending", "legacy_bypass_if_LAUNCH57_CAP_IDS_emptied"],
    }


def main() -> None:
    commit_sha = _git_sha()
    test_result = _run_tests()
    now = datetime.now(UTC).isoformat()

    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    cap_index = {row["capability_id"]: row for row in ssot["canonical_capabilities"]}
    for launch_id in BUILD_ORDER:
        for num in CAP_ROWS[launch_id]["numeric_ids"]:
            row = cap_index.get(f"CAP-{num:04d}")
            if row:
                _update_cap_row(row, launch_id, commit_sha, test_result)

    ssot["phase3_decision_batch1"] = {
        "phase": "3_DECISION",
        "batch": 1,
        "build_order_executed": BUILD_ORDER,
        "commit": commit_sha,
        "completed_at": now,
        "builder_status": "PENDING_VERIFICATION",
        "tests": test_result,
        "phase1_baseline": "92b1d00e",
        "phase2_baseline": "4d4dd6c7",
        "open_debt": {
            "legacy_bypass": "When LAUNCH57_DECISION_BATCH*_CAP_IDS emptied → batch01_dedicated generic delegate",
            "fix_mandatory": "NO unless decision path blocked",
        },
    }
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "3_DECISION_BATCH1_BUILD"
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BUILD_ORDER:
            continue
        meta = CAP_ROWS[ln]
        item["phase3_batch1_build"] = {
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta["runtime_path"],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase3_decision_batch1",
            "tests_found": meta["tests"],
            "evidence_found": ["governance/launch57/PHASE3_BATCH1_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
        }
        item["canonical_implementation"] = ["launch57.decision_batch1"]
        item["actual_consumer_paths"] = meta["consumer_paths"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"

    register["phase3_batch1_verification"] = {
        "PHASE": "3_DECISION",
        "BATCH": 1,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE3_BATCH1_EVIDENCE",
        "phase": "3_DECISION",
        "batch": 1,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "tests": test_result,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        f"# Phase 3 Batch 1\n\nBUILD_ORDER: {BUILD_ORDER}\nCOMMIT: {commit_sha}\nSTATUS: PENDING_VERIFICATION\n",
        encoding="utf-8",
    )
    print(f"Updated SSOT/register phase3 batch1 @ {commit_sha}")


if __name__ == "__main__":
    main()
