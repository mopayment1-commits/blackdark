"""Tests for CAP-649 dbt connector."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def dbt_env(monkeypatch, tmp_path):
    creds = {
        "type": "service_account",
        "project_id": "blackdark-test",
        "private_key_id": "k",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7\n-----END PRIVATE KEY-----\n",
        "client_email": "bq@test.iam.gserviceaccount.com",
        "client_id": "1",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    monkeypatch.setenv("BIGQUERY_PROJECT_ID", "blackdark-test")
    monkeypatch.setenv("BIGQUERY_DATASET", "blackdark_analytics")
    monkeypatch.setenv("BIGQUERY_CREDENTIALS_JSON", json.dumps(creds))
    monkeypatch.setenv("DBT_RUN_ENABLED", "true")
    evidence = tmp_path / "institutional_assurance"
    evidence.mkdir(parents=True)
    monkeypatch.setattr("dbt_connector._EVIDENCE_DIR", evidence)
    monkeypatch.setattr("dbt_connector._EVIDENCE_PATH", evidence / "dbt_run_evidence.json")
    monkeypatch.setattr("dbt_connector._BOOTSTRAP_STATUS_PATH", evidence / "dbt_bootstrap_status.json")
    monkeypatch.setattr("dbt_connector._PROFILES_DIR", evidence / "dbt_profiles")
    monkeypatch.setattr("dbt_connector.project_data_dir", lambda: tmp_path)
    return evidence


def test_dbt_live_ready_from_evidence(monkeypatch, dbt_env):
    evidence = {
        "run_id": "dbt_test123",
        "mart_rows_verified": 5,
        "mart_table_fqn": "blackdark-test.blackdark_analytics.mart_ingestion_daily",
    }
    (dbt_env / "dbt_run_evidence.json").write_text(json.dumps(evidence), encoding="utf-8")

    with patch("bigquery_export.bigquery_live_ready", return_value=True):
        from dbt_connector import dbt_live_ready

        assert dbt_live_ready() is True


@pytest.mark.asyncio
async def test_cap649_not_external_when_dbt_ready(monkeypatch, dbt_env):
    evidence = {
        "run_id": "dbt_test123",
        "mart_rows_verified": 3,
        "mart_table_fqn": "blackdark-test.blackdark_analytics.mart_ingestion_daily",
    }
    (dbt_env / "dbt_run_evidence.json").write_text(json.dumps(evidence), encoding="utf-8")

    with patch("bigquery_export.bigquery_live_ready", return_value=True):
        from cap978.catalog import is_external

        assert is_external(649) is False


@pytest.mark.asyncio
async def test_run_dbt_pipeline_records_evidence(monkeypatch, dbt_env):
    completed = subprocess_result = MagicMock(returncode=0, stdout="OK", stderr="")

    with (
        patch("bigquery_export.bigquery_live_ready", return_value=True),
        patch("dbt_connector.subprocess.run", return_value=completed),
        patch("dbt_connector._parse_run_results", return_value={"models_run": 2, "models_errored": 0, "success": True}),
        patch("dbt_connector._verify_models_in_bigquery", return_value={"mart_rows": 4, "staging_rows": 7}),
        patch("dbt_connector._resolve_dataset_location", return_value="EU"),
    ):
        from dbt_connector import get_run_evidence, run_dbt_pipeline

        evidence = await run_dbt_pipeline(operator="test")
        assert evidence["mart_rows_verified"] == 4
        assert evidence["gate"] == "CAP-649"
        assert get_run_evidence()["run_id"] == evidence["run_id"]
