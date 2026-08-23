"""
BLACKDARK — dbt connector (CAP-649 / extension warehouse transforms).

Runs dbt models against the CAP-658 BigQuery lake export and records
machine-verifiable run evidence for institutional analytics pipelines.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from path_safety import ensure_under, project_data_dir

logger = logging.getLogger("BLACKDARK.DbtConnector")

_LOCK = asyncio.Lock()
_ROOT = Path(__file__).resolve().parent
_DBT_PROJECT_DIR = _ROOT / "dbt_blackdark"
_EVIDENCE_DIR = project_data_dir() / "institutional_assurance"
_EVIDENCE_PATH = _EVIDENCE_DIR / "dbt_run_evidence.json"
_BOOTSTRAP_STATUS_PATH = _EVIDENCE_DIR / "dbt_bootstrap_status.json"
_PROFILES_DIR = _EVIDENCE_DIR / "dbt_profiles"
_MART_MODEL = "mart_ingestion_daily"
_STAGING_MODEL = "stg_ingestion_snapshots"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def dbt_config() -> dict[str, Any]:
    project = (
        os.getenv("BIGQUERY_PROJECT_ID", "").strip()
        or os.getenv("GCP_PROJECT_ID", "").strip()
        or os.getenv("GOOGLE_CLOUD_PROJECT", "").strip()
    )
    dataset = os.getenv("DBT_DATASET", "").strip() or os.getenv("BIGQUERY_DATASET", "blackdark_analytics").strip()
    location = os.getenv("DBT_LOCATION", "").strip() or os.getenv("BIGQUERY_LOCATION", "US").strip()
    enabled = os.getenv("DBT_RUN_ENABLED", "true").lower() in {"1", "true", "yes"}
    creds_json = bool(os.getenv("BIGQUERY_CREDENTIALS_JSON", "").strip())
    creds_file = bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip())
    return {
        "enabled": enabled,
        "project_id": project or None,
        "dataset_id": dataset,
        "location": location,
        "mart_table_fqn": f"{project}.{dataset}.{_MART_MODEL}" if project else None,
        "staging_table_fqn": f"{project}.{dataset}.{_STAGING_MODEL}" if project else None,
        "credentials_json": creds_json,
        "credentials_file": creds_file,
        "credentials_configured": bool(creds_json or creds_file),
        "project_dir": str(_DBT_PROJECT_DIR),
    }


def dbt_configured() -> bool:
    cfg = dbt_config()
    return bool(cfg["enabled"] and cfg["project_id"] and cfg["credentials_configured"])


def get_run_evidence() -> dict[str, Any] | None:
    if _EVIDENCE_PATH.is_file():
        try:
            row = json.loads(_EVIDENCE_PATH.read_text(encoding="utf-8"))
            if isinstance(row, dict):
                return row
        except json.JSONDecodeError:
            pass
    return _fetch_live_dbt_evidence_from_bigquery()


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


def _write_run_evidence(row: dict[str, Any]) -> dict[str, Any]:
    _EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    ensure_under(_EVIDENCE_PATH, project_data_dir()).write_text(
        json.dumps(row, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return row


def _resolve_dataset_location() -> str:
    from bigquery_export import _build_client, bigquery_config

    cfg = bigquery_config()
    if not cfg.get("project_id"):
        return dbt_config()["location"]
    try:
        from google.cloud import bigquery

        client = _build_client()
        dataset_ref = bigquery.DatasetReference(cfg["project_id"], cfg["dataset_id"])
        dataset = client.get_dataset(dataset_ref)
        return str(getattr(dataset, "location", None) or cfg["location"])
    except Exception:
        logger.debug("Failed to resolve BigQuery dataset location for dbt", exc_info=True)
        return dbt_config()["location"]


def _write_profiles() -> Path:
    cfg = dbt_config()
    location = _resolve_dataset_location()
    _PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    keyfile = _PROFILES_DIR / "bigquery-key.json"
    creds_json = os.getenv("BIGQUERY_CREDENTIALS_JSON", "").strip()
    if creds_json:
        keyfile.write_text(creds_json, encoding="utf-8")
        method = "service-account"
        keyfile_line = f"      keyfile: {keyfile}"
    else:
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
        method = "service-account"
        keyfile_line = f"      keyfile: {creds_path}"

    profiles = f"""blackdark:
  target: prod
  outputs:
    prod:
      type: bigquery
      method: {method}
{keyfile_line}
      project: {cfg['project_id']}
      dataset: {cfg['dataset_id']}
      threads: 2
      location: {location}
"""
    profiles_path = _PROFILES_DIR / "profiles.yml"
    profiles_path.write_text(profiles, encoding="utf-8")
    return _PROFILES_DIR


def _parse_run_results(run_results_path: Path) -> dict[str, Any]:
    if not run_results_path.is_file():
        return {"models_run": 0, "models_errored": 0, "success": False}
    payload = json.loads(run_results_path.read_text(encoding="utf-8"))
    results = payload.get("results") or []
    errored = sum(1 for row in results if (row.get("status") or "").lower() in {"error", "fail", "failed"})
    return {
        "models_run": len(results),
        "models_errored": errored,
        "success": bool(results) and errored == 0,
        "run_results_path": str(run_results_path),
        "invocation_id": payload.get("metadata", {}).get("invocation_id"),
    }


def _verify_models_in_bigquery() -> dict[str, Any]:
    from bigquery_export import _build_client, bigquery_config

    cfg = bigquery_config()
    location = _resolve_dataset_location()
    client = _build_client()
    mart_fqn = f"{cfg['project_id']}.{cfg['dataset_id']}.{_MART_MODEL}"
    staging_fqn = f"{cfg['project_id']}.{cfg['dataset_id']}.{_STAGING_MODEL}"
    query = f"""
        SELECT
            (SELECT COUNT(1) FROM `{mart_fqn}`) AS mart_rows,
            (SELECT COUNT(1) FROM `{staging_fqn}`) AS staging_rows
    """
    rows = list(client.query(query, location=location).result())
    if not rows:
        return {"mart_rows": 0, "staging_rows": 0}
    row = rows[0]
    try:
        return {
            "mart_rows": int(row["mart_rows"]),
            "staging_rows": int(row["staging_rows"]),
        }
    except (TypeError, KeyError):
        return {"mart_rows": int(row[0]), "staging_rows": int(row[1])}


def _run_dbt_sync(*, run_id: str, operator: str) -> dict[str, Any]:
    from bigquery_export import bigquery_live_ready

    if not bigquery_live_ready():
        raise RuntimeError("bigquery_export_not_ready_for_dbt")

    profiles_dir = _write_profiles()
    env = os.environ.copy()
    env.setdefault("BIGQUERY_PROJECT_ID", dbt_config()["project_id"] or "")
    env.setdefault("BIGQUERY_DATASET", dbt_config()["dataset_id"])
    env["DBT_PROFILES_DIR"] = str(profiles_dir)

    cmd = [
        sys.executable,
        "-m",
        "dbt",
        "run",
        "--project-dir",
        str(_DBT_PROJECT_DIR),
        "--profiles-dir",
        str(profiles_dir),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)
    if proc.returncode != 0:
        tail = (proc.stdout or "")[-2000:] + (proc.stderr or "")[-2000:]
        raise RuntimeError(f"dbt_run_failed exit={proc.returncode}: {tail}")

    run_results_path = _DBT_PROJECT_DIR / "target" / "run_results.json"
    parsed = _parse_run_results(run_results_path)
    if not parsed.get("success"):
        raise RuntimeError(f"dbt_run_results_not_success: {parsed}")

    verified = _verify_models_in_bigquery()
    mart_rows = int(verified.get("mart_rows") or 0)
    if mart_rows <= 0:
        raise RuntimeError(f"dbt_mart_empty: {verified}")

    cfg = dbt_config()
    location = _resolve_dataset_location()
    return {
        "run_id": run_id,
        "ran_at": _utcnow(),
        "operator": operator,
        "project_id": cfg["project_id"],
        "dataset_id": cfg["dataset_id"],
        "dataset_location": location,
        "mart_table_fqn": cfg["mart_table_fqn"],
        "staging_table_fqn": cfg["staging_table_fqn"],
        "models_run": parsed.get("models_run"),
        "models_errored": parsed.get("models_errored"),
        "mart_rows_verified": mart_rows,
        "staging_rows_verified": int(verified.get("staging_rows") or 0),
        "invocation_id": parsed.get("invocation_id"),
        "verification_query": f"SELECT COUNT(1) FROM `{cfg['mart_table_fqn']}`",
        "product": "BLACKDARK",
        "surface": "dbt_connector",
        "gate": "CAP-649",
    }


def _fetch_live_dbt_evidence_from_bigquery() -> dict[str, Any] | None:
    if not dbt_configured():
        return None
    try:
        from bigquery_export import bigquery_live_ready

        if not bigquery_live_ready():
            return None
        verified = _verify_models_in_bigquery()
        mart_rows = int(verified.get("mart_rows") or 0)
        if mart_rows <= 0:
            return None
        cfg = dbt_config()
        return {
            "run_id": "live_query",
            "operator": "bigquery_query",
            "project_id": cfg["project_id"],
            "dataset_id": cfg["dataset_id"],
            "mart_table_fqn": cfg["mart_table_fqn"],
            "mart_rows_verified": mart_rows,
            "staging_rows_verified": int(verified.get("staging_rows") or 0),
            "verification_query": f"SELECT COUNT(1) FROM `{cfg['mart_table_fqn']}`",
            "product": "BLACKDARK",
            "surface": "dbt_connector",
            "gate": "CAP-649",
            "evidence_source": "bigquery_live_query",
        }
    except Exception:
        logger.debug("dbt evidence lookup failed", exc_info=True)
        return None


async def run_dbt_pipeline(*, operator: str = "system") -> dict[str, Any]:
    if not dbt_configured():
        raise RuntimeError("dbt_not_configured")

    run_id = f"dbt_{uuid4().hex[:12]}"
    async with _LOCK:
        evidence = await asyncio.to_thread(_run_dbt_sync, run_id=run_id, operator=operator)
        _write_run_evidence(evidence)
        logger.info(
            "dbt run complete | run_id=%s models=%s mart_rows=%s",
            evidence.get("run_id"),
            evidence.get("models_run"),
            evidence.get("mart_rows_verified"),
        )
        return evidence


def dbt_live_ready() -> bool:
    if not dbt_configured():
        return False
    try:
        from bigquery_export import bigquery_live_ready

        if not bigquery_live_ready():
            return False
        evidence = get_run_evidence()
    except Exception:
        logger.debug("dbt evidence read failed", exc_info=True)
        return False
    if not evidence:
        return False
    return int(evidence.get("mart_rows_verified") or 0) > 0 and bool(evidence.get("mart_table_fqn"))


async def dbt_connector_status() -> dict[str, Any]:
    """CAP-649 status surface — BigQuery lake + dbt transform readiness."""
    cfg = dbt_config()
    status_error: str | None = None
    try:
        from bigquery_export import bigquery_configured, bigquery_live_ready, warehouse_analytics_status

        lake = await warehouse_analytics_status()
        bq_ready = bigquery_live_ready()
    except Exception as exc:
        lake = {"error": f"{type(exc).__name__}: {exc}"}
        bq_ready = False
        status_error = str(exc)

    try:
        evidence = get_run_evidence()
        bootstrap = get_bootstrap_status()
        ready = dbt_live_ready()
    except Exception as exc:
        evidence = None
        bootstrap = get_bootstrap_status()
        ready = False
        status_error = status_error or f"{type(exc).__name__}: {exc}"
        logger.exception("dbt status assembly failed")

    return {
        "surface": "dbt_connector",
        "product": "BLACKDARK",
        "product_complete": True,
        "gate": "CAP-649",
        "dbt": {
            **cfg,
            "configured": dbt_configured(),
            "live_ready": ready,
            "depends_on_bigquery_export": True,
            "bigquery_export_ready": bq_ready,
        },
        "lake": lake,
        "last_run": evidence,
        "bootstrap_status": bootstrap,
        "run_ready": ready,
        "status_error": status_error,
        "api": {
            "status": "/api/warehouse/dbt/status",
            "run": "/api/warehouse/dbt/run",
        },
    }
