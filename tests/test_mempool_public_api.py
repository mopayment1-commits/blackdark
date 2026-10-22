"""mempool.space public API (no key)."""

import pytest

from mempool_public_api import (
    fetch_btc_mempool_context,
    fetch_recommended_fees,
)


@pytest.fixture(autouse=True)
def _clear_mempool_cache(monkeypatch):
    monkeypatch.setattr("mempool_public_api._CACHE", {})


@pytest.mark.asyncio
async def test_fetch_recommended_fees(monkeypatch):
    async def fake_get(path):
        if path == "/v1/fees/recommended":
            return {
                "fastestFee": 5,
                "halfHourFee": 3,
                "hourFee": 2,
                "economyFee": 1,
                "minimumFee": 1,
            }
        return None

    monkeypatch.setattr("mempool_public_api._get_json", fake_get)
    row = await fetch_recommended_fees()
    assert row["fastest_sat_vb"] == 5
    assert row["hour_sat_vb"] == 2


@pytest.mark.asyncio
async def test_fetch_btc_mempool_context(monkeypatch):
    async def fake_get(path):
        if path == "/v1/fees/recommended":
            return {"fastestFee": 4, "hourFee": 2}
        if path == "/blocks/tip/height":
            return 800000
        return None

    monkeypatch.setattr("mempool_public_api._get_json", fake_get)
    ctx = await fetch_btc_mempool_context()
    assert ctx["fetched_ok"] is True
    assert ctx["no_api_key"] is True
    assert ctx["block_tip_height"] == 800000


@pytest.mark.asyncio
async def test_public_btc_mempool_route():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res = client.get("/api/public/btc/mempool-fees")
    assert res.status_code == 200
    body = res.json()
    assert body.get("source") == "mempool.space"


@pytest.mark.asyncio
async def test_oracle_quick_btc_includes_fees(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_ctx():
        return {
            "fetched_ok": True,
            "source": "mempool.space",
            "attribution": "Data: mempool.space",
            "recommended_fees": {"fastest_sat_vb": 3},
            "block_tip_height": 1,
        }

    async def fake_spot(pair):
        return {
            "price": 1.0,
            "change_24h": 0.0,
            "volume": 1.0,
            "quote_volume": 1.0,
            "source": "binance_rest:test",
        }

    monkeypatch.setattr("mempool_public_api.fetch_btc_mempool_context", fake_ctx)
    monkeypatch.setattr("binance_public_api.fetch_public_spot_market", fake_spot)
    async def no_defi(a):
        return {"fetched_ok": False}

    monkeypatch.setattr("defillama_public_api.fetch_defi_context_for_asset", no_defi)

    async def passthrough(m, a, session=None):
        return m

    monkeypatch.setattr("coinmarketcap_api.enrich_market_with_cmc_metadata", passthrough)

    client = TestClient(app)
    res = client.get("/oracle/BTC/quick?lang=en")
    assert res.status_code == 200
    assert res.json().get("btc_mempool_fees", {}).get("recommended_fees")
