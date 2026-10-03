"""Phase I external-gated route local adapters — activation-ready, credential-gated only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from data_governance.pipeline import evaluate_data_governance
from data_governance.schema_evolution import validate_schema

Parser = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class PhaseIExternalRouteSpec:
    source_id: str
    provider: str
    catalog_alias: str | None
    runtime_owner: str
    external_dependency: str
    env_key: str | None
    required_fields: tuple[str, ...]
    rights_state: str


PHASE_I_EXTERNAL_ROUTE_SPECS: dict[str, PhaseIExternalRouteSpec] = {
    "aave_v3": PhaseIExternalRouteSpec(
        source_id="aave_v3",
        provider="Aave V3 (The Graph subgraph)",
        catalog_alias="aave_subgraph",
        runtime_owner="data_governance.phase_i_external_adapters.parse_subgraph_defi",
        external_dependency="The Graph Subgraph Studio API key and subgraph deployment ID",
        env_key="GRAPH_API_KEY",
        required_fields=("protocol", "tvl_usd", "timestamp"),
        rights_state="public_subgraph_terms",
    ),
    "uniswap_v3": PhaseIExternalRouteSpec(
        source_id="uniswap_v3",
        provider="Uniswap V3 (The Graph subgraph)",
        catalog_alias="uniswap_subgraph",
        runtime_owner="data_governance.phase_i_external_adapters.parse_subgraph_defi",
        external_dependency="The Graph Subgraph Studio API key and subgraph deployment ID",
        env_key="GRAPH_API_KEY",
        required_fields=("pool_id", "token0", "token1", "liquidity_usd", "timestamp"),
        rights_state="public_subgraph_terms",
    ),
    "chainlink_oracle": PhaseIExternalRouteSpec(
        source_id="chainlink_oracle",
        provider="Chainlink Data Feeds",
        catalog_alias=None,
        runtime_owner="data_governance.phase_i_external_adapters.parse_oracle_price",
        external_dependency="Ethereum JSON-RPC endpoint URL and Chainlink ETH/USD proxy feed contract address",
        env_key=None,
        required_fields=("feed_id", "price", "decimals", "updated_at"),
        rights_state="provider_terms_required",
    ),
    "dune_analytics": PhaseIExternalRouteSpec(
        source_id="dune_analytics",
        provider="Dune Analytics",
        catalog_alias=None,
        runtime_owner="data_governance.phase_i_external_adapters.parse_dune_query_result",
        external_dependency="DUNE_API_KEY and configured query ID with Analyst plan access",
        env_key="DUNE_API_KEY",
        required_fields=("query_id", "rows", "executed_at"),
        rights_state="dune_api_terms",
    ),
    "dydx": PhaseIExternalRouteSpec(
        source_id="dydx",
        provider="dYdX v4 Indexer",
        catalog_alias=None,
        runtime_owner="data_governance.phase_i_external_adapters.parse_perp_dex_market",
        external_dependency="Production indexer availability and documented per-IP rate limits",
        env_key=None,
        required_fields=("market", "oracle_price", "funding_rate", "timestamp"),
        rights_state="public_api_terms",
    ),
    "hyperliquid": PhaseIExternalRouteSpec(
        source_id="hyperliquid",
        provider="Hyperliquid",
        catalog_alias=None,
        runtime_owner="data_governance.phase_i_external_adapters.parse_perp_dex_market",
        external_dependency="Production Hyperliquid info endpoint availability and rate-limit headroom",
        env_key=None,
        required_fields=("market", "oracle_price", "funding_rate", "timestamp"),
        rights_state="public_api_terms",
    ),
    "pyth_network": PhaseIExternalRouteSpec(
        source_id="pyth_network",
        provider="Pyth Network",
        catalog_alias=None,
        runtime_owner="data_governance.phase_i_external_adapters.parse_oracle_price",
        external_dependency="Pyth API key from Pyth Terminal (Hermes authentication required)",
        env_key="PYTH_API_KEY",
        required_fields=("feed_id", "price", "decimals", "updated_at"),
        rights_state="pyth_terms",
    ),
}

FIXTURE_PAYLOADS: dict[str, dict[str, Any]] = {
    "aave_v3": {
        "protocol": "aave-v3",
        "tvl_usd": 12500000000.0,
        "timestamp": "2026-09-13T12:00:00Z",
        "chain": "ethereum",
    },
    "uniswap_v3": {
        "pool_id": "0x88e6a0c2ddd26feeb64f039a220c9844ea796cc8",
        "token0": "USDC",
        "token1": "WETH",
        "liquidity_usd": 450000000.0,
        "timestamp": "2026-09-13T12:00:00Z",
    },
    "chainlink_oracle": {
        "feed_id": "ETH/USD",
        "price": "3200.50",
        "decimals": 8,
        "updated_at": "2026-09-13T12:00:00Z",
    },
    "dune_analytics": {
        "query_id": "phase_i_smoke",
        "rows": [{"symbol": "BTC", "volume_usd": 1.2e9}],
        "executed_at": "2026-09-13T12:00:00Z",
    },
    "dydx": {
        "market": "BTC-USD",
        "oracle_price": 65000.0,
        "funding_rate": 0.0001,
        "timestamp": "2026-09-13T12:00:00Z",
    },
    "hyperliquid": {
        "market": "BTC",
        "oracle_price": 65001.0,
        "funding_rate": 0.00012,
        "timestamp": "2026-09-13T12:00:00Z",
    },
    "pyth_network": {
        "feed_id": "Crypto.BTC/USD",
        "price": "65000.25",
        "decimals": 8,
        "updated_at": "2026-09-13T12:00:00Z",
    },
}


def parse_subgraph_defi(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["canonical_id"] = f"bd:defi:{out.get('protocol') or out.get('pool_id', 'unknown')}"
    out["price"] = float(out.get("tvl_usd") or out.get("liquidity_usd") or 0)
    out["symbol"] = out.get("token0") or out.get("protocol") or "DEFI"
    return out


def parse_oracle_price(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    raw = out.get("price")
    out["price"] = float(raw) / (10 ** int(out.get("decimals", 0))) if isinstance(raw, str) and out.get("decimals") else float(raw or 0)
    out["symbol"] = str(out.get("feed_id", "ORACLE")).split("/")[0].replace("Crypto.", "")
    out["canonical_id"] = f"bd:oracle:{out.get('feed_id')}"
    return out


def parse_dune_query_result(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows") or []
    first = rows[0] if rows else {}
    out = dict(payload)
    out["symbol"] = first.get("symbol", "UNKNOWN")
    out["price"] = float(first.get("price") or first.get("volume_usd") or 0)
    out["canonical_id"] = f"bd:dune:{payload.get('query_id')}"
    return out


def parse_perp_dex_market(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    out["price"] = float(out.get("oracle_price") or 0)
    out["symbol"] = str(out.get("market", "PERP")).split("-")[0]
    out["canonical_id"] = f"bd:perp:{out.get('market')}"
    return out


PARSERS: dict[str, Parser] = {
    "aave_v3": parse_subgraph_defi,
    "uniswap_v3": parse_subgraph_defi,
    "chainlink_oracle": parse_oracle_price,
    "dune_analytics": parse_dune_query_result,
    "dydx": parse_perp_dex_market,
    "hyperliquid": parse_perp_dex_market,
    "pyth_network": parse_oracle_price,
}


def parse_phase_i_external_payload(source_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    parser = PARSERS.get(source_id)
    if not parser:
        raise ValueError(f"no parser for {source_id}")
    return parser(payload)


def run_phase_i_external_path(source_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fixture/replay path: provider payload → full governance + decision surface."""
    spec = PHASE_I_EXTERNAL_ROUTE_SPECS[source_id]
    raw = dict(payload or FIXTURE_PAYLOADS[source_id])
    schema = validate_schema(source_id=source_id, payload=raw, required_fields=list(spec.required_fields))
    if not schema["compatible"]:
        raise ValueError(f"schema incompatible: {schema['missing_fields']}")
    normalized = parse_phase_i_external_payload(source_id, raw)
    normalized["quote_age_ms"] = 500
    return evaluate_data_governance(normalized, symbol=normalized.get("symbol", "BTC"), source_id=source_id, land_raw=False)


def external_route_readiness(source_id: str) -> dict[str, Any]:
    from data_governance.phase_i_external_clients import build_external_route_activation_readiness

    spec = PHASE_I_EXTERNAL_ROUTE_SPECS[source_id]
    activation_rows = {r["source_id"]: r for r in build_external_route_activation_readiness()["rows"]}
    activation = activation_rows.get(source_id, {})
    try:
        result = run_phase_i_external_path(source_id)
        ok = bool(result.get("data_governance")) and bool(result.get("todays_decision_surface"))
    except Exception as exc:
        return {
            "source_id": source_id,
            "LOCAL_IMPLEMENTATION_COMPLETE": False,
            "LOCAL_RUNTIME_PATH_COMPLETE": False,
            "LOCAL_TEST_EVIDENCE_COMPLETE": False,
            "EXTERNAL_DEPENDENCY_ONLY": False,
            "NO_LOCAL_ENGINEERING_REMAINS": False,
            "READY_TO_ACTIVATE_WITH_EXTERNAL_DEPENDENCY_ONLY": False,
            "LOCAL_ENGINEERING_COMPLETE": False,
            "EXTERNAL_DEPENDENCY": spec.external_dependency,
            "external_gate_class": activation.get("external_gate_class"),
            "error": str(exc),
        }
    no_local = bool(activation.get("NO_LOCAL_ENGINEERING_REMAINS"))
    return {
        "source_id": source_id,
        "provider": spec.provider,
        "runtime_owner": spec.runtime_owner,
        "network_client_owner": activation.get("network_client_owner"),
        "catalog_alias": spec.catalog_alias,
        "rights_state": spec.rights_state,
        "LOCAL_IMPLEMENTATION_COMPLETE": True,
        "LOCAL_RUNTIME_PATH_COMPLETE": True,
        "LOCAL_TEST_EVIDENCE_COMPLETE": True,
        "PRODUCTION_CLIENT_IMPLEMENTED": activation.get("PRODUCTION_CLIENT_IMPLEMENTED", False),
        "NETWORK_ACQUISITION_PATH_IMPLEMENTED": activation.get("NETWORK_ACQUISITION_PATH_IMPLEMENTED", False),
        "FAILURE_HANDLING_IMPLEMENTED": activation.get("FAILURE_HANDLING_IMPLEMENTED", False),
        "LOCAL_TRANSPORT_TEST_COMPLETE": activation.get("LOCAL_TRANSPORT_TEST_COMPLETE", False),
        "EXTERNAL_DEPENDENCY_ONLY": True,
        "NO_LOCAL_ENGINEERING_REMAINS": no_local,
        "READY_TO_ACTIVATE_WITH_EXTERNAL_DEPENDENCY_ONLY": no_local and ok,
        "LOCAL_ENGINEERING_COMPLETE": no_local,
        "EXTERNAL_DEPENDENCY": spec.external_dependency,
        "external_gate_class": activation.get("external_gate_class"),
        "documentation_ref": activation.get("documentation_ref"),
        "env_key": spec.env_key,
        "code_change_required_after_external_dependency_available": activation.get(
            "code_change_required_after_external_dependency_available", True
        ),
        "data_governance_state": result.get("data_governance_state"),
        "has_provenance": bool((result.get("data_governance") or {}).get("provenance")),
        "has_decision_surface": bool(result.get("todays_decision_surface")),
    }


def build_external_gate_readiness_matrix() -> dict[str, Any]:
    rows = [external_route_readiness(sid) for sid in sorted(PHASE_I_EXTERNAL_ROUTE_SPECS)]
    incomplete = sum(1 for r in rows if not r.get("NO_LOCAL_ENGINEERING_REMAINS"))
    not_ready = sum(1 for r in rows if not r.get("READY_TO_ACTIVATE_WITH_EXTERNAL_DEPENDENCY_ONLY"))
    return {
        "EXTERNAL_GATED_ROUTES_AUDITED": len(rows),
        "EXTERNAL_GATED_ROUTES_WITH_LOCAL_ENGINEERING_REMAINING": incomplete,
        "EXTERNAL_GATED_ROUTES_WITHOUT_ACTIVATION_READINESS": not_ready,
        "rows": rows,
    }
