"""Smoke tests for TODAY feed + API."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_today_feed_shape():
    from today_feed import build_today_feed

    payload = await build_today_feed(user=None)
    assert "greeting" in payload
    assert "since_you_left" in payload
    assert "market_pulse" in payload
    assert "needs_your_attention" in payload
    assert len(payload["needs_your_attention"]) == 3
    assert payload["data_status"] in {"live", "delayed"}


@pytest.mark.asyncio
async def test_today_api_endpoint():
    from dashboard import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/today")
        assert res.status_code == 200
        data = res.json()
        assert "since_you_left" in data
        assert "ask_suggestions" in data
