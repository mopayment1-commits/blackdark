"""Sealed Oracle prediction markets."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("SOFT_LAUNCH", "1")


@pytest.mark.asyncio
async def test_settlement_splits_losing_pool(tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "sealed.db"))
    from sealed_market_store import ensure_sealed_market_schema, insert_market, insert_bet, update_market
    from sealed_prediction_market import settle_market_for_prediction

    await ensure_sealed_market_schema()
    mid = await insert_market(
        {
            "prediction_id": 9001,
            "asset": "BTC",
            "decision_action": "ACT",
            "verdict_raw": "BULLISH",
            "certificate_hash": "abc" * 20,
            "sealed_at": "2026-10-01T00:00:00+00:00",
            "betting_closes_at": "2026-10-02T00:00:00+00:00",
            "status": "open",
        }
    )
    await update_market(mid, yes_pool_usdt=30.0, no_pool_usdt=70.0, total_pool_usdt=100.0, participant_count=2)
    await insert_bet({"market_id": mid, "user_id": 1, "side": "yes", "stake_usdt": 30.0})
    await insert_bet({"market_id": mid, "user_id": 2, "side": "no", "stake_usdt": 70.0})
    result = await settle_market_for_prediction(9001, label="correct")
    assert result["winning_side"] == "yes"
    assert result["platform_fee_usdt"] == pytest.approx(3.5, rel=1e-6)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "sealed_client.db"))
    from starlette.testclient import TestClient

    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_sealed_markets_pages(client):
    assert client.get("/sealed-markets").status_code == 200
    assert "Sealed Prediction Markets" in client.get("/sealed-markets").text
    assert client.get("/api/sealed-markets/public").status_code == 200


def test_max_bet_enforced(tmp_path, monkeypatch):
    import asyncio
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "sealed_bet.db"))
    from sealed_prediction_market import place_market_bet, on_oracle_prediction_sealed

    async def run():
        await on_oracle_prediction_sealed(
            42, asset="ETH", verdict="WAIT", price_at_prediction=100.0, timestamp="2026-10-01T00:00:00+00:00"
        )
        from sealed_market_store import adjust_user_balance

        await adjust_user_balance(1, 100.0)
        with pytest.raises(ValueError, match="50"):
            await place_market_bet(
                user_id=1, prediction_id=42, side="yes", stake_usdt=51.0, funding="internal"
            )

    asyncio.run(run())
