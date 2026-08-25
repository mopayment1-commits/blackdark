"""
Data Engineering Stack — Feature #223 dbt Connector merged (Sprint 0).

NOT standalone — internal tooling for production data pipelines.
Model tests + lineage mandatory. Wraps existing dbt_connector.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.DataEngineeringStack")

_FEATURE_ID = 223
_MERGED_INTO = "Data Engineering Stack"
_STANDALONE = False
_SPRINT = 0
_DBT_PROJECT = Path("dbt_blackdark")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def get_model_lineage() -> dict[str, Any]:
    """dbt model lineage — sources → staging → marts."""
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "lineage": {
            "sources": [
                {
                    "name": "blackdark_lake.ingestion_snapshots",
                    "type": "source",
                    "database": "BIGQUERY_PROJECT_ID",
                    "schema": "blackdark_analytics",
                },
            ],
            "staging": [
                {
                    "name": "stg_ingestion_snapshots",
                    "type": "view",
                    "depends_on": ["source.blackdark_lake.ingestion_snapshots"],
                    "materialized": "view",
                },
            ],
            "marts": [
                {
                    "name": "mart_ingestion_daily",
                    "type": "table",
                    "depends_on": ["stg_ingestion_snapshots"],
                    "materialized": "table",
                },
            ],
        },
        "lineage_display": (
            "ingestion_snapshots → stg_ingestion_snapshots → mart_ingestion_daily"
        ),
        "timestamp": _utcnow(),
    }


def get_model_tests() -> dict[str, Any]:
    """dbt model tests metadata — required for acceptance."""
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "tests": [
            {
                "model": "stg_ingestion_snapshots",
                "tests": ["not_null(snapshot_id)", "unique(snapshot_id)"],
                "status": "defined",
            },
            {
                "model": "mart_ingestion_daily",
                "tests": ["not_null(snapshot_date)", "unique(snapshot_date)"],
                "status": "defined",
            },
        ],
        "test_paths": ["dbt_blackdark/tests"],
        "model_tests_required": True,
        "timestamp": _utcnow(),
    }


async def data_engineering_stack_status() -> dict[str, Any]:
    """Unified Data Engineering Stack status — #223 merged, not standalone."""
    from dbt_connector import dbt_configured, dbt_connector_status, get_run_evidence

    dbt_status = await dbt_connector_status()
    lineage = get_model_lineage()
    tests = get_model_tests()
    evidence = get_run_evidence()

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "module": "Data Engineering Stack",
        "sprint": _SPRINT,
        "components": {
            223: "dbt Connector (merged)",
            "bigquery_lake": "CAP-658 export",
            "data_catalog": "#214",
            "data_storage": "#215",
        },
        "dbt": {
            "configured": dbt_configured(),
            "live_ready": dbt_status.get("run_ready", False),
            "surface": "internal_tooling",
            "not_standalone": True,
        },
        "lineage": lineage,
        "model_tests": tests,
        "last_run": evidence,
        "workflow_display": "Dune warehouse + dbt models → production analytics pipeline",
        "timestamp": _utcnow(),
    }


async def run_data_pipeline(*, operator: str = "system") -> dict[str, Any]:
    """Execute dbt pipeline via Data Engineering Stack."""
    from dbt_connector import run_dbt_pipeline

    result = await run_dbt_pipeline(operator=operator)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "pipeline_result": result,
        "lineage": get_model_lineage(),
        "model_tests": get_model_tests(),
        "timestamp": _utcnow(),
    }
