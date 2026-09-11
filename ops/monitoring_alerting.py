"""Post-deploy monitoring — uptime, latency, errors, instant operator alerts."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("BLACKDARK.Monitoring")

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / "data" / "monitoring_alert_state.json"
_ALERT_COOLDOWN_SEC = int(os.getenv("MONITORING_ALERT_COOLDOWN_SEC", "300"))
_LATENCY_WARN_MS = float(os.getenv("MONITORING_LATENCY_WARN_MS", "2000"))
_LATENCY_FAIL_MS = float(os.getenv("MONITORING_LATENCY_FAIL_MS", "5000"))


def _base_url() -> str:
    return (
        os.getenv("MONITORING_BASE_URL")
        or os.getenv("PUBLIC_BASE_URL")
        or f"http://127.0.0.1:{os.getenv('PORT', '8080')}"
    ).rstrip("/")


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"consecutive_failures": 0, "last_alert_ts": 0}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"consecutive_failures": 0, "last_alert_ts": 0}


def _save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


async def _send_ops_alert(title: str, body: str) -> dict[str, Any]:
    """Dispatch to Telegram ops chat and optional webhook."""
    results: dict[str, Any] = {"telegram": False, "webhook": False}
    text = f"🚨 {title}\n\n{body}"
    try:
        from alert_service import send_telegram_message

        chat = os.getenv("OPS_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if token and chat:
            await send_telegram_message(text, chat_id=chat)
            results["telegram"] = True
    except Exception:
        logger.exception("Telegram ops alert failed")

    webhook = os.getenv("MONITORING_WEBHOOK_URL", "").strip()
    if webhook:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    webhook,
                    json={"title": title, "body": body, "ts": datetime.now(UTC).isoformat()},
                )
                results["webhook"] = resp.status_code < 400
        except Exception:
            logger.exception("Monitoring webhook failed")
    return results


async def probe_endpoints() -> dict[str, Any]:
    """Probe live + ready; record uptime; alert on failure or high latency."""
    from uptime_monitor import record_probe

    base = _base_url()
    probes: list[dict[str, Any]] = []
    overall_ok = True

    for path, label in (("/health/live", "live"), ("/health/ready", "ready")):
        url = f"{base}{path}"
        t0 = time.perf_counter()
        row: dict[str, Any] = {"endpoint": path, "url": url, "ok": False}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
            latency = (time.perf_counter() - t0) * 1000
            row["status_code"] = resp.status_code
            row["latency_ms"] = round(latency, 2)
            row["ok"] = resp.status_code == 200
            if label == "live":
                slow = latency >= _LATENCY_WARN_MS
                row["slow"] = slow
                if latency >= _LATENCY_FAIL_MS:
                    row["ok"] = False
                    row["reason"] = "latency_threshold_exceeded"
        except Exception as exc:
            row["error"] = str(exc)
            row["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        probes.append(row)
        if not row.get("ok"):
            overall_ok = False
        record_probe(ok=bool(row.get("ok")), source=f"monitor_{label}", latency_ms=row.get("latency_ms"))

    state = _load_state()
    if overall_ok:
        state["consecutive_failures"] = 0
    else:
        state["consecutive_failures"] = int(state.get("consecutive_failures", 0)) + 1

    now = time.time()
    should_alert = (
        state["consecutive_failures"] >= int(os.getenv("MONITORING_FAIL_THRESHOLD", "2"))
        and (now - float(state.get("last_alert_ts") or 0)) >= _ALERT_COOLDOWN_SEC
    )
    alert_result = None
    if should_alert:
        failed = [p for p in probes if not p.get("ok")]
        body = json.dumps(failed, indent=2)[:1500]
        alert_result = await _send_ops_alert("BLACKDARK monitoring alert", body)
        state["last_alert_ts"] = now
    _save_state(state)

    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "base_url": base,
        "overall_ok": overall_ok,
        "probes": probes,
        "consecutive_failures": state["consecutive_failures"],
        "alert_sent": bool(alert_result),
        "alert_channels": alert_result,
        "thresholds": {
            "latency_warn_ms": _LATENCY_WARN_MS,
            "latency_fail_ms": _LATENCY_FAIL_MS,
            "fail_threshold": int(os.getenv("MONITORING_FAIL_THRESHOLD", "2")),
        },
    }


async def monitoring_status() -> dict[str, Any]:
    from uptime_monitor import uptime_stats

    stats = uptime_stats(window_hours=24.0)
    state = _load_state()
    return {
        "enabled": os.getenv("MONITORING_ENABLED", "true").lower() in {"1", "true", "yes"},
        "uptime_24h": stats,
        "alert_state": state,
        "ops_telegram_configured": bool(
            os.getenv("TELEGRAM_BOT_TOKEN") and (os.getenv("OPS_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID"))
        ),
        "webhook_configured": bool(os.getenv("MONITORING_WEBHOOK_URL")),
        "external_recommended": "UptimeRobot / Better Stack → /health/live every 60s",
    }


_monitor_task: asyncio.Task | None = None


async def _loop() -> None:
    interval = max(30, int(os.getenv("MONITORING_INTERVAL_SEC", "60")))
    logger.info("Monitoring loop started | interval=%ss | base=%s", interval, _base_url())
    while True:
        try:
            await probe_endpoints()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Monitoring probe cycle failed")
        await asyncio.sleep(interval)


def start_monitoring_loop() -> asyncio.Task | None:
    global _monitor_task
    if os.getenv("MONITORING_ENABLED", "true").lower() not in {"1", "true", "yes"}:
        return None
    if _monitor_task is not None and not _monitor_task.done():
        return _monitor_task
    _monitor_task = asyncio.create_task(_loop(), name="monitoring-alerting")
    return _monitor_task
