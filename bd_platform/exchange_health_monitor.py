"""
Exchange Health Monitor — Features #110 + #134 + unified Trust Layer (#132).

Platform status: API, withdrawal, deposit, trading — real-time + historical.
Merged with Exchange Quality Score (#132) in the same interface.
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
_WITHDRAWAL_HISTORY_PATH = Path("data/withdrawal_closure_snapshots.jsonl")

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


def _withdrawal_history_summary(exchange_id: str, *, months: int = 6) -> dict[str, Any]:
    """Historical withdrawal suspensions for #134."""
    from datetime import timedelta

    cutoff = datetime.now(UTC) - timedelta(days=months * 30)
    suspensions: list[str] = []
    if not _WITHDRAWAL_HISTORY_PATH.exists():
        return {"suspension_count_6mo": 0, "events": [], "summary": "No suspension history recorded"}

    try:
        for line in _WITHDRAWAL_HISTORY_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("exchange_id") or "").lower() != exchange_id.lower():
                continue
            ts = str(row.get("timestamp") or "")
            try:
                when = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except ValueError:
                continue
            if when < cutoff:
                continue
            status = str(row.get("withdrawal_status") or "").lower()
            if status in {"closed", "suspended", "restricted"}:
                suspensions.append(ts)
    except (OSError, json.JSONDecodeError):
        pass

    count = len(suspensions)
    summary = f"No withdrawal suspensions in last {months} months"
    if count == 1:
        summary = f"Withdrawals suspended 1x in last {months} months"
    elif count > 1:
        summary = f"Withdrawals suspended {count}x in last {months} months"

    return {
        "suspension_count_6mo": count,
        "events": suspensions[-5:],
        "summary": summary,
        "summary_ar": (
            f"لا إيقاف للسحب خلال {months} أشهر"
            if count == 0
            else f"السحب مُعلّق {count} مرات خلال {months} أشهر"
        ),
    }


def _build_platform_status(exchange_id: str, snap: dict[str, Any]) -> dict[str, Any]:
    """#134 — real-time platform status block."""
    dims = snap.get("dimensions") or {}
    operational = float(dims.get("operational") or 100)
    withdrawal = float(dims.get("withdrawal") or 100)
    w_status = _withdrawal_status(withdrawal)
    history = _withdrawal_history_summary(exchange_id)

    api_status = "up" if operational >= 50 else "degraded" if operational >= 20 else "down"
    withdrawal_status = {
        "normal": "open",
        "degraded": "partial",
        "restricted": "closed",
    }.get(w_status, "unknown")

    # Deposit follows withdrawal health proxy when no dedicated signal
    deposit_status = "open" if withdrawal >= 70 else "partial" if withdrawal >= 40 else "closed"
    trading_status = "active" if operational >= 40 and withdrawal >= 30 else "suspended"

    headline = f"{exchange_id.title()}: API {api_status}, withdrawals {withdrawal_status}"
    if history["suspension_count_6mo"] > 0:
        headline += f" — {history['summary']}"

    return {
        "feature_id": 134,
        "exchange_id": exchange_id,
        "api_status": api_status,
        "withdrawal_status": withdrawal_status,
        "deposit_status": deposit_status,
        "trading_status": trading_status,
        "operational_score": operational,
        "withdrawal_score": withdrawal,
        "history": history,
        "headline": headline,
        "real_time": True,
        "timestamp": snap.get("timestamp") or _utcnow(),
    }


def exchange_trust_dashboard(
    *,
    exchange_id: str | None = None,
) -> dict[str, Any]:
    """Unified #132 + #134 interface — quality score + platform status."""
    from bd_platform.exchange_quality_score import compute_quality_score, score_all_exchanges, score_exchange

    t0 = time.perf_counter()
    rows = _read_snapshots()
    latest = _latest_per_exchange(rows)

    if exchange_id:
        quality = score_exchange(exchange_id)
        key = exchange_id.lower().strip()
        snap = latest.get(key)
        platform = _build_platform_status(key, snap) if snap else None
        elapsed = time.perf_counter() - t0
        return {
            "ok": quality.get("ok", False),
            "features": ["#132", "#134", "#110"],
            "surface": "exchange_trust_dashboard",
            "exchange_id": key,
            "quality_score": quality.get("quality"),
            "platform_status": platform,
            "legal_disclaimer": LEGAL_DISCLAIMER,
            "methodology_transparent": True,
            "sla_met": elapsed <= 2.0,
            "timestamp": _utcnow(),
        }

    all_quality = score_all_exchanges()
    exchanges: list[dict[str, Any]] = []
    for item in all_quality.get("exchanges", []):
        ex_id = str(item.get("exchange_id") or "")
        snap = latest.get(ex_id)
        exchanges.append(
            {
                **item,
                "platform_status": _build_platform_status(ex_id, snap) if snap else None,
            }
        )

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "features": ["#132", "#134", "#110"],
        "surface": "exchange_trust_dashboard",
        "exchange_count": len(exchanges),
        "exchanges": exchanges,
        "methodology": all_quality.get("methodology"),
        "platform_status_134": _platform_status_134(),
        "legal_disclaimer": LEGAL_DISCLAIMER,
        "mode": "trust_layer",
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


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
            "platform_status": _build_platform_status(key, snap),
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

    platform_rows = [_build_platform_status(ex_id, snap) for ex_id, snap in sorted(latest.items())]

    return {
        "ok": True,
        "feature_id": 110,
        "exchange_count": len(alerts),
        "alerts": alerts,
        "platform_statuses": platform_rows,
        "platform_status_134": _platform_status_134(),
        "legal_disclaimer": LEGAL_DISCLAIMER,
        "mode": "risk_signal_only",
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }
