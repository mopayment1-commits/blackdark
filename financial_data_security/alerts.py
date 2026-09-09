"""Unusual access and bulk-export alerting."""

from __future__ import annotations

from typing import Any


def alert_bulk_export(*, actor: str, record_count: int, threshold: int = 100) -> dict[str, Any]:
    triggered = record_count >= threshold
    if triggered:
        try:
            from security_events import record_security_event

            record_security_event(
                event_type="bulk_financial_export",
                severity="high",
                detail={"actor": actor, "record_count": record_count},
            )
        except Exception:
            pass
    return {"triggered": triggered, "record_count": record_count, "threshold": threshold}


def alert_unusual_access(*, actor: str, action: str, risk_score: float, threshold: float = 0.8) -> dict[str, Any]:
    triggered = risk_score >= threshold
    if triggered:
        try:
            from security_events import record_security_event

            record_security_event(
                event_type="unusual_financial_access",
                severity="medium",
                detail={"actor": actor, "action": action, "risk_score": risk_score},
            )
        except Exception:
            pass
    return {"triggered": triggered, "risk_score": risk_score}
