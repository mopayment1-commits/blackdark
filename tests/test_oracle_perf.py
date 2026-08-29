"""Oracle perf harness for cProfile — exercises quick, explain, and unified paths."""

from __future__ import annotations

import asyncio

import pytest

ASSETS = ["BTC", "ETH", "SOL", "ADA", "AAVE", "ARB", "LINK", "XRP"]


@pytest.fixture(scope="module")
def oracle_client():
    from dashboard import app
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        yield client


def test_oracle_quick_perf_profile(oracle_client):
    for asset in ASSETS * 5:
        response = oracle_client.get(f"/oracle/{asset}/quick?ux_mode=beginner&lang=en")
        assert response.status_code == 200
        assert "opportunity_score" in response.json()


def test_oracle_quick_ar_lang_perf_profile(oracle_client):
    for asset in ASSETS * 3:
        response = oracle_client.get(f"/oracle/{asset}/quick?ux_mode=beginner&lang=ar")
        assert response.status_code == 200


def test_oracle_explain_perf_profile(oracle_client):
    for asset in ASSETS * 2:
        response = oracle_client.get(f"/oracle/{asset}/explain")
        assert response.status_code in {200, 403, 404}


def test_unified_oracle_compute_perf_profile():
    async def _run() -> None:
        from oracle_unified import compute_unified_oracle

        for asset in ASSETS * 4:
            await compute_unified_oracle(
                asset,
                price=50_000.0 if asset == "BTC" else 3_000.0,
                quote_volume=1_500_000_000.0,
                change=2.5,
                include_ml=False,
            )

    asyncio.run(_run())
