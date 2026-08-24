"""
Exchange Health Monitor — Feature #110 / #134 integration layer.

Withdrawal status alerts for exchanges — feeds Portfolio Risk (#109) and
Withdrawal Closure Alert (#123).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ExchangeHealthMonitor")

_SNAPSHOT_PATH = Path("data/exchange_health_snapshots.jsonl")
_ALERTS_PATH = Path("data/exchange_health_alerts.jsonl")

_WITHDRAWAL_CRITICAL = 50.0
_WITHDRAWAL_WARNING = 70.0
_HEALTH_CRITICAL = 40.0
_HEALTH_WARNING = 60.0

LEGAL_DISCLAIMER = (
    "Exchange Health Monitor provides operational risk signals only — not trading advice. "
    "Withdrawal restrictions may indicate insolvency risk, maintenance, or regulatory action. "
    "Not financial advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _read_snapshots() -> list[dict[str, Any]]:
    if not _SNAPSHOT_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in _SNAPSHOT_PATH.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        pass
    return rows


def _latest_per_exchange(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        ex_id = str(row.get("exchange_id") or "").lower()
        if not ex_id:
            continue
        prev = latest.get(ex_id)
        if not prev or str(row.get("timestamp") or "") >= str(prev.get("timestamp") or ""):
            latest[ex_id] = row
    return latest


def _withdrawal_status(withdrawal_score: float) -> str:
    if withdrawal_score < _WITHDRAWAL_CRITICAL:
        return "restricted"
    if withdrawal_score < _WITHDRAWAL_WARNING:
        return "degraded"
    return "normal"


def _alert_level(*, withdrawal: float, health_score: float, badge: str) -> str:
    badge_l = (badge or "").lower()
    if badge_l in {"blacklisted", "fraud"} or health_score < _HEALTH_CRITICAL:
        return "critical"
    if withdrawal < _WITHDRAWAL_CRITICAL or health_score < _HEALTH_WARNING:
        return "high"
    if withdrawal < _WITHDRAWAL_WARNING or badge_l == "caution":
        return "medium"
    return "low"


def _build_alert(exchange_id: str, snap: dict[str, Any]) -> dict[str, Any]:
    dims = snap.get("dimensions") or {}
    withdrawal = float(dims.get("withdrawal") or 100)
    health_score = float(snap.get("health_score") or 100)
    badge = str(snap.get("badge") or "Unknown")
    w_status = _withdrawal_status(withdrawal)
    level = _alert_level(withdrawal=withdrawal, health_score=health_score, badge=badge)

    headline = f"{exchange_id.title()}: withdrawals {w_status}"
    if level == "critical":
        headline = f"RED FLAG — {exchange_id.title()} withdrawal stress"
    elif level == "high":
        headline = f"{exchange_id.title()} withdrawals degraded"

    return {
        "exchange_id": exchange_id,
        "health_score": health_score,
        "badge": badge,
        "withdrawal_score": withdrawal,
        "withdrawal_status": w_status,
        "alert_level": level,
        "headline": headline,
        "timestamp": snap.get("timestamp") or _utcnow(),
        "integrates_feature_134": True,
        "serves_risk_management_109": True,
    }


def _platform_status_134() -> dict[str, Any]:
    try:
        from platform_universe import build_manifest_universe_block, exchanges_by_status

        ready = exchanges_by_status("ingestion_ready")
        block = build_manifest_universe_block()
        return {
            "ingestion_ready_count": len(ready),
            "coverage_percent": round(
                block.get("ingestion_ready_count", 0) / max(block.get("target_exchanges", 1), 1) * 100,
                1,
            ),
        }
    except Exception:
        return {"ingestion_ready_count": 0, "coverage_percent": 0}


def exchange_health_status(
    *,
    exchange_id: str | None = None,
    min_alert_level: str = "low",
) -> dict[str, Any]:
    t0 = time.perf_counter()
    rows = _read_snapshots()
    latest = _latest_per_exchange(rows)

    if exchange_id:
        key = exchange_id.lower().strip()
        snap = latest.get(key)
        if not snap:
            return {
                "ok": False,
                "error": "exchange_not_found",
                "exchange_id": key,
                "legal_disclaimer": LEGAL_DISCLAIMER,
                "sla_met": (time.perf_counter() - t0) <= 2.0,
            }
        return {
            "ok": True,
            "feature_id": 110,
            "alert": _build_alert(key, snap),
            "platform_status_134": _platform_status_134(),
            "legal_disclaimer": LEGAL_DISCLAIMER,
            "mode": "risk_signal_only",
            "sla_met": (time.perf_counter() - t0) <= 2.0,
            "timestamp": _utcnow(),
        }

    alerts = [_build_alert(ex_id, snap) for ex_id, snap in sorted(latest.items())]
    if min_alert_level != "low":
        levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        alerts = [a for a in alerts if levels.get(a["alert_level"], 0) >= levels.get(min_alert_level, 0)]

    return {
        "ok": True,
        "feature_id": 110,
        "exchange_count": len(alerts),
        "alerts": alerts,
        "platform_status_134": _platform_status_134(),
        "legal_disclaimer": LEGAL_DISCLAIMER,
        "mode": "risk_signal_only",
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }
