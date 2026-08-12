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
    row = {
        "alert_id": f"al_{uuid.uuid4().hex[:12]}",
        "org_id": org_id,
        "severity": severity,
        "channel": channel,
        "message": message,
        "dedupe_key": dedupe_key,
        "created_at": _utcnow(),
        "status": "queued",
    }
    return _append(_ALERTS, row)


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
