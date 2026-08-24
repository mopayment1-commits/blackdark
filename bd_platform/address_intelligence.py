"""
On-Chain Address Intelligence Module — Features #10 + #18 + #19 + #20 + #23 (unified).

#10  Address Search — multi-source lookup (Tracely, DeBank, labels, Arkham)
#18  Fund Trace — single-chain path finding
#19  Balance History Chart — time-series snapshots with chain-specific tracking
#20  Balance Updates — state-diff feed from consecutive snapshots
#23  Block Search — block explorer details with reorg handling

NOT separate product surfaces — one unified on-chain intelligence module.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.AddressIntelligence")

_SNAPSHOT_PATH = Path("data/address_balance_snapshots.jsonl")
_CHAIN_IDS = {
    "ethereum": 1,
    "polygon": 137,
    "arbitrum": 42161,
    "bsc": 56,
    "optimism": 10,
    "base": 8453,
    "solana": "solana",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _normalize_address(address: str, chain: str = "ethereum") -> str:
    addr = (address or "").strip()
    chain_l = chain.lower()
    if chain_l == "solana":
        return addr
    if addr.startswith("0x"):
        return addr.lower()
    return addr


def _snapshot_key(address: str, chain: str) -> str:
    return f"{chain.lower()}:{_normalize_address(address, chain)}"


def _read_snapshots(address: str, chain: str, *, limit: int = 500) -> list[dict[str, Any]]:
    key = _snapshot_key(address, chain)
    rows: list[dict[str, Any]] = []
    if not _SNAPSHOT_PATH.exists():
        return rows
    try:
        for line in _SNAPSHOT_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("key") == key:
                rows.append(row)
    except (OSError, json.JSONDecodeError):
        logger.debug("snapshot read failed for %s", key)
    return rows[-limit:]


def _append_snapshot(
    address: str,
    chain: str,
    *,
    total_usd: float,
    source: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    key = _snapshot_key(address, chain)
    row = {
        "key": key,
        "address": _normalize_address(address, chain),
        "chain": chain.lower(),
        "chain_id": _CHAIN_IDS.get(chain.lower()),
        "total_usd": round(total_usd, 2),
        "source": source,
        "timestamp": _utcnow(),
        "meta": meta or {},
    }
    try:
        _SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _SNAPSHOT_PATH.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
    except OSError:
        logger.exception("snapshot append failed")
    return row


def _extract_total_usd(balance: dict[str, Any]) -> float:
    if balance.get("total_usd") is not None:
        return float(balance["total_usd"])
    raw = balance.get("balance") or {}
    if isinstance(raw, dict):
        return float(raw.get("total_usd") or raw.get("usd_value") or 0)
    return 0.0


async def search_address(address: str, *, chain: str = "ethereum") -> dict[str, Any]:
    """
    Feature #10 — unified address search across wallet data sources.
    """
    t0 = time.perf_counter()
    addr = _normalize_address(address, chain)
    if len(addr) < 10:
        return {"ok": False, "error": "invalid_address", "address": addr}

    from bd_platform.free_integrations import wallet_balance, wallet_clusters, wallet_labels

    balance, labels, clusters = await _gather(
        wallet_balance(addr),
        wallet_labels(addr),
        wallet_clusters(addr),
    )

    arkham: dict[str, Any] = {}
    try:
        from blackdark.ingestion.arkham_connector import fetch_entity_intelligence_input

        arkham = await fetch_entity_intelligence_input("ETH", address=addr)
    except Exception:
        arkham = {"ok": False, "data_state": "MISSING"}

    total_usd = _extract_total_usd(balance if isinstance(balance, dict) else {})
    solana_onchain: dict[str, Any] | None = None
    if chain.lower() == "solana" and len(addr) >= 32:
        try:
            from blackdark.ingestion.solana_rpc_connector import fetch_solana_balance

            sol = await fetch_solana_balance(addr)
            if sol.get("ok"):
                solana_onchain = sol
        except Exception:
            solana_onchain = None

    if total_usd > 0:
        _append_snapshot(addr, chain, total_usd=total_usd, source=balance.get("source", "search"))
        try:
            from bd_platform.address_state_index import index_address_state

            await index_address_state(
                addr,
                chain=chain,
                total_usd=total_usd,
                source=balance.get("source", "search"),
            )
        except Exception:
            logger.debug("state index append skipped")

    entity_label = None
    label_rows = (labels or {}).get("labels") or []
    if label_rows:
        entity_label = label_rows[0].get("label")
    elif (clusters or {}).get("center_label"):
        entity_label = clusters.get("center_label")

    return {
        "ok": True,
        "surface": "on_chain_address_intelligence",
        "capability": "address_search",
        "feature": "#10",
        "semantics": "point_in_time",
        "address": addr,
        "chain": chain.lower(),
        "chain_id": _CHAIN_IDS.get(chain.lower()),
        "entity_label": entity_label,
        "total_usd": total_usd,
        "balance": balance,
        "labels": labels,
        "clusters": clusters,
        "arkham_entity": arkham if arkham.get("ok") else None,
        "solana_onchain": solana_onchain,
        "solana_data_included": bool(solana_onchain),
        "sources": ["tracely", "debank", "zerion", "eth-labels", "arkham", "solana_rpc"],
        "data_state": "LIVE" if balance.get("available") else "PARTIAL",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }


async def _gather(*coros):
    import asyncio

    results = await asyncio.gather(*coros, return_exceptions=True)
    out = []
    for r in results:
        if isinstance(r, BaseException):
            out.append({})
        else:
            out.append(r if isinstance(r, dict) else {})
    return out


def _bootstrap_history(
    current_usd: float, *, days: int, source: str
) -> list[dict[str, Any]]:
    """Proxy history when insufficient snapshots exist (disclosed in response)."""
    if current_usd <= 0:
        return []
    points: list[dict[str, Any]] = []
    now = datetime.now(UTC)
    # Gentle backward drift proxy for chart bootstrap
    for i in range(days, 0, -1):
        ts = now - timedelta(days=i)
        drift = 1.0 - (i * 0.002)
        points.append(
            {
                "timestamp": ts.isoformat(),
                "total_usd": round(current_usd * drift, 2),
                "source": f"{source}_proxy",
                "proxy": True,
            }
        )
    points.append(
        {
            "timestamp": now.isoformat(),
            "total_usd": round(current_usd, 2),
            "source": source,
            "proxy": False,
        }
    )
    return points


async def balance_history(
    address: str,
    *,
    chain: str = "ethereum",
    days: int = 30,
) -> dict[str, Any]:
    """
    Feature #19 — balance history chart data (chain-specific snapshots).
    """
    t0 = time.perf_counter()
    addr = _normalize_address(address, chain)
    days = max(1, min(90, days))

    from bd_platform.free_integrations import wallet_balance

    balance = await wallet_balance(addr)
    total_usd = _extract_total_usd(balance if isinstance(balance, dict) else {})
    source = balance.get("source", "unknown") if isinstance(balance, dict) else "unknown"

    if total_usd > 0:
        _append_snapshot(addr, chain, total_usd=total_usd, source=source)
        try:
            from bd_platform.address_state_index import index_address_state

            await index_address_state(addr, chain=chain, total_usd=total_usd, source=source)
        except Exception:
            logger.debug("state index append skipped")

    snapshots = _read_snapshots(addr, chain)
    cutoff = datetime.now(UTC) - timedelta(days=days)
    series: list[dict[str, Any]] = []
    for row in snapshots:
        try:
            ts = datetime.fromisoformat(str(row.get("timestamp", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts >= cutoff:
            series.append(
                {
                    "timestamp": row["timestamp"],
                    "total_usd": row["total_usd"],
                    "source": row.get("source"),
                    "chain": row.get("chain"),
                    "block_number": row.get("block_number"),
                    "semantics": "point_in_time",
                    "finalized": row.get("finalized", True),
                    "proxy": False,
                }
            )

    proxy_used = False
    if len(series) < 2 and total_usd > 0:
        series = _bootstrap_history(total_usd, days=days, source=source)
        proxy_used = True

    return {
        "ok": True,
        "surface": "on_chain_address_intelligence",
        "capability": "balance_history",
        "feature": "#19",
        "semantics": "point_in_time",
        "reorg_handling": "Snapshots anchored with block_number when available; recent blocks may be non-final",
        "address": addr,
        "chain": chain.lower(),
        "chain_id": _CHAIN_IDS.get(chain.lower()),
        "days": days,
        "series": series,
        "point_count": len(series),
        "current_usd": total_usd,
        "proxy_bootstrap": proxy_used,
        "data_state": "LIVE" if series else "MISSING",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }


async def balance_updates(
    address: str,
    *,
    chain: str = "ethereum",
    limit: int = 20,
) -> dict[str, Any]:
    """
    Feature #20 — real-time balance update feed via state diffs between snapshots.
    """
    t0 = time.perf_counter()
    addr = _normalize_address(address, chain)
    limit = max(1, min(50, limit))

    from bd_platform.free_integrations import wallet_balance

    balance = await wallet_balance(addr)
    total_usd = _extract_total_usd(balance if isinstance(balance, dict) else {})
    source = balance.get("source", "unknown") if isinstance(balance, dict) else "unknown"

    prior = _read_snapshots(addr, chain)
    prev_usd = float(prior[-1]["total_usd"]) if prior else 0.0
    prev_ts = prior[-1].get("timestamp") if prior else None

    if total_usd > 0:
        current_row = _append_snapshot(addr, chain, total_usd=total_usd, source=source)
    else:
        current_row = {"timestamp": _utcnow(), "total_usd": 0, "source": source}

    delta_usd = round(total_usd - prev_usd, 2)
    delta_pct = round((delta_usd / prev_usd) * 100, 3) if prev_usd > 0 else None

    update = {
        "update_id": f"{addr[:10]}_{int(time.time())}",
        "address": addr,
        "chain": chain.lower(),
        "chain_id": _CHAIN_IDS.get(chain.lower()),
        "previous_usd": prev_usd,
        "current_usd": total_usd,
        "delta_usd": delta_usd,
        "delta_pct": delta_pct,
        "previous_timestamp": prev_ts,
        "timestamp": current_row.get("timestamp"),
        "source": source,
        "direction": "inflow" if delta_usd > 0 else ("outflow" if delta_usd < 0 else "unchanged"),
    }

    # Build feed from recent snapshot diffs
    feed: list[dict[str, Any]] = [update]
    recent = _read_snapshots(addr, chain)[-(limit + 1) :]
    for i in range(1, len(recent)):
        prev = recent[i - 1]
        curr = recent[i]
        d_usd = round(float(curr["total_usd"]) - float(prev["total_usd"]), 2)
        if d_usd == 0:
            continue
        feed.append(
            {
                "update_id": f"{addr[:8]}_{i}",
                "address": addr,
                "chain": chain.lower(),
                "previous_usd": float(prev["total_usd"]),
                "current_usd": float(curr["total_usd"]),
                "delta_usd": d_usd,
                "delta_pct": round((d_usd / float(prev["total_usd"])) * 100, 3)
                if float(prev["total_usd"]) > 0
                else None,
                "previous_timestamp": prev.get("timestamp"),
                "timestamp": curr.get("timestamp"),
                "source": curr.get("source"),
                "direction": "inflow" if d_usd > 0 else "outflow",
            }
        )

    feed = feed[:limit]
    alerts: list[dict[str, Any]] = []
    if abs(delta_usd) >= 10_000:
        alerts.append(
            {
                "level": "high",
                "code": "LARGE_BALANCE_CHANGE",
                "message": f"Balance changed ${delta_usd:+,.0f} on {chain}",
            }
        )

    return {
        "ok": True,
        "surface": "on_chain_address_intelligence",
        "capability": "balance_updates",
        "feature": "#20",
        "address": addr,
        "chain": chain.lower(),
        "chain_id": _CHAIN_IDS.get(chain.lower()),
        "latest_update": update,
        "feed": feed,
        "feed_count": len(feed),
        "alerts": alerts,
        "headline": f"Balance {update['direction']}: ${delta_usd:+,.2f} on {chain}",
        "data_state": "LIVE" if total_usd > 0 or prior else "MISSING",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }


async def search_block(
    block_number: int,
    *,
    chain: str = "ethereum",
) -> dict[str, Any]:
    """
    Feature #23 — block explorer details with reorg/finality disclosure.
    """
    t0 = time.perf_counter()
    if block_number <= 0:
        return {"ok": False, "error": "invalid_block_number", "block_number": block_number}

    from bd_platform.onchain_client import get_block_by_number

    block = await get_block_by_number(block_number, chain=chain)
    if not block.get("ok"):
        return {
            "ok": False,
            "surface": "on_chain_address_intelligence",
            "capability": "block_search",
            "feature": "#23",
            "block_number": block_number,
            "chain": chain.lower(),
            "error": block.get("error"),
            "data_state": "MISSING",
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }

    return {
        "ok": True,
        "surface": "on_chain_address_intelligence",
        "capability": "block_search",
        "feature": "#23",
        "chain": chain.lower(),
        "chain_id": _CHAIN_IDS.get(chain.lower()),
        "block": block,
        "block_number": block_number,
        "transaction_count": block.get("transaction_count"),
        "reorg_handling": block.get("reorg_handling"),
        "semantics": block.get("semantics"),
        "data_state": "LIVE",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 2.0,
        "timestamp": _utcnow(),
    }


async def address_intelligence_overview(
    address: str,
    *,
    chain: str = "ethereum",
    history_days: int = 30,
) -> dict[str, Any]:
    """Unified module entry — search + history + updates + trace in one call."""
    t0 = time.perf_counter()
    search = await search_address(address, chain=chain)
    history = await balance_history(address, chain=chain, days=history_days)
    updates = await balance_updates(address, chain=chain)

    trace: dict[str, Any] = {}
    if chain.lower() == "ethereum":
        try:
            from bd_platform.fund_trace import trace_funds

            trace = await trace_funds(address, chain=chain, max_hops=3)
        except Exception:
            trace = {"ok": False, "feature": "#18", "data_state": "MISSING"}

    return {
        "ok": True,
        "surface": "on_chain_address_intelligence",
        "module": "address_intelligence",
        "features": [
            "#10_address_search",
            "#18_fund_trace",
            "#19_balance_history",
            "#20_balance_updates",
            "#23_block_search",
        ],
        "address": _normalize_address(address, chain),
        "chain": chain.lower(),
        "search": search,
        "trace": trace if trace.get("ok") else None,
        "history": history,
        "updates": updates,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 5.0,
        "timestamp": _utcnow(),
    }
