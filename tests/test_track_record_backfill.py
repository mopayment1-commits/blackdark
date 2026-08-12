"""Oracle track record backfill tests."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_backfill_from_database_mock():
    from oracle_track_record import backfill_from_database

    fake_unresolved = [{"id": 99, "asset": "BTC", "price_at_prediction": 50000, "verdict": "BUY", "opportunity_score": 70, "confidence": 80, "source": "test"}]
    fake_labeled = [{"id": 98, "asset": "ETH", "price_at_prediction": 3000, "verdict": "BUY", "resolved": 1, "price_after_24h": 3100, "outcome": "correct", "accuracy_score": 85, "label": "correct", "opportunity_score": 60, "confidence": 70, "source": "test"}]

    with patch("database.fetch_unresolved_oracle_predictions", new_callable=AsyncMock, return_value=fake_unresolved), \
         patch("database.fetch_labeled_oracle_predictions", new_callable=AsyncMock, return_value=fake_labeled), \
         patch("oracle_track_record.chain_summary", return_value={"integrity": {"valid": True}, "total_records": 2}):
        result = await backfill_from_database(limit=10)

    assert result["backfilled_created"] >= 1
    assert result["integrity_valid"] is True
