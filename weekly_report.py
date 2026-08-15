"""
BLACKDARK — Weekly AI Intelligence Report (Priority 5).

Aggregates oracle, arbitrage, whale, moat, forecast audit, and platform stats.
Persisted to SQLite for B2B / institutional snapshots.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


async def _safe(coro, default: Any) -> Any:
    try:
        return await coro
    except Exception:
        return default


async def build_weekly_report(*, persist: bool = True) -> dict[str, Any]:
    from arbitrage_catalog import scan_arbitrage_catalog
    from database import (
        fetch_arbitrage_alert_log,
        fetch_forecast_audit_stats,
        fetch_oracle_audit_stats,
        fetch_platform_analytics,
        fetch_platform_user_stats,
        fetch_simulation_logs,
        insert_weekly_report,
    )
    from research_lab import compute_economic_moat
    from whale_tracker import get_latest_institutional_context

    moat = await _safe(compute_economic_moat(), {})
    audit = await _safe(fetch_oracle_audit_stats(limit=100), {})
    forecast_audit = await _safe(fetch_forecast_audit_stats(limit=50), {})
    institutional = await _safe(get_latest_institutional_context(), {})
    catalog = await _safe(scan_arbitrage_catalog(), {})
    alerts = await _safe(fetch_arbitrage_alert_log(limit=50), [])
    sims = await _safe(fetch_simulation_logs(limit=20), [])
    analytics = await _safe(fetch_platform_analytics(), {})
    users = await _safe(fetch_platform_user_stats(), {})
    if not isinstance(moat, dict):
        moat = {}
    if not isinstance(audit, dict):
        audit = {}
    if not isinstance(forecast_audit, dict):
        forecast_audit = {}
    if not isinstance(institutional, dict):
        institutional = {}
    if not isinstance(catalog, dict):
        catalog = {}
    if not isinstance(alerts, list):
        alerts = []
    if not isinstance(sims, list):
        sims = []
    if not isinstance(analytics, dict):
        analytics = {}
    if not isinstance(users, dict):
        users = {}

    whale_alerts = institutional.get("whale_alerts") or []
    sectors = institutional.get("sector_flows") or []

    highlights: list[str] = []
    if float(audit.get("average_accuracy_percent") or 0) >= 55:
        highlights.append(
            f"Oracle accuracy at {audit.get('average_accuracy_percent')}% — above baseline."
        )
    if float(forecast_audit.get("average_accuracy_percent") or 0) > 0:
        highlights.append(
            f"Forecast engine audit: {forecast_audit.get('average_accuracy_percent')}% "
            f"({forecast_audit.get('resolved_forecasts')} resolved)."
        )
    if catalog.get("active_live_types", 0) > 0:
        highlights.append(
            f"{catalog['active_live_types']} live arbitrage types active from 77-type catalog."
        )
    if whale_alerts:
        highlights.append(f"{len(whale_alerts)} CVVD whale alerts detected this cycle.")
    if moat.get("moat_score", 0) >= 60:
        highlights.append(f"Economic moat score {moat['moat_score']}/100 — strong data depth.")
    if users.get("paid_subscribers", 0) > 0:
        highlights.append(f"{users['paid_subscribers']} paid subscribers on platform.")

    narrative = (
        f"BLACKDARK Weekly Report — Moat {moat.get('moat_score')}/100, "
        f"Oracle {audit.get('average_accuracy_percent')}% accuracy, "
        f"Forecast {forecast_audit.get('average_accuracy_percent')}% audit, "
        f"{catalog.get('active_live_types', 0) + catalog.get('active_proxy_types', 0)}/77 arb types, "
        f"{len(whale_alerts)} whale signals, {users.get('registered_users', 0)} users."
    )

    recent_raw = audit.get("recent")
    recent_slice = list(recent_raw)[:5] if isinstance(recent_raw, (list, tuple)) else []
    sector_rows = sectors if isinstance(sectors, list) else []

    report: dict[str, Any] = {
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
            "recent": recent_slice,
        },
        "forecast_performance": forecast_audit,
        "arbitrage_summary": {
            "catalog_total": 77,
            "active_live": catalog.get("active_live_types"),
            "active_proxy": catalog.get("active_proxy_types"),
            "profitable_opportunities": catalog.get("live_opportunities_found"),
            "alerts_logged": len(alerts),
        },
        "whale_intelligence": {
            "alert_count": len(whale_alerts),
            "sector_flows": len(sector_rows),
            "top_sectors": [s.get("sector") for s in sector_rows[:3]],
        },
        "platform": users,
        "simulations_run": len(sims),
        "platform_analytics": analytics,
        "b2b_ready": True,
        "export_formats": ["json", "markdown"],
    }

    if persist:
        try:
            report_id = await insert_weekly_report(narrative, report)
            report["report_id"] = report_id
        except Exception:
            report["persisted"] = False

    return report


def report_to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# BLACKDARK Weekly Intelligence Report",
        "",
        f"Generated: {report.get('generated_at', '')}",
        "",
        report.get("narrative", ""),
        "",
        "## Highlights",
    ]
    for item in report.get("highlights") or []:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Oracle",
            f"- Accuracy: {report.get('oracle_performance', {}).get('average_accuracy_percent')}%",
            f"- Predictions: {report.get('oracle_performance', {}).get('total_predictions')}",
            "",
            "## Economic Moat",
            f"- Score: {report.get('economic_moat', {}).get('score')}/100",
            "",
            "---",
            "BLACKDARK — Not financial advice.",
        ]
    )
    return "\n".join(lines)
