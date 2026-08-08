"""
BLACKDARK — Uptime probe recorder for 99.99% SLA due diligence.

Records health-check outcomes locally; external monitors (UptimeRobot, Datadog)
should also ping /health/live on the sidecar port.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import config

ProbeResult = Literal["ok", "fail"]

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "data" / "uptime_probes.jsonl"
SLA_TARGET = 99.99
_MAX_RETENTION_DAYS = int(os.getenv("UPTIME_LOG_RETENTION_DAYS", "90"))


def record_probe(*, ok: bool, source: str = "internal", latency_ms: float | None = None) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": datetime.now(UTC).isoformat(),
        "result": "ok" if ok else "fail",
        "source": source,
        "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _load_recent_probes(max_age_sec: float | None = None) -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    cutoff = time.time() - (max_age_sec or _MAX_RETENTION_DAYS * 86400)
    rows: list[dict[str, Any]] = []
    for raw_line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            row = json.loads(stripped)
            ts = datetime.fromisoformat(str(row["ts"]))
            if ts.timestamp() >= cutoff:
                rows.append(row)
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            continue
    return rows


def uptime_stats(*, window_hours: float = 24.0) -> dict[str, Any]:
    probes = _load_recent_probes(max_age_sec=window_hours * 3600)
    total = len(probes)
    ok = sum(1 for p in probes if p.get("result") == "ok")
    fail = total - ok
    uptime_pct = round((ok / total) * 100, 4) if total else 100.0
    allowed_downtime_min = round((100 - SLA_TARGET) / 100 * window_hours * 60, 2)
    actual_downtime_min = round((fail / max(total, 1)) * window_hours * 60, 2)

    return {
        "sla_target_percent": SLA_TARGET,
        "window_hours": window_hours,
        "probes_total": total,
        "probes_ok": ok,
        "probes_fail": fail,
        "uptime_percent": uptime_pct,
        "meets_sla": uptime_pct >= SLA_TARGET if total >= 10 else None,
        "allowed_downtime_minutes": allowed_downtime_min,
        "estimated_downtime_minutes": actual_downtime_min,
        "log_path": str(LOG_PATH),
        "architecture": {
            "mode": os.getenv("SERVICE_MODE", "all"),
            "health_sidecar": f"port {int(os.getenv('HEALTH_PORT', '8180'))}/health/live",
            "ha_compose": "docker compose -f docker-compose.ha.yml up -d",
            "replicas": {
                "web": int(os.getenv("WEB_REPLICAS", "2")),
                "arbitrage": int(os.getenv("ARBITRAGE_REPLICAS", "2")),
            },
        },
        "external_monitoring": {
            "endpoint": "/health/live",
            "recommended_interval_sec": 60,
            "template": "config/uptime_monitor.example.json",
        },
    }


def ha_architecture_status() -> dict[str, Any]:
    import shutil

    compose_ha = ROOT / "docker-compose.ha.yml"
    nginx_conf = ROOT / "nginx" / "blackdark.conf"
    return {
        "high_availability_ready": compose_ha.exists() and nginx_conf.exists(),
        "components": {
            "load_balancer": "nginx (round-robin)",
            "web_replicas": 2,
            "arbitrage_replicas": 2,
            "redis": "shared cache + pub/sub",
            "postgres": "primary DB (Timescale)",
            "health_sidecar": "per-service liveness <10ms",
            "kafka": "event bus (optional scale path)",
        },
        "docker_compose_ha": str(compose_ha),
        "nginx_config": str(nginx_conf),
        "railway_replicas": int(os.getenv("RAILWAY_NUM_REPLICAS", "2")),
        "docker_available": shutil.which("docker") is not None,
        "data_dir": str(config.DATA_DIR),
    }
