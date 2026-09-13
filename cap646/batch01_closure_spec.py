"""Batch01 (IDs 1–25) institutional closure spec — v6 §2.1 traceability."""

from __future__ import annotations

from cap646.batch01_dedicated import EXPECTED_SURFACE

BATCH01_OFFICIAL_RANGE = range(1, 26)

# At least one of these domain keys must be present in execute() result.
BATCH01_DOMAIN_PAYLOAD_KEYS: dict[int, tuple[str, ...]] = {
    1: ("smart_money_leaderboard",),
    2: ("wallet_profiler",),
    3: ("wallet_profiler_for_token",),
    4: ("smart_money_tracking",),
    5: ("smart_money_accumulation_detection",),
    6: ("screener",),
    7: ("holder_distribution", "holder_metrics"),
    8: ("top_holders_concentration", "holder_metrics"),
    9: ("distribution_score", "holder_metrics"),
    10: ("wallet_pnl_analysis",),
    11: ("historical_series", "win_rate_pct"),
    12: ("entries", "exits"),
    13: ("wallet_clusters", "counterparty_risk"),
    14: ("entity_label", "labels"),
    15: ("exchange_flow", "netflow_proxy"),
    16: ("candle_investigation",),
    17: ("alert_evaluation", "metric_trigger"),
    18: ("labels",),
    19: ("wallet_watchlists",),
    20: ("portfolio", "wallet_balance"),
    21: ("transaction_decoder",),
    22: ("due_diligence",),
    23: ("token_due_diligence",),
    24: ("research_agent",),
    25: ("explanation", "workflow", "signal"),
}

HANDLER_MODULE = "cap646.batch01_dedicated"
PRODUCTION_MODULE = "cap646.batch01_production"
DEEP_TEST_MODULE = "tests.cap646.test_batch01_institutional_deep"
FROM_SCRATCH_TEST = "tests.cap646.test_batch01_from_scratch"
RTM_ARTIFACT = "docs/BATCH01_INSTITUTIONAL_CLOSURE_1_25.json"


def expected_surface(capability_id: int) -> str:
    return EXPECTED_SURFACE[capability_id]
