"""
Transfer Network Micro-Utility (#108 + #120).

Ranks best networks for asset transfers (speed + cost + security).
Widget appears on transfer/withdraw search — integrated with user network preference (#120).

NOT a full bridge product — honest comparison micro-utility with live gas where available.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from bd_platform.cross_chain_warehouse import CHAIN_SEMANTICS

logger = logging.getLogger("BLACKDARK.TransferNetworkUtility")

_PREFS_PATH = Path("data/user_transfer_network_prefs.json")
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 30.0

SecurityTier = Literal["stable", "standard", "experimental"]

# Transfer routes per asset — network_id, chain, token standard, base fee estimate
_TRANSFER_NETWORKS: dict[str, list[dict[str, Any]]] = {
    "USDT": [
        {"network_id": "trc20", "label": "TRON (TRC20)", "chain": "tron", "security": "stable", "eta_min": 2, "base_fee_usd": 1.0},
        {"network_id": "bep20", "label": "BNB Chain (BEP20)", "chain": "bsc", "security": "stable", "eta_min": 3, "base_fee_usd": 0.3},
        {"network_id": "arbitrum", "label": "Arbitrum One", "chain": "arbitrum", "security": "stable", "eta_min": 5, "base_fee_usd": 0.5},
        {"network_id": "polygon", "label": "Polygon PoS", "chain": "polygon", "security": "stable", "eta_min": 4, "base_fee_usd": 0.1},
        {"network_id": "solana", "label": "Solana (SPL)", "chain": "solana", "security": "stable", "eta_min": 1, "base_fee_usd": 0.01},
        {"network_id": "erc20", "label": "Ethereum (ERC20)", "chain": "ethereum", "security": "stable", "eta_min": 12, "base_fee_usd": 8.0},
        {"network_id": "optimism", "label": "Optimism", "chain": "optimism", "security": "standard", "eta_min": 6, "base_fee_usd": 0.4},
        {"network_id": "base", "label": "Base", "chain": "base", "security": "standard", "eta_min": 5, "base_fee_usd": 0.3},
        {"network_id": "avax", "label": "Avalanche C-Chain", "chain": "avalanche", "security": "standard", "eta_min": 4, "base_fee_usd": 0.2},
    ],
    "USDC": [
        {"network_id": "trc20", "label": "TRON (TRC20)", "chain": "tron", "security": "stable", "eta_min": 2, "base_fee_usd": 1.0},
        {"network_id": "bep20", "label": "BNB Chain (BEP20)", "chain": "bsc", "security": "stable", "eta_min": 3, "base_fee_usd": 0.3},
        {"network_id": "arbitrum", "label": "Arbitrum One", "chain": "arbitrum", "security": "stable", "eta_min": 5, "base_fee_usd": 0.5},
        {"network_id": "polygon", "label": "Polygon PoS", "chain": "polygon", "security": "stable", "eta_min": 4, "base_fee_usd": 0.1},
        {"network_id": "solana", "label": "Solana (SPL)", "chain": "solana", "security": "stable", "eta_min": 1, "base_fee_usd": 0.01},
        {"network_id": "erc20", "label": "Ethereum (ERC20)", "chain": "ethereum", "security": "stable", "eta_min": 12, "base_fee_usd": 8.0},
        {"network_id": "base", "label": "Base", "chain": "base", "security": "standard", "eta_min": 5, "base_fee_usd": 0.3},
    ],
    "ETH": [
        {"network_id": "arbitrum", "label": "Arbitrum One", "chain": "arbitrum", "security": "stable", "eta_min": 5, "base_fee_usd": 0.5},
        {"network_id": "optimism", "label": "Optimism", "chain": "optimism", "security": "standard", "eta_min": 6, "base_fee_usd": 0.4},
        {"network_id": "base", "label": "Base", "chain": "base", "security": "standard", "eta_min": 5, "base_fee_usd": 0.3},
        {"network_id": "ethereum", "label": "Ethereum Mainnet", "chain": "ethereum", "security": "stable", "eta_min": 12, "base_fee_usd": 5.0},
        {"network_id": "polygon", "label": "Polygon PoS", "chain": "polygon", "security": "stable", "eta_min": 4, "base_fee_usd": 0.1},
    ],
    "BTC": [
        {"network_id": "bitcoin", "label": "Bitcoin Native", "chain": "bitcoin", "security": "stable", "eta_min": 30, "base_fee_usd": 2.0},
        {"network_id": "bep20", "label": "BNB Chain (BTCB)", "chain": "bsc", "security": "standard", "eta_min": 3, "base_fee_usd": 0.3},
        {"network_id": "erc20", "label": "Ethereum (WBTC)", "chain": "ethereum", "security": "stable", "eta_min": 12, "base_fee_usd": 8.0},
        {"network_id": "arbitrum", "label": "Arbitrum (WBTC)", "chain": "arbitrum", "security": "stable", "eta_min": 5, "base_fee_usd": 0.5},
    ],
}

# Extend CHAIN_SEMANTICS for chains used in transfers
_CHAIN_META: dict[str, dict[str, Any]] = {
    **CHAIN_SEMANTICS,
    "base": {
        "chain_id": 8453,
        "native_symbol": "ETH",
        "block_time_sec": 2,
        "finality_blocks": 20,
    },
    "bitcoin": {
        "chain_id": "bitcoin",
        "native_symbol": "BTC",
        "block_time_sec": 600,
        "finality_blocks": 6,
    },
}

_TRANSFER_GAS_UNITS = {
    "ethereum": 65_000,
    "bsc": 50_000,
    "arbitrum": 80_000,
    "polygon": 60_000,
    "optimism": 80_000,
    "base": 80_000,
    "avalanche": 60_000,
    "solana": 5_000,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_prefs() -> dict[str, Any]:
    if not _PREFS_PATH.exists():
        return {"users": {}}
    try:
        return json.loads(_PREFS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"users": {}}


def _save_prefs(data: dict[str, Any]) -> None:
    _PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _utcnow()
    _PREFS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_user_network_preference(user_id: str, asset: str) -> dict[str, Any] | None:
    """#120 — user's saved transfer network for an asset."""
    data = _load_prefs()
    user = (data.get("users") or {}).get(user_id) or {}
    pref = (user.get("networks") or {}).get(asset.upper())
    if not pref:
        return None
    return pref


def set_user_network_preference(
    user_id: str,
    asset: str,
    network_id: str,
    *,
    source: str = "user_selected",
) -> dict[str, Any]:
    """#120 — persist user's chosen transfer network."""
    asset_u = asset.upper()
    networks = _TRANSFER_NETWORKS.get(asset_u, [])
    match = next((n for n in networks if n["network_id"] == network_id.lower()), None)
    if not match:
        return {"ok": False, "error": "unknown_network_for_asset", "asset": asset_u, "network_id": network_id}

    data = _load_prefs()
    users = data.setdefault("users", {})
    row = users.setdefault(user_id, {"networks": {}, "updated_at": _utcnow()})
    row["networks"][asset_u] = {
        "network_id": match["network_id"],
        "label": match["label"],
        "chain": match["chain"],
        "source": source,
        "saved_at": _utcnow(),
    }
    row["updated_at"] = _utcnow()
    _save_prefs(data)
    return {
        "ok": True,
        "feature": "#120",
        "user_id": user_id,
        "asset": asset_u,
        "network_used": row["networks"][asset_u],
        "timestamp": _utcnow(),
    }


async def _live_fee_usd(chain: str, *, base_fee: float) -> tuple[float, str]:
    """Refresh fee from gas oracle when chain supported."""
    if chain in {"tron", "bitcoin"}:
        return base_fee, "static_estimate"
    try:
        from gas_oracle import get_swap_gas_usd

        live = await get_swap_gas_usd(chain, hops=1)
        if live is not None and live > 0:
            # Transfer typically ~40% of swap gas
            return round(max(0.01, live * 0.4), 2), "gas_oracle_live"
    except Exception:
        logger.debug("gas oracle unavailable for %s", chain)
    return base_fee, "static_estimate"


def _speed_score(eta_min: float) -> int:
    return max(10, min(100, int(100 - eta_min * 4)))


def _cost_score(fee_usd: float, *, amount_usd: float) -> int:
    if amount_usd <= 0:
        amount_usd = 1000.0
    pct = (fee_usd / amount_usd) * 100
    return max(10, min(100, int(100 - pct * 50)))


def _security_score(tier: SecurityTier) -> int:
    return {"stable": 95, "standard": 75, "experimental": 45}[tier]


def _composite_score(*, speed: int, cost: int, security: int) -> float:
    return round(speed * 0.35 + cost * 0.40 + security * 0.25, 1)


def _security_label(tier: SecurityTier) -> str:
    return {
        "stable": "Stable network",
        "standard": "Standard L2",
        "experimental": "Experimental — higher risk",
    }[tier]


async def rank_transfer_networks(
    asset: str = "USDT",
    *,
    amount_usd: float = 1_000.0,
    user_id: str | None = None,
) -> dict[str, Any]:
    """#108 — rank networks for transfer with speed/cost/security."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")
    networks = _TRANSFER_NETWORKS.get(sym)
    if not networks:
        return {
            "ok": False,
            "feature": "#108",
            "error": "asset_not_supported",
            "supported_assets": list(_TRANSFER_NETWORKS.keys()),
            "timestamp": _utcnow(),
        }

    ranked: list[dict[str, Any]] = []
    for net in networks:
        fee, fee_source = await _live_fee_usd(net["chain"], base_fee=float(net["base_fee_usd"]))
        tier: SecurityTier = net["security"]
        speed = _speed_score(float(net["eta_min"]))
        cost = _cost_score(fee, amount_usd=amount_usd)
        security = _security_score(tier)
        composite = _composite_score(speed=speed, cost=cost, security=security)
        chain_meta = _CHAIN_META.get(net["chain"], {})
        ranked.append(
            {
                "network_id": net["network_id"],
                "label": net["label"],
                "chain": net["chain"],
                "fee_usd": fee,
                "fee_source": fee_source,
                "eta_minutes": net["eta_min"],
                "speed_score": speed,
                "cost_score": cost,
                "security_score": security,
                "security_tier": tier,
                "security_label": _security_label(tier),
                "composite_score": composite,
                "block_time_sec": chain_meta.get("block_time_sec"),
                "finality_blocks": chain_meta.get("finality_blocks"),
            }
        )

    ranked.sort(key=lambda r: r["composite_score"], reverse=True)
    fastest_id = max(ranked, key=lambda r: r["speed_score"])["network_id"]
    cheapest_id = min(ranked, key=lambda r: r["fee_usd"])["network_id"]
    for i, row in enumerate(ranked, start=1):
        row["rank"] = i
        row["badges"] = []
        if i == 1:
            row["badges"].append("recommended")
        if row["network_id"] == fastest_id:
            row["badges"].append("fastest")
        if row["network_id"] == cheapest_id:
            row["badges"].append("cheapest")

    best = ranked[0]
    alerts: list[dict[str, Any]] = []
    for row in ranked:
        if row["security_tier"] == "experimental":
            alerts.append(
                {
                    "level": "warning",
                    "network_id": row["network_id"],
                    "message": f"{row['label']} is experimental — use stable networks for large transfers",
                }
            )
        if row["fee_usd"] > 5.0 and amount_usd < 500:
            alerts.append(
                {
                    "level": "info",
                    "network_id": row["network_id"],
                    "message": f"{row['label']} fee (${row['fee_usd']:.2f}) high relative to transfer size",
                }
            )

    user_network_block: dict[str, Any] | None = None
    if user_id:
        pref = get_user_network_preference(user_id, sym)
        if pref:
            user_row = next((r for r in ranked if r["network_id"] == pref.get("network_id")), None)
            if user_row:
                savings = round(user_row["fee_usd"] - best["fee_usd"], 2)
                user_network_block = {
                    "feature": "#120",
                    "network_id": user_row["network_id"],
                    "label": user_row["label"],
                    "fee_usd": user_row["fee_usd"],
                    "rank": user_row["rank"],
                    "is_recommended": user_row["rank"] == 1,
                    "savings_vs_best_usd": savings if savings > 0 else 0,
                    "message": (
                        f"Your network ({user_row['label']}) is optimal"
                        if user_row["rank"] == 1
                        else f"Switch to {best['label']} to save ~${abs(savings):.2f} on fees"
                    ),
                }

    headline = (
        f"Best for {sym} transfer: {best['label']} — "
        f"${best['fee_usd']:.2f} fee, ~{best['eta_minutes']} min, {best['security_label'].lower()}"
    )

    elapsed = time.perf_counter() - t0
    result = {
        "ok": True,
        "feature": "#108",
        "surface": "transfer_network_widget",
        "asset": sym,
        "amount_usd": amount_usd,
        "recommendations": ranked,
        "best_network": best,
        "user_network": user_network_block,
        "alerts": alerts[:5],
        "headline": headline,
        "accuracy_note": "Fees from live gas oracle when available; static fallback otherwise",
        "supported_networks_count": len(ranked),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }

    cache_key = f"{sym}:{amount_usd}"
    _CACHE[cache_key] = (time.time(), result)
    return result


async def transfer_network_widget(
    asset: str = "USDT",
    *,
    amount_usd: float = 1_000.0,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Combined widget payload (#108 + #120) for transfer search UI."""
    cache_key = f"{asset.upper()}:{amount_usd}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL and not user_id:
        return {**cached[1], "cache_hit": True}

    row = await rank_transfer_networks(asset, amount_usd=amount_usd, user_id=user_id)
    if not row.get("ok"):
        return row

    return {
        **row,
        "widget": {
            "title": f"Best networks to send {row['asset']}",
            "columns": ["network", "fee", "speed", "security", "rank"],
            "show_user_network": bool(user_id),
            "integrated_features": ["#108", "#120"],
        },
        "reports": {
            "summary": row["headline"],
            "cheapest": min(row["recommendations"], key=lambda r: r["fee_usd"]),
            "fastest": max(row["recommendations"], key=lambda r: r["speed_score"]),
            "most_secure": max(row["recommendations"], key=lambda r: r["security_score"]),
        },
    }


def transfer_network_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature": "#108",
        "companion": "#120",
        "role": "micro_utility_widget",
        "supported_assets": list(_TRANSFER_NETWORKS.keys()),
        "total_routes": sum(len(v) for v in _TRANSFER_NETWORKS.values()),
        "sla_target_ms": 2000,
        "cache_ttl_sec": _CACHE_TTL,
        "timestamp": _utcnow(),
    }
