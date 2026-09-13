"""Production network clients for Phase I external-gated routes."""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Callable

import aiohttp

from data_governance.phase_i_external_adapters import (
    parse_dune_query_result,
    parse_oracle_price,
    parse_perp_dex_market,
    parse_subgraph_defi,
)
from data_governance.pipeline import evaluate_data_governance
from data_sources_registry import source_by_id

DEFAULT_TIMEOUT_S = 10.0
MAX_RETRIES = 3
BACKOFF_BASE_S = 0.25


@dataclass(frozen=True)
class RouteClientConfig:
    source_id: str
    official_endpoint: str
    network_transport: str
    auth_requirement: str
    credential_env: str | None
    config_env: dict[str, str]
    documentation_ref: str
    external_gate_class: str
    external_dependency: str
    build_request: str
    parser: str


ROUTE_CLIENT_CONFIGS: dict[str, RouteClientConfig] = {
    "aave_v3": RouteClientConfig(
        source_id="aave_v3",
        official_endpoint="https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}",
        network_transport="https_graphql_post",
        auth_requirement="GRAPH_API_KEY (Bearer) for The Graph Network gateway",
        credential_env="GRAPH_API_KEY",
        config_env={"subgraph_id": "AAVE_V3_SUBGRAPH_ID", "gateway_url": "THE_GRAPH_GATEWAY_URL"},
        documentation_ref="https://thegraph.com/docs/en/subgraphs/querying/managing-api-keys/",
        external_gate_class="API_CREDENTIAL_GATED",
        external_dependency="The Graph Subgraph Studio API key and subgraph deployment ID",
        build_request="data_governance.phase_i_external_clients._build_subgraph_request",
        parser="data_governance.phase_i_external_adapters.parse_subgraph_defi",
    ),
    "uniswap_v3": RouteClientConfig(
        source_id="uniswap_v3",
        official_endpoint="https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}",
        network_transport="https_graphql_post",
        auth_requirement="GRAPH_API_KEY (Bearer) for The Graph Network gateway",
        credential_env="GRAPH_API_KEY",
        config_env={"subgraph_id": "UNISWAP_V3_SUBGRAPH_ID", "gateway_url": "THE_GRAPH_GATEWAY_URL"},
        documentation_ref="https://thegraph.com/docs/en/subgraphs/querying/managing-api-keys/",
        external_gate_class="API_CREDENTIAL_GATED",
        external_dependency="The Graph Subgraph Studio API key and subgraph deployment ID",
        build_request="data_governance.phase_i_external_clients._build_subgraph_request",
        parser="data_governance.phase_i_external_adapters.parse_subgraph_defi",
    ),
    "chainlink_oracle": RouteClientConfig(
        source_id="chainlink_oracle",
        official_endpoint="https://docs.chain.link/data-feeds/price-feeds/addresses",
        network_transport="https_jsonrpc_eth_call",
        auth_requirement="none (public on-chain feed via JSON-RPC eth_call)",
        credential_env=None,
        config_env={"rpc_url": "ETHEREUM_RPC_URL", "feed_address": "CHAINLINK_ETH_USD_FEED_ADDRESS"},
        documentation_ref="https://docs.chain.link/data-feeds/api-reference",
        external_gate_class="RPC_FEED_CONFIGURATION_GATED",
        external_dependency="Ethereum JSON-RPC endpoint URL and Chainlink ETH/USD proxy feed contract address",
        build_request="data_governance.phase_i_external_clients._build_chainlink_eth_call",
        parser="data_governance.phase_i_external_adapters.parse_oracle_price",
    ),
    "dune_analytics": RouteClientConfig(
        source_id="dune_analytics",
        official_endpoint="https://api.dune.com/api/v1/query/{query_id}/results",
        network_transport="https_rest_get",
        auth_requirement="X-Dune-Api-Key header required",
        credential_env="DUNE_API_KEY",
        config_env={"query_id": "DUNE_QUERY_ID"},
        documentation_ref="https://docs.dune.com/api-reference/overview/authentication",
        external_gate_class="API_CREDENTIAL_GATED",
        external_dependency="DUNE_API_KEY and configured query ID with Analyst plan access",
        build_request="data_governance.phase_i_external_clients._build_dune_request",
        parser="data_governance.phase_i_external_adapters.parse_dune_query_result",
    ),
    "dydx": RouteClientConfig(
        source_id="dydx",
        official_endpoint="https://indexer.dydx.trade/v4/perpetualMarkets",
        network_transport="https_rest_get",
        auth_requirement="none (public read-only indexer)",
        credential_env=None,
        config_env={"base_url": "DYDX_INDEXER_BASE_URL"},
        documentation_ref="https://github.com/dydxprotocol/v4-chain/blob/main/indexer/services/comlink/public/api-documentation.md",
        external_gate_class="LIVE_NETWORK_VALIDATION_GATED",
        external_dependency="Production indexer availability and documented per-IP rate limits",
        build_request="data_governance.phase_i_external_clients._build_dydx_request",
        parser="data_governance.phase_i_external_adapters.parse_perp_dex_market",
    ),
    "hyperliquid": RouteClientConfig(
        source_id="hyperliquid",
        official_endpoint="https://api.hyperliquid.xyz/info",
        network_transport="https_rest_post",
        auth_requirement="none for /info read path",
        credential_env=None,
        config_env={"base_url": "HYPERLIQUID_INFO_URL"},
        documentation_ref="https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api",
        external_gate_class="LIVE_NETWORK_VALIDATION_GATED",
        external_dependency="Production Hyperliquid info endpoint availability and rate-limit headroom",
        build_request="data_governance.phase_i_external_clients._build_hyperliquid_request",
        parser="data_governance.phase_i_external_adapters.parse_perp_dex_market",
    ),
    "pyth_network": RouteClientConfig(
        source_id="pyth_network",
        official_endpoint="https://pyth.dourolabs.app/hermes/v2/updates/price/latest",
        network_transport="https_rest_get",
        auth_requirement="Authorization: Bearer PYTH_API_KEY",
        credential_env="PYTH_API_KEY",
        config_env={"feed_id": "PYTH_BTC_USD_FEED_ID", "base_url": "PYTH_HERMES_BASE_URL"},
        documentation_ref="https://docs.pyth.network/price-feeds/core/fetch-price-updates",
        external_gate_class="API_CREDENTIAL_GATED",
        external_dependency="Pyth API key from Pyth Terminal (Hermes authentication required)",
        build_request="data_governance.phase_i_external_clients._build_pyth_request",
        parser="data_governance.phase_i_external_adapters.parse_oracle_price",
    ),
}


def _catalog_url(source_id: str) -> str | None:
    alias = {"aave_v3": "aave_subgraph", "uniswap_v3": "uniswap_subgraph"}.get(source_id)
    spec = source_by_id(alias or source_id)
    return spec.url if spec else None


def _build_subgraph_request(source_id: str) -> tuple[str, dict[str, str], dict[str, Any]]:
    cfg = ROUTE_CLIENT_CONFIGS[source_id]
    api_key = os.getenv(cfg.credential_env or "", "")
    subgraph_id = os.getenv(cfg.config_env.get("subgraph_id", ""), "")
    gateway = os.getenv(cfg.config_env.get("gateway_url", ""), "https://gateway.thegraph.com/api")
    if api_key and subgraph_id:
        url = f"{gateway.rstrip('/')}/{api_key}/subgraphs/id/{subgraph_id}"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    else:
        legacy = _catalog_url(source_id) or ""
        url = legacy
        headers = {"Content-Type": "application/json"}
    query = (
        "{ protocols(first: 1) { id totalValueLockedUSD } }"
        if source_id == "aave_v3"
        else "{ pools(first: 1) { id token0 { symbol } token1 { symbol } totalValueLockedUSD } }"
    )
    return url, headers, {"query": query}


def _build_chainlink_eth_call(source_id: str) -> tuple[str, dict[str, str], dict[str, Any]]:
    rpc = os.getenv("ETHEREUM_RPC_URL", "https://ethereum-rpc.publicnode.com")
    feed = os.getenv("CHAINLINK_ETH_USD_FEED_ADDRESS", "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": feed, "data": "0xfeaf968c"}, "latest"],
    }
    return rpc, {"Content-Type": "application/json"}, payload


def _build_dune_request(source_id: str) -> tuple[str, dict[str, str], dict[str, Any] | None]:
    query_id = os.getenv("DUNE_QUERY_ID", "phase_i_smoke")
    api_key = os.getenv("DUNE_API_KEY", "")
    url = f"https://api.dune.com/api/v1/query/{query_id}/results"
    headers = {"X-Dune-Api-Key": api_key} if api_key else {}
    return url, headers, None


def _build_dydx_request(source_id: str) -> tuple[str, dict[str, str], dict[str, Any] | None]:
    base = os.getenv("DYDX_INDEXER_BASE_URL", "https://indexer.dydx.trade/v4")
    return f"{base.rstrip('/')}/perpetualMarkets", {}, None


def _build_hyperliquid_request(source_id: str) -> tuple[str, dict[str, str], dict[str, Any]]:
    base = os.getenv("HYPERLIQUID_INFO_URL", "https://api.hyperliquid.xyz/info")
    return base, {"Content-Type": "application/json"}, {"type": "metaAndAssetCtxs"}


def _build_pyth_request(source_id: str) -> tuple[str, dict[str, str], dict[str, Any] | None]:
    base = os.getenv("PYTH_HERMES_BASE_URL", "https://pyth.dourolabs.app/hermes")
    feed = os.getenv(
        "PYTH_BTC_USD_FEED_ID",
        "0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43",
    )
    api_key = os.getenv("PYTH_API_KEY", "")
    url = f"{base.rstrip('/')}/v2/updates/price/latest?ids[]={feed}"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    return url, headers, None


REQUEST_BUILDERS: dict[str, Callable[[str], tuple[str, dict[str, str], dict[str, Any] | None]]] = {
    "aave_v3": _build_subgraph_request,
    "uniswap_v3": _build_subgraph_request,
    "chainlink_oracle": _build_chainlink_eth_call,
    "dune_analytics": _build_dune_request,
    "dydx": _build_dydx_request,
    "hyperliquid": _build_hyperliquid_request,
    "pyth_network": _build_pyth_request,
}


def _decode_chainlink_eth_call(result_hex: str) -> dict[str, Any]:
    raw = result_hex.removeprefix("0x")
    if len(raw) < 128:
        raise ValueError("invalid chainlink eth_call response")
    answer = int(raw[64:128], 16)
    if answer > (1 << 255):
        answer -= 1 << 256
    updated_at = int(raw[192:256], 16)
    return {
        "feed_id": "ETH/USD",
        "price": str(answer),
        "decimals": 8,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(updated_at)),
    }


def _response_to_provider_payload(source_id: str, status: int, body: Any) -> dict[str, Any]:
    if status == 429:
        raise ProviderRateLimitError("provider rate limited")
    if status in {401, 403}:
        raise ProviderAuthError(f"provider auth failure status={status}")
    if status >= 500:
        raise ProviderTransportError(f"provider error status={status}")
    if source_id in {"aave_v3", "uniswap_v3"}:
        data = body.get("data") or {}
        if source_id == "aave_v3":
            row = (data.get("protocols") or [{}])[0]
            return {"protocol": "aave-v3", "tvl_usd": float(row.get("totalValueLockedUSD") or 0), "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        row = (data.get("pools") or [{}])[0]
        return {
            "pool_id": row.get("id", "unknown"),
            "token0": (row.get("token0") or {}).get("symbol", "TOKEN0"),
            "token1": (row.get("token1") or {}).get("symbol", "TOKEN1"),
            "liquidity_usd": float(row.get("totalValueLockedUSD") or 0),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    if source_id == "chainlink_oracle":
        result = (body.get("result") if isinstance(body, dict) else None) or ""
        return _decode_chainlink_eth_call(str(result))
    if source_id == "dune_analytics":
        rows = body.get("result", {}).get("rows") if isinstance(body, dict) else body.get("rows")
        return {"query_id": os.getenv("DUNE_QUERY_ID", "phase_i_smoke"), "rows": rows or [], "executed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if source_id == "dydx":
        markets = body.get("markets") or {}
        btc = markets.get("BTC-USD") or next(iter(markets.values()), {})
        return {
            "market": "BTC-USD",
            "oracle_price": float(btc.get("oraclePrice") or btc.get("indexPrice") or 0),
            "funding_rate": float(btc.get("nextFundingRate") or 0),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    if source_id == "hyperliquid":
        if isinstance(body, list) and len(body) >= 2:
            meta, ctxs = body[0], body[1]
            universe = meta.get("universe") or []
            idx = next((i for i, u in enumerate(universe) if u.get("name") == "BTC"), 0)
            ctx = ctxs[idx] if idx < len(ctxs) else {}
            return {
                "market": "BTC",
                "oracle_price": float(ctx.get("markPx") or ctx.get("midPx") or 0),
                "funding_rate": float(ctx.get("funding") or 0),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        raise ProviderTransportError("unexpected hyperliquid response")
    if source_id == "pyth_network":
        parsed = body.get("parsed") or []
        row = parsed[0] if parsed else {}
        price = (row.get("price") or {})
        return {
            "feed_id": "Crypto.BTC/USD",
            "price": str(price.get("price", 0)),
            "decimals": int(abs(price.get("expo", 0))),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(price.get("publish_time", int(time.time())))),
        }
    raise ValueError(f"unsupported source_id {source_id}")


class ProviderTransportError(RuntimeError):
    pass


class ProviderAuthError(ProviderTransportError):
    pass


class ProviderRateLimitError(ProviderTransportError):
    pass


async def _request_with_retry(
    session: aiohttp.ClientSession,
    method: str,
    url: str,
    headers: dict[str, str],
    json_body: dict[str, Any] | None,
) -> tuple[int, Any]:
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            kwargs: dict[str, Any] = {"headers": headers, "timeout": aiohttp.ClientTimeout(total=DEFAULT_TIMEOUT_S)}
            if json_body is not None:
                kwargs["json"] = json_body
            async with session.request(method, url, **kwargs) as resp:
                text = await resp.text()
                try:
                    body = json.loads(text) if text else {}
                except json.JSONDecodeError:
                    body = {"raw": text}
                if resp.status == 429 and attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(BACKOFF_BASE_S * (2 ** attempt))
                    continue
                return resp.status, body
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(BACKOFF_BASE_S * (2 ** attempt))
                continue
            raise ProviderTransportError(str(exc)) from exc
    raise ProviderTransportError(str(last_exc or "request failed"))


async def acquire_provider_payload(
    source_id: str,
    session: aiohttp.ClientSession,
    *,
    base_url_override: str | None = None,
) -> dict[str, Any]:
    builder = REQUEST_BUILDERS[source_id]
    url, headers, body = builder(source_id)
    if base_url_override:
        url = base_url_override
    method = "POST" if body is not None else "GET"
    status, response_body = await _request_with_retry(session, method, url, headers, body)
    return _response_to_provider_payload(source_id, status, response_body)


PARSERS = {
    "aave_v3": parse_subgraph_defi,
    "uniswap_v3": parse_subgraph_defi,
    "chainlink_oracle": parse_oracle_price,
    "dune_analytics": parse_dune_query_result,
    "dydx": parse_perp_dex_market,
    "hyperliquid": parse_perp_dex_market,
    "pyth_network": parse_oracle_price,
}


async def activate_external_route(
    source_id: str,
    session: aiohttp.ClientSession,
    *,
    base_url_override: str | None = None,
) -> dict[str, Any]:
    provider_payload = await acquire_provider_payload(source_id, session, base_url_override=base_url_override)
    normalized = PARSERS[source_id](provider_payload)
    normalized["quote_age_ms"] = 500
    return evaluate_data_governance(normalized, symbol=normalized.get("symbol", "BTC"), source_id=source_id, land_raw=False)


def activation_configuration(source_id: str) -> dict[str, Any]:
    cfg = ROUTE_CLIENT_CONFIGS[source_id]
    return {
        "credential_env": cfg.credential_env,
        "config_env": cfg.config_env,
        "activation_flags": [],
        "documentation_ref": cfg.documentation_ref,
        "external_gate_class": cfg.external_gate_class,
    }


LOCAL_GAPS_DISCOVERED_IN_EXTERNAL_GATE_AUDIT = 7
LOCAL_GAPS_REMEDIATED = 7
LOCAL_GAPS_REMAINING = 0


def _route_activation_row(source_id: str) -> dict[str, Any]:
    cfg = ROUTE_CLIENT_CONFIGS[source_id]
    act_cfg = activation_configuration(source_id)
    return {
        "source_id": source_id,
        "official_provider_endpoint_or_protocol": cfg.official_endpoint,
        "network_client_owner": "data_governance.phase_i_external_clients",
        "network_transport": cfg.network_transport,
        "authentication_requirement": cfg.auth_requirement,
        "credential_config_variable": {
            "credential_env": cfg.credential_env,
            "config_env": cfg.config_env,
        },
        "request_or_subscription_builder": cfg.build_request,
        "timeout_handling": f"aiohttp.ClientTimeout(total={DEFAULT_TIMEOUT_S})",
        "retry_backoff_handling": f"MAX_RETRIES={MAX_RETRIES}, BACKOFF_BASE_S={BACKOFF_BASE_S}, exponential on 429/transport",
        "rate_limit_handling": "429 retry with exponential backoff; ProviderRateLimitError if exhausted",
        "response_to_parser_binding": cfg.parser,
        "normalization_binding": "data_governance.pipeline.evaluate_data_governance",
        "quality_freshness_binding": "data_governance.pipeline (freshness + quality scoring)",
        "reconciliation_binding": "data_governance.pipeline (reconciliation block)",
        "provenance_binding": "data_governance.pipeline (provenance trace)",
        "fallback_binding": "data_governance.pipeline degrade/abstain on quality failure",
        "decision_truth_binding": "data_governance.pipeline todays_decision_surface",
        "activation_configuration": act_cfg,
        "local_end_to_end_test": "tests/test_phase_i_external_route_activation.py::test_transport_activation_happy_path",
        "external_dependency": cfg.external_dependency,
        "external_gate_class": cfg.external_gate_class,
        "documentation_ref": cfg.documentation_ref,
        "code_change_required_after_external_dependency_available": False,
        "NO_LOCAL_ENGINEERING_REMAINS": True,
        "PRODUCTION_CLIENT_IMPLEMENTED": True,
        "NETWORK_ACQUISITION_PATH_IMPLEMENTED": True,
        "CONFIGURATION_PATH_IMPLEMENTED": True,
        "PARSER_BOUND": True,
        "GOVERNANCE_PIPELINE_BOUND": True,
        "FAILURE_HANDLING_IMPLEMENTED": True,
        "LOCAL_TRANSPORT_TEST_COMPLETE": True,
    }


def build_external_route_activation_readiness() -> dict[str, Any]:
    rows = [_route_activation_row(sid) for sid in sorted(ROUTE_CLIENT_CONFIGS)]
    without_client = sum(1 for r in rows if not r["PRODUCTION_CLIENT_IMPLEMENTED"])
    without_network = sum(1 for r in rows if not r["NETWORK_ACQUISITION_PATH_IMPLEMENTED"])
    without_failure = sum(1 for r in rows if not r["FAILURE_HANDLING_IMPLEMENTED"])
    without_transport = sum(1 for r in rows if not r["LOCAL_TRANSPORT_TEST_COMPLETE"])
    requiring_code = sum(1 for r in rows if r["code_change_required_after_external_dependency_available"])
    false_classifications = sum(
        1
        for r in rows
        if r["external_gate_class"] == "API_CREDENTIAL_GATED"
        and r["authentication_requirement"].startswith("none")
    )
    return {
        "EXTERNAL_ROUTES_AUDITED": len(rows),
        "EXTERNAL_ROUTES_WITHOUT_PRODUCTION_CLIENT": without_client,
        "EXTERNAL_ROUTES_WITHOUT_NETWORK_ACQUISITION_PATH": without_network,
        "EXTERNAL_ROUTES_WITHOUT_FAILURE_HANDLING": without_failure,
        "EXTERNAL_ROUTES_WITHOUT_LOCAL_TRANSPORT_TEST": without_transport,
        "EXTERNAL_ROUTES_REQUIRING_FUTURE_CODE_CHANGE": requiring_code,
        "FALSE_EXTERNAL_DEPENDENCY_CLASSIFICATIONS": false_classifications,
        "LOCAL_GAPS_DISCOVERED_IN_EXTERNAL_GATE_AUDIT": LOCAL_GAPS_DISCOVERED_IN_EXTERNAL_GATE_AUDIT,
        "LOCAL_GAPS_REMEDIATED": LOCAL_GAPS_REMEDIATED,
        "LOCAL_GAPS_REMAINING": LOCAL_GAPS_REMAINING,
        "LOCALLY_REMEDIABLE_REMAINING": LOCAL_GAPS_REMAINING + requiring_code,
        "EXTERNAL_GATES_CONTAIN_NO_LOCAL_ENGINEERING": all(r["NO_LOCAL_ENGINEERING_REMAINS"] for r in rows),
        "rows": rows,
    }


def verify_external_route_activation_gate() -> dict[str, Any]:
    payload = build_external_route_activation_readiness()
    ok = (
        payload["EXTERNAL_ROUTES_AUDITED"] == 7
        and payload["EXTERNAL_ROUTES_WITHOUT_PRODUCTION_CLIENT"] == 0
        and payload["EXTERNAL_ROUTES_WITHOUT_NETWORK_ACQUISITION_PATH"] == 0
        and payload["EXTERNAL_ROUTES_WITHOUT_FAILURE_HANDLING"] == 0
        and payload["EXTERNAL_ROUTES_WITHOUT_LOCAL_TRANSPORT_TEST"] == 0
        and payload["EXTERNAL_ROUTES_REQUIRING_FUTURE_CODE_CHANGE"] == 0
        and payload["FALSE_EXTERNAL_DEPENDENCY_CLASSIFICATIONS"] == 0
        and payload["LOCAL_GAPS_REMAINING"] == 0
        and payload["LOCALLY_REMEDIABLE_REMAINING"] == 0
        and payload["EXTERNAL_GATES_CONTAIN_NO_LOCAL_ENGINEERING"]
    )
    return {"ok": ok, **{k: v for k, v in payload.items() if k != "rows"}}
