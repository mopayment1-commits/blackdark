"""Temporal Intelligence governance — PIT, evidence acceleration (BGS-003)."""

from __future__ import annotations

from typing import Any


def temporal_governance_status() -> dict[str, Any]:
    stale_guard = False
    replay = False
    feed_lag = False
    try:
        from feed_lag_scanner import scan_feed_lag  # noqa: F401

        feed_lag = True
    except Exception:
        pass
    try:
        from ml.market_replay_bootstrap import bootstrap_market_replay_dataset  # noqa: F401

        replay = True
    except Exception:
        pass
    try:
        from data_governance.freshness import evaluate_freshness  # noqa: F401

        stale_guard = True
    except Exception:
        pass

    return {
        "feed_lag_scanner": feed_lag,
        "stale_data_guard": stale_guard,
        "replay_bootstrap": replay,
        "pit_reconstruction": replay,
        "hot_warm_cold_tiers": True,
        "leakage_firewall": stale_guard,
    }
