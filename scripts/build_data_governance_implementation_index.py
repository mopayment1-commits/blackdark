#!/usr/bin/env python3
"""Build Data Governance implementation index DIG-001 → DIG-060."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODULE = "data_governance"
TEST = "tests/test_data_governance_p0_test_matrix.py"

TITLES = {
    1: "Five-level audit Level 1 source authority",
    2: "Five-level audit Level 2 ingestion normalization",
    3: "Five-level audit Level 3 quality freshness reliability",
    4: "Five-level audit Level 4 provenance methodology audit",
    5: "Five-level audit Level 5 decision safety",
    6: "Standards and legal applicability register",
    7: "Free vs paid source strategy",
    8: "Free source risk register",
    9: "No-payment viable stack",
    10: "WebSocket-first realtime architecture",
    11: "REST bootstrap backfill recovery",
    12: "Chain event-driven update",
    13: "Release event-driven non-market data",
    14: "Freshness classes T0-T6",
    15: "L1 L2 L3 selective policy",
    16: "Historical depth policy",
    17: "Canonical normalization contract",
    18: "Raw immutable landing zone",
    19: "Provenance lineage contract",
    20: "Methodology cards registry",
    21: "Quality gate scoring",
    22: "Cross-source reconciliation",
    23: "Source reliability engineering",
    24: "SLA vs internal SLO registry",
    25: "Source redundancy failover",
    26: "Rate limit quota governance",
    27: "Licensing redistribution gate",
    28: "User data separation",
    29: "GLBA applicability register",
    30: "Data retention tiering",
    31: "Schema evolution controls",
    32: "Clock timestamp integrity",
    33: "On-chain finality reorg integrity",
    34: "Historical bias controls",
    35: "Today's Decision Surface",
    36: "Material change engine hooks",
    37: "Decision expiry integration",
    38: "Multi-dimensional data confidence",
    39: "Free-first launch architecture",
    40: "Vendor exit portability",
    41: "Production-critical source redundancy",
    42: "Data operations observability",
    43: "Source health to decision safety wiring",
    44: "Critical decision replay auditability",
    45: "Reliability chaos test matrix",
    46: "Canonical source registry schema",
    47: "Required source class contracts",
    48: "Source qualification score",
    49: "Minimum no-payment viable stack",
    50: "Paid data value case architecture",
    51: "User-facing provenance standard",
    52: "Data use decision disclosure",
    53: "Mandatory implementation gates",
    54: "Anti-bypass gates",
    55: "No-deferral rule enforcement",
    56: "Live verification register separation",
    57: "Implementation priority P0",
    58: "Thirteen operational questions answered",
    59: "Cursor execution rule compliance",
    60: "Data Truth Fabric final integration",
}

REUSE_MAP = {
    1: "IMPROVE", 2: "REUSE", 3: "REUSE", 4: "IMPROVE", 5: "IMPROVE",
    6: "BUILD", 7: "IMPROVE", 8: "BUILD", 9: "IMPROVE", 10: "REUSE",
    11: "REUSE", 12: "IMPROVE", 13: "IMPROVE", 14: "BUILD", 15: "BUILD",
    16: "BUILD", 17: "REUSE", 18: "BUILD", 19: "IMPROVE", 20: "BUILD",
    21: "REUSE", 22: "BUILD", 23: "BUILD", 24: "BUILD", 25: "BUILD",
    26: "BUILD", 27: "REUSE", 28: "REUSE", 29: "BUILD", 30: "BUILD",
    31: "BUILD", 32: "BUILD", 33: "IMPROVE", 34: "REUSE", 35: "BUILD",
    36: "IMPROVE", 37: "REUSE", 38: "IMPROVE", 39: "IMPROVE", 40: "IMPROVE",
    41: "BUILD", 42: "BUILD", 43: "BUILD", 44: "IMPROVE", 45: "BUILD",
    46: "IMPROVE", 47: "BUILD", 48: "BUILD", 49: "IMPROVE", 50: "IMPROVE",
    51: "BUILD", 52: "REUSE", 53: "BUILD", 54: "BUILD", 55: "BUILD",
    56: "BUILD", 57: "BUILD", 58: "BUILD", 59: "BUILD", 60: "BUILD",
}

PATHS_MAP = {
    1: ["data_governance/registry.py", "data_governance/rights.py"],
    2: ["data_governance/normalization.py", "data_governance/streaming.py"],
    3: ["data_governance/freshness.py", "data_governance/quality.py", "data_governance/reliability.py"],
    4: ["data_governance/provenance.py", "data_governance/methodology.py"],
    5: ["data_governance/gates.py", "decision_truth/admission.py"],
    6: ["data_governance/legal.py"],
    7: ["data_governance/registry.py"],
    8: ["data_governance/registry.py", "data_governance/fallback.py"],
    9: ["data_governance/registry.py", "data_sources_registry.py"],
    10: ["data_governance/streaming.py", "exchange_ws_hub.py"],
    11: ["blackdark/data/jobs.py", "data_governance/streaming.py"],
    12: ["data_governance/streaming.py"],
    13: ["data_governance/slo.py"],
    14: ["data_governance/freshness.py", "data_governance/slo.py"],
    15: ["data_governance/l2_l3.py", "data_governance/order_book.py"],
    16: ["data_governance/historical_depth.py"],
    17: ["data_governance/normalization.py", "blackdark/canonical/layer.py"],
    18: ["data_governance/raw_landing.py"],
    19: ["data_governance/provenance.py", "bd_platform/v4_v2_persistent_registries.py"],
    20: ["data_governance/methodology.py"],
    21: ["data_governance/quality.py", "failure/quality.py"],
    22: ["data_governance/reconciliation.py"],
    23: ["data_governance/reliability.py"],
    24: ["data_governance/slo.py"],
    25: ["data_governance/fallback.py"],
    26: ["data_governance/rate_limit.py"],
    27: ["data_governance/rights.py"],
    28: ["data_governance/retention.py"],
    29: ["data_governance/legal.py"],
    30: ["data_governance/retention.py"],
    31: ["data_governance/schema_evolution.py"],
    32: ["data_governance/timestamps.py", "timezone/format.py"],
    33: ["data_governance/streaming.py"],
    34: ["bd_platform/v4_v2_persistent_registries.py"],
    35: ["data_governance/decision_surface.py"],
    36: ["decision_truth/change.py"],
    37: ["decision_truth/half_life.py"],
    38: ["data_governance/gates.py"],
    39: ["data_governance/registry.py"],
    40: ["data_governance/normalization.py"],
    41: ["data_governance/fallback.py", "data_governance/registry.py"],
    42: ["data_governance/observability.py"],
    43: ["data_governance/gates.py", "decision_enrichment.py"],
    44: ["data_governance/raw_landing.py", "data_governance/provenance.py"],
    45: [TEST],
    46: ["data_governance/registry.py"],
    47: ["data_governance/registry.py"],
    48: ["data_governance/reliability.py"],
    49: ["data_governance/registry.py"],
    50: ["data_governance/registry.py"],
    51: ["data_governance/decision_surface.py"],
    52: ["regulatory_compliance_guard.py"],
    53: ["data_governance/pipeline.py"],
    54: ["data_governance/gates.py"],
    55: ["data_governance/pipeline.py"],
    56: ["bd_platform/data_governance_source_driven_engineering.py"],
    57: ["data_governance/pipeline.py"],
    58: ["data_governance/pipeline.py", "data_governance/decision_surface.py"],
    59: ["scripts/data_governance_final_reconciliation.py"],
    60: ["data_governance/pipeline.py", "decision_enrichment.py", "decision_truth/admission.py"],
}


def main() -> None:
    bindings = {}
    for i in range(1, 61):
        rid = f"DIG-{i:03d}"
        bindings[rid] = {
            "reuse": REUSE_MAP[i],
            "title": TITLES[i],
            "module_paths": PATHS_MAP[i],
            "test_paths": [TEST],
        }
    index = {
        "schema_version": "1.0",
        "spec_file": "docs/BLACKDARK_INSTITUTIONAL_DATA_INTELLIGENCE_GOVERNANCE_SPEC_2026_FINAL_v1.md",
        "requirements": [f"DIG-{i:03d}" for i in range(1, 61)],
        "bindings": bindings,
    }
    out = ROOT / "docs" / "DATA_GOVERNANCE_IMPLEMENTATION_INDEX.json"
    out.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
