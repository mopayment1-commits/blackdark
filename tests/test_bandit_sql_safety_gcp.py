"""Regression tests for BigQuery/DBT identifier validation (Bandit B608 remediation)."""

import pytest

from sql_safety import (
    require_bq_dataset_id,
    require_bq_location,
    require_bq_table_fqn,
    require_gcp_project_id,
)


def test_gcp_project_validation_accepts_valid():
    assert require_gcp_project_id("my-project-123") == "my-project-123"


def test_gcp_project_validation_rejects_injection():
    with pytest.raises(ValueError):
        require_gcp_project_id("proj; DROP TABLE users")


def test_bq_table_fqn_builds_safely():
    fqn = require_bq_table_fqn("my-project-123", "blackdark", "ingestion_snapshots")
    assert fqn == "my-project-123.blackdark.ingestion_snapshots"


def test_bq_location_validation():
    assert require_bq_location("US") == "US"
    with pytest.raises(ValueError):
        require_bq_location("US; evil")


def test_bigquery_config_validates_identifiers(monkeypatch):
    monkeypatch.setenv("BIGQUERY_PROJECT_ID", "test-project-99")
    monkeypatch.setenv("BIGQUERY_DATASET", "blackdark")
    monkeypatch.setenv("BIGQUERY_TABLE", "ingestion_snapshots")
    from bigquery_export import bigquery_config

    cfg = bigquery_config()
    assert cfg["table_fqn"] == "test-project-99.blackdark.ingestion_snapshots"


def test_bigquery_config_rejects_bad_project(monkeypatch):
    monkeypatch.setenv("BIGQUERY_PROJECT_ID", "bad;project")
    from bigquery_export import bigquery_config

    with pytest.raises(ValueError):
        bigquery_config()


def test_dbt_config_validates_identifiers(monkeypatch):
    monkeypatch.setenv("BIGQUERY_PROJECT_ID", "test-project-99")
    monkeypatch.setenv("DBT_DATASET", "blackdark_analytics")
    from dbt_connector import dbt_config

    cfg = dbt_config()
    assert "test-project-99.blackdark_analytics.mart_ingestion_daily" == cfg["mart_table_fqn"]
