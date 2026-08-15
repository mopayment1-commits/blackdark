"""
BLACKDARK — Daily Intelligence Report (Plan Point 44 — daily leg).

Lightweight 24h snapshot: oracle, arb, whale, moat, platform stats.
Reuses weekly_reports table with report_type=daily_intelligence.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


async def build_daily_report(*, persist: bool = True) -> dict[str, Any]:
    from database import (
        fetch_arbitrage_alert_log,
        fetch_forecast_audit_stats,
        fetch_oracle_audit_stats,
        fetch_platform_analytics,
        fetch_platform_user_stats,
        insert_weekly_report,
    )
    from market_intel import build_profit_analytics
    from opportunity_tracker import export_state
    from research_lab import compute_economic_moat
    from whale_tracker import get_latest_institutional_context

    moat = await compute_economic_moat()
    audit = await fetch_oracle_audit_stats(limit=50)
    forecast_audit = await fetch_forecast_audit_stats(limit=30)
    profit = await build_profit_analytics()
    institutional = await get_latest_institutional_context()
    alerts = await fetch_arbitrage_alert_log(limit=24)
    analytics = await fetch_platform_analytics()
    users = await fetch_platform_user_stats()
    durations = export_state()

    whale_count = len(institutional.get("whale_alerts") or [])
    profitable_alerts = sum(
        1
        for row in alerts
        if float(json.loads(row.get("payload_json") or "{}").get("net_profit_usdt") or 0) > 0
    )

    narrative = (
        f"BLACKDARK Daily — Oracle {audit.get('average_accuracy_percent')}% · "
        f"{profitable_alerts}/{len(alerts)} arb alerts · "
        f"Moat {moat.get('moat_score')}/100 · "
        f"{users.get('registered_users', 0)} users · "
        f"{durations.get('active_count', 0)} live opp durations tracked"
    )

    report: dict[str, Any] = {
        "report_type": "daily_intelligence",
        "generated_at": _utcnow_iso(),
        "narrative": narrative,
        "oracle_accuracy_percent": audit.get("average_accuracy_percent", 0),
        "forecast_accuracy_percent": forecast_audit.get("average_accuracy_percent", 0),
        "moat_score": moat.get("moat_score", 0),
        "whale_alerts_24h": whale_count,
        "arb_alerts_24h": len(alerts),
        "profitable_arb_alerts": profitable_alerts,
        "profit_analytics": profit,
        "platform": {
            **analytics,
            **users,
        },
        "opportunity_durations": {
            "active_count": durations.get("active_count", 0),
            "top_active": (durations.get("active") or [])[:5],
        },
    }

    if persist:
        try:
            report_id = await insert_weekly_report(narrative, report)
            report["report_id"] = report_id
        except Exception:
            report["persisted"] = False

    return report


def daily_report_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# BLACKDARK Daily Intelligence Report",
            "",
            f"**Generated:** {report.get('generated_at')}",
            "",
            report.get("narrative", ""),
            "",
            "## Key Metrics",
            f"- Oracle accuracy: {report.get('oracle_accuracy_percent')}%",
            f"- Forecast audit: {report.get('forecast_accuracy_percent')}%",
            f"- Moat score: {report.get('moat_score')}/100",
            f"- Whale alerts (cycle): {report.get('whale_alerts_24h')}",
            (f"- Arb alerts (24h): {report.get('arb_alerts_24h')} "
            f"({report.get('profitable_arb_alerts')} profitable)"),
            f"- Registered users: {report.get('platform', {}).get('registered_users', 0)}",
            f"- Paid subscribers: {report.get('platform', {}).get('paid_subscribers', 0)}",
            "",
            "_Not financial advice._",
        ]
    )
