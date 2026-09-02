"""Shared helpers for batch dedicated modules — Extract Function (CLOSURE-MANDATE-FINAL item 3)."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from cap646.evidence_class import ai_compliance_footer

_ROOT = Path(__file__).resolve().parents[1]
_SEED_PATH = _ROOT / "data/legal_retail_commercial_seed.json"


def seed() -> dict[str, Any]:
    if _SEED_PATH.is_file():
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    return {}


def sym(params: dict[str, Any]) -> str:
    return str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")


def addr(params: dict[str, Any]) -> str:
    return str(params.get("address") or params.get("wallet") or "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb").strip()


def success_from(payload: Any) -> bool:
    if isinstance(payload, dict):
        if "success" in payload:
            return bool(payload.get("success"))
        if "ok" in payload:
            return bool(payload.get("ok"))
        return bool(payload)
    return bool(payload)


def wrap(
    capability_id: int,
    *,
    expected_surface: dict[int, str],
    symbol: str,
    payload_key: str,
    payload: Any,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "capability_id": capability_id,
        "surface": expected_surface[capability_id],
        "symbol": symbol,
        payload_key: payload,
        "success": success_from(payload),
    }
    if extra:
        body.update(extra)
    return ai_compliance_footer(body)


def provenance_hot_storage_payload(symbol: str) -> dict[str, Any]:
    """Shared #63 / #106 data-quality provenance payload — Eliminate jscpd clone."""
    from data_provenance_score import compute_data_provenance_score
    from hot_storage import get_hot_storage_stats

    provenance = compute_data_provenance_score(symbol=symbol)
    hot = get_hot_storage_stats()
    return {
        "provenance": provenance,
        "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else hot,
    }


async def holder_analytics_bundle(symbol: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Fetch holder analytics once — shared by batch01 #7/#8/#9 (CLOSURE-MANDATE-VERIFY)."""
    from bd_platform.free_integrations import holder_analytics

    dist = await holder_analytics(symbol)
    metrics = dist.get("metrics") or {}
    return dist, metrics


def holder_analytics_footer(
    capability_id: int,
    surface: str,
    symbol: str,
    dist: dict[str, Any],
    metrics: dict[str, Any],
    *,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Common ai_compliance_footer for holder-analytics capabilities."""
    body: dict[str, Any] = {
        "capability_id": capability_id,
        "surface": surface,
        "symbol": symbol,
        "holder_metrics": metrics,
        "source": dist.get("source"),
        "success": bool(dist.get("available")),
    }
    if extra:
        body.update(extra)
    return ai_compliance_footer(body)


async def holder_analytics_locked(symbol: str) -> tuple[dict[str, Any], dict[str, Any], float]:
    """Bundle + locked_supply_pct — shared by batch01 #8/#9 (Parameterize Function)."""
    dist, metrics = await holder_analytics_bundle(symbol)
    locked_pct = float(metrics.get("locked_supply_pct") or 0)
    return dist, metrics, locked_pct


def exchange_netflow_probe(params: dict[str, Any], symbol: str) -> tuple[str, dict[str, Any]]:
    """Shared exchange netflow probe — batch01 #15/#44 (CLOSURE-MANDATE-VERIFY)."""
    from bd_platform.heroes_capability_layer import exchange_netflow_intelligence_48

    exchange = str(params.get("exchange") or "binance")
    netflow = exchange_netflow_intelligence_48(exchange=exchange, asset=symbol)
    return exchange, netflow


def exchange_netflow_footer(
    capability_id: int,
    surface: str,
    symbol: str,
    exchange: str,
    netflow: dict[str, Any],
    *,
    flow_payload_key: str,
) -> dict[str, Any]:
    """Parameterize netflow payload key (#15 exchange_flow vs #44 netflow)."""
    return ai_compliance_footer(
        {
            "capability_id": capability_id,
            "surface": surface,
            "symbol": symbol,
            "exchange": exchange,
            flow_payload_key: netflow,
            "netflow_proxy": netflow.get("netflow_proxy"),
            "success": netflow.get("ok", True),
        }
    )


def make_wrap_binding(expected_surface: dict[int, str]) -> Callable[..., dict[str, Any]]:
    """Factory for batch-specific wrap helpers — single Extract Function site (CWE-1041)."""

    def binding(
        capability_id: int,
        *,
        symbol: str,
        payload_key: str,
        payload: Any,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return wrap(
            capability_id,
            expected_surface=expected_surface,
            symbol=symbol,
            payload_key=payload_key,
            payload=payload,
            extra=extra,
        )

    return binding


async def execute_dedicated_caps(
    capability_id: int,
    *,
    params: dict[str, Any] | None,
    dedicated_ids: frozenset[int],
    overlap_batch01_ids: frozenset[int],
    dispatch: dict[int, Callable[..., Awaitable[dict[str, Any]]]],
    overlap_error: str,
    not_dedicated_error: str,
) -> dict[str, Any]:
    """Shared execute() tail for batch02/batch03 dedicated modules."""
    if capability_id in overlap_batch01_ids:
        raise ValueError(overlap_error)
    if capability_id not in dedicated_ids:
        raise ValueError(not_dedicated_error)
    params = dict(params or {})
    symbol = sym(params)
    address = addr(params)
    fn = dispatch[capability_id]
    return await fn(symbol=symbol, address=address, params=params)
