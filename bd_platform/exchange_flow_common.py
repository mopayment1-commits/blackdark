"""Shared exchange flow intelligence utilities — inflow/outflow/netflow reconciliation."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ExchangeFlowCommon")

_SEED_PATH = Path("data/exchange_intelligence_hub_seed.json")
_VARIANCE_ALERT_THRESHOLD = 0.001  # 0.1%


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "exchange_clusters": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("exchange intelligence seed load failed: %s", exc)
        return {"assets": {}, "exchange_clusters": {}}


def seed_path() -> Path:
    return _SEED_PATH


def format_usd(value: float, *, signed: bool = False) -> str:
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        text = f"${abs_val / 1_000_000_000:.2f}B"
    elif abs_val >= 1_000_000:
        text = f"${abs_val / 1_000_000:.0f}M"
    else:
        text = f"${abs_val:,.0f}"
    if signed and value < 0:
        return f"-{text}"
    if signed and value > 0:
        return f"+{text}"
    return text


def reconcile_flows(inflow_usd: float, outflow_usd: float, netflow_usd: float) -> dict[str, Any]:
    """Verify Inflow - Outflow = Netflow closure."""
    expected_net = inflow_usd - outflow_usd
    variance_usd = abs(netflow_usd - expected_net)
    base = max(abs(inflow_usd), abs(outflow_usd), 1.0)
    variance_pct = variance_usd / base
    reconciled = variance_pct <= _VARIANCE_ALERT_THRESHOLD

    return {
        "inflow_usd": inflow_usd,
        "outflow_usd": outflow_usd,
        "netflow_usd": netflow_usd,
        "expected_netflow_usd": round(expected_net, 2),
        "variance_usd": round(variance_usd, 2),
        "variance_pct": round(variance_pct * 100, 4),
        "reconciled": reconciled,
        "internal_alert": not reconciled,
        "closure_formula": "Inflow - Outflow = Netflow",
        "closure_display": (
            f"Inflow: {format_usd(inflow_usd)} | Outflow: {format_usd(outflow_usd)} | "
            f"Netflow: {format_usd(netflow_usd, signed=True)} | "
            f"Closure: Inflow - Outflow = Netflow | "
            f"Reconciled: {'Yes' if reconciled else 'No'} | "
            f"Variance: {format_usd(variance_usd)}"
        ),
        "netflow_display": (
            f"Netflow = Inflow - Outflow | Verified: {'Yes' if reconciled else 'No'} | "
            f"Last Reconciliation: {_utcnow()[:16].replace('T', ' ')}"
        ),
        "last_reconciliation": _utcnow(),
    }


def build_cluster_metadata(seed: dict[str, Any]) -> dict[str, Any]:
    """Versioned exchange cluster metadata."""
    clusters = seed.get("exchange_clusters") or {}
    version = seed.get("cluster_version", "4.2")
    last_updated = seed.get("cluster_last_updated", "2026-08-25")
    parts = []
    for name, cfg in clusters.items():
        count = cfg.get("address_count", 0)
        parts.append(f"{name.title()}: {count}")
    return {
        "version": version,
        "last_updated": last_updated,
        "exchanges": clusters,
        "display": (
            f"Exchange Cluster v{version} | "
            + " | ".join(parts)
            + f" | Last Updated: {last_updated}"
        ),
    }


def build_exchange_breakdown(breakdown: dict[str, Any], *, flow_key: str) -> dict[str, Any]:
    """Exchange breakdown — no total without per-exchange split."""
    entries = []
    total = 0.0
    for exchange, data in breakdown.items():
        amount = float(data.get(flow_key, 0))
        total += amount
    for exchange, data in breakdown.items():
        amount = float(data.get(flow_key, 0))
        pct = round(amount / total * 100, 1) if total else 0.0
        entries.append({
            "exchange": exchange,
            "amount_usd": amount,
            "pct": pct,
            "display": f"{exchange.title()}: {format_usd(amount)} ({pct}%)",
        })
    entries.sort(key=lambda e: -e["amount_usd"])
    parts = [e["display"] for e in entries]
    return {
        "entries": entries,
        "total_usd": total,
        "display": " | ".join(parts) + f" | Total: {format_usd(total)}",
    }


def build_chain_validation(chain_data: dict[str, Any]) -> dict[str, Any]:
    """Chain-specific validation display."""
    parts = []
    for chain, amounts in chain_data.items():
        for asset, amount in amounts.items():
            parts.append(f"{chain.title()}: {amount:,.2f} {asset.upper()}")
    return {
        "chains": chain_data,
        "display": " | ".join(parts) if parts else "Chain validation unavailable",
    }


def build_address_dedupe(dedupe: dict[str, Any]) -> dict[str, Any]:
    return {
        "unique_addresses_analyzed": dedupe.get("unique_addresses", 0),
        "internal_transfers_excluded": dedupe.get("internal_transfers_excluded", True),
        "display": (
            f"Unique addresses analyzed: {dedupe.get('unique_addresses', 0):,} | "
            f"Internal transfers excluded: "
            f"{'Yes' if dedupe.get('internal_transfers_excluded', True) else 'No'}"
        ),
    }
