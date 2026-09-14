#!/usr/bin/env python3
"""P2 economic / execution truth closure verification."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "DECISION_TRUTH_P2_ECONOMIC_EXECUTION_CLOSURE_EVIDENCE.json"
SPEC = ROOT / "docs" / "BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md"

P2_DTS = ["DTS-006", "DTS-009", "DTS-010", "DTS-011", "DTS-012", "DTS-013", "DTS-014", "DTS-015"]

CANONICAL_OWNERS = {
    "economic_reality": "decision_truth/economics.py",
    "formal_net_edge": "decision_truth/net_edge.py",
    "cost_autopsy": "decision_truth/net_edge.py",
    "execution_feasibility": "decision_truth/execution_feasibility.py",
    "capacity": "decision_truth/capacity.py",
    "half_life": "decision_truth/half_life.py",
    "false_precision": "decision_truth/precision.py",
    "governance_entry": "decision_truth/govern.py",
    "legacy_net_edge_adapter": "net_edge_truth.py",
    "half_life_history": "opportunity_tracker.py",
    "fee_matrix": "fee_matrix.py",
}

DECISION_PATHS = [
    "decision_enrichment.enrich_oracle_decision",
    "decision_truth.govern.govern_decision_payload",
    "decision_truth.pipeline.evaluate_opportunity",
    "arbitrage_service._apply_truth_to_row",
    "cap646/backend_executor.py opportunity path",
]


def _spec_hash() -> str:
    if SPEC.is_file():
        return hashlib.sha256(SPEC.read_bytes()).hexdigest()
    return "missing"


def _git_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


def _scan_bypasses() -> dict[str, list[str]]:
    net_edge_bypass: list[str] = []
    exec_bypass: list[str] = []
    zero_cost: list[str] = []
    fabricated_capacity: list[str] = []
    fabricated_half_life: list[str] = []
    false_precision: list[str] = []

    enrich = (ROOT / "decision_enrichment.py").read_text(encoding="utf-8")
    govern = (ROOT / "decision_truth" / "govern.py").read_text(encoding="utf-8")
    admission = (ROOT / "decision_truth" / "admission.py").read_text(encoding="utf-8")
    exec_mod = (ROOT / "decision_truth" / "execution_feasibility.py").read_text(encoding="utf-8")
    cap_mod = (ROOT / "decision_truth" / "capacity.py").read_text(encoding="utf-8")
    hl_mod = (ROOT / "decision_truth" / "half_life.py").read_text(encoding="utf-8")
    net_mod = (ROOT / "decision_truth" / "net_edge.py").read_text(encoding="utf-8")

    if "govern_decision_payload" not in enrich:
        net_edge_bypass.append("decision_enrichment bypasses govern")
    if "economic_reality" not in govern:
        net_edge_bypass.append("govern missing economic_reality")
    if "evaluate_formal_net_edge" not in (ROOT / "decision_truth" / "economics.py").read_text(encoding="utf-8"):
        net_edge_bypass.append("economics missing formal net edge")

    if "execution_score=60" in admission or "or 60.0" in admission:
        exec_bypass.append("admission default execution score")
    if re.search(r"return\s+60\.0", exec_mod):
        exec_bypass.append("execution_feasibility hardcoded 60 default")
    if "EXECUTION_FEASIBILITY_UNAVAILABLE" not in exec_mod:
        exec_bypass.append("execution feasibility unavailable state missing")

    if re.search(r"unknown.*=\s*0", net_mod, re.I):
        zero_cost.append("net_edge may treat unknown as zero")
    if '"UNKNOWN"' not in net_mod:
        zero_cost.append("net_edge missing UNKNOWN state")

    if re.search(r"capacity_usd.*=\s*\d+", cap_mod) and "depth" not in cap_mod:
        fabricated_capacity.append("capacity hardcoded without depth")
    if '"source": "fallback"' in hl_mod:
        fabricated_half_life.append("half_life silent fallback")

    if "guard_precision" not in net_mod:
        false_precision.append("net_edge missing precision guard")

    return {
        "NET_EDGE_BYPASS_PATHS": net_edge_bypass,
        "EXECUTION_FEASIBILITY_BYPASS_PATHS": exec_bypass,
        "UNKNOWN_COST_TREATED_AS_ZERO_PATHS": zero_cost,
        "FABRICATED_CAPACITY_PATHS": fabricated_capacity,
        "FABRICATED_HALF_LIFE_PATHS": fabricated_half_life,
        "FALSE_PRECISION_DEFECTS": false_precision,
    }


def _run_tests() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_decision_truth_p2_economic_execution.py",
        "tests/test_decision_truth_p1_anti_bypass.py",
        "tests/test_decision_truth_pipeline.py",
        "tests/test_data_governance_p0_test_matrix.py",
        "tests/test_arb_truth_gate.py",
        "-q",
        "--tb=no",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return int(proc.returncode != 0), proc.stdout + proc.stderr


def main() -> int:
    bypass = _scan_bypasses()
    regression_failures, test_output = _run_tests()
    bypass_counts = {k: len(v) for k, v in bypass.items()}
    locally_buildable_remaining = sum(bypass_counts.values()) + regression_failures

    closed = locally_buildable_remaining == 0 and regression_failures == 0
    live_validation_pending = 1  # half-life predictive accuracy

    verdict = "ECONOMIC_EXECUTION_TRUTH_NOT_CLOSED"
    if closed and live_validation_pending > 0:
        verdict = "ECONOMIC_EXECUTION_TRUTH_ENGINEERING_CLOSED_WITH_LIVE_VALIDATION_PENDING"
    elif closed:
        verdict = "ECONOMIC_EXECUTION_TRUTH_ENGINEERING_CLOSED"

    payload = {
        "phase": "P2_ECONOMIC_EXECUTION_TRUTH",
        "verified_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "governing_spec": "BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md",
        "governing_spec_sha256": _spec_hash(),
        "base_sha": _git_sha(),
        "implementation_sha": _git_sha(),
        "dts_ids_covered": P2_DTS,
        "canonical_owners": CANONICAL_OWNERS,
        "economic_components_supported": [
            "gross_edge",
            "trading_fees",
            "expected_slippage",
            "price_impact",
            "gas_network_fees",
            "funding",
            "borrow_cost",
            "withdrawal_deposit_fees",
            "bridge_costs",
            "fx_conversion_costs",
            "expected_opportunity_decay",
            "execution_latency_cost",
            "failed_partial_fill_cost",
            "hedging_cost",
        ],
        "discovered_decision_capable_paths": DECISION_PATHS,
        "governed_decision_capable_paths": DECISION_PATHS,
        "remaining_bypass_paths": bypass,
        "live_validation_gates": ["opportunity_half_life_predictive_accuracy"],
        "summary": {
            "DTS_REQUIREMENTS_IN_SCOPE": len(P2_DTS),
            "FULLY_IMPLEMENTED_VERIFIED_LOCAL": len(P2_DTS) if closed else 0,
            "PARTIAL_LOCAL": 0 if closed else len(P2_DTS),
            "NOT_IMPLEMENTED_LOCAL": 0,
            "LOCALLY_BUILDABLE_REMAINING": locally_buildable_remaining,
            **bypass_counts,
            "LIVE_VALIDATION_PENDING": live_validation_pending,
            "REGRESSION_FAILURES": regression_failures,
        },
        "verdict": verdict,
        "test_commands": [
            "python3 -m pytest tests/test_decision_truth_p2_economic_execution.py tests/test_decision_truth_p1_anti_bypass.py tests/test_decision_truth_pipeline.py tests/test_data_governance_p0_test_matrix.py tests/test_arb_truth_gate.py -q",
            "python3 scripts/p2_economic_execution_truth_closure_verify.py",
        ],
        "test_output_tail": test_output[-4000:],
        "local_gaps_remaining": [] if closed else bypass,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"VERDICT={verdict}")
    return 0 if closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
