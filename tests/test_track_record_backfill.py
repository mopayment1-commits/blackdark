"""Oracle track record backfill tests."""

from unittest.mock import AsyncMock, patch

import pytest

import oracle_audit_chain as chain


@pytest.mark.asyncio
async def test_backfill_from_database_mock(tmp_path, monkeypatch):
    """Backfill must succeed on an isolated intact chain (not ambient disk state)."""
    path = tmp_path / "track_record_chain.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)

    from oracle_track_record import backfill_from_database

    fake_unresolved = [
        {
            "id": 99,
            "asset": "BTC",
            "price_at_prediction": 50000,
            "verdict": "BUY",
            "opportunity_score": 70,
            "confidence": 80,
            "source": "test",
        }
    ]
    fake_labeled = [
        {
            "id": 98,
            "asset": "ETH",
            "price_at_prediction": 3000,
            "verdict": "BUY",
            "resolved": 1,
            "price_after_24h": 3100,
            "outcome": "correct",
            "accuracy_score": 85,
            "label": "correct",
            "opportunity_score": 60,
            "confidence": 70,
            "source": "test",
        }
    ]

    with (
        patch(
            "database.fetch_unresolved_oracle_predictions",
            new_callable=AsyncMock,
            return_value=fake_unresolved,
        ),
        patch(
            "database.fetch_labeled_oracle_predictions",
            new_callable=AsyncMock,
            return_value=fake_labeled,
        ),
    ):
        result = await backfill_from_database(limit=10)

    assert result["backfilled_created"] >= 1
    assert result["integrity_valid"] is True
    assert path.exists()
    assert chain.verify_chain()["valid"] is True


@pytest.mark.asyncio
async def test_backfill_refuses_broken_ambient_chain(tmp_path, monkeypatch):
    """Production fail-closed: must not extend a tampered chain."""
    path = tmp_path / "broken.jsonl"
    monkeypatch.setattr(chain, "CHAIN_PATH", path)
    chain.append_prediction_record({"asset": "BTC", "verdict": "bullish"})
    # Tamper first record
    import json

    raw = json.loads(path.read_text(encoding="utf-8").strip())
    raw["verdict"] = "HACKED"
    path.write_text(json.dumps(raw) + "\n", encoding="utf-8")
    assert chain.verify_chain()["valid"] is False

    from oracle_track_record import backfill_from_database

    with (
        patch(
            "database.fetch_unresolved_oracle_predictions",
            new_callable=AsyncMock,
            return_value=[
                {
                    "id": 1,
                    "asset": "BTC",
                    "price_at_prediction": 1,
                    "verdict": "BUY",
                    "source": "test",
                }
            ],
        ),
        patch(
            "database.fetch_labeled_oracle_predictions",
            new_callable=AsyncMock,
            return_value=[],
        ),
        pytest.raises(RuntimeError, match="oracle_audit_chain_integrity_failed"),
    ):
        await backfill_from_database(limit=10)
