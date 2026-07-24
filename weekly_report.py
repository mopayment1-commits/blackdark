"""
BLACKDARK — Weekly AI Intelligence Report (Wave 6 / Excel).

Aggregates oracle accuracy, arbitrage activity, whale flows, sentiment,
and economic moat into a B2B-ready weekly snapshot.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def build_weekly_report() -> dict[str, Any]:
    from arbitrage_catalog import scan_arbitrage_catalog
    from database import (
        fetch_arbitrage_alert_log,
        fetch_oracle_audit_stats,
        fetch_platform_analytics,
        fetch_simulation_logs,
    )
    from research_lab import compute_economic_moat
    from whale_tracker import get_latest_institutional_context

    moat = await compute_economic_moat()
    audit = await fetch_oracle_audit_stats(limit=100)
    institutional = await get_latest_institutional_context()
    catalog = await scan_arbitrage_catalog()
    alerts = await fetch_arbitrage_alert_log(limit=50)
    sims = await fetch_simulation_logs(limit=20)
    analytics = await fetch_platform_analytics()

    whale_alerts = institutional.get("whale_alerts") or []
    sectors = institutional.get("sector_flows") or []

    highlights = []
    if float(audit.get("average_accuracy_percent") or 0) >= 55:
        highlights.append(f"Oracle accuracy at {audit.get('average_accuracy_percent')}% — above baseline.")
    if catalog.get("active_live_types", 0) > 0:
        highlights.append(
            f"{catalog['active_live_types']} live arbitrage types active from 77-type catalog."
        )
    if whale_alerts:
        highlights.append(f"{len(whale_alerts)} CVVD whale alerts detected this cycle.")
    if moat.get("moat_score", 0) >= 60:
        highlights.append(f"Economic moat score {moat['moat_score']}/100 — strong data depth.")

    narrative = (
        f"BLACKDARK Weekly Report — Moat {moat.get('moat_score')}/100, "
        f"Oracle {audit.get('average_accuracy_percent')}% accuracy, "
        f"{catalog.get('active_live_types', 0) + catalog.get('active_proxy_types', 0)}/77 arb types active, "
        f"{len(whale_alerts)} whale signals, {len(alerts)} arb alerts logged."
    )

    return {
        "report_type": "weekly_intelligence",
        "generated_at": _utcnow_iso(),
        "narrative": narrative,
        "highlights": highlights or ["System operational — accumulating market data."],
        "economic_moat": {
            "score": moat.get("moat_score"),
            "label": moat.get("moat_label"),
            "total_records": moat.get("total_data_records"),
            "replication_years": moat.get("replication_estimate_years"),
        },
        "oracle_performance": {
            "total_predictions": audit.get("total_predictions"),
            "average_accuracy_percent": audit.get("average_accuracy_percent"),
            "recent": (audit.get("recent") or [])[:5],
        },
        "arbitrage_summary": {
            "catalog_total": 77,
            "active_live": catalog.get("active_live_types"),
            "active_proxy": catalog.get("active_proxy_types"),
            "profitable_opportunities": catalog.get("live_opportunities_found"),
            "alerts_logged": len(alerts),
        },
        "whale_intelligence": {
            "alert_count": len(whale_alerts),
            "sector_flows": len(sectors),
            "top_sectors": [s.get("sector") for s in sectors[:3]],
        },
        "simulations_run": len(sims),
        "platform_analytics": analytics,
    }
