"""Exchange Inflow Intelligence — paired module for #242 closure requirements."""

from __future__ import annotations

import time
from typing import Any

from bd_platform.exchange_flow_common import (
    build_address_dedupe,
    build_chain_validation,
    build_cluster_metadata,
    build_exchange_breakdown,
    format_usd,
    load_seed,
    reconcile_flows,
)

_FEATURE_ID = 241
_STANDALONE = False
_MERGED_INTO = "Exchange Intelligence Hub (#734-736)"

_DISCLAIMER_TEXT = (
    "Exchange inflows represent on-chain movements from external addresses to labeled exchange "
    "addresses. Not all inflows indicate buying intent. Not investment advice."
)


def build_inflow_card(asset_data: dict[str, Any], seed: dict[str, Any]) -> dict[str, Any]:
    inflow = float(asset_data.get("inflow_usd", 0))
    outflow = float(asset_data.get("outflow_usd", 0))
    netflow = float(asset_data.get("netflow_usd", 0))

    reconciliation = reconcile_flows(inflow, outflow, netflow)
    cluster = build_cluster_metadata(seed)
    breakdown = build_exchange_breakdown(asset_data.get("exchange_breakdown") or {}, flow_key="inflow_usd")
    chain_val = build_chain_validation(asset_data.get("chain_breakdown") or {})
    dedupe = build_address_dedupe(asset_data.get("address_dedupe") or {})

    return {
        "feature_id": _FEATURE_ID,
        "asset": asset_data.get("symbol", "BTC"),
        "inflow_usd": inflow,
        "inflow_display": format_usd(inflow),
        "reconciliation": reconciliation,
        "cluster": cluster,
        "exchange_breakdown": breakdown,
        "chain_validation": chain_val,
        "address_dedupe": dedupe,
        "chart": asset_data.get("inflow_chart") or [],
        "risk_context_only": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
    }


def build_inflow_dashboard(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("assets") or {}).get(sym)
    if not asset_data:
        return {"ok": False, "error": "asset_not_tracked", "asset": sym}
    card = build_inflow_card({**asset_data, "symbol": sym}, seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {"ok": True, "feature_id": _FEATURE_ID, "standalone": _STANDALONE, "tab": "inflow", **card, "latency_ms": elapsed}
