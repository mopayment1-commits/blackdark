"""Central data mesh — per-source fetch + Oracle hub integration."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_build_mesh_at_least_two_free_sources():
    from central_data_mesh import build_central_mesh_context

    mesh = await build_central_mesh_context("BTC", profile="minimal")
    assert mesh.get("enabled") is True
    active = mesh.get("sources_active") or []
    assert len(active) >= 2
    assert "frankfurter" in active
    assert "sec_edgar" in active


@pytest.mark.asyncio
async def test_merge_mesh_into_hub_enriches_factors():
    from central_data_mesh import build_central_mesh_context, merge_mesh_into_hub

    mesh = await build_central_mesh_context("BTC", profile="minimal")
    hub = merge_mesh_into_hub({"enabled": True, "macro": {}, "sentiment": {}}, mesh)
    assert hub.get("macro", {}).get("fx_usd_rates")
    assert len(mesh.get("sources_active") or []) >= 2


def test_oracle_quick_includes_central_mesh():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/oracle/BTC/quick?lang=en")
    assert res.status_code == 200
    body = res.json()
    mesh = body.get("central_data_mesh") or {}
    active = mesh.get("sources_active") or []
    assert len(active) >= 2


def test_mesh_sources_have_fallback_when_key_missing():
    from central_data_mesh import fetch_marketaux_news
    import aiohttp

    async def _run():
        async with aiohttp.ClientSession() as session:
            return await fetch_marketaux_news(session, symbol="BTC")

    import asyncio

    row = asyncio.run(_run())
    if not (__import__("os").getenv("MARKETAUX_API_KEY")):
        assert row.get("ok") is False
        assert row.get("fallback") == "missing_api_key"
