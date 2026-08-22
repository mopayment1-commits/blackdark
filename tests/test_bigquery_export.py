"""Tests for CAP-658 BigQuery warehouse export."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def bigquery_env(monkeypatch, tmp_path):
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
    monkeypatch.setenv("BIGQUERY_DATASET", "blackdark")
    monkeypatch.setenv("BIGQUERY_TABLE", "ingestion_snapshots")
    monkeypatch.setenv("BIGQUERY_CREDENTIALS_JSON", json.dumps(creds))
    monkeypatch.setenv("BIGQUERY_EXPORT_ENABLED", "true")
    evidence = tmp_path / "institutional_assurance"
    evidence.mkdir(parents=True)
    monkeypatch.setattr("bigquery_export._EVIDENCE_DIR", evidence)
    monkeypatch.setattr("bigquery_export._EVIDENCE_PATH", evidence / "bigquery_export_evidence.json")
    monkeypatch.setattr("bigquery_export.project_data_dir", lambda: tmp_path)
    return evidence


@pytest.mark.asyncio
async def test_bigquery_export_writes_verified_evidence(monkeypatch, tmp_path, bigquery_env):
    import config

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap658.db"))
    await __import__("database").init_db()

    from database import insert_ingestion_snapshot
    from bigquery_export import export_ingestion_snapshots_to_bigquery, get_export_evidence, bigquery_live_ready

    await insert_ingestion_snapshot(
        "coingecko_trending",
        "sentiment",
        {"symbols": ["BTC", "ETH"], "value": 62},
        status="ok",
    )

    mock_client = MagicMock()
    mock_client.insert_rows_json.return_value = []
    mock_query_job = MagicMock()
    mock_query_job.result.return_value = [{"row_count": 1}]
    mock_client.query.return_value = mock_query_job
    mock_client.get_table.side_effect = Exception("missing")
    mock_client.create_table.return_value = None

    with patch("bigquery_export._build_client", return_value=mock_client):
        evidence = await export_ingestion_snapshots_to_bigquery(operator="test")

    assert evidence["rows_sent"] == 1
    assert evidence["rows_verified"] == 1
    assert evidence["gate"] == "CAP-658"
    assert get_export_evidence()["export_id"] == evidence["export_id"]
    assert bigquery_live_ready() is True


@pytest.mark.asyncio
async def test_cap658_not_external_when_bigquery_ready(monkeypatch, tmp_path, bigquery_env):
    evidence = {
        "export_id": "exp_test123",
        "rows_verified": 3,
        "table_fqn": "blackdark-test.blackdark.ingestion_snapshots",
    }
    (bigquery_env / "bigquery_export_evidence.json").write_text(json.dumps(evidence), encoding="utf-8")

    from cap978.catalog import is_external

    assert is_external(658) is False


@pytest.mark.asyncio
async def test_cap658_execute_when_ready(monkeypatch, tmp_path, bigquery_env):
    import config

    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "cap658.db"))
    await __import__("database").init_db()
    evidence = {
        "export_id": "exp_test123",
        "rows_verified": 2,
        "table_fqn": "blackdark-test.blackdark.ingestion_snapshots",
    }
    (bigquery_env / "bigquery_export_evidence.json").write_text(json.dumps(evidence), encoding="utf-8")

    from cap978.verify import execute_extension

    result = await execute_extension(658, params={"symbol": "BTC", "tier": "elite"})
    assert result["success"] is True
    assert result["surface"] == "white_label_embedded_analytics"
    assert result["result"]["export_ready"] is True
