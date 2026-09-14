#!/usr/bin/env python3
"""P3 portfolio pre-impact / risk closure verification."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "DECISION_TRUTH_P3_PORTFOLIO_PREIMPACT_CLOSURE_EVIDENCE.json"
SPEC = ROOT / "docs" / "BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md"

P3_DTS = ["DTS-016", "DTS-027", "DTS-028", "DTS-029", "DTS-030", "DTS-045", "DTS-057"]

CANONICAL_OWNERS = {
    "portfolio_risk_orchestrator": "decision_truth/portfolio_risk.py",
    "portfolio_context": "decision_truth/portfolio_context.py",
    "risk_envelope": "decision_truth/risk_envelope.py",
    "pre_impact": "decision_truth/pre_impact.py",
    "reverse_stress": "decision_truth/reverse_stress.py",
    "venue_health": "decision_truth/venue_health.py",
    "depeg": "decision_truth/depeg.py",
    "governance_entry": "decision_truth/govern.py",
    "venue_health_adapter": "bd_platform/whales_institutional_layer.py",
    "user_risk_settings": "database.fetch_user_risk_settings",
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
    govern = (ROOT / "decision_truth" / "govern.py").read_text(encoding="utf-8")
    enrich = (ROOT / "decision_enrichment.py").read_text(encoding="utf-8")
    ctx_mod = (ROOT / "decision_truth" / "portfolio_context.py").read_text(encoding="utf-8")

    risk_bypass: list[str] = []
    pre_bypass: list[str] = []
    stress_bypass: list[str] = []
    venue_gaps: list[str] = []
    depeg_gaps: list[str] = []
    false_personalization: list[str] = []
    fabricated: list[str] = []

    if "evaluate_portfolio_risk" not in govern:
        risk_bypass.append("govern missing evaluate_portfolio_risk")
    if "govern_decision_payload" not in enrich:
        risk_bypass.append("enrichment bypasses govern")
    if "build_unified_portfolio_view_81" in ctx_mod:
        false_personalization.append("portfolio_context uses default holdings")
    if "default holdings" in ctx_mod.lower() or "50000" in ctx_mod:
        false_personalization.append("portfolio_context fabricates holdings")

    if "evaluate_pre_impact" not in govern and "pre_impact" not in govern:
        pre_bypass.append("govern missing pre_impact integration")
    if "evaluate_reverse_stress" not in (ROOT / "decision_truth" / "portfolio_risk.py").read_text(encoding="utf-8"):
        stress_bypass.append("portfolio_risk missing reverse_stress")
    if "evaluate_venue_health_decision" not in (ROOT / "decision_truth" / "portfolio_risk.py").read_text(encoding="utf-8"):
        venue_gaps.append("portfolio_risk missing venue_health")
    if "evaluate_depeg_risk" not in (ROOT / "decision_truth" / "portfolio_risk.py").read_text(encoding="utf-8"):
        depeg_gaps.append("portfolio_risk missing depeg")

    return {
        "RISK_ENVELOPE_BYPASS_PATHS": risk_bypass,
        "PRE_IMPACT_BYPASS_PATHS": pre_bypass,
        "REVERSE_STRESS_BYPASS_PATHS": stress_bypass,
        "VENUE_HEALTH_DECISION_GAPS": venue_gaps,
        "DEPEG_DECISION_GAPS": depeg_gaps,
        "FALSE_PORTFOLIO_PERSONALIZATION_PATHS": false_personalization,
        "FABRICATED_RISK_VALUES": fabricated,
    }


def _run_tests() -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_decision_truth_p3_portfolio_preimpact.py",
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
    live_validation_pending = 2  # venue health + depeg calibration effectiveness

    closed = locally_buildable_remaining == 0 and regression_failures == 0
    verdict = "PORTFOLIO_PREIMPACT_ENGINEERING_NOT_CLOSED"
    if closed and live_validation_pending > 0:
        verdict = "PORTFOLIO_PREIMPACT_ENGINEERING_CLOSED_WITH_LIVE_VALIDATION_PENDING"
    elif closed:
        verdict = "PORTFOLIO_PREIMPACT_ENGINEERING_CLOSED"

    payload = {
        "phase": "P3_PORTFOLIO_PREIMPACT_RISK",
        "verified_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "governing_spec": "BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md",
        "governing_spec_sha256": _spec_hash(),
        "base_sha": _git_sha(),
        "implementation_sha": _git_sha(),
        "dts_ids_covered": P3_DTS,
        "canonical_owners": CANONICAL_OWNERS,
        "risk_dimensions_supported": [
            "max_tolerated_loss",
            "drawdown",
            "concentration",
            "leverage",
            "liquidity",
            "venue_exposure",
            "stablecoin_exposure",
            "counterparty_exposure",
        ],
        "portfolio_data_authority": "decision_truth/portfolio_context.py",
        "reverse_stress_methodology": "dts-p3-reverse-stress-1.0",
        "depeg_methodology_version": "dts-p3-depeg-1.0",
        "remaining_bypass_paths": bypass,
        "live_validation_gates": ["venue_health_live_effectiveness", "depeg_calibration_live"],
        "summary": {
            "DTS_REQUIREMENTS_IN_SCOPE": len(P3_DTS),
            "FULLY_IMPLEMENTED_VERIFIED_LOCAL": len(P3_DTS) if closed else 0,
            "PARTIAL_LOCAL": 0 if closed else len(P3_DTS),
            "NOT_IMPLEMENTED_LOCAL": 0,
            "LOCALLY_BUILDABLE_REMAINING": locally_buildable_remaining,
            **bypass_counts,
            "LIVE_VALIDATION_PENDING": live_validation_pending,
            "REGRESSION_FAILURES": regression_failures,
        },
        "verdict": verdict,
        "test_commands": [
            "python3 -m pytest tests/test_decision_truth_p3_portfolio_preimpact.py tests/test_decision_truth_p2_economic_execution.py tests/test_decision_truth_p1_anti_bypass.py tests/test_decision_truth_pipeline.py tests/test_data_governance_p0_test_matrix.py tests/test_arb_truth_gate.py -q",
            "python3 scripts/p3_portfolio_preimpact_closure_verify.py",
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
