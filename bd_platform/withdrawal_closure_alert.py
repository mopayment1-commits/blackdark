"""
Withdrawal Closure Alert — Feature #123 (Risk Signal, Sprint 2 — highest priority).

Per-asset withdrawal suspension alerts integrated with:
  - Portfolio Risk Management (#109)
  - Exchange Health Monitor (#110)
  - Exchange Platform Status (#134)

Example:
  "Binance suspended withdrawals for TOKEN — classification: elevated risk (not maintenance).
   Action: reduce exposure — verify official announcements."
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.WithdrawalClosure")

_SNAPSHOT_PATH = Path("data/withdrawal_closure_snapshots.jsonl")
_ALERTS_PATH = Path("data/withdrawal_closure_alerts.jsonl")
_KNOWN_PATH = Path("data/withdrawal_closure_known.json")
_CACHE_PATH = Path("data/withdrawal_closure_cache.json")

_DISCLAIMER = (
    "Withdrawal closure alerts are risk signals — not trading advice. "
    "Temporary maintenance and insolvency-driven freezes can look similar early on. "
    "Always verify on official exchange channels. BLACKDARK cannot guarantee fund safety."
)

_CACHE_TTL_SEC = 300


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_known() -> dict[str, Any]:
    if not _KNOWN_PATH.exists():
        return {"assets": {}}
    try:
        return json.loads(_KNOWN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"assets": {}}


def _save_known(data: dict[str, Any]) -> None:
    _KNOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _utcnow()
    _KNOWN_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _append_snapshot(row: dict[str, Any]) -> None:
    _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _SNAPSHOT_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _append_alert(row: dict[str, Any]) -> None:
    _ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _ALERTS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _cache_get() -> dict[str, Any] | None:
    if not _CACHE_PATH.exists():
        return None
    try:
        blob = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        if float(blob.get("expires_at", 0)) > time.time():
            return blob.get("payload")
    except (OSError, json.JSONDecodeError, TypeError):
        pass
    return None


def _cache_set(payload: dict[str, Any]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        json.dumps({"expires_at": time.time() + _CACHE_TTL_SEC, "payload": payload}, indent=2),
        encoding="utf-8",
    )


def classify_closure(
    *,
    exchange_id: str,
    asset: str,
    withdrawal_score: float,
    health_score: float,
    badge: str,
    duration_minutes: float | None = None,
) -> dict[str, Any]:
    """Distinguish maintenance vs dangerous closure."""
    badge_l = (badge or "").lower()
    if duration_minutes is not None and duration_minutes < 90 and withdrawal_score >= 40:
        classification = "likely_maintenance"
        confidence = 0.78
        analysis = (
            "Short-duration suspension with moderate exchange health — "
            "may be scheduled maintenance. Still verify official status page."
        )
        alert_level = "medium"
    elif badge_l in {"blacklisted", "fraud"} or health_score < 40:
        classification = "dangerous_closure"
        confidence = 0.94
        analysis = (
            "Exchange health critically degraded — pattern consistent with "
            "insolvency or regulatory freeze (FTX-class risk). Treat as urgent."
        )
        alert_level = "critical"
    elif withdrawal_score < 30 or health_score < 55:
        classification = "elevated_risk"
        confidence = 0.88
        analysis = (
            "Withdrawal restriction with poor exchange health — not typical short maintenance. "
            "Reduce exposure and avoid new deposits."
        )
        alert_level = "high"
    else:
        classification = "uncertain"
        confidence = 0.72
        analysis = (
            "Withdrawal paused — insufficient data to classify. "
            "Monitor official announcements and #134 platform status."
        )
        alert_level = "medium"

    return {
        "classification": classification,
        "confidence": confidence,
        "analysis": analysis,
        "alert_level": alert_level,
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


def _exchange_health_context(exchange_id: str) -> dict[str, Any]:
    try:
        from bd_platform.exchange_health_monitor import exchange_health_status

        return exchange_health_status(exchange_id=exchange_id)
    except Exception:
        return {}


def _portfolio_risk_hook(exchange_id: str, asset: str, alert_level: str) -> dict[str, Any]:
    """Lightweight #109 integration hook."""
    return {
        "feature": "#109",
        "action": "review_portfolio_exposure",
        "exchange_id": exchange_id,
        "asset": asset,
        "urgency": alert_level,
        "message": (
            f"Review {asset} exposure on {exchange_id.title()} — withdrawal closure detected"
            if alert_level in {"high", "critical"}
            else f"Monitor {asset} on {exchange_id.title()}"
        ),
    }


def record_withdrawal_closure(
    *,
    exchange_id: str,
    asset: str,
    withdrawal_score: float = 20.0,
    health_score: float = 45.0,
    badge: str = "caution",
    duration_minutes: float | None = None,
) -> dict[str, Any]:
    """Record and alert on per-asset withdrawal closure."""
    t0 = time.perf_counter()
    ex = exchange_id.lower().strip()
    sym = asset.upper().strip()
    key = f"{ex}:{sym}"

    known = _load_known()
    assets = known.setdefault("assets", {})
    prev = assets.get(key, {}).get("status")
    assets[key] = {"status": "withdrawal_closed", "updated_at": _utcnow()}
    _save_known(known)

    classification = classify_closure(
        exchange_id=ex,
        asset=sym,
        withdrawal_score=withdrawal_score,
        health_score=health_score,
        badge=badge,
        duration_minutes=duration_minutes,
    )

    headline = (
        f"{ex.title()} suspended withdrawals for {sym} — "
        f"classification: {classification['classification'].replace('_', ' ')}. "
        f"{classification['analysis']}"
    )

    alert = {
        "feature_id": 123,
        "exchange_id": ex,
        "asset": sym,
        "withdrawal_status": "closed",
        "withdrawal_score": withdrawal_score,
        "health_score": health_score,
        "badge": badge,
        "previous_status": prev,
        "headline": headline,
        "classification": classification["classification"],
        "confidence": classification["confidence"],
        "analysis": classification["analysis"],
        "alert_level": classification["alert_level"],
        "portfolio_risk": _portfolio_risk_hook(ex, sym, classification["alert_level"]),
        "platform_status_134": _platform_status_134(),
        "exchange_health_110": _exchange_health_context(ex),
        "mode": "risk_signal_only",
        "timestamp": _utcnow(),
    }
    _append_snapshot(alert)
    if classification["alert_level"] in {"medium", "high", "critical"}:
        _append_alert(alert)

    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        **alert,
        "disclaimer": _DISCLAIMER,
        "sla_met": elapsed <= 2.0,
        "latency_ms": round(elapsed * 1000, 1),
    }


def scan_withdrawal_closures(*, limit: int = 50) -> dict[str, Any]:
    """Return recent withdrawal closure alerts (#123)."""
    t0 = time.perf_counter()
    cached = _cache_get()
    if cached:
        out = dict(cached)
        out["cache_hit"] = True
        out["sla_met"] = (time.perf_counter() - t0) <= 2.0
        return out

    alerts: list[dict[str, Any]] = []
    if _ALERTS_PATH.exists():
        try:
            for line in reversed(_ALERTS_PATH.read_text(encoding="utf-8").splitlines()):
                if line.strip():
                    alerts.append(json.loads(line))
                if len(alerts) >= limit:
                    break
        except (OSError, json.JSONDecodeError):
            pass

    critical = [a for a in alerts if a.get("alert_level") in {"high", "critical"}]
    summary = "No active per-asset withdrawal closures in feed"
    if critical:
        summary = (
            f"{len(critical)} high-priority withdrawal closure(s) — "
            "review portfolio risk (#109) immediately"
        )

    elapsed = time.perf_counter() - t0
    out = {
        "ok": True,
        "feature_id": 123,
        "product_name": "Withdrawal Closure Alert",
        "surface": "risk_signal",
        "integrated_features": ["#109", "#110", "#134"],
        "summary": summary,
        "alert_count": len(alerts),
        "critical_count": len(critical),
        "alerts": alerts,
        "disclaimer": _DISCLAIMER,
        "mode": "risk_signal_only",
        "cache_hit": False,
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }
    _cache_set(out)
    return out


def enrich_portfolio_risk(payload: dict[str, Any], closures: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["withdrawal_closure_alerts"] = {
        "enabled": closures.get("ok", False),
        "critical_count": closures.get("critical_count", 0),
        "alerts": closures.get("alerts", [])[:5],
        "disclaimer": _DISCLAIMER,
    }
    return out
