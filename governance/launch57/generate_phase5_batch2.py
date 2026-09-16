#!/usr/bin/env python3
"""Launch-57 Phase 5 Derivatives Batch 2 — SSOT + register (builder PENDING only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE5_BATCH2_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE5_BATCH2_REPORT.md"
LAYER_REPORT = ROOT / "governance/launch57/PHASE5_DERIVATIVES_HABITS_LAYER_REPORT.md"

SOURCE_COMMIT = "00704dd1"
BUILD_ORDER = [30, 31, 32, 33]

CAP_ROWS: dict[int, dict] = {
    30: {
        "cap_ids": ["CAP-0050", "CAP-0508"],
        "numeric_ids": [50, 508],
        "name": "Order book intelligence (L1 minimum)",
        "entrypoint": "order_book_intelligence",
        "runtime_path": "cap646/institutional_official_production.py → launch57/derivatives_batch2.py",
        "consumer_paths": ["launch57/derivatives_batch2.py", "cap646/fallbacks.py", "live_book_hub.py"],
        "semantic_oracle": "L1 top-of-book declared — deeper depth not claimed",
        "tests": ["tests/launch57/test_derivatives_batch2.py::test_order_book_l1_depth_declaration"],
    },
    31: {
        "cap_ids": ["CAP-0056"],
        "numeric_ids": [56],
        "name": "Token screener (general market)",
        "entrypoint": "general_market_token_screener",
        "runtime_path": "cap646/institutional_official_production.py → launch57/derivatives_batch2.py",
        "consumer_paths": ["launch57/derivatives_batch2.py", "bd_platform/market_rankings.py"],
        "semantic_oracle": "general market rankings on live spine",
        "tests": ["tests/launch57/test_derivatives_batch2.py::test_dispatch_all_batch2_caps"],
    },
    32: {
        "cap_ids": ["CAP-0019"],
        "numeric_ids": [19],
        "name": "Watchlists (limited token + wallet)",
        "entrypoint": "limited_watchlists",
        "runtime_path": "cap646/institutional_official_production.py → launch57/derivatives_batch2.py",
        "consumer_paths": ["launch57/derivatives_batch2.py", "bd_platform/security_trust_data_layer.py"],
        "semantic_oracle": "limited watchlist scope — no full multi-venue mesh",
        "tests": ["tests/launch57/test_derivatives_batch2.py::test_limited_watchlists_scope"],
    },
    33: {
        "cap_ids": ["CAP-0017"],
        "numeric_ids": [17],
        "name": "Smart Alerts (price + flow + whale + decision)",
        "entrypoint": "smart_alerts_composite",
        "runtime_path": "cap646/institutional_official_production.py → launch57/derivatives_batch2.py",
        "consumer_paths": ["launch57/derivatives_batch2.py", "instant_alert_engine.py", "whale_tracker.py"],
        "semantic_oracle": "local alert evaluation live; external push BLOCKED_EXTERNAL if telegram missing",
        "tests": ["tests/launch57/test_derivatives_batch2.py::test_smart_alerts_blocked_external_when_no_telegram"],
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
            "tests/launch57/test_derivatives_batch2.py",
            "tests/launch57/test_derivatives_institutional_wire.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_derivatives_batch{2,institutional_wire}.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def _update_cap_row(cap: dict, launch_id: int, commit_sha: str, test_result: dict) -> None:
    meta = CAP_ROWS[launch_id]
    cap["canonical_implementation"] = "launch57.derivatives_batch2"
    cap["actual_consumer_paths"] = meta["consumer_paths"]
    cap["launch57_phase5_batch2"] = {
        "phase": "5_DERIVATIVES_HABITS",
        "batch": 2,
        "launch_item_id": launch_id,
        "builder_status": "PENDING_VERIFICATION",
        "prior_pass_trusted_for_launch": "NO",
        "runtime_path": meta["runtime_path"],
        "consumer_paths": meta["consumer_paths"],
        "backend_module": "launch57.derivatives_batch2",
        "backend_entrypoint": meta["entrypoint"],
        "binding_source": "launch57_phase5_derivatives_batch2",
        "semantic_oracle": meta["semantic_oracle"],
        "tests_run": meta["tests"],
        "tests_result": "PASS" if test_result["passed"] else "FAIL",
        "evidence_reference": "governance/launch57/PHASE5_BATCH2_EVIDENCE.json",
        "commit_sha": commit_sha,
        "known_gaps": ["independent_verification_pending", "legacy_bypass_if_LAUNCH57_DERIVATIVES_BATCH2_CAP_IDS_emptied"],
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

    ssot["phase5_derivatives_batch2"] = {
        "phase": "5_DERIVATIVES_HABITS",
        "batch": 2,
        "build_order_executed": BUILD_ORDER,
        "commit": commit_sha,
        "completed_at": now,
        "builder_status": "PENDING_VERIFICATION",
        "tests": test_result,
        "phase4_baseline": SOURCE_COMMIT,
        "phase5_complete": True,
        "open_debt": {
            "legacy_bypass": "When LAUNCH57_DERIVATIVES_BATCH*_CAP_IDS emptied → batch01/batch02/batch21_dedicated",
            "fix_mandatory": "NO unless derivatives/habits path blocked",
        },
    }
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "5_DERIVATIVES_BATCH2_BUILD"
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BUILD_ORDER:
            continue
        meta = CAP_ROWS[ln]
        item["phase5_batch2_build"] = {
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta["runtime_path"],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase5_derivatives_batch2",
            "handler_module": "launch57.derivatives_batch2",
            "tests_found": meta["tests"],
            "evidence_found": ["governance/launch57/PHASE5_BATCH2_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
        }
        item["canonical_implementation"] = ["launch57.derivatives_batch2"]
        item["actual_consumer_paths"] = meta["consumer_paths"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"

    register["phase5_batch2_verification"] = {
        "PHASE": "5_DERIVATIVES_HABITS",
        "BATCH": 2,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
        "PHASE5_COMPLETE": True,
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE5_BATCH2_EVIDENCE",
        "phase": "5_DERIVATIVES_HABITS",
        "batch": 2,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "handler_module": "launch57.derivatives_batch2",
        "tests": test_result,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        f"# Phase 5 Batch 2\n\nBUILD_ORDER: {BUILD_ORDER}\nCOMMIT: {commit_sha}\nSTATUS: PENDING_VERIFICATION\n",
        encoding="utf-8",
    )
    LAYER_REPORT.write_text(
        f"""# Phase 5 Derivatives + Habits Layer

BUILD_ORDER: 25→26→27→28→29→30→31→32→33
COMMIT: {commit_sha}
STATUS: PENDING_VERIFICATION (builder max)

## Handler modules
- launch57.derivatives_batch1 (items 25-29)
- launch57.derivatives_batch2 (items 30-33)

## Legacy bypass debt
When LAUNCH57_DERIVATIVES_BATCH*_CAP_IDS emptied → batch01/batch02/batch21_dedicated generic delegate.
""",
        encoding="utf-8",
    )
    print(f"Updated SSOT/register phase5 batch2 @ {commit_sha}")


if __name__ == "__main__":
    main()
