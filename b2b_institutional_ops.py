"""B2B reporting / alert orchestration / SLA instrumentation (honest foundations)."""

from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_REPORTS = safe_data_file("b2b_reports.jsonl")
_ALERTS = safe_data_file("alert_orchestration.jsonl")
_SLA = safe_data_file("sla_events.jsonl")
_DATA_BASE = Path(__file__).resolve().parent / "data"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _append(path, row: dict[str, Any]) -> dict[str, Any]:
    p = ensure_under(path, _DATA_BASE)
    p.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def generate_committee_report(
    *,
    org_id: str,
    title: str,
    evidence_pack: dict[str, Any],
    actor: str,
) -> dict[str, Any]:
    row = {
        "report_id": f"rpt_{uuid.uuid4().hex[:12]}",
        "org_id": org_id,
        "title": title,
        "evidence_pack": evidence_pack,
        "actor": actor,
        "created_at": _utcnow(),
        "kind": "committee_evidence",
    }
    return _append(_REPORTS, row)


def _deliver_channel(channel: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch alert to a channel sink. Unknown channels fail closed.

    - inbox/pager/email/slack: durable local sink (operator MTA/chat connectors optional)
    - webhook: real HTTP POST when ALERT_WEBHOOK_URL is set; otherwise fail-closed
      (no simulated success)
    """
    import os
    import urllib.error
    import urllib.request

    channel = (channel or "").strip().lower()
    allowed = {"inbox", "pager", "webhook", "email", "slack"}
    if channel not in allowed:
        return {"delivered": False, "reason": "channel_unknown", "channel": channel}

    if channel == "webhook":
        url = (os.getenv("ALERT_WEBHOOK_URL") or "").strip()
        if not url:
            receipt = {
                "delivered": False,
                "channel": channel,
                "transport": "webhook",
                "reason": "ALERT_WEBHOOK_URL_unset_fail_closed",
                "delivered_at": _utcnow(),
            }
            delivery_path = ensure_under(_DATA_BASE / "alert_deliveries.jsonl", _DATA_BASE)
            _append(delivery_path, {**receipt, "alert_id": payload.get("alert_id")})
            return receipt
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "User-Agent": "BLACKDARK-Alert/1.0"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310 — operator URL
                status = getattr(resp, "status", 0) or 0
            ok = 200 <= int(status) < 300
            receipt = {
                "delivered": ok,
                "channel": channel,
                "transport": "http_webhook",
                "http_status": int(status),
                "reason": None if ok else f"http_{status}",
                "delivered_at": _utcnow(),
            }
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            receipt = {
                "delivered": False,
                "channel": channel,
                "transport": "http_webhook",
                "reason": f"webhook_error:{type(exc).__name__}",
                "delivered_at": _utcnow(),
            }
        delivery_path = ensure_under(_DATA_BASE / "alert_deliveries.jsonl", _DATA_BASE)
        _append(delivery_path, {**receipt, "alert_id": payload.get("alert_id")})
        return receipt

    # inbox = in-app durable delivery (true local product path).
    # pager/email/slack require connector env; otherwise accepted but not delivered.
    if channel == "inbox":
        receipt = {
            "delivered": True,
            "channel": channel,
            "transport": "in_app_inbox",
            "delivered_at": _utcnow(),
            "payload_digest": str(abs(hash(json.dumps(payload, sort_keys=True, default=str))) % 10**12),
        }
    else:
        connector_env = {
            "pager": "ALERT_PAGER_WEBHOOK_URL",
            "email": "ALERT_EMAIL_SMTP_URL",
            "slack": "ALERT_SLACK_WEBHOOK_URL",
        }.get(channel)
        connector = (os.getenv(connector_env) or "").strip() if connector_env else ""
        if not connector:
            receipt = {
                "delivered": False,
                "accepted": True,
                "channel": channel,
                "transport": "pending_connector",
                "reason": f"{connector_env}_unset",
                "delivered_at": _utcnow(),
            }
        else:
            # Connector URL present — attempt HTTP POST (same fail-closed contract as webhook).
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                connector,
                data=body,
                headers={"Content-Type": "application/json", "User-Agent": "BLACKDARK-Alert/1.0"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
                    status = getattr(resp, "status", 0) or 0
                ok = 200 <= int(status) < 300
                receipt = {
                    "delivered": ok,
                    "channel": channel,
                    "transport": f"http_{channel}",
                    "http_status": int(status),
                    "reason": None if ok else f"http_{status}",
                    "delivered_at": _utcnow(),
                }
            except (urllib.error.URLError, TimeoutError, ValueError) as exc:
                receipt = {
                    "delivered": False,
                    "channel": channel,
                    "transport": f"http_{channel}",
                    "reason": f"connector_error:{type(exc).__name__}",
                    "delivered_at": _utcnow(),
                }
    delivery_path = ensure_under(_DATA_BASE / "alert_deliveries.jsonl", _DATA_BASE)
    _append(delivery_path, {**receipt, "alert_id": payload.get("alert_id")})
    return receipt


def orchestrate_alert(
    *,
    org_id: str,
    severity: str,
    channel: str,
    message: str,
    dedupe_key: str,
) -> dict[str, Any]:
    severity = severity.lower()
    if severity not in {"low", "medium", "high", "critical"}:
        raise ValueError("invalid_severity")
    # Deduplicate recent identical keys
    existing = _tail(_ALERTS, limit=200)
    for row in reversed(existing):
        if row.get("org_id") == org_id and row.get("dedupe_key") == dedupe_key and row.get("status") in {
            "queued",
            "acked",
            "silenced",
            "delivered",
        }:
            return {**row, "deduplicated": True}
    priority = {"low": 4, "medium": 3, "high": 2, "critical": 1}[severity]
    row = {
        "alert_id": f"al_{uuid.uuid4().hex[:12]}",
        "org_id": org_id,
        "severity": severity,
        "priority": priority,
        "channel": channel,
        "message": message,
        "dedupe_key": dedupe_key,
        "created_at": _utcnow(),
        "status": "queued",
        "escalation": "pager" if severity in {"high", "critical"} else "inbox",
        "ack_required": severity in {"high", "critical"},
    }
    delivery = _deliver_channel(channel, row)
    row["delivery"] = delivery
    if delivery.get("delivered"):
        row["status"] = "delivered"
    elif delivery.get("accepted"):
        row["status"] = "accepted_pending_connector"
    else:
        row["status"] = "delivery_failed"
        row["gate"] = "fail_closed"
    return _append(_ALERTS, row)


def acknowledge_alert(alert_id: str, *, actor: str) -> dict[str, Any]:
    rows = _tail(_ALERTS, limit=500)
    for row in rows:
        if row.get("alert_id") == alert_id:
            row["status"] = "acked"
            row["acked_by"] = actor
            row["acked_at"] = _utcnow()
            return _append(_ALERTS, row)
    raise ValueError("alert_not_found")


def silence_alert(alert_id: str, *, actor: str, reason: str = "") -> dict[str, Any]:
    rows = _tail(_ALERTS, limit=500)
    for row in rows:
        if row.get("alert_id") == alert_id:
            row["status"] = "silenced"
            row["silenced_by"] = actor
            row["silence_reason"] = reason
            row["silenced_at"] = _utcnow()
            return _append(_ALERTS, row)
    raise ValueError("alert_not_found")


def _tail(path, limit: int = 100) -> list[dict[str, Any]]:
    p = ensure_under(path, _DATA_BASE)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:]


def record_sla_event(
    *,
    org_id: str,
    metric: str,
    value: float,
    target: float,
    unit: str = "ms",
) -> dict[str, Any]:
    ok = float(value) <= float(target)
    row = {
        "sla_id": f"sla_{uuid.uuid4().hex[:12]}",
        "org_id": org_id,
        "metric": metric,
        "value": float(value),
        "target": float(target),
        "unit": unit,
        "ok": ok,
        "breached": not ok,
        "created_at": _utcnow(),
        "ts_ms": int(time.time() * 1000),
    }
    return _append(_SLA, row)


def b2b_status() -> dict[str, Any]:
    return {
        "surface": "b2b_institutional_ops",
        "reporting": True,
        "alert_orchestration": True,
        "alert_delivery": True,
        "sla_instrumentation": True,
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "note": "Committee reports, alert queue+channel delivery receipts, SLA breach metrics.",
    }
