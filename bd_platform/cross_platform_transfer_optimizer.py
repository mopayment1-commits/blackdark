"""
Cross-Platform Transfer Optimizer — Feature #119 (Sprint 2).

Fee-saving route optimizer across CEX platforms — NOT a profit or arbitrage tool.
Integrated with Transfer Network Utility (#108) and user network prefs (#120).

Example:
  "To move USDT from Binance to Kraken, the optimal path is:
   Binance → BEP20 → Bridge → ERC20 → Kraken. Cost: $2.5. Duration: 4 minutes."
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import Any

from bd_platform.transfer_network_utility import (
    _live_fee_usd,
    get_network_by_id,
    get_user_network_preference,
    rank_transfer_networks,
)

logger = logging.getLogger("BLACKDARK.TransferOptimizer")

_DISCLAIMER = (
    "Cross-Platform Transfer Optimizer suggests lowest-cost transfer routes based on "
    "public fee estimates and network rankings. BLACKDARK does not execute transfers, "
    "guarantee delivery times, or promise profit. Exchange withdrawal/deposit availability "
    "and bridge liquidity change frequently — verify on each platform before sending."
)

_CEX_DEPOSIT_NETWORKS: dict[str, dict[str, list[str]]] = {
    "binance": {
        "USDT": ["bep20", "trc20", "erc20", "arbitrum", "polygon", "solana", "optimism", "base"],
        "USDC": ["bep20", "trc20", "erc20", "arbitrum", "polygon", "solana", "base"],
        "ETH": ["ethereum", "arbitrum", "optimism", "base", "polygon"],
        "BTC": ["bitcoin", "bep20", "erc20", "arbitrum"],
    },
    "kraken": {
        "USDT": ["trc20", "erc20", "arbitrum"],
        "USDC": ["erc20", "arbitrum", "solana"],
        "ETH": ["ethereum", "arbitrum"],
        "BTC": ["bitcoin"],
    },
    "okx": {
        "USDT": ["trc20", "bep20", "erc20", "arbitrum", "polygon", "solana"],
        "USDC": ["bep20", "erc20", "arbitrum", "polygon", "solana"],
        "ETH": ["ethereum", "arbitrum", "optimism", "base"],
        "BTC": ["bitcoin", "bep20"],
    },
    "bybit": {
        "USDT": ["trc20", "bep20", "erc20", "arbitrum", "polygon", "solana"],
        "USDC": ["bep20", "erc20", "arbitrum", "solana"],
        "ETH": ["ethereum", "arbitrum", "optimism"],
        "BTC": ["bitcoin", "bep20"],
    },
    "coinbase": {
        "USDT": ["erc20", "solana", "base", "polygon"],
        "USDC": ["erc20", "solana", "base", "polygon"],
        "ETH": ["ethereum", "base", "optimism", "polygon"],
        "BTC": ["bitcoin"],
    },
}

_CEX_WITHDRAWAL_FEE_USD: dict[str, float] = {
    "binance": 0.0,
    "kraken": 0.0,
    "okx": 0.0,
    "bybit": 0.0,
    "coinbase": 0.0,
}

_BRIDGES: list[dict[str, Any]] = [
    {"from_network": "bep20", "to_network": "erc20", "label": "Bridge", "fee_usd": 1.5, "eta_min": 2},
    {"from_network": "bep20", "to_network": "arbitrum", "label": "Bridge", "fee_usd": 1.2, "eta_min": 2},
    {"from_network": "polygon", "to_network": "erc20", "label": "Bridge", "fee_usd": 1.8, "eta_min": 3},
    {"from_network": "arbitrum", "to_network": "erc20", "label": "Bridge", "fee_usd": 0.8, "eta_min": 1},
    {"from_network": "trc20", "to_network": "erc20", "label": "Bridge", "fee_usd": 2.0, "eta_min": 4},
    {"from_network": "solana", "to_network": "erc20", "label": "Bridge", "fee_usd": 2.5, "eta_min": 5},
    {"from_network": "bep20", "to_network": "trc20", "label": "Bridge", "fee_usd": 1.0, "eta_min": 3},
]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_cex(name: str) -> str:
    return name.strip().lower().replace(" ", "")


def _network_label(asset: str, network_id: str) -> str:
    net = get_network_by_id(asset, network_id)
    if net:
        return str(net.get("label") or network_id.upper())
    return network_id.upper()


async def _network_cost(asset: str, network_id: str, *, amount_usd: float, cache: dict[str, tuple[float, int]]) -> tuple[float, int]:
    key = f"{asset}:{network_id}:{amount_usd}"
    if key in cache:
        return cache[key]
    net = get_network_by_id(asset, network_id)
    if not net:
        cache[key] = (99.0, 60)
        return cache[key]
    fee, _ = await _live_fee_usd(net["chain"], base_fee=float(net["base_fee_usd"]))
    result = (fee, int(net["eta_min"]))
    cache[key] = result
    return result


def _path_steps(
    source_cex: str,
    dest_cex: str,
    asset: str,
    network_id: str,
) -> list[str]:
    label = _network_label(asset, network_id).split("(")[-1].replace(")", "").strip()
    if not label:
        label = network_id.upper()
    return [source_cex.title(), label, dest_cex.title()]


async def _evaluate_direct_path(
    source_cex: str,
    dest_cex: str,
    asset: str,
    network_id: str,
    *,
    amount_usd: float,
    cost_cache: dict[str, tuple[float, int]],
) -> dict[str, Any] | None:
    src_nets = set(_CEX_DEPOSIT_NETWORKS.get(source_cex, {}).get(asset, []))
    dst_nets = set(_CEX_DEPOSIT_NETWORKS.get(dest_cex, {}).get(asset, []))
    if network_id not in src_nets or network_id not in dst_nets:
        return None

    fee, eta = await _network_cost(asset, network_id, amount_usd=amount_usd, cache=cost_cache)
    withdraw_fee = _CEX_WITHDRAWAL_FEE_USD.get(source_cex, 0.0)
    total_cost = round(fee + withdraw_fee, 2)
    steps = _path_steps(source_cex, dest_cex, asset, network_id)
    return {
        "path_type": "direct",
        "network_id": network_id,
        "steps": steps,
        "step_labels": steps,
        "total_cost_usd": total_cost,
        "duration_min": eta,
        "bridge_hops": 0,
        "accuracy_estimate": 0.97,
    }


async def _evaluate_bridged_path(
    source_cex: str,
    dest_cex: str,
    asset: str,
    withdraw_net: str,
    deposit_net: str,
    bridge: dict[str, Any],
    *,
    amount_usd: float,
    cost_cache: dict[str, tuple[float, int]],
) -> dict[str, Any] | None:
    src_nets = set(_CEX_DEPOSIT_NETWORKS.get(source_cex, {}).get(asset, []))
    dst_nets = set(_CEX_DEPOSIT_NETWORKS.get(dest_cex, {}).get(asset, []))
    if withdraw_net not in src_nets or deposit_net not in dst_nets:
        return None
    if bridge["from_network"] != withdraw_net or bridge["to_network"] != deposit_net:
        return None

    w_fee, w_eta = await _network_cost(asset, withdraw_net, amount_usd=amount_usd, cache=cost_cache)
    d_fee, d_eta = await _network_cost(asset, deposit_net, amount_usd=amount_usd, cache=cost_cache)
    bridge_fee = float(bridge["fee_usd"])
    bridge_eta = int(bridge["eta_min"])
    withdraw_fee = _CEX_WITHDRAWAL_FEE_USD.get(source_cex, 0.0)
    total_cost = round(w_fee + bridge_fee + d_fee + withdraw_fee, 2)
    duration = w_eta + bridge_eta + d_eta

    w_label = _network_label(asset, withdraw_net).split("(")[-1].replace(")", "").strip() or withdraw_net.upper()
    d_label = _network_label(asset, deposit_net).split("(")[-1].replace(")", "").strip() or deposit_net.upper()
    steps = [source_cex.title(), w_label, bridge["label"], d_label, dest_cex.title()]

    return {
        "path_type": "bridged",
        "withdraw_network": withdraw_net,
        "deposit_network": deposit_net,
        "bridge": bridge["label"],
        "steps": steps,
        "step_labels": steps,
        "total_cost_usd": total_cost,
        "duration_min": duration,
        "bridge_hops": 1,
        "accuracy_estimate": 0.95,
    }


def _format_headline(
    asset: str,
    source_cex: str,
    dest_cex: str,
    path: dict[str, Any],
) -> str:
    arrow = " → ".join(path["steps"])
    return (
        f"To move {asset} from {source_cex.title()} to {dest_cex.title()}, "
        f"the optimal path is: {arrow}. "
        f"Cost: ${path['total_cost_usd']:.1f}. Duration: {path['duration_min']} minutes."
    )


async def optimize_cross_platform_transfer(
    *,
    asset: str = "USDT",
    source_cex: str = "binance",
    dest_cex: str = "kraken",
    amount_usd: float = 1_000.0,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Find lowest-cost transfer route between two CEX platforms."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")
    src = _normalize_cex(source_cex)
    dst = _normalize_cex(dest_cex)

    if src not in _CEX_DEPOSIT_NETWORKS or dst not in _CEX_DEPOSIT_NETWORKS:
        return {
            "ok": False,
            "feature": "#119",
            "error": "unsupported_cex",
            "supported_cex": sorted(_CEX_DEPOSIT_NETWORKS.keys()),
            "timestamp": _utcnow(),
        }
    if sym not in _CEX_DEPOSIT_NETWORKS[src]:
        return {
            "ok": False,
            "feature": "#119",
            "error": "asset_not_supported",
            "supported_assets": sorted(_CEX_DEPOSIT_NETWORKS[src].keys()),
            "timestamp": _utcnow(),
        }
    if src == dst:
        return {
            "ok": False,
            "feature": "#119",
            "error": "same_source_and_destination",
            "timestamp": _utcnow(),
        }

    candidates: list[dict[str, Any]] = []
    cost_cache: dict[str, tuple[float, int]] = {}
    common = set(_CEX_DEPOSIT_NETWORKS[src][sym]) & set(_CEX_DEPOSIT_NETWORKS[dst][sym])

    direct_tasks = [
        _evaluate_direct_path(src, dst, sym, net_id, amount_usd=amount_usd, cost_cache=cost_cache)
        for net_id in common
    ]
    bridge_tasks = [
        _evaluate_bridged_path(
            src,
            dst,
            sym,
            bridge["from_network"],
            bridge["to_network"],
            bridge,
            amount_usd=amount_usd,
            cost_cache=cost_cache,
        )
        for bridge in _BRIDGES
    ]
    evaluated = await asyncio.gather(*direct_tasks, *bridge_tasks)
    candidates = [p for p in evaluated if p is not None]

    if not candidates:
        return {
            "ok": False,
            "feature": "#119",
            "error": "no_route_found",
            "source_cex": src,
            "dest_cex": dst,
            "asset": sym,
            "timestamp": _utcnow(),
        }

    candidates.sort(key=lambda p: (p["total_cost_usd"], p["duration_min"]))
    best = candidates[0]
    alternatives = candidates[1:4]

    network_ranking = await rank_transfer_networks(sym, amount_usd=amount_usd, user_id=user_id)
    user_pref_block: dict[str, Any] | None = None
    if user_id:
        pref = get_user_network_preference(user_id, sym)
        if pref:
            pref_path = next(
                (c for c in candidates if c.get("network_id") == pref.get("network_id") or c.get("withdraw_network") == pref.get("network_id")),
                None,
            )
            user_pref_block = {
                "feature": "#120",
                "preferred_network": pref.get("network_id"),
                "label": pref.get("label"),
                "matches_optimal": pref_path == best if pref_path else False,
                "message": (
                    "Your saved network matches the optimal route"
                    if pref_path == best
                    else f"Optimal route may save fees vs your saved network ({pref.get('label')})"
                ),
            }

    elapsed = time.perf_counter() - t0
    headline = _format_headline(sym, src, dst, best)

    alerts: list[dict[str, Any]] = []
    if best["duration_min"] > 15:
        alerts.append({"level": "info", "message": "Route exceeds 15 minutes — consider faster network if urgency matters"})
    if best.get("bridge_hops", 0) > 0:
        alerts.append({"level": "warning", "message": "Route includes a bridge hop — verify bridge liquidity and limits"})

    return {
        "ok": True,
        "feature": "#119",
        "mode": "fee_saving_optimizer",
        "surface": "cross_platform_transfer",
        "integrated_features": ["#108", "#120"],
        "asset": sym,
        "source_cex": src,
        "dest_cex": dst,
        "amount_usd": amount_usd,
        "optimal_path": best,
        "headline": headline,
        "alternatives": alternatives,
        "network_ranking": {
            "best_network": network_ranking.get("best_network"),
            "recommendations_count": len(network_ranking.get("recommendations") or []),
        },
        "user_network": user_pref_block,
        "alerts": alerts,
        "reports": {
            "summary": headline,
            "cost_breakdown_usd": best["total_cost_usd"],
            "duration_min": best["duration_min"],
            "paths_evaluated": len(candidates),
        },
        "disclaimer": _DISCLAIMER,
        "accuracy_estimate": best.get("accuracy_estimate", 0.95),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


def transfer_optimizer_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature": "#119",
        "title": "Cross-Platform Transfer Optimizer",
        "integrated_features": ["#108", "#120"],
        "supported_cex": sorted(_CEX_DEPOSIT_NETWORKS.keys()),
        "supported_assets": sorted({a for nets in _CEX_DEPOSIT_NETWORKS.values() for a in nets}),
        "bridge_routes": len(_BRIDGES),
        "sla_target_ms": 2000,
        "mode": "fee_saving_optimizer",
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }
