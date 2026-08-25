"""Exchange Netflow Intelligence — paired module for #242 reconciliation."""

from __future__ import annotations

import time
from typing import Any

from bd_platform.exchange_flow_common import (
    build_cluster_metadata,
    format_usd,
    load_seed,
    reconcile_flows,
)

_FEATURE_ID = 243
_STANDALONE = False
_MERGED_INTO = "Exchange Intelligence Hub (#734-736)"

_DISCLAIMER_TEXT = (
    "Exchange netflow is the difference between inflows and outflows on labeled exchange addresses. "
    "Net outflow does not necessarily indicate selling. Not investment advice."
)


def build_netflow_card(asset_data: dict[str, Any], seed: dict[str, Any]) -> dict[str, Any]:
    inflow = float(asset_data.get("inflow_usd", 0))
    outflow = float(asset_data.get("outflow_usd", 0))
    netflow = float(asset_data.get("netflow_usd", 0))

    reconciliation = reconcile_flows(inflow, outflow, netflow)
    cluster = build_cluster_metadata(seed)
    direction = "inflow" if netflow > 0 else "outflow" if netflow < 0 else "neutral"

    return {
        "feature_id": _FEATURE_ID,
        "asset": asset_data.get("symbol", "BTC"),
        "netflow_usd": netflow,
        "netflow_display": format_usd(netflow, signed=True),
        "direction": direction,
        "reconciliation": reconciliation,
        "cluster": cluster,
        "chart": asset_data.get("netflow_chart") or [],
        "risk_context_only": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
    }


def build_netflow_dashboard(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("assets") or {}).get(sym)
    if not asset_data:
        return {"ok": False, "error": "asset_not_tracked", "asset": sym}
    card = build_netflow_card({**asset_data, "symbol": sym}, seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {"ok": True, "feature_id": _FEATURE_ID, "standalone": _STANDALONE, "tab": "netflow", **card, "latency_ms": elapsed}
