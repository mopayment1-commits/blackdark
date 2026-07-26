"""
BLACKDARK — Cloud efficiency / infrastructure metrics (Buyer Requirement #9).
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any


def collect_infra_metrics() -> dict[str, Any]:
    """Lightweight RAM/CPU snapshot for cloud cost monitoring."""
    metrics: dict[str, Any] = {
        "timestamp": time.time(),
        "python_version": sys.version.split()[0],
        "service_mode": os.getenv("SERVICE_MODE", "all"),
    }

    try:
        import psutil

        proc = psutil.Process()
        mem = proc.memory_info()
        metrics["process"] = {
            "rss_mb": round(mem.rss / 1024 / 1024, 2),
            "cpu_percent": proc.cpu_percent(interval=0.1),
        }
        metrics["system"] = {
            "cpu_count": psutil.cpu_count(),
            "memory_available_mb": round(psutil.virtual_memory().available / 1024 / 1024, 2),
            "memory_percent": psutil.virtual_memory().percent,
        }
    except ImportError:
        metrics["process"] = {"rss_mb": None, "note": "install psutil for detailed metrics"}
        metrics["system"] = {}

    try:
        from live_book_hub import hub_stats
        from market_cache import cache_stats
        from scan_coordinator import coordinator_stats

        metrics["efficiency"] = {
            "live_book_entries": hub_stats().get("entries", 0),
            "market_cache": cache_stats(),
            "scan_coordinator": coordinator_stats(),
        }
    except Exception:
        metrics["efficiency"] = {}

    try:
        from data_sources_registry import registry_summary

        metrics["data_sources"] = registry_summary()
    except Exception:
        pass

    metrics["cost_rating"] = _cost_rating(metrics)
    return metrics


def _cost_rating(metrics: dict[str, Any]) -> str:
    rss = (metrics.get("process") or {}).get("rss_mb")
    if rss is None:
        return "unknown"
    if rss < 256:
        return "excellent"
    if rss < 512:
        return "good"
    if rss < 1024:
        return "moderate"
    return "heavy"
