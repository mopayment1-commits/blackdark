#!/usr/bin/env python3
"""Launch-57 Phase 4 Smart Money Batch 1 — SSOT + register (builder PENDING only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE4_BATCH1_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE4_BATCH1_REPORT.md"

SOURCE_COMMIT = "9adef8c0"
BUILD_ORDER = [20, 16, 17, 13, 14]

CAP_ROWS: dict[int, dict] = {
    20: {
        "cap_ids": ["CAP-0092"],
        "numeric_ids": [92],
        "name": "Address Labels & Cohorts (limited nucleus)",
        "entrypoint": "address_labels_cohorts",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch1.py",
        "consumer_paths": ["launch57/smart_money_batch1.py", "launch57/smart_money_common.py", "bd_platform/onchain_platform_layer.py"],
        "semantic_oracle": "limited cohort nucleus on live spine; STALE blocks",
        "tests": ["tests/launch57/test_smart_money_batch1.py"],
    },
    16: {
        "cap_ids": ["CAP-0015", "CAP-0071"],
        "numeric_ids": [15, 71],
        "name": "Exchange Flow Intelligence (in/out/net)",
        "entrypoint": "exchange_flow_intelligence",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch1.py",
        "consumer_paths": ["launch57/smart_money_batch1.py", "cap646/dedicated_common.py"],
        "semantic_oracle": "netflow from launch57 data spine price context",
        "tests": ["tests/launch57/test_smart_money_batch1.py::test_exchange_flow_live_path"],
    },
    17: {
        "cap_ids": ["CAP-0072", "CAP-0075"],
        "numeric_ids": [72, 75],
        "name": "Exchange Whale Ratio + internal-flow filter",
        "entrypoint": "exchange_whale_ratio",
        "runtime_paths": ["launch57/smart_money_batch1.py:exchange_whale_ratio", "launch57/smart_money_batch1.py:internal_flow_filter"],
        "consumer_paths": ["launch57/smart_money_batch1.py", "exchange_internal_flow_filter.py"],
        "semantic_oracle": "whale ratio + internal flow classification on live spine",
        "tests": ["tests/launch57/test_smart_money_batch1.py::test_dispatch_all_batch1_caps"],
    },
    13: {
        "cap_ids": ["CAP-0005"],
        "numeric_ids": [5],
        "name": "Accumulation / Distribution Detection",
        "entrypoint": "accumulation_distribution_detection",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch1.py",
        "consumer_paths": ["launch57/smart_money_batch1.py", "whale_signal_classifier.py"],
        "semantic_oracle": "whale narratives filtered by symbol on live spine",
        "tests": ["tests/launch57/test_smart_money_batch1.py::test_dispatch_all_batch1_caps"],
    },
    14: {
        "cap_ids": ["CAP-0006"],
        "numeric_ids": [6],
        "name": "Smart Money Token Screener",
        "entrypoint": "smart_money_token_screener",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch1.py",
        "consumer_paths": ["launch57/smart_money_batch1.py", "bd_platform/free_tier_capabilities.py"],
        "semantic_oracle": "screener aggregates leaderboard on live spine",
        "tests": ["tests/launch57/test_smart_money_batch1.py::test_token_screener_live"],
    },
}


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        ["python3", "-m", "pytest", "tests/launch57/test_smart_money_batch1.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_smart_money_batch1.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def _update_cap_row(cap: dict, launch_id: int, commit_sha: str, test_result: dict) -> None:
    meta = CAP_ROWS[launch_id]
    cap_num = int(cap["capability_id"].split("-")[1])
    cap["canonical_implementation"] = "launch57.smart_money_batch1"
    cap["actual_consumer_paths"] = meta["consumer_paths"]
    cap["launch57_phase4_batch1"] = {
        "phase": "4_SMART_MONEY_INSTANT",
        "batch": 1,
        "launch_item_id": launch_id,
        "builder_status": "PENDING_VERIFICATION",
        "prior_pass_trusted_for_launch": "NO",
        "runtime_path": meta.get("runtime_path") or meta.get("runtime_paths", [""])[0],
        "consumer_paths": meta["consumer_paths"],
        "backend_module": "launch57.smart_money_batch1",
        "backend_entrypoint": meta["entrypoint"],
        "binding_source": "launch57_phase4_smart_money_batch1",
        "semantic_oracle": meta["semantic_oracle"],
        "tests_run": meta["tests"],
        "tests_result": "PASS" if test_result["passed"] else "FAIL",
        "evidence_reference": "governance/launch57/PHASE4_BATCH1_EVIDENCE.json",
        "commit_sha": commit_sha,
        "known_gaps": ["independent_verification_pending", "legacy_bypass_if_LAUNCH57_SMART_MONEY_BATCH1_CAP_IDS_emptied"],
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

    ssot["phase4_smart_money_batch1"] = {
        "phase": "4_SMART_MONEY_INSTANT",
        "batch": 1,
        "build_order_executed": BUILD_ORDER,
        "commit": commit_sha,
        "completed_at": now,
        "builder_status": "PENDING_VERIFICATION",
        "tests": test_result,
        "phase3_baseline": SOURCE_COMMIT,
        "open_debt": {
            "legacy_bypass": "When LAUNCH57_SMART_MONEY_BATCH1_CAP_IDS emptied → batch01_dedicated/batch02_dedicated",
            "fix_mandatory": "NO unless smart-money path blocked",
        },
    }
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "4_SMART_MONEY_BATCH1_BUILD"
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BUILD_ORDER:
            continue
        meta = CAP_ROWS[ln]
        item["phase4_batch1_build"] = {
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta.get("runtime_path") or meta.get("runtime_paths", [""])[0],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase4_smart_money_batch1",
            "handler_module": "launch57.smart_money_batch1",
            "tests_found": meta["tests"],
            "evidence_found": ["governance/launch57/PHASE4_BATCH1_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
        }
        item["canonical_implementation"] = ["launch57.smart_money_batch1"]
        item["actual_consumer_paths"] = meta["consumer_paths"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"

    register["phase4_batch1_verification"] = {
        "PHASE": "4_SMART_MONEY_INSTANT",
        "BATCH": 1,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE4_BATCH1_EVIDENCE",
        "phase": "4_SMART_MONEY_INSTANT",
        "batch": 1,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "handler_module": "launch57.smart_money_batch1",
        "tests": test_result,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        f"# Phase 4 Batch 1\n\nBUILD_ORDER: {BUILD_ORDER}\nCOMMIT: {commit_sha}\nSTATUS: PENDING_VERIFICATION\n",
        encoding="utf-8",
    )
    print(f"Updated SSOT/register phase4 batch1 @ {commit_sha}")


if __name__ == "__main__":
    main()
