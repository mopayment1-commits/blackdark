"""
InfluxDB time-series adapter for BLACKDARK ETL (#118).

Writes market/on-chain metrics to InfluxDB when configured; falls back to local JSONL
so the pipeline works in dev without Influx running.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.InfluxTS")

_FALLBACK_PATH = Path("data/etl/timeseries_fallback.jsonl")
_CLIENT: Any = None


def enabled() -> bool:
    url = (getattr(config, "INFLUXDB_URL", None) or "").strip()
    return bool(url)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _client() -> Any | None:
    global _CLIENT
    if not enabled():
        return None
    if _CLIENT is not None:
        return _CLIENT
    try:
        from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

        _CLIENT = InfluxDBClientAsync(
            url=config.INFLUXDB_URL,
            token=config.INFLUXDB_TOKEN,
            org=config.INFLUXDB_ORG,
        )
        return _CLIENT
    except Exception as exc:
        logger.warning("InfluxDB client unavailable: %s", exc)
        return None


def _append_fallback(row: dict[str, Any]) -> None:
    _FALLBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _FALLBACK_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


async def write_point(
    measurement: str,
    *,
    tags: dict[str, str] | None = None,
    fields: dict[str, float | int | str | bool],
    timestamp_ns: int | None = None,
) -> dict[str, Any]:
    """Write one time-series point; returns backend used."""
    tags = tags or {}
    ts = timestamp_ns or int(time.time() * 1_000_000_000)
    row = {
        "measurement": measurement,
        "tags": tags,
        "fields": fields,
        "timestamp_ns": ts,
        "written_at": _utcnow(),
    }

    client = await _client()
    if client is None:
        _append_fallback(row)
        return {"ok": True, "backend": "jsonl_fallback", "path": str(_FALLBACK_PATH)}

    try:
        from influxdb_client import Point
        from influxdb_client.client.write_api import ASYNCHRONOUS

        point = Point(measurement)
        for k, v in tags.items():
            point = point.tag(k, str(v))
        for k, v in fields.items():
            if isinstance(v, bool):
                point = point.field(k, v)
            elif isinstance(v, int):
                point = point.field(k, float(v))
            else:
                point = point.field(k, v)
        point = point.time(ts)

        write_api = client.write_api(write_options=ASYNCHRONOUS)
        await write_api.write(bucket=config.INFLUXDB_BUCKET, org=config.INFLUXDB_ORG, record=point)
        return {"ok": True, "backend": "influxdb", "measurement": measurement}
    except Exception as exc:
        logger.warning("Influx write failed, using fallback: %s", exc)
        _append_fallback(row)
        return {"ok": True, "backend": "jsonl_fallback", "error": str(exc)}


async def query_recent(
    measurement: str,
    *,
    limit: int = 100,
    domain: str | None = None,
) -> list[dict[str, Any]]:
    """Query recent points — Influx when live, else scan JSONL fallback."""
    client = await _client()
    if client is not None:
        try:
            query = (
                f'from(bucket:"{config.INFLUXDB_BUCKET}") '
                f'|> range(start: -30d) '
                f'|> filter(fn: (r) => r._measurement == "{measurement}") '
                f'|> limit(n:{limit})'
            )
            tables = await client.query_api().query(query=query, org=config.INFLUXDB_ORG)
            rows: list[dict[str, Any]] = []
            for table in tables or []:
                for record in table.records or []:
                    rows.append(
                        {
                            "measurement": record.get_measurement(),
                            "field": record.get_field(),
                            "value": record.get_value(),
                            "time": record.get_time().isoformat() if record.get_time() else None,
                            "tags": {k: record.values.get(k) for k in ("domain", "asset", "source")},
                        }
                    )
            if domain:
                rows = [r for r in rows if (r.get("tags") or {}).get("domain") == domain]
            return rows[:limit]
        except Exception as exc:
            logger.warning("Influx query failed: %s", exc)

    if not _FALLBACK_PATH.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in _FALLBACK_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("measurement") != measurement:
            continue
        if domain and (row.get("tags") or {}).get("domain") != domain:
            continue
        out.append(row)
    return out[-limit:]


def timeseries_status() -> dict[str, Any]:
    fallback_rows = 0
    if _FALLBACK_PATH.exists():
        fallback_rows = sum(1 for ln in _FALLBACK_PATH.read_text(encoding="utf-8").splitlines() if ln.strip())
    return {
        "enabled": enabled(),
        "backend": "influxdb" if enabled() else "jsonl_fallback",
        "url_set": bool((getattr(config, "INFLUXDB_URL", None) or "").strip()),
        "bucket": getattr(config, "INFLUXDB_BUCKET", "blackdark"),
        "fallback_rows": fallback_rows,
        "retention_days": getattr(config, "ETL_RETENTION_DAYS", 730),
    }
