"""
Unified Alert Center — aggregates alerts from 6 sources into one chronological feed.

Sources:
  1. Arbitrage (#429)
  2. Risk / Capital Protection (#410)
  3. Whale / Smart Money (#408)
  4. Events (#443)
  5. Exchange Health (#456)
  6. Stablecoin Health (#467)
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

_FEATURE_ID = 434
_TITLE = "Unified Alert Center"
_ALERT_TYPES = (
    "arbitrage",
    "risk",
    "whale",
    "events",
    "exchange",
    "stablecoin",
    "inbox",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_alert(
    *,
    alert_type: str,
    title: str,
    body: str,
    severity: str = "info",
    source_feature: int | None = None,
    payload: dict[str, Any] | None = None,
    created_at: str | None = None,
    alert_id: str | None = None,
) -> dict[str, Any]:
    ts = created_at or _utcnow()
    return {
        "id": alert_id or f"ual_{alert_type}_{hash(title + body) % 10**8}",
        "alert_type": alert_type,
        "title": title,
        "body": body,
        "severity": severity,
        "source_feature": source_feature,
        "payload": payload or {},
        "created_at": ts,
        "read": False,
        "unified": True,
    }


def _collect_arbitrage_alerts() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    try:
        from bd_platform.unified_arbitrage_engine import build_opportunity_alert_panel

        panel = build_opportunity_alert_panel()
        for a in panel.get("alerts") or []:
            alerts.append(_normalize_alert(
                alert_type="arbitrage",
                title=a.get("title") or "Arbitrage opportunity",
                body=a.get("display") or a.get("reason") or "",
                severity="watch",
                source_feature=429,
                payload=a,
            ))
    except Exception:
        pass
    return alerts


def _collect_risk_alerts() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    try:
        from bd_platform.capital_protection_controls import build_capital_awareness_panel

        panel = build_capital_awareness_panel()
        for a in (panel.get("portfolio_ai_alerts") or {}).get("alerts") or []:
            alerts.append(_normalize_alert(
                alert_type="risk",
                title="Portfolio risk",
                body=a.get("display") or "",
                severity=a.get("severity") or "watch",
                source_feature=410,
                payload=a,
            ))
    except Exception:
        pass
    return alerts


def _collect_whale_alerts() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    try:
        from bd_platform.smart_money_flow_tracker import build_smart_money_flow_panel

        panel = build_smart_money_flow_panel("BTC")
        analysis = panel.get("analysis") or panel
        if analysis.get("whale_label"):
            alerts.append(_normalize_alert(
                alert_type="whale",
                title=f"Whale signal · {analysis.get('asset', 'BTC')}",
                body=analysis.get("display") or analysis.get("whale_label") or "",
                severity="watch",
                source_feature=408,
                payload=analysis,
            ))
    except Exception:
        pass
    return alerts


def _collect_event_alerts() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    try:
        from bd_platform.event_sentiment_monitor import build_alerts

        panel = build_alerts(hours_ahead=72)
        for a in panel.get("alerts") or []:
            alerts.append(_normalize_alert(
                alert_type="events",
                title=a.get("title") or "Upcoming event",
                body=a.get("display") or a.get("summary") or "",
                severity=a.get("severity") or "info",
                source_feature=443,
                payload=a,
            ))
    except Exception:
        pass
    return alerts


def _collect_exchange_alerts() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    try:
        from bd_platform.exchange_health_monitor import build_portfolio_exchange_exposure_alerts

        panel = build_portfolio_exchange_exposure_alerts()
        for a in panel.get("alerts") or []:
            alerts.append(_normalize_alert(
                alert_type="exchange",
                title="Exchange health",
                body=a.get("display") or "",
                severity=a.get("severity") or "watch",
                source_feature=456,
                payload=a,
            ))
    except Exception:
        pass
    return alerts


def _collect_stablecoin_alerts() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    try:
        from bd_platform.stablecoin_health_monitor import build_portfolio_stablecoin_alerts

        panel = build_portfolio_stablecoin_alerts()
        for a in panel.get("alerts") or []:
            alerts.append(_normalize_alert(
                alert_type="stablecoin",
                title="Stablecoin exposure",
                body=a.get("display") or "",
                severity=a.get("severity") or "watch",
                source_feature=467,
                payload=a,
            ))
    except Exception:
        pass
    return alerts


def _collect_inbox_alerts() -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    try:
        from in_app_alerts import list_in_app_alerts

        for a in list_in_app_alerts(limit=20):
            alerts.append(_normalize_alert(
                alert_type="inbox",
                title=a.get("title") or "In-app alert",
                body=a.get("body") or "",
                severity=a.get("level") or "info",
                created_at=a.get("created_at"),
                alert_id=a.get("id"),
                payload=a.get("payload"),
            ))
            alerts[-1]["read"] = a.get("read", False)
    except Exception:
        pass
    return alerts


_COLLECTORS = {
    "arbitrage": _collect_arbitrage_alerts,
    "risk": _collect_risk_alerts,
    "whale": _collect_whale_alerts,
    "events": _collect_event_alerts,
    "exchange": _collect_exchange_alerts,
    "stablecoin": _collect_stablecoin_alerts,
    "inbox": _collect_inbox_alerts,
}


def build_unified_alert_feed(
    *,
    limit: int = 50,
    alert_type: str | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    all_alerts: list[dict[str, Any]] = []

    types = [alert_type] if alert_type and alert_type in _COLLECTORS else list(_COLLECTORS.keys())
    for t in types:
        all_alerts.extend(_COLLECTORS[t]())

    all_alerts.sort(key=lambda a: a.get("created_at") or "", reverse=True)
    feed = all_alerts[: max(1, min(limit, 100))]

    counts: dict[str, int] = {}
    for a in all_alerts:
        counts[a["alert_type"]] = counts.get(a["alert_type"], 0) + 1

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "alerts": feed,
        "count": len(feed),
        "total_collected": len(all_alerts),
        "counts_by_type": counts,
        "filter": alert_type,
        "available_types": list(_ALERT_TYPES),
        "sources": {
            "arbitrage": 429,
            "risk": 410,
            "whale": 408,
            "events": 443,
            "exchange": 456,
            "stablecoin": 467,
            "inbox": None,
        },
        "alerts_only": True,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def unified_alert_center_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "alert_types": list(_ALERT_TYPES),
        "source_count": 6,
        "timestamp": _utcnow(),
    }
