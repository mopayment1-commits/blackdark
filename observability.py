"""
BLACKDARK — Observability (Sentry + Prometheus metrics + structured JSON logging).
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

logger = logging.getLogger("BLACKDARK.Observability")

_metrics: dict[str, float] = {
    "http_requests_total": 0,
    "oracle_queries_total": 0,
    "arbitrage_scans_total": 0,
    "auth_logins_total": 0,
    "behavior_events_total": 0,
    "errors_total": 0,
}


class JsonLogFormatter(logging.Formatter):
    """Emit structured JSON logs to stdout for institutional observability."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_structured_logging() -> dict[str, Any]:
    enabled = os.getenv("JSON_LOGS", "true").strip().lower() in {"1", "true", "yes"}
    if not enabled:
        return {"structured_json_logging": False}
    root = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    return {"structured_json_logging": True}


def init_sentry() -> dict[str, Any]:
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        return {"enabled": False, "reason": "SENTRY_DSN not set"}
    try:
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=dsn,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            environment=os.getenv("ENV", os.getenv("RAILWAY_ENVIRONMENT", "development")),
            integrations=[LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)],
        )
        logger.info("Sentry initialized")
        return {"enabled": True}
    except Exception as exc:
        logger.warning("Sentry init failed: %s", exc)
        return {"enabled": False, "error": str(exc)}


def increment_metric(name: str, amount: float = 1.0) -> None:
    if name not in _metrics:
        _metrics[name] = 0.0
    _metrics[name] += amount


def prometheus_metrics_text() -> str:
    lines = [
        "# HELP blackdark_up BLACKDARK process up",
        "# TYPE blackdark_up gauge",
        "blackdark_up 1",
    ]
    for key, value in sorted(_metrics.items()):
        metric = f"blackdark_{key}"
        lines.append(f"# TYPE {metric} counter")
        lines.append(f"{metric} {value}")
    lines.append(f"blackdark_process_uptime_seconds {time.time():.0f}")
    return "\n".join(lines) + "\n"


def observability_status() -> dict[str, Any]:
    return {
        "sentry_configured": bool(os.getenv("SENTRY_DSN", "").strip()),
        "metrics_endpoint": "/metrics",
        "counters": dict(_metrics),
    }
