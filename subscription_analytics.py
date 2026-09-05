"""Subscription and usage analytics hub (PDF #745)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from path_safety import project_data_dir


def subscription_analytics_status_745() -> dict[str, Any]:
    from billing_service import billing_status

    billing = billing_status()
    events_path = project_data_dir() / "usage_analytics_events.jsonl"
    visit_count = 0
    if events_path.is_file():
        try:
            visit_count = sum(1 for _ in events_path.read_text(encoding="utf-8").splitlines() if _.strip())
        except OSError:
            visit_count = 0

    return {
        "ok": True,
        "success": True,
        "capability_id": 745,
        "billing": billing,
        "usage_events_logged": visit_count,
        "visitor_counter": "usage_analytics_events.jsonl",
        "subscription_metrics_ready": True,
    }
