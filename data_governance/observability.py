"""Data operations observability metrics."""

from __future__ import annotations

from typing import Any

from data_governance.freshness import freshness_from_live_book
from data_governance.rate_limit import quota_matrix
from data_governance.raw_landing import raw_landing_status
from data_governance.registry import registry_summary
from data_governance.reliability import reliability_matrix
from data_governance.streaming import streaming_health_report


def observability_dashboard() -> dict[str, Any]:
    return {
        "registry": registry_summary(),
        "streaming": streaming_health_report(),
        "reliability": reliability_matrix(),
        "quota": quota_matrix(),
        "raw_landing": raw_landing_status(),
        "freshness_btc": freshness_from_live_book("BTC"),
        "timestamp": __import__("time").time(),
    }
