#!/usr/bin/env python3
"""Launch-57 Phase 4 Smart Money Batch 3 — SSOT + register (builder PENDING only)."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE4_BATCH3_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE4_BATCH3_REPORT.md"
LAYER_REPORT = ROOT / "governance/launch57/PHASE4_SMART_MONEY_LAYER_REPORT.md"

SOURCE_COMMIT = "9adef8c0"
BUILD_ORDER = [55, 56, 57]

CAP_ROWS: dict[int, dict] = {
    55: {
        "cap_ids": ["CAP-0238"],
        "numeric_ids": [238],
        "name": "Pump & Dump / manipulation pattern alerts",
        "entrypoint": "pump_dump_manipulation_alerts",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch3.py",
        "consumer_paths": ["launch57/smart_money_batch3.py", "sentiment_manipulation_guard.py", "whale_tracker.py"],
        "semantic_oracle": "pump phrase + whale manipulation alerts on live spine",
        "tests": ["tests/launch57/test_smart_money_batch3.py::test_pump_dump_detects_phrases"],
    },
    56: {
        "cap_ids": ["CAP-0297"],
        "numeric_ids": [297],
        "name": "Suspicious activity flags (mini — not full AML)",
        "entrypoint": "suspicious_activity_flags",
        "runtime_path": "cap646/institutional_official_production.py → launch57/smart_money_batch3.py",
        "consumer_paths": ["launch57/smart_money_batch3.py", "bd_platform/derivatives_onchain_intelligence_layer.py"],
        "semantic_oracle": "mini AML flags only — not full investigation platform",
        "tests": ["tests/launch57/test_smart_money_batch3.py::test_suspicious_flags_mini_aml_not_full_platform"],
    },
    57: {
        "cap_ids": ["CAP-0916"],
        "numeric_ids": [916],
        "name": "Exchange transparency / risk indicators (cautious)",
        "entrypoint": "exchange_transparency_risk_indicators",
        "runtime_path": "cap646/runtime.py → cap978/verify.py → launch57/smart_money_batch3.py",
        "consumer_paths": ["launch57/smart_money_batch3.py", "bd_platform/institutional_b2b_layer.py"],
        "semantic_oracle": "cautious indicators only — solvency/reserve guarantee FORBIDDEN",
        "tests": ["tests/launch57/test_smart_money_batch3.py::test_exchange_transparency_forbids_solvency_claim"],
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
            "tests/launch57/test_smart_money_batch3.py",
            "tests/launch57/test_smart_money_institutional_wire.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_smart_money_batch3.py tests/launch57/test_smart_money_institutional_wire.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "passed": proc.returncode == 0,
    }


def _update_cap_row(cap: dict, launch_id: int, commit_sha: str, test_result: dict) -> None:
    meta = CAP_ROWS[launch_id]
    cap["canonical_implementation"] = "launch57.smart_money_batch3"
    cap["actual_consumer_paths"] = meta["consumer_paths"]
    cap["launch57_phase4_batch3"] = {
        "phase": "4_SMART_MONEY_INSTANT",
        "batch": 3,
        "launch_item_id": launch_id,
        "builder_status": "PENDING_VERIFICATION",
        "prior_pass_trusted_for_launch": "NO",
        "runtime_path": meta["runtime_path"],
        "consumer_paths": meta["consumer_paths"],
        "backend_module": "launch57.smart_money_batch3",
        "backend_entrypoint": meta["entrypoint"],
        "binding_source": "launch57_phase4_smart_money_batch3",
        "semantic_oracle": meta["semantic_oracle"],
        "tests_run": meta["tests"],
        "tests_result": "PASS" if test_result["passed"] else "FAIL",
        "evidence_reference": "governance/launch57/PHASE4_BATCH3_EVIDENCE.json",
        "commit_sha": commit_sha,
        "known_gaps": ["independent_verification_pending", "legacy_bypass_if_LAUNCH57_SMART_MONEY_BATCH3_CAP_IDS_emptied"],
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

    ssot["phase4_smart_money_batch3"] = {
        "phase": "4_SMART_MONEY_INSTANT",
        "batch": 3,
        "build_order_executed": BUILD_ORDER,
        "commit": commit_sha,
        "completed_at": now,
        "builder_status": "PENDING_VERIFICATION",
        "tests": test_result,
        "phase3_baseline": SOURCE_COMMIT,
        "phase4_complete": True,
        "open_debt": {
            "legacy_bypass": "When LAUNCH57_SMART_MONEY_BATCH*_CAP_IDS emptied → batch01/batch02/batch10/batch12_dedicated",
            "cap916_runtime": "cap978/verify.py intercept for extension scope >826",
            "fix_mandatory": "NO unless smart-money path blocked",
        },
    }
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "4_SMART_MONEY_BATCH3_BUILD"
    register["generated_at"] = now
    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BUILD_ORDER:
            continue
        meta = CAP_ROWS[ln]
        item["phase4_batch3_build"] = {
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta["runtime_path"],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase4_smart_money_batch3",
            "handler_module": "launch57.smart_money_batch3",
            "tests_found": meta["tests"],
            "evidence_found": ["governance/launch57/PHASE4_BATCH3_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
        }
        item["canonical_implementation"] = ["launch57.smart_money_batch3"]
        item["actual_consumer_paths"] = meta["consumer_paths"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"

    register["phase4_batch3_verification"] = {
        "PHASE": "4_SMART_MONEY_INSTANT",
        "BATCH": 3,
        "BUILD_ORDER_EXECUTED": BUILD_ORDER,
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
        "PHASE4_COMPLETE": True,
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE4_BATCH3_EVIDENCE",
        "phase": "4_SMART_MONEY_INSTANT",
        "batch": 3,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BUILD_ORDER,
        "handler_module": "launch57.smart_money_batch3",
        "tests": test_result,
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(
        f"# Phase 4 Batch 3\n\nBUILD_ORDER: {BUILD_ORDER}\nCOMMIT: {commit_sha}\nSTATUS: PENDING_VERIFICATION\n",
        encoding="utf-8",
    )
    LAYER_REPORT.write_text(
        f"""# Phase 4 Smart Money + Instant Layer

BUILD_ORDER: 20→16→17→13→14→15→18→19→53→54→55→56→57
COMMIT: {commit_sha}
STATUS: PENDING_VERIFICATION (builder max — no PASS_ENGINEERING from builder)

## Handler modules
- launch57.smart_money_batch1 (items 20,16,17,13,14)
- launch57.smart_money_batch2 (items 15,18,19,53,54)
- launch57.smart_money_batch3 (items 55,56,57)

## Legacy bypass debt (documented, not fixed)
When LAUNCH57_SMART_MONEY_BATCH*_CAP_IDS emptied → batch01/batch02/batch10/batch12_dedicated generic delegate.

## CAP-0916 extension path
cap646/runtime.py → cap978/verify.py → launch57.smart_money_batch3
""",
        encoding="utf-8",
    )
    print(f"Updated SSOT/register phase4 batch3 @ {commit_sha}")


if __name__ == "__main__":
    main()
