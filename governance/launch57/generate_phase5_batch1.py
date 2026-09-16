#!/usr/bin/env python3
"""Launch-57 Phase 5 Derivatives Batch 1 — SSOT + register (builder PENDING only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE5_BATCH1_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE5_BATCH1_REPORT.md"

SOURCE_COMMIT = "00704dd1"
BUILD_ORDER = [25, 26, 27, 28, 29]

CAP_ROWS: dict[int, dict] = {
    25: {
        "cap_ids": ["CAP-0085", "CAP-0048"],
        "numeric_ids": [85, 48],
        "name": "Futures OI intelligence",
        "entrypoint": "futures_open_interest_intelligence",
        "runtime_path": "cap646/institutional_official_production.py → launch57/derivatives_batch1.py",
        "consumer_paths": ["launch57/derivatives_batch1.py", "bd_platform/derivatives_hub.py"],
        "semantic_oracle": "OI from derivatives hub on live spine",
        "tests": ["tests/launch57/test_derivatives_batch1.py"],
    },
    26: {
        "cap_ids": ["CAP-0086"],
        "numeric_ids": [86],
        "name": "Funding rate intelligence",
        "entrypoint": "funding_rate_intelligence",
        "runtime_path": "cap646/institutional_official_production.py → launch57/derivatives_batch1.py",
        "consumer_paths": ["launch57/derivatives_batch1.py", "bd_platform/derivatives_hub.py"],
        "semantic_oracle": "funding rate on live spine; STALE blocks",
        "tests": ["tests/launch57/test_derivatives_batch1.py::test_funding_rate_blocks_stale"],
    },
    27: {
        "cap_ids": ["CAP-0088"],
        "numeric_ids": [88],
        "name": "Liquidation intelligence / light heatmap",
        "entrypoint": "liquidation_intelligence_light",
        "runtime_path": "cap646/institutional_official_production.py → launch57/derivatives_batch1.py",
        "consumer_paths": ["launch57/derivatives_batch1.py", "bd_platform/liquidation_radar.py"],
        "semantic_oracle": "light heatmap only — global coverage FORBIDDEN",
        "tests": ["tests/launch57/test_derivatives_batch1.py::test_liquidation_light_heatmap_disclaimer"],
    },
    28: {
        "cap_ids": ["CAP-0089", "CAP-0087"],
        "numeric_ids": [89, 87],
        "name": "Taker buy/sell + leverage ratio",
        "entrypoint": "taker_buy_sell_pressure",
        "runtime_path": "cap646/institutional_official_production.py → launch57/derivatives_batch1.py",
        "consumer_paths": ["launch57/derivatives_batch1.py", "bd_platform/heroes_capability_layer.py"],
        "semantic_oracle": "taker pressure + leverage on live spine",
        "tests": ["tests/launch57/test_derivatives_batch1.py::test_dispatch_all_batch1_caps"],
    },
    29: {
        "cap_ids": ["CAP-0090"],
        "numeric_ids": [90],
        "name": "Derivatives sentiment composite",
        "entrypoint": "derivatives_sentiment_composite",
        "runtime_path": "cap646/institutional_official_production.py → launch57/derivatives_batch1.py",
        "consumer_paths": ["launch57/derivatives_batch1.py", "sentiment_engine.py"],
        "semantic_oracle": "composite from sentiment + derivatives on live spine",
        "tests": ["tests/launch57/test_derivatives_batch1.py::test_dispatch_all_batch1_caps"],
    },
}


def _git_sha() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _run_tests() -> dict:
    proc = subprocess.run(
        ["python3", "-m", "pytest", "tests/launch57/test_derivatives_batch1.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_derivatives_batch1.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def _update_cap_row(cap: dict, launch_id: int, commit_sha: str, test_result: dict) -> None:
    meta = CAP_ROWS[launch_id]
    cap["canonical_implementation"] = "launch57.derivatives_batch1"
    cap["actual_consumer_paths"] = meta["consumer_paths"]
    cap["launch57_phase5_batch1"] = {
        "phase": "5_DERIVATIVES_HABITS",
        "batch": 1,
        "launch_item_id": launch_id,
        "builder_status": "PENDING_VERIFICATION",
        "prior_pass_trusted_for_launch": "NO",
        "runtime_path": meta["runtime_path"],
        "consumer_paths": meta["consumer_paths"],
        "backend_module": "launch57.derivatives_batch1",
        "backend_entrypoint": meta["entrypoint"],
        "binding_source": "launch57_phase5_derivatives_batch1",
        "semantic_oracle": meta["semantic_oracle"],
        "tests_run": meta["tests"],
        "tests_result": "PASS" if test_result["passed"] else "FAIL",
        "evidence_reference": "governance/launch57/PHASE5_BATCH1_EVIDENCE.json",
        "commit_sha": commit_sha,
        "known_gaps": ["independent_verification_pending", "legacy_bypass_if_LAUNCH57_DERIVATIVES_BATCH1_CAP_IDS_emptied"],
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

    ssot["phase5_derivatives_batch1"] = {
        "phase": "5_DERIVATIVES_HABITS",
        "batch": 1,
        "build_order_executed": BUILD_ORDER,
        "commit": commit_sha,
        "completed_at": now,
        "builder_status": "PENDING_VERIFICATION",
        "tests": test_result,
        "phase4_baseline": SOURCE_COMMIT,
        "open_debt": {
            "legacy_bypass": "When LAUNCH57_DERIVATIVES_BATCH1_CAP_IDS emptied → batch02_dedicated",
            "fix_mandatory": "NO unless derivatives path blocked",
        },
    }
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "5_DERIVATIVES_BATCH1_BUILD"
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BUILD_ORDER:
            continue
        meta = CAP_ROWS[ln]
        item["phase5_batch1_build"] = {
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta["runtime_path"],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase5_derivatives_batch1",
            "handler_module": "launch57.derivatives_batch1",
            "tests_found": meta["tests"],
            "evidence_found": ["governance/launch57/PHASE5_BATCH1_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
        }
        item["canonical_implementation"] = ["launch57.derivatives_batch1"]
        item["actual_consumer_paths"] = meta["consumer_paths"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"

    register["phase5_batch1_verification"] = {
        "PHASE": "5_DERIVATIVES_HABITS",
        "BATCH": 1,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE5_BATCH1_EVIDENCE",
        "phase": "5_DERIVATIVES_HABITS",
        "batch": 1,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "handler_module": "launch57.derivatives_batch1",
        "tests": test_result,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        f"# Phase 5 Batch 1\n\nBUILD_ORDER: {BUILD_ORDER}\nCOMMIT: {commit_sha}\nSTATUS: PENDING_VERIFICATION\n",
        encoding="utf-8",
    )
    print(f"Updated SSOT/register phase5 batch1 @ {commit_sha}")


if __name__ == "__main__":
    main()
