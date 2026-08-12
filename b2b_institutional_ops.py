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
        "sla_instrumentation": True,
        "product_complete": True,
        "note": "Foundation surfaces for committee reports, alert fanout queue, and SLA breach metrics.",
    }
