#!/usr/bin/env python3
"""Launch-57 Phase 2 Trust Batch 2 — SSOT + register + completion report."""

from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "BLACKDARK_CAPABILITY_CURRENT_STATE.json"
REGISTER_PATH = ROOT / "governance/launch57/LAUNCH57_REGISTER.json"
EVIDENCE_PATH = ROOT / "governance/launch57/PHASE2_BATCH2_EVIDENCE.json"
REPORT_PATH = ROOT / "governance/launch57/PHASE2_BATCH2_REPORT.md"
COMPLETE_REPORT_PATH = ROOT / "governance/launch57/PHASE2_TRUST_LAYER_REPORT.md"

SOURCE_COMMIT = "92b1d00e"
BATCH2_ORDER = [47, 48, 44, 45, 46]
PHASE2_ORDER = [6, 5, 4, 3, 2, 47, 48, 44, 45, 46]

ITEM_ROWS: dict[int, dict] = {
    47: {
        "name": "One-click risk disclosure",
        "build_decision": "EXTEND",
        "entrypoint": "one_click_risk_disclosure",
        "runtime_path": "launch57/trust_batch2.py:one_click_risk_disclosure",
        "consumer_paths": [
            "launch57/trust_batch2.py",
            "decision_truth/product/reject_proof.py",
            "decision_certificate.py",
        ],
        "semantic_oracle": "compliance_footer + reject_proof from canonical govern pipeline only",
        "tests": ["tests/launch57/test_trust_batch2.py::test_one_click_risk_disclosure"],
    },
    48: {
        "name": "Abstain/reject reasons visible",
        "build_decision": "EXTEND",
        "entrypoint": "abstain_reject_reasons_visible",
        "runtime_path": "launch57/trust_batch2.py:abstain_reject_reasons_visible",
        "consumer_paths": [
            "launch57/trust_batch2.py",
            "decision_truth/product/no_decision.py",
            "decision_truth/product/rejection_engine.py",
        ],
        "semantic_oracle": "first_class_state; hidden_as_error=False",
        "tests": ["tests/launch57/test_trust_batch2.py::test_abstain_reject_reasons_first_class"],
    },
    44: {
        "name": "Shareable decision card (OG)",
        "build_decision": "EXTEND",
        "entrypoint": "shareable_decision_card",
        "runtime_path": "launch57/trust_batch2.py:shareable_decision_card",
        "consumer_paths": [
            "launch57/trust_batch2.py",
            "decision_certificate.py",
        ],
        "semantic_oracle": "OG metadata + share_urls; alias CAP-0641",
        "tests": ["tests/launch57/test_trust_batch2.py::test_shareable_decision_card_og_metadata"],
    },
    45: {
        "name": "Shareable accuracy page",
        "build_decision": "EXTEND",
        "entrypoint": "shareable_accuracy_page",
        "runtime_path": "launch57/trust_batch2.py:shareable_accuracy_page",
        "consumer_paths": [
            "launch57/trust_batch2.py",
            "oracle_track_record.py",
        ],
        "semantic_oracle": "live_only metrics; alias CAP-0640",
        "tests": ["tests/launch57/test_trust_batch2.py::test_shareable_accuracy_page_live_only"],
    },
    46: {
        "name": "Guest trust surface",
        "build_decision": "EXTEND",
        "entrypoint": "guest_trust_surface",
        "runtime_path": "launch57/trust_batch2.py:guest_trust_surface",
        "consumer_paths": [
            "launch57/trust_batch2.py",
            "governance/anonymous_visitor_governance.py",
        ],
        "semantic_oracle": "anonymous visitor governance status; no PII leak",
        "tests": ["tests/launch57/test_trust_batch2.py::test_guest_trust_surface"],
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
            "tests/launch57/test_trust_batch1.py",
            "tests/launch57/test_trust_batch2.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "command": "python3 -m pytest tests/launch57/test_trust_batch1.py tests/launch57/test_trust_batch2.py -q",
        "exit_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "passed": proc.returncode == 0,
    }


def main() -> None:
    commit_sha = _git_sha()
    test_result = _run_tests()
    now = datetime.now(UTC).isoformat()

    ssot = json.loads(SSOT_PATH.read_text(encoding="utf-8"))
    phase2 = ssot.get("phase2_trust_batch1") or {}
    phase2.update(
        {
            "batch2_order_executed": BATCH2_ORDER,
            "full_build_order_executed": PHASE2_ORDER,
            "final_commit": commit_sha,
            "batch2_completed_at": now,
            "phase2_trust_layer_complete": True,
            "builder_status": "PENDING_VERIFICATION",
            "tests_all": test_result,
        }
    )
    ssot["phase2_trust_layer"] = phase2
    SSOT_PATH.write_text(json.dumps(ssot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    register["phase"] = "2_TRUST_COMPLETE"
    register["final_commit"] = commit_sha
    register["generated_at"] = now

    for item in register.get("launch57_register", []):
        ln = item.get("launch_number")
        if ln not in BATCH2_ORDER:
            continue
        meta = ITEM_ROWS[ln]
        item["phase2_batch2_build"] = {
            "build_decision": meta["build_decision"],
            "builder_status": "PENDING_VERIFICATION",
            "runtime_path": meta["runtime_path"],
            "consumer_paths": meta["consumer_paths"],
            "binding_source": "launch57_phase2_trust_batch2",
            "tests_found": meta["tests"],
            "evidence_found": ["governance/launch57/PHASE2_BATCH2_EVIDENCE.json"],
            "blocker": None,
            "prior_pass_trusted_for_launch": "NO",
            "commit_sha": commit_sha,
        }
        item["canonical_implementation"] = ["launch57.trust_batch2"]
        item["actual_consumer_paths"] = meta["consumer_paths"]
        item["tests_found"] = meta["tests"]
        item["current_engineering_status"] = "PENDING_VERIFICATION"
        item["pass_engineering_reconciliation"] = "PENDING_INDEPENDENT_VERIFICATION"

    register["phase2_batch2_verification"] = {
        "PHASE": "2_TRUST",
        "BATCH": 2,
        "BUILD_ORDER_EXECUTED": BATCH2_ORDER,
        "FULL_PHASE2_ORDER": PHASE2_ORDER,
        "PHASE2_TRUST_LAYER_COMPLETE": "YES",
        "MAX_BUILDER_STATUS": "PENDING_VERIFICATION",
        "PASS_LIVE": "NOT_APPLICABLE",
        "STOP": "Phase 3 not started",
    }
    REGISTER_PATH.write_text(json.dumps(register, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    evidence = {
        "artifact": "PHASE2_BATCH2_EVIDENCE",
        "phase": "2_TRUST",
        "batch": 2,
        "source_commit": SOURCE_COMMIT,
        "final_commit": commit_sha,
        "generated_at": now,
        "build_order": BATCH2_ORDER,
        "full_phase2_order": PHASE2_ORDER,
        "tests": test_result,
        "items": {
            str(lid): {**ITEM_ROWS[lid], "builder_status": "PENDING_VERIFICATION", "commit_sha": commit_sha}
            for lid in BATCH2_ORDER
        },
    }
    EVIDENCE_PATH.write_text(json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    REPORT_PATH.write_text(
        "\n".join(
            [
                "# Launch-57 Phase 2 — Trust Batch 2 Report",
                "",
                f"BUILD_ORDER: {BATCH2_ORDER}",
                f"COMMIT: {commit_sha}",
                "",
            ]
            + [f"## #{lid} {ITEM_ROWS[lid]['name']} — PENDING_VERIFICATION" for lid in BATCH2_ORDER]
        )
        + "\n",
        encoding="utf-8",
    )

    table_rows = [
        "| Launch # | Name | Status | Module | Blocker |",
        "|----------|------|--------|--------|---------|",
        "| 6 | Evidence class visible | PENDING_VERIFICATION | launch57.trust_batch1 | — |",
        "| 5 | Net-Edge / Cost Autopsy | PENDING_VERIFICATION | launch57.trust_batch1 (CAP-0639) | — |",
        "| 4 | Public Accuracy Ledger | PENDING_VERIFICATION | launch57.trust_batch1 (CAP-0640) | — |",
        "| 3 | Decision Certificate + hash | PENDING_VERIFICATION | launch57.trust_batch1 (CAP-0641) | — |",
        "| 2 | Single-Sentence Oracle | PENDING_VERIFICATION | launch57.trust_batch1 | — |",
        "| 47 | One-click risk disclosure | PENDING_VERIFICATION | launch57.trust_batch2 | — |",
        "| 48 | Abstain/reject reasons | PENDING_VERIFICATION | launch57.trust_batch2 | — |",
        "| 44 | Shareable decision card | PENDING_VERIFICATION | launch57.trust_batch2 | — |",
        "| 45 | Shareable accuracy page | PENDING_VERIFICATION | launch57.trust_batch2 | — |",
        "| 46 | Guest trust surface | PENDING_VERIFICATION | launch57.trust_batch2 | — |",
    ]
    complete = [
        "# Launch-57 Phase 2 — Trust Layer Complete",
        "",
        "## Status: PENDING_VERIFICATION (all 10 items)",
        "",
        f"Phase 1 baseline: {SOURCE_COMMIT} (PASS_ENGINEERING — not rebuilt)",
        f"Phase 2 commit: {commit_sha}",
        f"BUILD_ORDER: {PHASE2_ORDER}",
        "",
        "## Open debt (documented, not fixed in Phase 2)",
        "- **legacy bypass**: when `LAUNCH57_BATCH*_CAP_IDS` intercept is emptied, institutional path falls back to `batch26_dedicated` / `verified.py` with `success=True` generic delegate",
        "- Not mandatory fix unless trust path is blocked",
        "",
        *table_rows,
        "",
        "## Tests",
        f"```\n{test_result['command']}\n{test_result['stdout']}\n```",
        "",
        "**STOP** — Phase 3 not started.",
    ]
    COMPLETE_REPORT_PATH.write_text("\n".join(complete) + "\n", encoding="utf-8")
    print(f"Updated SSOT/register phase2 complete @ {commit_sha}")


if __name__ == "__main__":
    main()
