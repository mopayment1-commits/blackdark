"""Batch02 (IDs 26–50) institutional closure spec — v6 §2.1 traceability."""

from __future__ import annotations

from cap646.batch02_official_production import EXPECTED_SURFACE

BATCH02_OFFICIAL_RANGE = range(26, 51)

BATCH02_DOMAIN_PAYLOAD_KEYS: dict[int, tuple[str, ...]] = {
    26: ("price_move_explanation",),
    27: ("trend", "tracked_entities"),
    28: ("conviction_score", "alert"),
    29: ("decision_engine",),
    30: ("provenance_score", "confidence_tier"),
    31: ("cross_signal_confirmation",),
    32: ("contradiction_detection",),
    33: ("actionability_score", "alerts"),
    34: ("clear_answer", "beginner_mode"),
    35: ("market_compass",),
    36: ("metrics_library",),
    37: ("entity_adjusted_metrics",),
    38: ("data", "free_tier"),
    39: ("data", "free_tier"),
    40: ("macro",),
    41: ("sopr_profitability",),
    42: ("holder_cohorts",),
    43: ("supply_dynamics",),
    44: ("netflow", "netflow_proxy"),
    45: ("data", "free_tier"),
    46: ("treasury_company_intelligence",),
    47: ("overview", "probe"),
    48: ("overview",),
    49: ("data",),
    50: ("book", "hub_stats"),
}

HANDLER_MODULE = "cap646.batch02_official_production"
PRODUCTION_MODULE = "cap646.batch02_official_production"
DEEP_TEST_MODULE = "tests.cap646.test_batch02_institutional_deep"
FROM_SCRATCH_TEST = "tests.cap646.test_batch02_from_scratch"
RTM_ARTIFACT = "docs/BATCH02_INSTITUTIONAL_CLOSURE_26_50.json"


def expected_surface(capability_id: int) -> str:
    return EXPECTED_SURFACE[capability_id]
