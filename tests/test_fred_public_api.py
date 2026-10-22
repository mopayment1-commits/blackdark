"""FRED macro API client."""

import pytest

from fred_public_api import fetch_macro_context, usage_stats, _indicator_from_series


@pytest.fixture(autouse=True)
def _reset_fred(monkeypatch, tmp_path):
    monkeypatch.setattr("fred_public_api._CACHE", {})
    monkeypatch.setattr("fred_public_api._RPS_TIMES", __import__("collections").deque())
    usage = tmp_path / "fred_api_usage.json"
    monkeypatch.setattr("fred_public_api._USAGE_PATH", usage)
    monkeypatch.setattr("fred_public_api.FRED_API_KEY", "test-key")
    monkeypatch.setattr("fred_public_api.FRED_DAILY_LIMIT", 1000)


def test_usage_stats_configured():
    stats = usage_stats()
    assert stats["configured"] is True
    assert stats["remaining_today"] == 1000


@pytest.mark.asyncio
async def test_indicator_from_series(monkeypatch):
    async def fake_obs(series_id, *, limit=2):
        if series_id == "FEDFUNDS":
            return [{"date": "2026-09-01", "value": 5.25}, {"date": "2026-08-01", "value": 5.0}]
        return []

    monkeypatch.setattr("fred_public_api._fetch_observations", fake_obs)
    row = await _indicator_from_series(
        "fed_funds_rate",
        {"series_id": "FEDFUNDS", "title": "Fed funds", "unit": "percent"},
    )
    assert row["value"] == 5.25
    assert row.get("change_from_prior") == 0.25


@pytest.mark.asyncio
async def test_fetch_macro_context(monkeypatch):
    async def fake_ind(key, meta):
        return {"series_id": meta["series_id"], "value": 1.0, "date": "2026-01-01"}

    monkeypatch.setattr("fred_public_api._indicator_from_series", fake_ind)
    ctx = await fetch_macro_context()
    assert ctx["ok"] is True
    assert "fed_funds_rate" in ctx["indicators"]


@pytest.mark.asyncio
async def test_not_configured(monkeypatch):
    monkeypatch.setattr("fred_public_api.FRED_API_KEY", "")
    ctx = await fetch_macro_context()
    assert ctx["ok"] is False
    assert ctx["error"] == "not_configured"


def test_public_fred_usage_route():
    from dashboard import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    res = client.get("/api/public/macro/fred/usage")
    assert res.status_code == 200
    assert "daily_limit" in res.json()


@pytest.mark.asyncio
async def test_oracle_quick_includes_fred(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_macro():
        return {
            "fetched_ok": True,
            "source": "fred",
            "attribution": "Data: FRED",
            "indicators": {"fed_funds_rate": {"value": 5.0}},
        }

    async def fake_spot(pair):
        return {
            "price": 1.0,
            "change_24h": 0.0,
            "volume": 1.0,
            "quote_volume": 1.0,
            "source": "binance_rest:test",
        }

    monkeypatch.setattr("fred_public_api.fetch_macro_context", fake_macro)
    monkeypatch.setattr("binance_public_api.fetch_public_spot_market", fake_spot)

    async def no_defi(a):
        return {"fetched_ok": False}

    monkeypatch.setattr("defillama_public_api.fetch_defi_context_for_asset", no_defi)

    async def passthrough(m, a, session=None):
        return m

    monkeypatch.setattr("coinmarketcap_api.enrich_market_with_cmc_metadata", passthrough)

    client = TestClient(app)
    res = client.get("/oracle/ETH/quick?lang=en")
    assert res.status_code == 200
    assert res.json().get("fred_macro_context", {}).get("indicators")
