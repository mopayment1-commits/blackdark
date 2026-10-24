"""ChangeNOW partner swap helpers (non-custodial)."""

import pytest

from changenow_api import (
    create_exchange,
    fetch_estimate,
    fetch_min_amount,
    swap_meta,
)


@pytest.mark.asyncio
async def test_swap_meta():
    m = swap_meta()
    assert m["provider"] == "changenow"
    assert m["non_custodial"] is True
    assert m["commission_model"] == "revenue_share"


@pytest.mark.asyncio
async def test_fetch_min_amount(monkeypatch):
    async def fake_get(path, *, params=None, api_key=False):
        if "min-amount" in path:
            return {"minAmount": 0.001}
        return None

    monkeypatch.setattr("changenow_api._get_json", fake_get)
    row = await fetch_min_amount("btc", "eth")
    assert row["min_amount"] == 0.001


@pytest.mark.asyncio
async def test_fetch_estimate_v1_fallback(monkeypatch):
    async def fake_get(path, *, params=None, api_key=False):
        if "exchange-amount" in path:
            return {"estimatedAmount": 1.5}
        return None

    monkeypatch.setattr("changenow_api.CHANGENOW_API_KEY", "")
    monkeypatch.setattr("changenow_api._get_json", fake_get)
    row = await fetch_estimate("btc", "eth", 0.01)
    assert row["to_amount"] == 1.5
    assert row["source"] == "changenow_v1"


@pytest.mark.asyncio
async def test_create_exchange_without_key():
    status, data = await create_exchange(
        from_currency="btc",
        to_currency="eth",
        from_amount=0.01,
        payout_address="0xD1220A0cf47c7B9Be7A2E6A89F429762e7b9aDb",
    )
    assert status == 503
    assert data["non_custodial"] is True


@pytest.mark.asyncio
async def test_public_swap_estimate_route(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_estimate(*args, **kwargs):
        return {
            "from_currency": "btc",
            "to_currency": "eth",
            "from_amount": 0.01,
            "to_amount": 0.3,
            "source": "changenow_v1",
        }

    monkeypatch.setattr("changenow_api.fetch_estimate", fake_estimate)
    client = TestClient(app)
    res = client.get(
        "/api/public/swap/estimate?from_currency=btc&to_currency=eth&from_amount=0.01"
    )
    assert res.status_code == 200
    assert res.json()["to_amount"] == 0.3


@pytest.mark.asyncio
async def test_swap_page_route():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res = client.get("/swap")
    assert res.status_code == 200
    assert "non-custodial" in res.text.lower() or "Non-custodial" in res.text
