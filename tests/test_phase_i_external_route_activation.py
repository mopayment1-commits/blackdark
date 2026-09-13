"""Transport-level activation tests for Phase I external-gated routes."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import aiohttp
import pytest
from aiohttp import web

from data_governance.phase_i_external_clients import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTransportError,
    ROUTE_CLIENT_CONFIGS,
    activate_external_route,
    acquire_provider_payload,
    build_external_route_activation_readiness,
    verify_external_route_activation_gate,
)

CHAINLINK_RESULT = (
    "0x"
    + "0" * 64
    + format(320050000000, "x").zfill(64)
    + "0" * 64
    + format(1714746101, "x").zfill(64)
    + "0" * 64
)

MOCK_RESPONSES: dict[str, Any] = {
    "aave_v3": {"data": {"protocols": [{"id": "1", "totalValueLockedUSD": "12500000000"}]}},
    "uniswap_v3": {
        "data": {
            "pools": [
                {
                    "id": "0x88e6a0c2ddd26feeb64f039a220c9844ea796cc8",
                    "token0": {"symbol": "USDC"},
                    "token1": {"symbol": "WETH"},
                    "totalValueLockedUSD": "450000000",
                }
            ]
        }
    },
    "chainlink_oracle": {"jsonrpc": "2.0", "id": 1, "result": CHAINLINK_RESULT},
    "dune_analytics": {"result": {"rows": [{"symbol": "BTC", "volume_usd": 1.2e9}]}},
    "dydx": {"markets": {"BTC-USD": {"oraclePrice": "65000", "nextFundingRate": "0.0001"}}},
    "hyperliquid": [{"universe": [{"name": "BTC"}]}, [{"markPx": "65001", "funding": "0.00012"}]],
    "pyth_network": {
        "parsed": [
            {
                "price": {"price": "6500025000000", "expo": -8, "publish_time": 1714746101},
            }
        ]
    },
}


def _make_handler(body: Any, status: int = 200):
    async def handler(request: web.Request) -> web.Response:
        if request.method == "POST":
            await request.json()
        return web.json_response(body, status=status)

    return handler


@pytest.fixture
async def mock_server():
    runners: list[web.AppRunner] = []

    async def _start(source_id: str, body: Any = None, status: int = 200) -> str:
        app = web.Application()
        app.router.add_route("*", "/{path:.*}", _make_handler(body or MOCK_RESPONSES[source_id], status))
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        runners.append(runner)
        port = site._server.sockets[0].getsockname()[1]  # type: ignore[attr-defined]
        return f"http://127.0.0.1:{port}/"

    yield _start

    for runner in runners:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_transport_activation_happy_path(mock_server):
    for source_id in ROUTE_CLIENT_CONFIGS:
        url = await mock_server(source_id)
        async with aiohttp.ClientSession() as session:
            result = await activate_external_route(source_id, session, base_url_override=url)
        assert result.get("data_governance_state")
        assert result.get("todays_decision_surface")
        assert (result.get("data_governance") or {}).get("provenance")


@pytest.mark.asyncio
async def test_acquire_provider_payload_via_client(mock_server):
    for source_id in ROUTE_CLIENT_CONFIGS:
        url = await mock_server(source_id)
        async with aiohttp.ClientSession() as session:
            payload = await acquire_provider_payload(source_id, session, base_url_override=url)
        assert payload


@pytest.mark.asyncio
@pytest.mark.parametrize("status,exc", [(401, ProviderAuthError), (403, ProviderAuthError), (500, ProviderTransportError)])
async def test_provider_error_statuses(mock_server, status, exc):
    url = await mock_server("dydx", body={"error": "fail"}, status=status)
    async with aiohttp.ClientSession() as session:
        with pytest.raises(exc):
            await acquire_provider_payload("dydx", session, base_url_override=url)


@pytest.mark.asyncio
async def test_rate_limit_raises(mock_server):
    url = await mock_server("dydx", body={"error": "rate"}, status=429)
    async with aiohttp.ClientSession() as session:
        with pytest.raises(ProviderRateLimitError):
            await acquire_provider_payload("dydx", session, base_url_override=url)


@pytest.mark.asyncio
async def test_malformed_response_raises(mock_server):
    async def bad_handler(request: web.Request) -> web.Response:
        return web.Response(text="not-json", status=200)

    app = web.Application()
    app.router.add_route("*", "/{path:.*}", bad_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]  # type: ignore[attr-defined]
    url = f"http://127.0.0.1:{port}/"
    try:
        async with aiohttp.ClientSession() as session:
            with pytest.raises((ProviderTransportError, ValueError, KeyError)):
                await acquire_provider_payload("hyperliquid", session, base_url_override=url)
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_connection_failure_raises():
    async with aiohttp.ClientSession() as session:
        with pytest.raises(ProviderTransportError):
            await acquire_provider_payload(
                "dydx",
                session,
                base_url_override="http://127.0.0.1:1/unreachable",
            )


def test_activation_readiness_matrix_gate():
    payload = build_external_route_activation_readiness()
    gate = verify_external_route_activation_gate()
    assert payload["EXTERNAL_ROUTES_AUDITED"] == 7
    assert payload["LOCAL_GAPS_DISCOVERED_IN_EXTERNAL_GATE_AUDIT"] == 7
    assert payload["LOCAL_GAPS_REMEDIATED"] == 7
    assert payload["LOCAL_GAPS_REMAINING"] == 0
    assert gate["ok"] is True
    for row in payload["rows"]:
        assert row["NO_LOCAL_ENGINEERING_REMAINS"] is True
        assert row["code_change_required_after_external_dependency_available"] is False


def test_public_routes_not_api_credential_gated():
    payload = build_external_route_activation_readiness()
    by_id = {r["source_id"]: r for r in payload["rows"]}
    assert by_id["dydx"]["external_gate_class"] == "LIVE_NETWORK_VALIDATION_GATED"
    assert by_id["hyperliquid"]["external_gate_class"] == "LIVE_NETWORK_VALIDATION_GATED"
    assert by_id["chainlink_oracle"]["external_gate_class"] == "RPC_FEED_CONFIGURATION_GATED"
    assert payload["FALSE_EXTERNAL_DEPENDENCY_CLASSIFICATIONS"] == 0
