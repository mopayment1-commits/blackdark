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
_SLA_MIN_PROBES = int(os.getenv("MONITORING_SLA_MIN_PROBES", "10"))


def _base_url() -> str:
    return (
        os.getenv("MONITORING_BASE_URL")
        or os.getenv("PUBLIC_BASE_URL")
        or os.getenv("APP_BASE_URL")
        or f"http://127.0.0.1:{os.getenv('PORT', '8080')}"
    ).rstrip("/")


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"consecutive_failures": 0, "last_alert_ts": 0, "last_signal_alerts": {}}
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"consecutive_failures": 0, "last_alert_ts": 0, "last_signal_alerts": {}}


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


async def _maybe_alert_signal(
    state: dict[str, Any],
    *,
    signal_key: str,
    fired: bool,
    title: str,
    body: str,
) -> dict[str, Any] | None:
    """Cooldown per signal type (error_rate, sla_breach, vendor_throttle)."""
    if not fired:
        return None
    now = time.time()
    last_signals = state.setdefault("last_signal_alerts", {})
    last_ts = float(last_signals.get(signal_key) or 0)
    if (now - last_ts) < _ALERT_COOLDOWN_SEC:
        return None
    result = await _send_ops_alert(title, body)
    last_signals[signal_key] = now
    return result


async def check_health_signals() -> dict[str, Any]:
    """Non-HTTP health signals: error rate, SLA, vendor throttling."""
    from runtime_verification import alert_status
    from uptime_monitor import uptime_stats

    error = await alert_status()
    uptime = uptime_stats(window_hours=24.0)
    vendor: dict[str, Any] = {}
    try:
        from ops.vendor_rate_limit_watchdog import should_alert_vendor_throttle, vendor_rate_limit_status

        vendor = vendor_rate_limit_status()
        vendor_alert, vendor_reason = should_alert_vendor_throttle()
    except Exception as exc:
        vendor_alert, vendor_reason = False, None
        vendor = {"error": str(exc)}

    sla_breach = (
        uptime.get("meets_sla") is False
        and int(uptime.get("probes_total") or 0) >= _SLA_MIN_PROBES
    )
    slow_probe = False
    try:
        from observability import observability_status

        counters = (observability_status().get("counters") or {})
        slow = float(counters.get("very_slow_requests_total") or 0)
        slow_probe = slow > 0 and float(counters.get("http_requests_total") or 0) > 50
    except Exception:
        pass

    return {
        "error_rate": error,
        "uptime_24h": uptime,
        "vendor_rate_limits": vendor,
        "signals": {
            "error_rate_alert": bool(error.get("alert_fired")),
            "sla_breach": sla_breach,
            "vendor_throttle": vendor_alert,
            "vendor_throttle_reason": vendor_reason,
            "slow_requests": slow_probe,
        },
    }


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
    alert_results: list[dict[str, Any]] = []
    if should_alert:
        failed = [p for p in probes if not p.get("ok")]
        body = json.dumps(failed, indent=2)[:1500]
        result = await _send_ops_alert("BLACKDARK monitoring alert — endpoint failure", body)
        alert_results.append({"type": "endpoint_failure", "channels": result})
        state["last_alert_ts"] = now

    signals = await check_health_signals()
    sig = signals.get("signals") or {}
    if sig.get("error_rate_alert"):
        metrics = (signals.get("error_rate") or {}).get("metrics") or {}
        body = (
            f"Error rate {metrics.get('error_rate_percent')}% exceeds threshold.\n"
            f"Requests: {metrics.get('http_requests_total')} Errors: {metrics.get('errors_total')}"
        )
        r = await _maybe_alert_signal(state, signal_key="error_rate", fired=True, title="BLACKDARK — high error rate", body=body)
        if r:
            alert_results.append({"type": "error_rate", "channels": r})

    if sig.get("sla_breach"):
        uptime = signals.get("uptime_24h") or {}
        body = (
            f"24h uptime {uptime.get('uptime_percent')}% below SLA {uptime.get('sla_target_percent')}%.\n"
            f"Fails: {uptime.get('probes_fail')} / {uptime.get('probes_total')}"
        )
        r = await _maybe_alert_signal(state, signal_key="sla_breach", fired=True, title="BLACKDARK — SLA breach", body=body)
        if r:
            alert_results.append({"type": "sla_breach", "channels": r})

    if sig.get("vendor_throttle"):
        vendor = signals.get("vendor_rate_limits") or {}
        body = json.dumps(vendor.get("signals") or vendor, indent=2)[:1500]
        r = await _maybe_alert_signal(
            state,
            signal_key="vendor_throttle",
            fired=True,
            title=f"BLACKDARK — vendor rate limit ({sig.get('vendor_throttle_reason')})",
            body=body,
        )
        if r:
            alert_results.append({"type": "vendor_throttle", "channels": r})

    _save_state(state)

    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "base_url": base,
        "overall_ok": overall_ok and not any(
            sig.get(k) for k in ("error_rate_alert", "sla_breach", "vendor_throttle")
        ),
        "probes": probes,
        "health_signals": signals,
        "consecutive_failures": state["consecutive_failures"],
        "alerts_sent": alert_results,
        "thresholds": {
            "latency_warn_ms": _LATENCY_WARN_MS,
            "latency_fail_ms": _LATENCY_FAIL_MS,
            "fail_threshold": int(os.getenv("MONITORING_FAIL_THRESHOLD", "2")),
            "alert_cooldown_sec": _ALERT_COOLDOWN_SEC,
        },
    }


async def monitoring_status() -> dict[str, Any]:
    from uptime_monitor import uptime_stats

    stats = uptime_stats(window_hours=24.0)
    state = _load_state()
    signals = await check_health_signals()
    ops_telegram = bool(
        os.getenv("TELEGRAM_BOT_TOKEN") and (os.getenv("OPS_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID"))
    )
    return {
        "enabled": os.getenv("MONITORING_ENABLED", "true").lower() in {"1", "true", "yes"},
        "uptime_24h": stats,
        "health_signals": signals,
        "alert_state": state,
        "ops_telegram_configured": ops_telegram,
        "webhook_configured": bool(os.getenv("MONITORING_WEBHOOK_URL")),
        "sentry_configured": bool(os.getenv("SENTRY_DSN")),
        "external_recommended": "UptimeRobot / Better Stack → /health/live every 60s",
        "setup_script": "python3 scripts/setup_monitoring.py",
        "rate_limit_audit": "python3 scripts/free_api_rate_limit_audit.py",
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
