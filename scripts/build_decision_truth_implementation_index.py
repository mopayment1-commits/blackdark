#!/usr/bin/env python3
"""Build Decision Truth implementation index DTS-001 → DTS-060."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BINDINGS: dict[str, dict] = {
    "DTS-001": {"reuse": "IMPROVE", "title": "No opportunity without economic reality", "module_paths": ["decision_truth/net_edge.py", "decision_truth/pipeline.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-002": {"reuse": "BUILD", "title": "Decision outputs require net edge, risk, grade, evidence, freshness", "module_paths": ["decision_truth/contract.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-003": {"reuse": "REUSE", "title": "Explicit abstention", "module_paths": ["failure/decision.py", "decision_truth/admission.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-004": {"reuse": "REUSE", "title": "User agency", "module_paths": ["regulatory_compliance_guard.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-005": {"reuse": "BUILD", "title": "No hidden assumptions", "module_paths": ["decision_truth/methodology.py", "decision_truth/net_edge.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-006": {"reuse": "BUILD", "title": "No false precision", "module_paths": ["decision_truth/net_edge.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-007": {"reuse": "REUSE", "title": "Calm default UX", "module_paths": ["decision_truth/pipeline.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-008": {"reuse": "REUSE", "title": "Evidence before marketing claims", "module_paths": ["regulatory_compliance_guard.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-009": {"reuse": "IMPROVE", "title": "Formal Net-Edge spec", "module_paths": ["decision_truth/net_edge.py", "net_edge_truth.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-010": {"reuse": "BUILD", "title": "Cost autopsy", "module_paths": ["decision_truth/net_edge.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-011": {"reuse": "BUILD", "title": "Net-edge uncertainty", "module_paths": ["decision_truth/net_edge.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-012": {"reuse": "BUILD", "title": "Realizable edge", "module_paths": ["decision_truth/net_edge.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-013": {"reuse": "BUILD", "title": "Execution feasibility score", "module_paths": ["decision_truth/execution.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-014": {"reuse": "BUILD", "title": "Opportunity capacity", "module_paths": ["decision_truth/capacity.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-015": {"reuse": "IMPROVE", "title": "Opportunity half-life", "module_paths": ["decision_truth/half_life.py", "opportunity_tracker.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-016": {"reuse": "BUILD", "title": "Reverse stress testing", "module_paths": ["decision_truth/risk.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-017": {"reuse": "BUILD", "title": "Signal admission gate", "module_paths": ["decision_truth/admission.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-018": {"reuse": "IMPROVE", "title": "Decision contract", "module_paths": ["decision_truth/contract.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-019": {"reuse": "BUILD", "title": "Opportunity rejection engine", "module_paths": ["decision_truth/rejection.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-020": {"reuse": "BUILD", "title": "Why NOT engine", "module_paths": ["decision_truth/rejection.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-021": {"reuse": "BUILD", "title": "Calibration ledger", "module_paths": ["decision_truth/calibration.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-022": {"reuse": "BUILD", "title": "Pre-registered outcome ledger", "module_paths": ["decision_truth/outcome.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-023": {"reuse": "BUILD", "title": "Decision change detector", "module_paths": ["decision_truth/change.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-024": {"reuse": "BUILD", "title": "Safety floor", "module_paths": ["decision_truth/pipeline.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-025": {"reuse": "BUILD", "title": "Six Heroes default", "module_paths": ["decision_truth/pipeline.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-026": {"reuse": "REUSE", "title": "Optional command view", "module_paths": ["templates/dashboard.html"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-027": {"reuse": "BUILD", "title": "Risk budget envelope", "module_paths": ["decision_truth/risk.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-028": {"reuse": "BUILD", "title": "Pre-impact alerts", "module_paths": ["decision_truth/risk.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-029": {"reuse": "BUILD", "title": "Exchange health protection", "module_paths": ["decision_truth/risk.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-030": {"reuse": "BUILD", "title": "Stablecoin de-peg protection", "module_paths": ["decision_truth/risk.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-031": {"reuse": "BUILD", "title": "Smart money context", "module_paths": ["decision_truth/smart_money.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-032": {"reuse": "BUILD", "title": "Attribution confidence", "module_paths": ["decision_truth/smart_money.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-033": {"reuse": "BUILD", "title": "No unsupported causality", "module_paths": ["decision_truth/smart_money.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-034": {"reuse": "BUILD", "title": "Daily evidence autopsy", "module_paths": ["decision_truth/daily_autopsy.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-035": {"reuse": "BUILD", "title": "Evidence-backed sentences", "module_paths": ["decision_truth/daily_autopsy.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-036": {"reuse": "REUSE", "title": "User-local delivery", "module_paths": ["timezone/format.py", "decision_truth/daily_autopsy.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-037": {"reuse": "BUILD", "title": "Simulation beside decision", "module_paths": ["decision_truth/simulation.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-038": {"reuse": "IMPROVE", "title": "Simulation methodology", "module_paths": ["decision_truth/simulation.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-039": {"reuse": "BUILD", "title": "Simulation disclosures", "module_paths": ["decision_truth/simulation.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-040": {"reuse": "BUILD", "title": "Portfolio-aware simulation", "module_paths": ["decision_truth/simulation.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-041": {"reuse": "BUILD", "title": "Evidence grade methodology", "module_paths": ["decision_truth/evidence.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-042": {"reuse": "BUILD", "title": "Explainable grade", "module_paths": ["decision_truth/evidence.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-043": {"reuse": "REUSE", "title": "Evidence class", "module_paths": ["cap646/evidence_class.py", "decision_truth/evidence.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-044": {"reuse": "BUILD", "title": "Wow reject bad opportunities", "module_paths": ["decision_truth/rejection.py", "decision_truth/pipeline.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-045": {"reuse": "BUILD", "title": "Wow portfolio pre-impact", "module_paths": ["decision_truth/risk.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-046": {"reuse": "BUILD", "title": "Wow NO DECISION", "module_paths": ["decision_truth/admission.py", "decision_enrichment.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-047": {"reuse": "BUILD", "title": "Full evidence trail", "module_paths": ["decision_truth/pipeline.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-048": {"reuse": "BUILD", "title": "30-second truth surface", "module_paths": ["decision_truth/pipeline.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-049": {"reuse": "REUSE", "title": "Block strategic defects", "module_paths": ["regulatory_compliance_guard.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-050": {"reuse": "BUILD", "title": "Methodology versioning", "module_paths": ["decision_truth/methodology.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-051": {"reuse": "BUILD", "title": "Evidence provenance", "module_paths": ["decision_truth/pipeline.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-052": {"reuse": "IMPROVE", "title": "No silent fallback", "module_paths": ["decision_truth/admission.py", "failure/freshness.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-053": {"reuse": "REUSE", "title": "Failure integration", "module_paths": ["failure/decision.py", "decision_truth/admission.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-054": {"reuse": "REUSE", "title": "Timezone integration", "module_paths": ["timezone/format.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-055": {"reuse": "IMPROVE", "title": "I18N 38 locales", "module_paths": ["i18n_service.py", "decision_truth/rejection.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-056": {"reuse": "BUILD", "title": "Accessibility WCAG 2.2 AA", "module_paths": ["static/js/bd_failure.js"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-057": {"reuse": "BUILD", "title": "User-specific risk safety", "module_paths": ["decision_truth/risk.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-058": {"reuse": "BUILD", "title": "Anti-cherry-picking", "module_paths": ["decision_truth/outcome.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-059": {"reuse": "BUILD", "title": "Calibration-aware confidence", "module_paths": ["decision_truth/calibration.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
    "DTS-060": {"reuse": "BUILD", "title": "Decision history integrity", "module_paths": ["decision_truth/change.py"], "test_paths": ["tests/test_decision_truth_p0_test_matrix.py"]},
}


def main() -> None:
    index = {
        "schema_version": "1.0",
        "spec_file": "docs/BLACKDARK_DECISION_TRUTH_SYSTEM_INSTITUTIONAL_FINAL_v1.md",
        "requirements": [f"DTS-{i:03d}" for i in range(1, 61)],
        "bindings": BINDINGS,
    }
    out = ROOT / "docs" / "DECISION_TRUTH_IMPLEMENTATION_INDEX.json"
    out.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
