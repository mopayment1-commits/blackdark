"""Phase 8 — Runtime Verification & Observability."""

from __future__ import annotations

import logging
import os
from typing import Any

from compounding_common import utcnow

logger = logging.getLogger("BLACKDARK.RuntimeVerification")

_ALERT_THRESHOLDS = {
    "error_rate_percent": float(os.getenv("ALERT_ERROR_RATE_PERCENT", "5")),
    "latency_p95_ms": float(os.getenv("ALERT_LATENCY_P95_MS", "2000")),
}


async def verify_phase(phase: int) -> dict[str, Any]:
    verifiers = {
        1: _verify_phase_01,
        2: _verify_phase_02,
        3: _verify_phase_03,
        4: _verify_phase_04,
        5: _verify_phase_05,
        6: _verify_phase_06,
        7: _verify_phase_07,
        8: _verify_phase_08,
    }
    fn = verifiers.get(phase)
    if not fn:
        return {"phase": phase, "ok": False, "error": "unknown_phase"}
    try:
        result = await fn()
        result["phase"] = phase
        result["verified_at"] = utcnow()
        return result
    except Exception as exc:
        logger.exception("phase %s verify failed", phase)
        return {"phase": phase, "ok": False, "error": type(exc).__name__, "detail": str(exc)}


async def phase_verify_all() -> dict[str, Any]:
    results = []
    for p in range(1, 9):
        results.append(await verify_phase(p))
    return {
        "ok": all(r.get("ok") for r in results),
        "phases": results,
        "verified_at": utcnow(),
    }


async def alert_status() -> dict[str, Any]:
    from observability import observability_status

    status = observability_status()
    counters = status.get("counters") or {}
    requests = float(counters.get("http_requests_total") or 0)
    errors = float(counters.get("errors_total") or 0)
    error_rate = (errors / requests * 100.0) if requests else 0.0
    fired = error_rate > _ALERT_THRESHOLDS["error_rate_percent"]
    return {
        "thresholds": _ALERT_THRESHOLDS,
        "metrics": {"http_requests_total": requests, "errors_total": errors, "error_rate_percent": round(error_rate, 4)},
        "alert_fired": fired,
        "alert_reason": "error_rate_exceeded" if fired else None,
        "checked_at": utcnow(),
    }


async def _verify_phase_01() -> dict[str, Any]:
    from audit_registry import fetch_audit_logs

    rows = await fetch_audit_logs(limit=1)
    return {"ok": True, "proof": "audit_logs_readable", "sample_count": len(rows)}


async def _verify_phase_02() -> dict[str, Any]:
    from knowledge_graph import graph_stats

    stats = await graph_stats()
    return {"ok": True, "proof": "knowledge_graph_tables", "stats": stats}


async def _verify_phase_03() -> dict[str, Any]:
    from database import get_connection

    async with get_connection() as db:
        raw = await (await db.execute("SELECT COUNT(*) FROM market_signals")).fetchone()
    count = int(list(dict(raw).values())[0])
    return {"ok": True, "proof": "market_signals_table", "signal_rows": count}


async def _verify_phase_04() -> dict[str, Any]:
    from learning_compounding import accuracy_track_record

    track = await accuracy_track_record(limit=5)
    return {"ok": True, "proof": "learning_track_record", "oracle_resolved": track.get("oracle", {}).get("resolved_count", 0)}


async def _verify_phase_05() -> dict[str, Any]:
    from trust_compounding import list_evidence

    items = await list_evidence(limit=1)
    return {"ok": True, "proof": "trust_evidence_store", "evidence_rows": len(items)}


async def _verify_phase_06() -> dict[str, Any]:
    from distribution_compounding import analytics_summary

    summary = await analytics_summary(limit=1)
    return {"ok": True, "proof": "analytics_events", "total_events": summary.get("total_events", 0)}


async def _verify_phase_07() -> dict[str, Any]:
    from corporate_compounding import compliance_status

    status = await compliance_status()
    return {"ok": True, "proof": "compliance_status", "has_external_markers": bool(status.get("external_dependencies"))}


async def _verify_phase_08() -> dict[str, Any]:
    from observability import observability_status, prometheus_metrics_text

    metrics = prometheus_metrics_text()
    status = observability_status()
    alerts = await alert_status()
    return {
        "ok": bool(metrics) and bool(status),
        "proof": "metrics_and_observability",
        "metrics_bytes": len(metrics),
        "structured_logging": bool(os.getenv("JSON_LOGS", "true").lower() in {"1", "true", "yes"}),
        "alerts": alerts,
    }
