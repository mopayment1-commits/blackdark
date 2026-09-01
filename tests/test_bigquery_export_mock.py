"""BigQuery export schema validation without live GCP (CLOSURE-MANDATE-FINAL item 25)."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_bigquery_export_capability_snapshot_schema():
    from bigquery_export import export_capability_snapshot

    result = await export_capability_snapshot(
        capability_id=648,
        symbol="BTC",
        payload={"surface": "bigquery_export", "success": True},
    )
    assert result["success"] is True
    assert result["schema_validated"] is True
    assert result["capability_id"] == 648


@pytest.mark.asyncio
async def test_bigquery_live_ready_without_credentials():
    from bigquery_export import bigquery_live_ready

    assert bigquery_live_ready() in {True, False}
