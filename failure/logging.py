"""Structured failure logging with secret redaction (ERR-021, ERR-022)."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

from safe_errors import public_error

logger = logging.getLogger("BLACKDARK.Failure")

_REDACT = re.compile(
    r"(password|api[_-]?key|secret|token|otp|refresh|session|recovery|private[_-]?key|"
    r"authorization:\s*bearer\s+\S+|stripe[_-]?sk|postgres://|redis://)",
    re.IGNORECASE,
)


def redact_payload(value: Any) -> Any:
    if isinstance(value, str):
        return _REDACT.sub("[REDACTED]", value)
    if isinstance(value, dict):
        return {k: redact_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_payload(v) for v in value]
    return value


def log_failure(
    *,
    correlation_id: str,
    component: str,
    operation: str,
    failure_class: str,
    certainty: str,
    severity: str,
    user_impact: str,
    message_key: str | None = None,
    retry_count: int = 0,
    dependency: str | None = None,
    latency_ms: float | None = None,
    source: str | None = None,
    fallback_used: bool = False,
    resolution: str | None = None,
    exc: BaseException | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = redact_payload(
        {
            "correlation_id": correlation_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "component": component,
            "operation": operation,
            "failure_class": failure_class,
            "certainty": certainty,
            "severity": severity,
            "user_impact": user_impact,
            "retry_count": retry_count,
            "dependency": dependency,
            "latency_ms": latency_ms,
            "source": source,
            "fallback_used": fallback_used,
            "message_key": message_key,
            "resolution": resolution,
            "extra": extra or {},
        }
    )
    msg = public_error(exc, fallback=operation, log=False) if exc else operation
    logger.log(
        _severity_to_level(severity),
        "failure_event %s",
        json.dumps(record, ensure_ascii=False),
        exc_info=exc is not None and severity in {"ERROR", "CRITICAL"},
    )
    return record


def _severity_to_level(severity: str) -> int:
    return {
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }.get(severity.upper(), logging.ERROR)
