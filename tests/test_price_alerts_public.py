"""Simple public price alerts."""

import pytest

from price_alerts_public import (
    create_alert,
    delete_alert,
    evaluate_alerts,
    normalize_client_id,
)


@pytest.fixture
def client_id():
    return "a1b2c3d4-e5f6-7890-abcd-ef1234567890"


@pytest.fixture(autouse=True)
def _tmp_store(tmp_path, monkeypatch):
    store = tmp_path / "price_alerts_public.json"
    monkeypatch.setattr("price_alerts_public._STORE_PATH", store)


@pytest.mark.asyncio
async def test_create_and_evaluate(client_id, monkeypatch):
    async def fake_spot(symbol):
        return {"price": 100.0, "source": "binance_rest:test"}

    monkeypatch.setattr("price_alerts_public._spot_price", fake_spot)
    created = await create_alert(
        client_id=client_id,
        symbol="BTC",
        direction="above",
        target_price=90.0,
    )
    assert created["ok"] is True
    out = await evaluate_alerts(client_id)
    assert out["ok"] is True
    assert len(out["alerts"]) == 1
    assert out["alerts"][0]["triggered"] is True


@pytest.mark.asyncio
async def test_delete_alert(client_id, monkeypatch):
    async def fake_spot(symbol):
        return {"price": 1.0, "source": "t"}

    monkeypatch.setattr("price_alerts_public._spot_price", fake_spot)
    created = await create_alert(
        client_id=client_id,
        symbol="ETH",
        direction="below",
        target_price=5000.0,
    )
    aid = created["alert"]["id"]
    assert delete_alert(client_id, aid)["ok"] is True
    out = await evaluate_alerts(client_id)
    assert len(out["alerts"]) == 0


def test_normalize_client_id():
    assert normalize_client_id("short") is None
    assert normalize_client_id("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


@pytest.mark.asyncio
async def test_public_price_alerts_api(client_id, monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_spot(symbol):
        return {"price": 50.0, "source": "test"}

    monkeypatch.setattr("price_alerts_public._spot_price", fake_spot)
    client = TestClient(app)
    res = client.post(
        "/api/public/price-alerts",
        json={
            "client_id": client_id,
            "symbol": "BTC",
            "direction": "above",
            "target_price": 40.0,
        },
    )
    assert res.status_code == 200
    res2 = client.get(f"/api/public/price-alerts?client_id={client_id}")
    assert res2.status_code == 200
    assert len(res2.json().get("alerts") or []) >= 1
