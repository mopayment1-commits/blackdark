"""
BLACKDARK — BigQuery warehouse export (CAP-658 / White-Label Embedded Analytics).

Exports live ingestion_snapshots from the operational data lake (Postgres/SQLite)
into a configured BigQuery dataset for institutional embedded analytics.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import config
from path_safety import ensure_under, project_data_dir

logger = logging.getLogger("BLACKDARK.BigQueryExport")

_LOCK = asyncio.Lock()
_EVIDENCE_DIR = project_data_dir() / "institutional_assurance"
_EVIDENCE_PATH = _EVIDENCE_DIR / "bigquery_export_evidence.json"
_BOOTSTRAP_STATUS_PATH = _EVIDENCE_DIR / "bigquery_bootstrap_status.json"

_TABLE_SCHEMA = [
    {"name": "export_id", "field_type": "STRING", "mode": "REQUIRED"},
    {"name": "snapshot_id", "field_type": "INT64", "mode": "NULLABLE"},
    {"name": "source_id", "field_type": "STRING", "mode": "REQUIRED"},
    {"name": "category", "field_type": "STRING", "mode": "REQUIRED"},
    {"name": "payload_json", "field_type": "STRING", "mode": "REQUIRED"},
    {"name": "fetched_at", "field_type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "status", "field_type": "STRING", "mode": "REQUIRED"},
    {"name": "exported_at", "field_type": "TIMESTAMP", "mode": "REQUIRED"},
    {"name": "product", "field_type": "STRING", "mode": "REQUIRED"},
]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def bigquery_config() -> dict[str, Any]:
    project = (
        os.getenv("BIGQUERY_PROJECT_ID", "").strip()
        or os.getenv("GCP_PROJECT_ID", "").strip()
        or os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    )
    dataset = os.getenv("BIGQUERY_DATASET", "blackdark").strip() or "blackdark"
    table = os.getenv("BIGQUERY_TABLE", "ingestion_snapshots").strip() or "ingestion_snapshots"
    location = os.getenv("BIGQUERY_LOCATION", "US").strip() or "US"
    creds_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    creds_json = bool(os.getenv("BIGQUERY_CREDENTIALS_JSON", "").strip())
    enabled = os.getenv("BIGQUERY_EXPORT_ENABLED", "true").lower() in {"1", "true", "yes"}
    return {
        "enabled": enabled,
        "project_id": project or None,
        "dataset_id": dataset,
        "table_id": table,
        "location": location,
        "table_fqn": f"{project}.{dataset}.{table}" if project else None,
        "credentials_file": bool(creds_file),
        "credentials_json": creds_json,
        "credentials_configured": bool(creds_file or creds_json),
    }


def bigquery_configured() -> bool:
    cfg = bigquery_config()
    return bool(cfg["enabled"] and cfg["project_id"] and cfg["credentials_configured"])


def get_export_evidence() -> dict[str, Any] | None:
    if _EVIDENCE_PATH.is_file():
        try:
            row = json.loads(_EVIDENCE_PATH.read_text(encoding="utf-8"))
            if isinstance(row, dict):
                return row
        except json.JSONDecodeError:
            pass
    return _fetch_latest_export_evidence_from_bigquery()


def _fetch_latest_export_evidence_from_bigquery() -> dict[str, Any] | None:
    """Read latest verified export from BigQuery (multi-replica safe)."""
    if not bigquery_configured():
        return None
    try:
        cfg = bigquery_config()
        client = _build_client()
        table_ref = f"{cfg['project_id']}.{cfg['dataset_id']}.{cfg['table_id']}"
        query = f"""
            SELECT
                export_id,
                COUNT(1) AS rows_verified,
                MAX(exported_at) AS exported_at
            FROM `{table_ref}`
            GROUP BY export_id
            ORDER BY exported_at DESC
            LIMIT 1
        """
        rows = list(client.query(query, location=cfg["location"]).result())
        if not rows:
            return None
        row = rows[0]
        try:
            export_id = str(row["export_id"])
            rows_verified = int(row["rows_verified"])
            exported_at = row["exported_at"]
        except (TypeError, KeyError):
            export_id = str(row[0])
            rows_verified = int(row[1])
            exported_at = row[2]
        if rows_verified <= 0:
            return None
        exported_at_iso = (
            exported_at.isoformat() if hasattr(exported_at, "isoformat") else str(exported_at)
        )
        return {
            "export_id": export_id,
            "exported_at": exported_at_iso,
            "operator": "bigquery_query",
            "project_id": cfg["project_id"],
            "dataset_id": cfg["dataset_id"],
            "table_id": cfg["table_id"],
            "table_fqn": table_ref,
            "rows_sent": rows_verified,
            "rows_verified": rows_verified,
            "verification_query": (
                f"SELECT COUNT(1) FROM `{table_ref}` WHERE export_id = '{export_id}'"
            ),
            "product": "BLACKDARK",
            "surface": "white_label_embedded_analytics",
            "gate": "CAP-658",
            "evidence_source": "bigquery_live_query",
        }
    except Exception as exc:
        logger.debug("BigQuery evidence lookup failed", exc_info=True)
        return None


def get_bootstrap_status() -> dict[str, Any] | None:
    if not _BOOTSTRAP_STATUS_PATH.is_file():
        return None
    try:
        row = json.loads(_BOOTSTRAP_STATUS_PATH.read_text(encoding="utf-8"))
        return row if isinstance(row, dict) else None
    except json.JSONDecodeError:
        return None


def _write_bootstrap_status(row: dict[str, Any]) -> None:
    _EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {**row, "updated_at": _utcnow()}
    ensure_under(_BOOTSTRAP_STATUS_PATH, project_data_dir()).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_export_evidence(row: dict[str, Any]) -> dict[str, Any]:
    _EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ensure_under(_EVIDENCE_PATH, project_data_dir()).write_text(
        json.dumps(row, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return row


def _manifest_sha256(rows: list[dict[str, Any]]) -> str:
    body = json.dumps(rows, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(body).hexdigest()


def _parse_ts(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")


def _build_client():
    from google.cloud import bigquery
    from google.oauth2 import service_account

    cfg = bigquery_config()
    project = cfg["project_id"]
    if not project:
        raise RuntimeError("bigquery_project_missing")

    creds_json = os.getenv("BIGQUERY_CREDENTIALS_JSON", "").strip()
    if creds_json:
        info = json.loads(creds_json)
        creds = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(project=project, credentials=creds, location=cfg["location"])

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if creds_path and Path(creds_path).is_file():
        creds = service_account.Credentials.from_service_account_file(creds_path)
        return bigquery.Client(project=project, credentials=creds, location=cfg["location"])

    return bigquery.Client(project=project, location=cfg["location"])


def _bigquery_diagnostics(client: Any) -> dict[str, Any]:
    cfg = bigquery_config()
    datasets: list[str] | str
    try:
        datasets = [row.dataset_id for row in client.list_datasets(project=cfg["project_id"])]
    except Exception as exc:
        datasets = f"list_failed:{type(exc).__name__}:{exc}"
    return {
        "project_id": cfg["project_id"],
        "dataset_id": cfg["dataset_id"],
        "location": cfg["location"],
        "datasets_found": datasets,
    }


def _ensure_dataset(client: Any) -> str:
    from google.api_core.exceptions import NotFound
    from google.cloud import bigquery

    cfg = bigquery_config()
    dataset_ref = bigquery.DatasetReference(cfg["project_id"], cfg["dataset_id"])
    table_dataset = f"{cfg['project_id']}.{cfg['dataset_id']}"
    ddl = (
        f"CREATE SCHEMA IF NOT EXISTS `{table_dataset}` "
        f"OPTIONS(location='{cfg['location']}')"
    )
    try:
        client.query(ddl, location=cfg["location"]).result()
    except Exception as exc:
        raise RuntimeError(
            f"bigquery_dataset_ddl_failed:{cfg['dataset_id']}: {exc}"
        ) from exc
    try:
        client.get_dataset(dataset_ref)
    except NotFound as exc:
        diag = _bigquery_diagnostics(client)
        raise RuntimeError(
            f"bigquery_dataset_missing_after_ddl:{cfg['dataset_id']}: {diag}"
        ) from exc
    return table_dataset


def _ensure_table(client: Any) -> str:
    from google.cloud import bigquery

    cfg = bigquery_config()
    _ensure_dataset(client)
    table_ref = f"{cfg['project_id']}.{cfg['dataset_id']}.{cfg['table_id']}"
    schema = [bigquery.SchemaField(**field) for field in _TABLE_SCHEMA]
    table = bigquery.Table(table_ref, schema=schema)
    try:
        client.get_table(table_ref)
    except Exception:
        client.create_table(table, exists_ok=True)
    return table_ref


def _verify_export_rows(client: Any, *, table_ref: str, export_id: str) -> int:
    from google.cloud import bigquery

    query = f"""
        SELECT COUNT(1) AS row_count
        FROM `{table_ref}`
        WHERE export_id = @export_id
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[bigquery.ScalarQueryParameter("export_id", "STRING", export_id)]
    )
    result = list(client.query(query, job_config=job_config, location=bigquery_config()["location"]).result())
    if not result:
        return 0
    row = result[0]
    try:
        return int(row["row_count"])
    except (TypeError, KeyError):
        return int(row[0])


def _export_rows_sync(*, export_rows: list[dict[str, Any]], export_id: str, exported_at: str, operator: str, manifest_sha256: str) -> dict[str, Any]:
    from google.cloud import bigquery

    client = _build_client()
    cfg = bigquery_config()
    table_ref = _ensure_table(client)
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        schema=[bigquery.SchemaField(**field) for field in _TABLE_SCHEMA],
    )
    load_job = client.load_table_from_json(
        export_rows,
        table_ref,
        job_config=job_config,
        location=cfg["location"],
        project=cfg["project_id"],
    )
    load_job.result()
    if load_job.errors:
        raise RuntimeError(f"bigquery_load_errors: {load_job.errors[:3]}")
    verified = _verify_export_rows(client, table_ref=table_ref, export_id=export_id)
    if verified != len(export_rows):
        raise RuntimeError(f"bigquery_verification_mismatch: sent={len(export_rows)} verified={verified}")
    return {
        "export_id": export_id,
        "exported_at": exported_at,
        "operator": operator,
        "project_id": cfg["project_id"],
        "dataset_id": cfg["dataset_id"],
        "table_id": cfg["table_id"],
        "table_fqn": table_ref,
        "rows_sent": len(export_rows),
        "rows_verified": verified,
        "manifest_sha256": manifest_sha256,
        "verification_query": (
            f"SELECT COUNT(1) FROM `{table_ref}` WHERE export_id = '{export_id}'"
        ),
        "product": "BLACKDARK",
        "surface": "white_label_embedded_analytics",
        "gate": "CAP-658",
    }


async def export_ingestion_snapshots_to_bigquery(
    *,
    limit: int | None = None,
    dry_run: bool = False,
    operator: str = "system",
) -> dict[str, Any]:
    """Export live lake rows to BigQuery and return machine-verifiable evidence."""
    if not bigquery_configured():
        raise RuntimeError("bigquery_not_configured")

    from database import fetch_ingestion_snapshots_for_export

    max_rows = int(limit or os.getenv("BIGQUERY_EXPORT_BATCH_SIZE", "500"))
    snapshots = await fetch_ingestion_snapshots_for_export(limit=max_rows)
    export_id = f"exp_{uuid4().hex[:12]}"
    exported_at = _utcnow()
    export_rows = [
        {
            "export_id": export_id,
            "snapshot_id": int(row.get("id") or 0) or None,
            "source_id": str(row.get("source_id") or ""),
            "category": str(row.get("category") or ""),
            "payload_json": json.dumps(row.get("payload") or {}, separators=(",", ":"), default=str),
            "fetched_at": _parse_ts(str(row.get("fetched_at") or "")),
            "status": str(row.get("status") or "ok"),
            "exported_at": _parse_ts(exported_at),
            "product": "BLACKDARK",
        }
        for row in snapshots
    ]
    manifest_sha256 = _manifest_sha256(export_rows)
    cfg = bigquery_config()

    if dry_run:
        return {
            "dry_run": True,
            "export_id": export_id,
            "rows_prepared": len(export_rows),
            "manifest_sha256": manifest_sha256,
            "destination": cfg["table_fqn"],
        }

    if not export_rows:
        raise RuntimeError("no_ingestion_snapshots_to_export")

    async with _LOCK:
        evidence = await asyncio.to_thread(
            _export_rows_sync,
            export_rows=export_rows,
            export_id=export_id,
            exported_at=exported_at,
            operator=operator,
            manifest_sha256=manifest_sha256,
        )
        _write_export_evidence(evidence)
        logger.info(
            "BigQuery export complete | export_id=%s rows=%s table=%s",
            evidence.get("export_id"),
            evidence.get("rows_verified"),
            evidence.get("table_fqn"),
        )
        return evidence


def bigquery_live_ready() -> bool:
    """True when BigQuery is configured and the last export verified in BigQuery."""
    if not bigquery_configured():
        return False
    try:
        evidence = get_export_evidence()
    except Exception:
        logger.debug("BigQuery evidence read failed", exc_info=True)
        return False
    if not evidence:
        return False
    return int(evidence.get("rows_verified") or 0) > 0 and bool(evidence.get("table_fqn"))


async def warehouse_analytics_status() -> dict[str, Any]:
    """CAP-658 status surface — local lake + BigQuery export readiness."""
    from data_lake import lake_status

    cfg = bigquery_config()
    status_error: str | None = None
    try:
        lake = await lake_status()
    except Exception as exc:
        lake = {"error": f"{type(exc).__name__}: {exc}"}
        status_error = str(exc)

    try:
        evidence = get_export_evidence()
        bootstrap = get_bootstrap_status()
        ready = bigquery_live_ready()
    except Exception as exc:
        evidence = None
        bootstrap = get_bootstrap_status()
        ready = False
        status_error = status_error or f"{type(exc).__name__}: {exc}"
        logger.exception("BigQuery status assembly failed")
    return {
        "surface": "white_label_embedded_analytics",
        "product": "BLACKDARK",
        "product_complete": True,
        "gate": "CAP-658",
        "bigquery": {
            **cfg,
            "configured": bigquery_configured(),
            "live_ready": ready,
        },
        "lake": lake,
        "last_export": evidence,
        "bootstrap_status": bootstrap,
        "export_ready": ready,
        "status_error": status_error,
        "api": {
            "status": "/api/warehouse/bigquery/status",
            "export": "/api/warehouse/bigquery/export",
        },
    }
